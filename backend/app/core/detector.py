import torch
from ultralytics import YOLO


class VehicleDetector:
    def __init__(self, model_path="models/best.pt", confidence=0.40, min_box_area=380):
        # Store model path
        self.model_path = model_path

        # Minimum confidence required for detection
        # (0.40 trims the low-confidence far-field clutter that caused
        #  flickering detections and ID inflation)
        self.confidence = confidence

        # Drop very small boxes (tiny far-away blobs). These are the main
        # source of unstable tracks / ID switching. Tune if needed.
        self.min_box_area = min_box_area

        # Load YOLO model
        self.model = YOLO(self.model_path)

        # Use GPU if available, otherwise fall back to CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        # Classes allowed in our traffic system
        self.allowed_classes = {
            "accident",
            "bus",
            "car",
            "motorcycle",
            "truck",
        }

    def detect(self, frame):
        # Run YOLO detection on frame
        results = self.model(
            frame,
            conf=self.confidence,
            imgsz=640,
            device=self.device,
            half=(self.device == "cuda"),  # FP16 is much faster on the T4 GPU
            verbose=False,
        )[0]

        # Store clean detection results
        detections = []

        for box in results.boxes:
            # Get class ID from YOLO result
            class_id = int(box.cls[0])

            # Convert class ID to class name
            class_name = self.model.names[class_id]

            # Ignore non-traffic classes
            if class_name not in self.allowed_classes:
                continue

            # Get confidence score
            confidence = float(box.conf[0])

            # Get bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Skip tiny far-field detections (reduces ID switching)
            # Accidents are always kept regardless of size.
            area = (x2 - x1) * (y2 - y1)
            if class_name != "accident" and area < self.min_box_area:
                continue

            # Save detection
            detections.append(
                {
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                }
            )

        return detections


if __name__ == "__main__":
    detector = VehicleDetector()
    print("Detector loaded successfully")
