from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Video, VehicleEvent, TrafficSnapshot, AccidentEvent

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_latest_video_id(db: Session):
    latest_video = db.query(Video).order_by(Video.id.desc()).first()
    return latest_video.id if latest_video else None


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    video_id = get_latest_video_id(db)

    if video_id is None:
        return {
            "total_vehicles": 0,
            "incoming": 0,
            "outgoing": 0,
            "cars": 0,
            "trucks": 0,
            "buses": 0,
            "motorcycles": 0,
            "accidents": 0,
            "current_density": "Low",
        }

    total_vehicles = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id).count()
    incoming = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.direction == "incoming").count()
    outgoing = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.direction == "outgoing").count()
    cars = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "car").count()
    trucks = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "truck").count()
    buses = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "bus").count()
    motorcycles = db.query(VehicleEvent).filter(VehicleEvent.video_id == video_id, VehicleEvent.vehicle_type == "motorcycle").count()
    accidents = db.query(AccidentEvent).filter(AccidentEvent.video_id == video_id).count()

    latest_snapshot = db.query(TrafficSnapshot).filter(
        TrafficSnapshot.video_id == video_id
    ).order_by(TrafficSnapshot.timestamp.desc()).first()

    return {
        "video_id": video_id,
        "total_vehicles": total_vehicles,
        "incoming": incoming,
        "outgoing": outgoing,
        "cars": cars,
        "trucks": trucks,
        "buses": buses,
        "motorcycles": motorcycles,
        "accidents": accidents,
        "current_density": latest_snapshot.density_level if latest_snapshot else "Low",
    }


@router.get("/snapshots")
def get_snapshots(db: Session = Depends(get_db)):
    video_id = get_latest_video_id(db)

    if video_id is None:
        return []

    snapshots = db.query(TrafficSnapshot).filter(
        TrafficSnapshot.video_id == video_id
    ).order_by(TrafficSnapshot.timestamp.desc()).limit(50).all()

    return [
        {
            "id": s.id,
            "video_id": s.video_id,
            "timestamp": s.timestamp,
            "total_count": s.total_count,
            "incoming_count": s.incoming_count,
            "outgoing_count": s.outgoing_count,
            "active_vehicles": s.total_active_vehicles,
            "car_count": s.car_count,
            "bus_count": s.bus_count,
            "truck_count": s.truck_count,
            "motorcycle_count": s.motorcycle_count,
            "density_level": s.density_level,
            "fps": s.fps,
        }
        for s in snapshots
    ]


@router.get("/vehicle-events")
def get_vehicle_events(db: Session = Depends(get_db)):
    video_id = get_latest_video_id(db)

    if video_id is None:
        return []

    events = db.query(VehicleEvent).filter(
        VehicleEvent.video_id == video_id
    ).order_by(VehicleEvent.crossing_time.desc()).limit(100).all()

    return [
        {
            "id": e.id,
            "video_id": e.video_id,
            "track_id": e.track_id,
            "vehicle_type": e.vehicle_type,
            "direction": e.direction,
            "confidence": e.confidence,
            "crossing_time": e.crossing_time,
        }
        for e in events
    ]


@router.get("/recent-events")
def get_recent_events(db: Session = Depends(get_db)):
    video_id = get_latest_video_id(db)

    if video_id is None:
        return []

    events = db.query(VehicleEvent).filter(
        VehicleEvent.video_id == video_id
    ).order_by(VehicleEvent.crossing_time.desc()).limit(10).all()

    return [
        {
            "id": e.id,
            "video_id": e.video_id,
            "track_id": e.track_id,
            "vehicle_type": e.vehicle_type,
            "direction": e.direction,
            "confidence": e.confidence,
            "crossing_time": e.crossing_time,
        }
        for e in events
    ]


@router.get("/accidents")
def get_accidents(db: Session = Depends(get_db)):
    video_id = get_latest_video_id(db)

    if video_id is None:
        return []

    accidents = db.query(AccidentEvent).filter(
        AccidentEvent.video_id == video_id
    ).order_by(AccidentEvent.timestamp.desc()).limit(50).all()

    return [
        {
            "id": a.id,
            "video_id": a.video_id,
            "track_id": a.track_id,
            "confidence": a.confidence,
            "frame_number": a.frame_number,
            "bbox": a.bbox,
            "timestamp": a.timestamp,
        }
        for a in accidents
    ]