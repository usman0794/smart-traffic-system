import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.video_processor import VideoProcessor

router = APIRouter(prefix="/videos", tags=["Videos"])

UPLOAD_DIR = Path("videos")
OUTPUT_DIR = Path("outputs")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@router.post("/upload")
def upload_video(file: UploadFile = File(...)):
    if not file.filename.endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(
            status_code=400,
            detail="Only video files are allowed"
        )

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Video uploaded successfully",
        "filename": file.filename,
        "path": str(file_path)
    }


@router.post("/process/{filename}")
def process_video(filename: str):
    input_path = UPLOAD_DIR / filename

    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    output_path = OUTPUT_DIR / f"processed_{filename}"

    processor = VideoProcessor(
        model_path="models/best.pt",
        input_video=str(input_path),
        output_video=str(output_path),
    )

    processor.process()

    return {
        "message": "Video processed successfully",
        "input_video": str(input_path),
        "output_video": str(output_path)
    }