from app.database.db import engine, Base

# Import models so SQLAlchemy knows them
from app.database.models import (
    Video,
    VehicleEvent,
    TrafficSnapshot,
    AccidentEvent,
)


def create_tables():
    """
    Create all database tables.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


if __name__ == "__main__":
    create_tables()