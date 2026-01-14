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
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS photographs (
                photograph_id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                image_path TEXT NOT NULL,
                keep_all INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                photograph_id INTEGER NOT NULL,
                tile_index INTEGER NOT NULL,
                confidence REAL NOT NULL,
                FOREIGN KEY (photograph_id) REFERENCES photographs(photograph_id)
            )
        """)
        self.conn.commit()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def log_photograph(
        self,
        timestamp: datetime,
        image_path: str,
        keep_all: bool = False,
    ) -> int:
        """Log a photograph and return its ID."""
        if self.conn is None:
            raise RuntimeError("Database not open")
        cursor = self.conn.execute(
            "INSERT INTO photographs (captured_at, image_path, keep_all) VALUES (?, ?, ?)",
            (timestamp.isoformat(), image_path, int(keep_all)),
        )
        self.conn.commit()
        return cursor.lastrowid

    def log_detection(
        self,
        photograph_id: int,
        tile_index: int,
        confidence: float,
    ) -> None:
        """Log a detection for a photograph."""
        if self.conn is None:
            raise RuntimeError("Database not open")
        self.conn.execute(
            "INSERT INTO detections (photograph_id, tile_index, confidence) VALUES (?, ?, ?)",
            (photograph_id, tile_index, confidence),
        )
        self.conn.commit()

    def get_recent_photographs(self, limit: int = 50) -> list[dict]:
        """Get recent photographs with detection counts."""
        if self.conn is None:
            raise RuntimeError("Database not open")
        cursor = self.conn.execute("""
            SELECT
                p.photograph_id,
                p.captured_at,
                p.image_path,
                p.keep_all,
                COUNT(d.detection_id) as detection_count
            FROM photographs p
            LEFT JOIN detections d ON p.photograph_id = d.photograph_id
            GROUP BY p.photograph_id
            ORDER BY p.captured_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_photograph(self, photograph_id: int) -> dict | None:
        """Get a photograph with its detections."""
        if self.conn is None:
            raise RuntimeError("Database not open")
        cursor = self.conn.execute(
            "SELECT * FROM photographs WHERE photograph_id = ?",
            (photograph_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        photo = dict(row)
        cursor = self.conn.execute(
            "SELECT tile_index, confidence FROM detections WHERE photograph_id = ?",
            (photograph_id,),
        )
        photo["detections"] = [dict(r) for r in cursor.fetchall()]
        return photo

    def get_stats(self) -> dict:
        """Get summary statistics."""
        if self.conn is None:
            raise RuntimeError("Database not open")

        photo_count = self.conn.execute("SELECT COUNT(*) FROM photographs").fetchone()[0]
        detection_count = self.conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]

        return {
            "total_photographs": photo_count,
            "total_detections": detection_count,
        }

    def __enter__(self) -> "Database":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
