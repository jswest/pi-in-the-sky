"""Pi in the Sky - Bird detection for Raspberry Pi."""

__version__ = "0.1.0"

from pisky.camera import Camera, list_cameras
from pisky.database import Database
from pisky.detector import BirdDetector, Detection

__all__ = ["Camera", "list_cameras", "Database", "BirdDetector", "Detection"]
