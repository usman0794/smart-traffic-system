from app.database.models import (
    Video,
    VehicleEvent,
    TrafficSnapshot,
    AccidentEvent,
)


# =====================================================
# VIDEO OPERATIONS
# =====================================================

def create_video(
    db,
    filename,
    source_type="upload",
    status="pending",
    model_used="best.pt"
):
    """
    Create new video record.
    """

    video = Video(
        filename=filename,
        source_type=source_type,
        status=status,
        model_used=model_used,
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    return video


def update_video_status(
    db,
    video_id,
    status,
    output_path=None,
):
    """
    Update video processing status.
    """

    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        return None

    video.status = status

    if output_path:
        video.output_path = output_path

    db.commit()
    db.refresh(video)

    return video


# =====================================================
# VEHICLE EVENTS
# =====================================================

def save_vehicle_event(
    db,
    video_id,
    track_id,
    vehicle_type,
    direction,
    confidence=None,
):
    """
    Save vehicle crossing event.
    """

    event = VehicleEvent(
        video_id=video_id,
        track_id=str(track_id),
        vehicle_type=vehicle_type,
        direction=direction,
        confidence=confidence,
    )

    db.add(event)
    db.commit()

    return event


# =====================================================
# SNAPSHOTS
# =====================================================

def save_snapshot(
    db,
    video_id,
    total_count,
    incoming_count,
    outgoing_count,
    active_vehicles,
    class_counts,
    density_level,
    fps,
):
    """
    Save periodic traffic analytics snapshot.
    """

    snapshot = TrafficSnapshot(
        video_id=video_id,
        total_count=total_count,
        incoming_count=incoming_count,
        outgoing_count=outgoing_count,
        total_active_vehicles=active_vehicles,
        car_count=class_counts.get("car", 0),
        bus_count=class_counts.get("bus", 0),
        truck_count=class_counts.get("truck", 0),
        motorcycle_count=class_counts.get("motorcycle", 0),
        density_level=density_level,
        fps=fps,
    )

    db.add(snapshot)
    db.commit()

    return snapshot


# =====================================================
# ACCIDENT EVENTS
# =====================================================

def save_accident_event(
    db,
    video_id,
    track_id,
    confidence,
    frame_number,
    bbox,
):
    """
    Save accident detection event.
    """

    accident = AccidentEvent(
        video_id=video_id,
        track_id=str(track_id),
        confidence=confidence,
        frame_number=frame_number,
        bbox=str(bbox),
    )

    db.add(accident)
    db.commit()

    return accident