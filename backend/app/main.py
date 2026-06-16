from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.analytics import router as analytics_router
from app.api.videos import router as videos_router
from app.database.db import engine, Base

from app.database import models
from app.api import reports


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Traffic Intelligence System",
    description="YOLO11 + DeepSORT traffic analytics backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(analytics_router)
app.include_router(videos_router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "message": "Smart Traffic Intelligence System API is running"
    }