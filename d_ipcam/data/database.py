"""SQLite database connection management."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    port INTEGER DEFAULT 554,
                    username TEXT DEFAULT 'admin',
                    password TEXT DEFAULT '',
                    channel INTEGER DEFAULT 1,
                    subtype INTEGER DEFAULT 1,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Add subtype column if missing (migration for existing databases)
            try:
                conn.execute("ALTER TABLE cameras ADD COLUMN subtype INTEGER DEFAULT 1")
            except Exception:
                pass  # Column already exists

            # Create index on IP for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cameras_ip ON cameras(ip)
            """)

            conn.commit()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections.

        Yields:
            SQLite connection with row factory enabled
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
