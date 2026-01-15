from datetime import datetime

import click
import cv2
from loguru import logger

from pisky.camera import GRID_COLS, GRID_ROWS, TILE_SIZE, Camera, list_cameras
from pisky.database import Database
from pisky.detector import BirdDetector
from pisky.paths import (
    MODEL_URL,
    get_data_dir,
    get_database_path,
    get_images_dir,
    get_model_path,
)


@click.group()
@click.version_option()
def cli() -> None:
    """Pi in the Sky - Bird detection from webcam."""
    pass


@cli.command("info")
def info_cmd() -> None:
    """Show configuration and paths."""
    model_path = get_model_path()
    model_status = "downloaded" if model_path.exists() else "not downloaded"

    click.echo("Pi in the Sky configuration:")
    click.echo(f"  Data directory: {get_data_dir()}")
    click.echo(f"  Images:         {get_images_dir()}")
    click.echo(f"  Database:       {get_database_path()}")
    click.echo(f"  Model:          {model_path} ({model_status})")
    click.echo(f"  Model source:   {MODEL_URL}")


@cli.command("list")
def list_cmd() -> None:
    """List available cameras."""
    cameras = list_cameras()
    if cameras:
        click.echo("Available cameras:")
        for index, name in cameras:
            click.echo(f"  {index}: {name}")
    else:
        click.echo("No cameras found")


@cli.command("shoot")
@click.option("--keep-all", is_flag=True, help="Keep all images even if no birds detected")
@click.option("--camera", "camera_index", type=int, default=0, help="Camera index (default: 0)")
def shoot_cmd(keep_all: bool, camera_index: int) -> int | None:
    """Capture image and detect birds. Returns photograph_id if saved."""
    images_dir = get_images_dir()
    images_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")

    detector = BirdDetector()
    logger.info("Bird detector loaded")

    with Camera(camera_index) as cam, Database() as db:
        image, tiles = cam.capture_tiles()
        if image is not None:
            image_filename = f"{timestamp}.jpg"
            image_path = images_dir / image_filename

            # Run detection on each tile, collect results
            all_detections = []
            for i, tile in enumerate(tiles):
                detections = detector.detect(tile)
                if detections or keep_all:
                    tile_path = images_dir / f"{timestamp}_{i:02d}.jpg"
                    cv2.imwrite(str(tile_path), tile)
                for det in detections:
                    logger.info(f"Tile {i:02d}: bird detected (confidence: {det.confidence:.2f})")
                    all_detections.append((i, det.confidence))

            # Save image and log to database if we have detections or keep_all
            if all_detections or keep_all:
                cv2.imwrite(str(image_path), image)
                photograph_id = db.log_photograph(now, image_filename, keep_all)
                for tile_index, confidence in all_detections:
                    db.log_detection(photograph_id, tile_index, confidence)
                logger.info(f"Saved {image_filename} with {len(all_detections)} detection(s)")
                return photograph_id
            else:
                logger.info("No birds detected")
                return None
        else:
            logger.error("Could not capture frame")
            return None


@cli.command("test")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--debug", is_flag=True, help="Show all detected classes, not just birds")
def test_cmd(image_path: str, debug: bool) -> None:
    """Test detection on an image file without saving to database."""
    image = cv2.imread(image_path)
    if image is None:
        click.echo(f"Error: Could not read {image_path}")
        return

    click.echo(f"Image size: {image.shape[1]}x{image.shape[0]}")

    # Tile the image
    h, w = image.shape[:2]
    crop_w = TILE_SIZE * GRID_COLS
    crop_h = TILE_SIZE * GRID_ROWS

    if w < crop_w or h < crop_h:
        scale = max(crop_w / w, crop_h / h)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
        h, w = image.shape[:2]

    x_offset = (w - crop_w) // 2
    y_offset = (h - crop_h) // 2
    cropped = image[y_offset : y_offset + crop_h, x_offset : x_offset + crop_w]

    tiles = []
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            tile = cropped[y : y + TILE_SIZE, x : x + TILE_SIZE]
            tiles.append(tile)

    click.echo(f"Cropped to: {cropped.shape[1]}x{cropped.shape[0]}, {len(tiles)} tiles")

    detector = BirdDetector()
    click.echo("Running detection...")

    total = 0
    for i, tile in enumerate(tiles):
        if debug:
            all_detections = detector.detect_all(tile, min_confidence=0.1)
            if all_detections:
                click.echo(f"  Tile {i:02d}: {all_detections}")

        detections = detector.detect(tile, min_confidence=0)
        for det in detections:
            marker = "✓" if det.confidence >= 0.33 else " "
            click.echo(f"  {marker} Tile {i:02d}: bird (confidence: {det.confidence:.2f})")
            if det.confidence >= 0.33:
                total += 1

    click.echo(f"Total: {total} detection(s) above threshold")


@cli.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", default=8000, type=int, help="Port to bind to (default: 8000)")
def serve_cmd(host: str, port: int) -> None:
    """Start the API server."""
    from pisky.server import run_server

    click.echo(f"Starting server at http://{host}:{port}")
    run_server(host=host, port=port)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
