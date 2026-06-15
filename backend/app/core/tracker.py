from deep_sort_realtime.deepsort_tracker import DeepSort


class VehicleTracker:
    def __init__(self):
        # Optimized DeepSORT settings for faster CPU processing
        self.tracker = DeepSort(
            max_age=15,           # Keep track for fewer frames if detection is missed
            n_init=1,             # Confirm track after 1 detection for speed
            max_iou_distance=0.7  # Matching threshold
        )

    def update(self, detections, frame=None):
        # Convert YOLO detections into DeepSORT format
        deepsort_detections = []

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]

            # DeepSORT format: [x, y, width, height]
            width = x2 - x1
            height = y2 - y1

            deepsort_detections.append(
                (
                    [x1, y1, width, height],
                    det["confidence"],
                    det["class_name"]
                )
            )

        # Update tracker
        tracks = self.tracker.update_tracks(
            deepsort_detections,
            frame=frame
        )

        tracked_objects = []

        for track in tracks:
            # Skip weak/unconfirmed tracks
            if not track.is_confirmed():
                continue

            # Unique ID assigned by DeepSORT
            track_id = track.track_id

            # Bounding box: left, top, right, bottom
            ltrb = track.to_ltrb()

            tracked_objects.append({
                "track_id": track_id,
                "bbox": [int(x) for x in ltrb],
                "class_name": track.get_det_class()
            })

        return tracked_objects


if __name__ == "__main__":
    tracker = VehicleTracker()
    print("Tracker loaded successfully")