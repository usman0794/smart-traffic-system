from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Load environment variables
load_dotenv()

# Get database URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing in .env")

# Create database engine
#
# Neon (free tier) auto-suspends compute after a few minutes idle and closes
# idle connections. Without these settings the app reuses a dead connection
# and crashes with "server closed the connection unexpectedly".
#
#   pool_pre_ping  -> test each connection before using it; reconnect if dead
#   pool_recycle   -> drop connections older than 5 min (before Neon kills them)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=2,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
