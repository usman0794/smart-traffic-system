import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

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
def process_video(filename: str, road_mode: str = "two_way"):
    input_path = UPLOAD_DIR / filename

    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    output_name = f"processed_{filename}"
    output_path = OUTPUT_DIR / output_name

    processor = VideoProcessor(
        model_path="models/best.pt",
        input_video=str(input_path),
        output_video=str(output_path),
        road_mode=road_mode,
    )

    processor.process()

    return {
        "message": "Video processed successfully",
        "input_video": str(input_path),
        "output_video": str(output_path),
        "download_name": output_name
    }


@router.get("/stream/{filename}")
def stream_video(filename: str, road_mode: str = "two_way"):
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
        road_mode=road_mode,
    )

    return StreamingResponse(
        processor.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/download/{filename}")
def download_video(filename: str):
    # Serve a processed output video as a file download
    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed video not found"
        )

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename,
    )
