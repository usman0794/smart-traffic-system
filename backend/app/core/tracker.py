import torch
from deep_sort_realtime.deepsort_tracker import DeepSort


class VehicleTracker:
    """
    DeepSORT wrapper tuned to KEEP THE SAME ID on a vehicle for longer.

    The far-field / crowded area caused tracks to die and re-spawn with new
    IDs (ID switching -> over-counting). The settings below favour track
    continuity:
      * max_age large  -> a vehicle can be 'missed' for many frames and still
                          keep its ID when it reappears.
      * n_init slightly higher -> a track must be seen a few times before it is
                          confirmed, killing flickering false tracks.
      * appearance (cosine) matching + nn_budget -> re-attach the same car by
                          how it looks, not just position.
    """

    def __init__(self):
        # Run the appearance embedder on GPU when available
        use_gpu = torch.cuda.is_available()

        self.tracker = DeepSort(
            max_age=45,               # was 15 -> keep lost tracks ~3x longer
            n_init=3,                 # confirm after 3 hits (fewer ghost IDs)
            max_iou_distance=0.7,     # motion/position gating
            max_cosine_distance=0.3,  # appearance gating (re-id same car)
            nn_budget=100,            # remember up to 100 appearance samples
            embedder_gpu=use_gpu,     # run the appearance model on the GPU
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
                    det["class_name"],
                )
            )

        # Update tracker
        tracks = self.tracker.update_tracks(
            deepsort_detections,
            frame=frame,
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

            tracked_objects.append(
                {
                    "track_id": track_id,
                    "bbox": [int(x) for x in ltrb],
                    "class_name": track.get_det_class(),
                }
            )

        return tracked_objects


if __name__ == "__main__":
    tracker = VehicleTracker()
    print("Tracker loaded successfully")
