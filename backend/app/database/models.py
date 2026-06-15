from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.db import Base


class Video(Base):
    __tablename__ = "videos"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Original uploaded video filename
    filename = Column(String, nullable=False)

    # Source type: upload / webcam / rtsp / youtube
    source_type = Column(String, default="upload")

    # Status: pending / processing / completed / failed
    status = Column(String, default="pending")

    # Path of processed output video
    output_path = Column(String, nullable=True)

    # Model used: yolo11n.pt / best.pt
    model_used = Column(String, nullable=True)

    # Upload time
    created_at = Column(DateTime, default=datetime.utcnow)

    # Processing completion time
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    vehicle_events = relationship("VehicleEvent", back_populates="video")
    traffic_snapshots = relationship("TrafficSnapshot", back_populates="video")
    accident_events = relationship("AccidentEvent", back_populates="video")


class VehicleEvent(Base):
    __tablename__ = "vehicle_events"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to videos table
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # DeepSORT track ID
    track_id = Column(String, nullable=False)

    # Vehicle type: car / bus / truck / motorcycle
    vehicle_type = Column(String, nullable=False)

    # Direction: incoming / outgoing
    direction = Column(String, nullable=False)

    # Detection confidence score
    confidence = Column(Float, nullable=True)

    # Time when vehicle crossed count line
    crossing_time = Column(DateTime, default=datetime.utcnow)

    # Relationship
    video = relationship("Video", back_populates="vehicle_events")


class TrafficSnapshot(Base):
    __tablename__ = "traffic_snapshots"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to videos table
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # Snapshot timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Total counted vehicles
    total_count = Column(Integer, default=0)

    # Incoming vehicles count
    incoming_count = Column(Integer, default=0)

    # Outgoing vehicles count
    outgoing_count = Column(Integer, default=0)

    # Vehicles visible in current frame
    total_active_vehicles = Column(Integer, default=0)

    # Running vehicle type counts
    car_count = Column(Integer, default=0)
    bus_count = Column(Integer, default=0)
    truck_count = Column(Integer, default=0)
    motorcycle_count = Column(Integer, default=0)

    # Low / Medium / High
    density_level = Column(String, nullable=True)

    # Processing FPS
    fps = Column(Float, nullable=True)

    # Relationship
    video = relationship("Video", back_populates="traffic_snapshots")


class AccidentEvent(Base):
    __tablename__ = "accident_events"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to videos table
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # DeepSORT track ID if available
    track_id = Column(String, nullable=True)

    # Accident confidence score
    confidence = Column(Float, nullable=True)

    # Frame number where accident was detected
    frame_number = Column(Integer, nullable=True)

    # Bounding box saved as text/json string
    bbox = Column(Text, nullable=True)

    # Detection timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    video = relationship("Video", back_populates="accident_events")