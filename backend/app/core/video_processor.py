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


class VideoProcessor:
    def __init__(
        self,
        model_path="models/best.pt",
        input_video="videos/test.mp4",
        output_video="outputs/output.mp4",
    ):
        # Custom YOLO model path
        self.model_path = model_path

        # Input and output video paths
        self.input_video = input_video
        self.output_video = output_video

        # Core CV modules
        self.detector = VehicleDetector(model_path=self.model_path)
        self.tracker = VehicleTracker()
        self.density = TrafficDensity()

        # Speed optimization settings
        # Process every 5th frame only
        self.frame_skip = 5

        # Resize video frame before YOLO inference
        self.resize_width = 640

    def process(self):
        # Fresh counter for every new uploaded video
        counter = VehicleCounter(line_position_ratio=0.6)

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
                line_y = count_result["line_y"]
                cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2)

                # Draw tracked objects
                for obj in tracked_objects:
                    track_id = obj["track_id"]
                    x1, y1, x2, y2 = obj["bbox"]
                    class_name = obj.get("class_name", "vehicle")

                    # Red box for accidents, green box for vehicles
                    box_color = (0, 0, 255) if class_name == "accident" else (0, 255, 0)

                    # Save accident event to database
                    if class_name == "accident":
                        save_accident_event(
                            db=db,
                            video_id=video_id,
                            track_id=track_id,
                            confidence=1.0,
                            frame_number=frame_id,
                            bbox=[x1, y1, x2, y2],
                        )

                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                    # Draw label with class and tracking ID
                    label = f"{class_name} ID:{track_id}"
                    cv2.putText(
                        frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        box_color,
                        2,
                    )

                # Calculate processing FPS
                elapsed_time = time.time() - start_time
                processing_fps = frame_id / elapsed_time if elapsed_time > 0 else 0

                # Get vehicle class counts
                class_counts = count_result["class_counts"]

                # Save traffic snapshot every 100 frames
                if frame_id % 100 == 0:
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

                # Overlay settings
                y = 40
                gap = 35

                overlay_items = [
                    f"Total: {count_result['total_count']}",
                    f"Incoming: {count_result['incoming_count']}",
                    f"Outgoing: {count_result['outgoing_count']}",
                    f"Cars: {class_counts['car']}",
                    f"Trucks: {class_counts['truck']}",
                    f"Buses: {class_counts['bus']}",
                    f"Motorcycles: {class_counts['motorcycle']}",
                    f"Density: {density_level}",
                    f"FPS: {processing_fps:.2f}",
                ]

                # Draw overlay text
                for item in overlay_items:
                    cv2.putText(
                        frame,
                        item,
                        (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2,
                    )
                    y += gap

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


if __name__ == "__main__":
    processor = VideoProcessor(
        model_path="models/best.pt",
        input_video="videos/test.mp4",
        output_video="outputs/output.mp4",
    )

    processor.process()
