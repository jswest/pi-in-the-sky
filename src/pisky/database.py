import sqlite3
from datetime import datetime
from pathlib import Path

from pisky.paths import get_database_path


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path if db_path is not None else get_database_path()
        self.conn: sqlite3.Connection | None = None

    def open(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                photographed_at TEXT NOT NULL,
                tile_index INTEGER NOT NULL,
                confidence REAL NOT NULL,
                image_path TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def log_detection(
        self,
        timestamp: datetime,
        tile_index: int,
        confidence: float,
        image_path: str,
    ) -> None:
        if self.conn is None:
            raise RuntimeError("Database not open")
        self.conn.execute(
            "INSERT INTO detections (photographed_at, tile_index, confidence, image_path) VALUES (?, ?, ?, ?)",
            (timestamp.isoformat(), tile_index, confidence, image_path),
        )
        self.conn.commit()

    def __enter__(self) -> "Database":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
