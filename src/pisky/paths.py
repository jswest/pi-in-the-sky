import io
import os
import zipfile
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Model source - SSD MobileNet V1 quantized, trained on COCO
MODEL_URL = "https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"
MODEL_FILENAME = "detect.tflite"


def get_data_dir() -> Path:
    """Get the data directory for models, images, and database.

    Uses PISKY_DATA_DIR environment variable if set,
    otherwise defaults to ~/.pisky.
    """
    env_dir = os.environ.get("PISKY_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("/home") / "john" / ".pisky"


def get_model_path() -> Path:
    """Get path to the TFLite model file."""
    return get_data_dir() / "models" / MODEL_FILENAME


def ensure_model_downloaded() -> Path:
    """Ensure the model is downloaded, downloading if necessary."""
    model_path = get_model_path()

    if model_path.exists():
        return model_path

    logger.info(f"Model not found at {model_path}")
    logger.info(f"Downloading from {MODEL_URL}")

    model_path.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(MODEL_URL) as response:
        zip_data = io.BytesIO(response.read())

    with zipfile.ZipFile(zip_data) as zf:
        for name in zf.namelist():
            if name == MODEL_FILENAME:
                model_path.write_bytes(zf.read(name))
                break

    logger.info(f"Model saved to {model_path}")
    return model_path


def get_images_dir() -> Path:
    """Get path to the images directory."""
    return get_data_dir() / "images"


def get_database_path() -> Path:
    """Get path to the SQLite database."""
    return get_data_dir() / "detections.db"
