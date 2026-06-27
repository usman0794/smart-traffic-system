import cv2
import time
from pathlib import Path

from app.core.detector import VehicleDetector
from app.core.tracker import VehicleTracker
from app.core.counter import VehicleCounter
from app.core.density import TrafficDensity

from app.database.db import SessionLocal
from app.database.crud import (
    create_video,
    update_video_status,
    save_vehicle_event,
    save_snapshot,
    save_accident_event,
)


# ---------------------------------------------------------------------------
# Professional overlay styling
# ---------------------------------------------------------------------------
# Colors are BGR (OpenCV order). One distinct color per vehicle class so the
# boxes are readable at a glance.
CLASS_COLORS = {
    "car": (76, 175, 80),         # green
    "truck": (0, 152, 255),       # orange
    "bus": (255, 152, 0),         # blue
    "motorcycle": (200, 70, 220), # purple
    "accident": (60, 60, 255),    # red
}
DEFAULT_COLOR = (76, 175, 80)
WHITE = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX


class VideoProcessor:
    def __init__(
        self,
        model_path="models/best.pt",
        input_video="videos/test.mp4",
        output_video="outputs/output.mp4",
        road_mode="two_way",
    ):
        # Custom YOLO model path
        self.model_path = model_path

        # Input and output video paths
        self.input_video = input_video
        self.output_video = output_video
        self.road_mode = road_mode

        # Core CV modules
        self.detector = VehicleDetector(model_path=self.model_path)
        self.tracker = VehicleTracker()
        self.density = TrafficDensity()

        # Speed optimization settings
        # Process frame only
        self.frame_skip = 1

        # Resize video frame before YOLO inference
        self.resize_width = 640

        # Hide the ID label on boxes shorter than this many pixels.
        # (Stops the unreadable label "smear" in the crowded far field.)
        self.min_label_height = 22

    # ------------------------------------------------------------------
    # Drawing helpers (shared by saved video + live stream)
    # ------------------------------------------------------------------
    @staticmethod
    def _class_color(class_name):
        return CLASS_COLORS.get(class_name, DEFAULT_COLOR)

    @staticmethod
    def _density_color(level):
        return {
            "Low": (76, 175, 80),
            "Medium": (0, 200, 255),
            "High": (60, 60, 255),
        }.get(level, WHITE)

    def _draw_box(self, frame, x1, y1, x2, y2, label, color, draw_label=True):
        """Draw a clean bounding box with an optional filled label chip."""
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

        if not draw_label or not label:
            return

        scale = 0.5
        thick = 1
        (tw, th), _ = cv2.getTextSize(label, FONT, scale, thick)

        # Label chip sits just above the box (or just below if no room on top)
        chip_h = th + 8
        if y1 - chip_h >= 0:
            top = y1 - chip_h
            bottom = y1
        else:
            top = y1
            bottom = y1 + chip_h

        right = min(x1 + tw + 10, frame.shape[1])
        cv2.rectangle(frame, (x1, top), (right, bottom), color, -1, cv2.LINE_AA)
        cv2.putText(
            frame,
            label,
            (x1 + 5, bottom - 5),
            FONT,
            scale,
            WHITE,
            thick,
            cv2.LINE_AA,
        )

    def _draw_stats_panel(self, frame, lines):
        """Draw a translucent panel (top-left) with colored stat lines.

        `lines` is a list of (text, color) tuples.
        """
        scale = 0.6
        thick = 1
        pad = 12
        line_h = 26

        max_w = 0
        for text, _ in lines:
            (tw, _th), _ = cv2.getTextSize(text, FONT, scale, thick)
            max_w = max(max_w, tw)

        box_w = max_w + pad * 2
        box_h = line_h * len(lines) + pad

        # Translucent dark background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (10 + box_w, 10 + box_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

        y = 10 + pad + 12
        for text, color in lines:
            cv2.putText(frame, text, (10 + pad, y), FONT, scale, color, thick, cv2.LINE_AA)
            y += line_h

    def _draw_count_line(self, frame, line_y, width):
        cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2, cv2.LINE_AA)

    def _build_panel(self, count_result, class_counts, density_level, processing_fps):
        return [
            (f"Total: {count_result['total_count']}", WHITE),
            (f"Incoming: {count_result['incoming_count']}", WHITE),
            (f"Outgoing: {count_result['outgoing_count']}", WHITE),
            (f"Cars: {class_counts['car']}", CLASS_COLORS["car"]),
            (f"Trucks: {class_counts['truck']}", CLASS_COLORS["truck"]),
            (f"Buses: {class_counts['bus']}", CLASS_COLORS["bus"]),
            (f"Motorcycles: {class_counts['motorcycle']}", CLASS_COLORS["motorcycle"]),
            (f"Density: {density_level}", self._density_color(density_level)),
            (f"FPS: {processing_fps:.2f}", WHITE),
        ]

    # ------------------------------------------------------------------
    # Saved-video processing
    # ------------------------------------------------------------------
    def process(self):
        # Fresh counter for every new uploaded video
        counter = VehicleCounter(
            line_position_ratio=0.6,
            road_mode=self.road_mode
        )

        # Open input video
        cap = cv2.VideoCapture(self.input_video)

        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open video: {self.input_video}")

        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Create output directory if missing
        Path(self.output_video).parent.mkdir(parents=True, exist_ok=True)

        # Output video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(self.output_video, fourcc, fps, (width, height))

        # Counters and timers
        frame_id = 0
        start_time = time.time()

        # Store latest processed results for skipped frames
        last_tracked_objects = []
        last_count_result = None
        last_density_level = "Low"

        # Database session
        db = SessionLocal()
        video_id = None

        try:
            # Create video record in database
            video = create_video(
                db=db,
                filename=Path(self.input_video).name,
                source_type="upload",
                status="processing",
                model_used=Path(self.model_path).name,
            )
            video_id = video.id
            print(f"Video Record Created: {video_id}")

            # Save each accident track only once
            saved_accident_ids = set()

            while True:
                # Read next frame
                ret, frame = cap.read()

                # Stop when video ends
                if not ret:
                    break

                frame_id += 1

                # Only run YOLO + DeepSORT every N frames for speed
                if frame_id % self.frame_skip == 0:
                    # Resize frame while keeping aspect ratio
                    resize_height = int(height * (self.resize_width / width))
                    small_frame = cv2.resize(frame, (self.resize_width, resize_height))

                    # Detect on resized frame
                    detections = self.detector.detect(small_frame)

                    # Scale boxes back to original frame size
                    scale_x = width / self.resize_width
                    scale_y = height / resize_height

                    for det in detections:
                        x1, y1, x2, y2 = det["bbox"]
                        det["bbox"] = [
                            int(x1 * scale_x),
                            int(y1 * scale_y),
                            int(x2 * scale_x),
                            int(y2 * scale_y),
                        ]

                    # Track objects using DeepSORT
                    tracked_objects = self.tracker.update(detections, frame=frame)

                    # Update counting logic
                    count_result = counter.update(tracked_objects, height)

                    # Save vehicle crossing events to database
                    for event in count_result["crossing_events"]:
                        save_vehicle_event(
                            db=db,
                            video_id=video_id,
                            track_id=event["track_id"],
                            vehicle_type=event["vehicle_type"],
                            direction=event["direction"],
                            confidence=None,
                        )

                    # Calculate active vehicles and density
                    active_vehicles = len(tracked_objects)
                    density_level = self.density.calculate(active_vehicles)

                    # Save latest values for skipped frames
                    last_tracked_objects = tracked_objects
                    last_count_result = count_result
                    last_density_level = density_level

                else:
                    # Reuse last processed values for skipped frames
                    tracked_objects = last_tracked_objects
                    count_result = last_count_result
                    density_level = last_density_level
                    active_vehicles = len(tracked_objects)

                # If no processed frame yet, just write original frame
                if count_result is None:
                    writer.write(frame)
                    continue

                # Draw count line
                self._draw_count_line(frame, count_result["line_y"], width)

                # Draw tracked objects (color-coded by class)
                for obj in tracked_objects:
                    track_id = obj["track_id"]
                    x1, y1, x2, y2 = obj["bbox"]
                    class_name = obj.get("class_name", "vehicle")

                    color = self._class_color(class_name)

                    # Save accident event to database
                    if class_name == "accident" and track_id not in saved_accident_ids:
                        save_accident_event(
                            db=db,
                            video_id=video_id,
                            track_id=track_id,
                            confidence=1.0,
                            frame_number=frame_id,
                            bbox=[x1, y1, x2, y2],
                        )

                        saved_accident_ids.add(track_id)

                    # Hide label on tiny far-field boxes to avoid the smear
                    draw_label = (y2 - y1) >= self.min_label_height
                    label = f"{class_name} #{track_id}"
                    self._draw_box(frame, x1, y1, x2, y2, label, color, draw_label)

                # Calculate processing FPS
                elapsed_time = time.time() - start_time
                processing_fps = frame_id / elapsed_time if elapsed_time > 0 else 0

                # Get vehicle class counts
                class_counts = count_result["class_counts"]

                # Save traffic snapshot every 200 frames
                if frame_id % 200 == 0:
                    save_snapshot(
                        db=db,
                        video_id=video_id,
                        total_count=count_result["total_count"],
                        incoming_count=count_result["incoming_count"],
                        outgoing_count=count_result["outgoing_count"],
                        active_vehicles=active_vehicles,
                        class_counts=class_counts,
                        density_level=density_level,
                        fps=processing_fps,
                    )
                    print(f"Snapshot Saved @ Frame {frame_id}")

                # Professional stats panel
                panel = self._build_panel(
                    count_result, class_counts, density_level, processing_fps
                )
                self._draw_stats_panel(frame, panel)

                # Save processed frame
                writer.write(frame)

                # Terminal progress every 50 frames
                if frame_id % 50 == 0:
                    print(
                        f"Frame: {frame_id} | "
                        f"Total: {count_result['total_count']} | "
                        f"Incoming: {count_result['incoming_count']} | "
                        f"Outgoing: {count_result['outgoing_count']} | "
                        f"Active: {active_vehicles} | "
                        f"Density: {density_level} | "
                        f"FPS: {processing_fps:.2f}"
                    )

            # Mark video as completed in database
            update_video_status(
                db=db,
                video_id=video_id,
                status="completed",
                output_path=self.output_video,
            )

            print("Processing completed")
            print(f"Output saved at: {self.output_video}")

        except Exception as error:
            # Mark video as failed if any error happens
            if video_id is not None:
                update_video_status(
                    db=db,
                    video_id=video_id,
                    status="failed",
                    output_path=self.output_video,
                )

            print(f"Processing failed: {error}")
            raise

        finally:
            # Always release video resources and close DB session
            cap.release()
            writer.release()
            db.close()

    # ------------------------------------------------------------------
    # Live MJPEG stream
    # ------------------------------------------------------------------
    def generate_frames(self, stream_width=960, jpeg_quality=75, show_every=1):
        """
        BALANCED real-time live MJPEG generator.

          * stream_width=960 + jpeg_quality=75 -> sharp enough, still small.
          * Full overlay (color-coded boxes + stats panel), like the saved video.
          * NO database writes inside the loop -> Neon latency never stalls a
            frame. (The 'Process Video' button still saves everything.)
          * Generator stops cleanly when the browser disconnects.

        Tune from the endpoint, e.g.:
          generate_frames(stream_width=1280, jpeg_quality=85)  # higher quality
          generate_frames(stream_width=640, jpeg_quality=60, show_every=2)  # faster
        """
        # Fresh counter for every new stream
        counter = VehicleCounter(
            line_position_ratio=0.6,
            road_mode=self.road_mode,
        )

        # Open input video
        cap = cv2.VideoCapture(self.input_video)

        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open video: {self.input_video}")

        # Original size -> compute stream size (keep aspect ratio)
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if orig_w == 0:
            orig_w = stream_width
        stream_height = int(orig_h * (stream_width / orig_w)) or stream_width

        # JPEG encode params (quality vs size tradeoff)
        jpeg_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

        # Counters and timers
        frame_id = 0
        start_time = time.time()

        # Store latest processed results for skipped frames
        last_tracked_objects = []
        last_count_result = None
        last_density_level = "Low"

        try:
            while True:
                # Read next frame
                ret, frame = cap.read()

                # Stop when video ends
                if not ret:
                    break

                frame_id += 1

                # Downscale once -> all work below is on the small frame
                frame = cv2.resize(frame, (stream_width, stream_height))

                # Run YOLO + DeepSORT every N frames; reuse results otherwise
                if frame_id % self.frame_skip == 0:
                    detections = self.detector.detect(frame)

                    tracked_objects = self.tracker.update(detections, frame=frame)
                    count_result = counter.update(tracked_objects, stream_height)

                    active_vehicles = len(tracked_objects)
                    density_level = self.density.calculate(active_vehicles)

                    last_tracked_objects = tracked_objects
                    last_count_result = count_result
                    last_density_level = density_level

                else:
                    tracked_objects = last_tracked_objects
                    count_result = last_count_result
                    density_level = last_density_level
                    active_vehicles = len(tracked_objects)

                # Optional frame dropping to stay live
                if show_every > 1 and frame_id % show_every != 0:
                    continue

                # If nothing processed yet, stream the raw small frame
                if count_result is None:
                    ok, buffer = cv2.imencode(".jpg", frame, jpeg_params)
                    if ok:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + buffer.tobytes()
                            + b"\r\n"
                        )
                    continue

                # Draw count line
                self._draw_count_line(frame, count_result["line_y"], stream_width)

                # Draw tracked objects (color-coded by class)
                for obj in tracked_objects:
                    track_id = obj["track_id"]
                    x1, y1, x2, y2 = obj["bbox"]
                    class_name = obj.get("class_name", "vehicle")

                    color = self._class_color(class_name)
                    draw_label = (y2 - y1) >= self.min_label_height
                    label = f"{class_name} #{track_id}"
                    self._draw_box(frame, x1, y1, x2, y2, label, color, draw_label)

                # Live FPS
                elapsed_time = time.time() - start_time
                processing_fps = frame_id / elapsed_time if elapsed_time > 0 else 0

                class_counts = count_result["class_counts"]

                # Professional stats panel (same info as the saved video)
                panel = self._build_panel(
                    count_result, class_counts, density_level, processing_fps
                )
                self._draw_stats_panel(frame, panel)

                # Encode and yield
                ok, buffer = cv2.imencode(".jpg", frame, jpeg_params)
                if not ok:
                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + buffer.tobytes()
                    + b"\r\n"
                )

        except GeneratorExit:
            # Browser disconnected / stopped watching -> stop immediately
            print("Live viewer disconnected - stopping stream")

        finally:
            # No DB session in live mode -> just release the capture
            cap.release()
            print("Live stream released")


if __name__ == "__main__":
    processor = VideoProcessor(
        model_path="models/best.pt",
        input_video="videos/test.mp4",
        output_video="outputs/output.mp4",
    )

    processor.process()
