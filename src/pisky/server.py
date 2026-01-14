import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pisky.database import Database
from pisky.paths import get_images_dir


class PhotographSummary(BaseModel):
    photograph_id: int
    captured_at: str
    image_path: str
    keep_all: bool
    detection_count: int


class Detection(BaseModel):
    tile_index: int
    confidence: float
    tile_url: str


class PhotographDetail(BaseModel):
    photograph_id: int
    captured_at: str
    image_url: str
    keep_all: bool
    detections: list[Detection]


class Stats(BaseModel):
    total_photographs: int
    total_detections: int


class ShootResponse(BaseModel):
    photograph_id: int | None
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to do
    yield
    # Shutdown: nothing to do


app = FastAPI(
    title="Pi in the Sky API",
    description="Bird detection API for Raspberry Pi",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/photographs", response_model=list[PhotographSummary])
def list_photographs(limit: int = 50):
    """List recent photographs with detection counts."""
    with Database() as db:
        rows = db.get_recent_photographs(limit)
    return [
        PhotographSummary(
            photograph_id=row["photograph_id"],
            captured_at=row["captured_at"],
            image_path=row["image_path"],
            keep_all=bool(row["keep_all"]),
            detection_count=row["detection_count"],
        )
        for row in rows
    ]


@app.get("/api/photographs/{photograph_id}", response_model=PhotographDetail)
def get_photograph(photograph_id: int):
    """Get a photograph with its detections."""
    with Database() as db:
        photo = db.get_photograph(photograph_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photograph not found")

    # Build tile URLs from image path
    base_name = photo["image_path"].rsplit(".", 1)[0]
    detections = [
        Detection(
            tile_index=d["tile_index"],
            confidence=d["confidence"],
            tile_url=f"/images/{base_name}_{d['tile_index']:02d}.jpg",
        )
        for d in photo["detections"]
    ]

    return PhotographDetail(
        photograph_id=photo["photograph_id"],
        captured_at=photo["captured_at"],
        image_url=f"/images/{photo['image_path']}",
        keep_all=bool(photo["keep_all"]),
        detections=detections,
    )


@app.get("/api/stats", response_model=Stats)
def get_stats():
    """Get summary statistics."""
    with Database() as db:
        stats = db.get_stats()
    return Stats(**stats)


@app.post("/api/shoot", response_model=ShootResponse)
def trigger_shoot():
    """Trigger a capture with --keep-all flag."""
    result = subprocess.run(
        [sys.executable, "-m", "pisky.cli", "shoot", "--keep-all"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return ShootResponse(
            photograph_id=None,
            message=f"Capture failed: {result.stderr}",
        )

    # Try to get the most recent photograph
    with Database() as db:
        recent = db.get_recent_photographs(limit=1)
        if recent:
            return ShootResponse(
                photograph_id=recent[0]["photograph_id"],
                message="Capture complete",
            )
        return ShootResponse(
            photograph_id=None,
            message="Capture complete but no photograph saved",
        )


@app.get("/images/{filename}")
def serve_image(filename: str):
    """Serve an image from the images directory."""
    images_dir = get_images_dir()
    image_path = images_dir / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Prevent path traversal
    if not image_path.resolve().is_relative_to(images_dir.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(image_path, media_type="image/jpeg")


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the FastAPI server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)
