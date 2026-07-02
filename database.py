"""
Database module for managing authorized persons and detection logs
"""

import sqlite3
import pickle
from datetime import datetime
from typing import List, Optional, Tuple
import numpy as np
import config


class Database:
    """Handles all database operations for the door lock system"""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            self.cursor = self.connection.cursor()

            # Enable WAL mode for better concurrent access
            self.cursor.execute("PRAGMA journal_mode=WAL")

            # Set busy timeout
            self.cursor.execute("PRAGMA busy_timeout=30000")

            if config.DEBUG_MODE:
                print(f"Database connected: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise

    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            # Authorized persons table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS authorized_persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    face_encoding BLOB NOT NULL,
                    photo_path TEXT NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Detection logs table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    photo_path TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_authorized BOOLEAN NOT NULL,
                    person_id INTEGER,
                    face_encoding BLOB,
                    FOREIGN KEY (person_id) REFERENCES authorized_persons (id)
                )
            """)

            # Create index for faster queries
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_detection_timestamp
                ON detection_logs(timestamp DESC)
            """)

            self.connection.commit()
            if config.DEBUG_MODE:
                print("Database tables created/verified")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            raise

    def add_authorized_person(self, name: str, face_encoding: np.ndarray,
                             photo_path: str) -> int:
        """
        Add a new authorized person to the database

        Args:
            name: Person's name
            face_encoding: Face encoding as numpy array
            photo_path: Path to the person's photo

        Returns:
            ID of the newly added person
        """
        try:
            # Serialize the face encoding
            encoding_blob = pickle.dumps(face_encoding)

            self.cursor.execute("""
                INSERT INTO authorized_persons (name, face_encoding, photo_path)
                VALUES (?, ?, ?)
            """, (name, encoding_blob, photo_path))

            self.connection.commit()
            person_id = self.cursor.lastrowid

            if config.DEBUG_MODE:
                print(f"Added authorized person: {name} (ID: {person_id})")

            return person_id
        except sqlite3.Error as e:
            print(f"Error adding authorized person: {e}")
            raise

    def get_all_authorized_persons(self) -> List[Tuple[int, str, np.ndarray, str]]:
        """
        Get all authorized persons from the database

        Returns:
            List of tuples: (id, name, face_encoding, photo_path)
        """
        try:
            self.cursor.execute("""
                SELECT id, name, face_encoding, photo_path
                FROM authorized_persons
            """)

            results = []
            for row in self.cursor.fetchall():
                try:
                    person_id, name, encoding_blob, photo_path = row
                    face_encoding = pickle.loads(encoding_blob)
                    results.append((person_id, name, face_encoding, photo_path))
                except Exception as e:
                    print(f"Error unpickling encoding for person {person_id}: {e}")
                    continue

            return results
        except sqlite3.Error as e:
            print(f"Error retrieving authorized persons: {e}")
            return []

    def get_all_authorized_persons_info(self) -> List[dict]:
        """
        Get all authorized persons metadata without face encodings
        (Safe for web interface - avoids unpickling face encodings)

        Returns:
            List of dictionaries with person info (id, name, photo_path, registered_at)
        """
        try:
            self.cursor.execute("""
                SELECT id, name, photo_path, registered_at
                FROM authorized_persons
                ORDER BY registered_at DESC
            """)

            results = []
            for row in self.cursor.fetchall():
                person_id, name, photo_path, registered_at = row
                results.append({
                    'id': person_id,
                    'name': name,
                    'photo_path': photo_path,
                    'registered_at': registered_at
                })

            return results
        except sqlite3.Error as e:
            print(f"Error retrieving authorized persons info: {e}")
            return []

    def update_person_photo_path(self, person_id: int, photo_path: str) -> bool:
        """
        Update the photo path for an authorized person

        Args:
            person_id: ID of the person
            photo_path: New photo path

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute("""
                UPDATE authorized_persons
                SET photo_path = ?
                WHERE id = ?
            """, (photo_path, person_id))

            self.connection.commit()

            if config.DEBUG_MODE:
                print(f"Updated photo path for person ID {person_id}: {photo_path}")

            return True
        except sqlite3.Error as e:
            print(f"Error updating photo path: {e}")
            return False

    def delete_authorized_person(self, person_id: int) -> bool:
        """
        Delete an authorized person from the database

        Args:
            person_id: ID of the person to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute("""
                DELETE FROM authorized_persons WHERE id = ?
            """, (person_id,))

            self.connection.commit()

            if config.DEBUG_MODE:
                print(f"Deleted authorized person ID: {person_id}")

            return True
        except sqlite3.Error as e:
            print(f"Error deleting authorized person: {e}")
            return False

    def log_detection(self, photo_path: str, is_authorized: bool,
                     person_id: Optional[int] = None,
                     face_encoding: Optional[np.ndarray] = None) -> int:
        """
        Log a face detection event

        Args:
            photo_path: Path to the detection photo
            is_authorized: Whether the person is authorized
            person_id: ID of the authorized person (if applicable)
            face_encoding: Face encoding for reference

        Returns:
            ID of the log entry
        """
        try:
            # Serialize face encoding if provided
            encoding_blob = pickle.dumps(face_encoding) if face_encoding is not None else None

            self.cursor.execute("""
                INSERT INTO detection_logs
                (photo_path, is_authorized, person_id, face_encoding)
                VALUES (?, ?, ?, ?)
            """, (photo_path, is_authorized, person_id, encoding_blob))

            self.connection.commit()
            log_id = self.cursor.lastrowid

            if config.DEBUG_MODE:
                auth_status = "authorized" if is_authorized else "unauthorized"
                print(f"Logged detection: {auth_status} (ID: {log_id})")

            return log_id
        except sqlite3.Error as e:
            print(f"Error logging detection: {e}")
            raise

    def get_recent_detections(self, limit: int = 10) -> List[dict]:
        """
        Get recent detection logs

        Args:
            limit: Maximum number of logs to retrieve

        Returns:
            List of detection log dictionaries
        """
        try:
            self.cursor.execute("""
                SELECT
                    dl.id,
                    dl.photo_path,
                    dl.timestamp,
                    dl.is_authorized,
                    dl.person_id,
                    ap.name
                FROM detection_logs dl
                LEFT JOIN authorized_persons ap ON dl.person_id = ap.id
                ORDER BY dl.timestamp DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in self.cursor.fetchall():
                log_id, photo_path, timestamp, is_authorized, person_id, name = row
                results.append({
                    'id': log_id,
                    'photo_path': photo_path,
                    'timestamp': timestamp,
                    'is_authorized': bool(is_authorized),
                    'person_id': person_id,
                    'name': name if name else 'Unknown'
                })

            return results
        except sqlite3.Error as e:
            print(f"Error retrieving recent detections: {e}")
            return []

    def get_detection_count(self) -> Tuple[int, int]:
        """
        Get total detection counts

        Returns:
            Tuple of (total_detections, authorized_detections)
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM detection_logs")
            total = self.cursor.fetchone()[0]

            self.cursor.execute("""
                SELECT COUNT(*) FROM detection_logs WHERE is_authorized = 1
            """)
            authorized = self.cursor.fetchone()[0]

            return total, authorized
        except sqlite3.Error as e:
            print(f"Error getting detection count: {e}")
            return 0, 0

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            if config.DEBUG_MODE:
                print("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience function for quick database access
def get_database() -> Database:
    """Get a database instance"""
    return Database()
