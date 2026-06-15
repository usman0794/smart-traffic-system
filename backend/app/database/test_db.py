from app.database.db import SessionLocal
from app.database.crud import (
    create_video,
    save_vehicle_event,
    save_snapshot,
    save_accident_event,
)


def test_database():
    db = SessionLocal()

    try:
        # Create test video
        video = create_video(
            db=db,
            filename="test.mp4",
            source_type="upload",
            status="completed",
            model_used="best.pt"
        )

        print(f"Video Created: {video.id}")

        # Vehicle event
        save_vehicle_event(
            db=db,
            video_id=video.id,
            track_id=1,
            vehicle_type="car",
            direction="incoming",
            confidence=0.95,
        )

        print("Vehicle Event Saved")

        # Snapshot
        save_snapshot(
            db=db,
            video_id=video.id,
            total_count=10,
            incoming_count=7,
            outgoing_count=3,
            active_vehicles=5,
            class_counts={
                "car": 6,
                "bus": 1,
                "truck": 2,
                "motorcycle": 1,
            },
            density_level="Medium",
            fps=5.4,
        )

        print("Traffic Snapshot Saved")

        # Accident event
        save_accident_event(
            db=db,
            video_id=video.id,
            track_id=99,
            confidence=0.92,
            frame_number=100,
            bbox=[100, 100, 300, 300],
        )

        print("Accident Event Saved")

        print("Database Test Successful")

    finally:
        db.close()


if __name__ == "__main__":
    test_database()