"""Camera repository for database operations."""

from datetime import datetime

from d_ipcam.data.database import Database
from d_ipcam.data.models import Camera


class CameraNotFoundError(Exception):
    """Raised when a camera is not found."""
    pass


class CameraRepository:
    """Repository for camera CRUD operations."""

    def __init__(self, database: Database) -> None:
        """Initialize repository with database connection.

        Args:
            database: Database instance
        """
        self.db = database

    def get_all(self) -> list[Camera]:
        """Get all cameras.

        Returns:
            List of all cameras
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cameras ORDER BY name"
            )
            rows = cursor.fetchall()
            return [self._row_to_camera(row) for row in rows]

    def get_enabled(self) -> list[Camera]:
        """Get all enabled cameras.

        Returns:
            List of enabled cameras
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cameras WHERE enabled = 1 ORDER BY name"
            )
            rows = cursor.fetchall()
            return [self._row_to_camera(row) for row in rows]

    def get_by_id(self, camera_id: int) -> Camera:
        """Get a camera by ID.

        Args:
            camera_id: Camera ID

        Returns:
            Camera instance

        Raises:
            CameraNotFoundError: If camera not found
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cameras WHERE id = ?",
                (camera_id,)
            )
            row = cursor.fetchone()

            if row is None:
                raise CameraNotFoundError(f"Camera with ID {camera_id} not found")

            return self._row_to_camera(row)

    def get_by_ip(self, ip: str) -> Camera | None:
        """Get a camera by IP address.

        Args:
            ip: IP address

        Returns:
            Camera instance or None if not found
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cameras WHERE ip = ?",
                (ip,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_camera(row)

    def save(self, camera: Camera) -> Camera:
        """Save a camera (insert or update).

        Args:
            camera: Camera to save

        Returns:
            Saved camera with ID populated
        """
        if camera.id is None:
            return self._insert(camera)
        else:
            return self._update(camera)

    def _insert(self, camera: Camera) -> Camera:
        """Insert a new camera.

        Args:
            camera: Camera to insert

        Returns:
            Camera with ID populated
        """
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cameras (name, ip, port, username, password, channel, subtype, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    camera.name,
                    camera.ip,
                    camera.port,
                    camera.username,
                    camera.password,
                    camera.channel,
                    camera.subtype,
                    1 if camera.enabled else 0,
                )
            )
            conn.commit()
            camera.id = cursor.lastrowid
            return camera

    def _update(self, camera: Camera) -> Camera:
        """Update an existing camera.

        Args:
            camera: Camera to update

        Returns:
            Updated camera
        """
        camera.updated_at = datetime.now()

        with self.db.connection() as conn:
            conn.execute(
                """
                UPDATE cameras
                SET name = ?, ip = ?, port = ?, username = ?, password = ?,
                    channel = ?, subtype = ?, enabled = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    camera.name,
                    camera.ip,
                    camera.port,
                    camera.username,
                    camera.password,
                    camera.channel,
                    camera.subtype,
                    1 if camera.enabled else 0,
                    camera.updated_at,
                    camera.id,
                )
            )
            conn.commit()
            return camera

    def delete(self, camera_id: int) -> None:
        """Delete a camera by ID.

        Args:
            camera_id: Camera ID to delete
        """
        with self.db.connection() as conn:
            conn.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
            conn.commit()

    def _row_to_camera(self, row) -> Camera:
        """Convert a database row to a Camera instance.

        Args:
            row: SQLite Row object

        Returns:
            Camera instance
        """
        # Handle missing subtype column for old databases
        subtype = row["subtype"] if "subtype" in row.keys() else 1

        return Camera(
            id=row["id"],
            name=row["name"],
            ip=row["ip"],
            port=row["port"],
            username=row["username"],
            password=row["password"],
            channel=row["channel"],
            subtype=subtype,
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
