import sys
from pathlib import Path

import cv2
from numpy import ndarray

TILE_SIZE = 300
GRID_COLS = 6
GRID_ROWS = 3


def list_cameras(max_index: int = 10) -> list[tuple[int, str]]:
    """Return list of (index, name) for available cameras."""
    cameras = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Try to get camera name on Linux
            name = "Unknown"
            sysfs_path = Path(f"/sys/class/video4linux/video{i}/name")
            if sysfs_path.exists():
                name = sysfs_path.read_text().strip()
            elif sys.platform == "darwin":
                name = f"Camera {i}"
            cameras.append((i, name))
            cap.release()
    return cameras


class Camera:
    def __init__(self, index: int = 0) -> None:
        self.index = index
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.index)
        return self.cap.isOpened()

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def capture(self) -> ndarray | None:
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def capture_tiles(self) -> tuple[ndarray | None, list[ndarray]]:
        """Capture a frame and return the cropped image and 300x300 tiles."""
        frame = self.capture()
        if frame is None:
            return None, []

        # Crop to 1800x900 (centered)
        h, w = frame.shape[:2]
        crop_w = TILE_SIZE * GRID_COLS
        crop_h = TILE_SIZE * GRID_ROWS
        x_offset = (w - crop_w) // 2
        y_offset = (h - crop_h) // 2
        cropped = frame[y_offset : y_offset + crop_h, x_offset : x_offset + crop_w]

        # Split into tiles
        tiles = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                tile = cropped[y : y + TILE_SIZE, x : x + TILE_SIZE]
                tiles.append(tile)

        return cropped, tiles

    def __enter__(self) -> "Camera":
        if not self.open():
            raise RuntimeError(f"Could not open camera at index {self.index}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
