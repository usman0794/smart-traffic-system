from ultralytics import YOLO


class VehicleDetector:
    def __init__(self, model_path="models/best.pt", confidence=0.35):
        # Store model path
        self.model_path = model_path

        # Minimum confidence required for detection
        self.confidence = confidence

        # Load YOLO model
        self.model = YOLO(self.model_path)

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
            verbose=False
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

            # Save detection
            detections.append({
                "class_name": class_name,
                "confidence": confidence,
                "bbox": [int(x1), int(y1), int(x2), int(y2)]
            })

        return detections


if __name__ == "__main__":
    detector = VehicleDetector()
    print("Detector loaded successfully")