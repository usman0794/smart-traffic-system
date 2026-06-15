class VehicleCounter:
    def __init__(self, line_position_ratio=0.6):
        # IDs of vehicles already counted
        self.counted_ids = set()

        # Total vehicle count
        self.total_count = 0

        # Direction-wise counting
        self.direction_counts = {
            "incoming": 0,  # top to bottom
            "outgoing": 0,  # bottom to top
        }

        # Vehicle type counting
        self.class_counts = {
            "bus": 0,
            "car": 0,
            "motorcycle": 0,
            "truck": 0,
        }

        # Store previous center point of each tracked vehicle
        self.previous_centers = {}

        # Count line position, e.g. 0.6 = 60% height
        self.line_position_ratio = line_position_ratio

    def get_center(self, bbox):
        # Bounding box format: [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox

        # Calculate center point
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        return center_x, center_y

    def update(self, tracked_objects, frame_height):
        # Convert ratio to actual y-coordinate
        line_y = int(frame_height * self.line_position_ratio)

        # Store crossing events
        crossing_events = []

        for obj in tracked_objects:
            track_id = obj["track_id"]
            bbox = obj["bbox"]
            class_name = obj.get("class_name", "unknown")

            # Skip accident for vehicle counting
            if class_name == "accident":
                continue

            # Current center point
            center_x, center_y = self.get_center(bbox)

            # Check previous center exists
            if track_id in self.previous_centers:
                prev_x, prev_y = self.previous_centers[track_id]

                # Vehicle moves top to bottom
                crossed_down = prev_y < line_y <= center_y

                # Vehicle moves bottom to top
                crossed_up = prev_y > line_y >= center_y

                # Count only once
                if track_id not in self.counted_ids and (crossed_down or crossed_up):
                    direction = "incoming" if crossed_down else "outgoing"

                    # Mark as counted
                    self.counted_ids.add(track_id)

                    # Increase total count
                    self.total_count += 1

                    # Increase direction count
                    self.direction_counts[direction] += 1

                    # Increase vehicle class count
                    if class_name in self.class_counts:
                        self.class_counts[class_name] += 1

                    # Save event
                    crossing_events.append({
                        "track_id": track_id,
                        "vehicle_type": class_name,
                        "direction": direction,
                    })

            # Save current center for next frame
            self.previous_centers[track_id] = (center_x, center_y)

        return {
            "line_y": line_y,
            "total_count": self.total_count,
            "incoming_count": self.direction_counts["incoming"],
            "outgoing_count": self.direction_counts["outgoing"],
            "class_counts": self.class_counts,
            "direction_counts": self.direction_counts,
            "crossing_events": crossing_events,
        }


if __name__ == "__main__":
    counter = VehicleCounter()
    print("Counter loaded successfully")