"""
Logger module for saving detection photos and managing logs
"""

import os
from datetime import datetime
from typing import Optional
import numpy as np
from PIL import Image
import config


class PhotoLogger:
    """Handles photo logging for all detections"""

    def __init__(self):
        """Initialize the photo logger"""
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure log directories exist"""
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        os.makedirs(config.AUTHORIZED_FACES_DIR, exist_ok=True)

    def save_detection_photo(self, frame: np.ndarray,
                            person_id: Optional[int] = None) -> str:
        """
        Save a detection photo to the logs directory

        Args:
            frame: Image as numpy array (RGB format)
            person_id: ID of the detected person (None if unknown)

        Returns:
            Path to the saved photo
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now()
            person_str = f"person_{person_id}" if person_id else "unknown"
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{person_str}.jpg"
            filepath = os.path.join(config.LOGS_DIR, filename)

            # Convert numpy array to PIL Image and save
            image = Image.fromarray(frame)
            image.save(filepath, quality=85)

            if config.DEBUG_MODE:
                print(f"Detection photo saved: {filename}")

            return filepath

        except Exception as e:
            print(f"Error saving detection photo: {e}")
            return None

    def save_authorized_face(self, frame: np.ndarray, person_id: int,
                            name: str) -> str:
        """
        Save an authorized person's photo

        Args:
            frame: Image as numpy array (RGB format)
            person_id: ID of the authorized person
            name: Name of the person

        Returns:
            Path to the saved photo
        """
        try:
            # Generate filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_'))
            safe_name = safe_name.replace(' ', '_')
            filename = f"{person_id}_{safe_name}.jpg"
            filepath = os.path.join(config.AUTHORIZED_FACES_DIR, filename)

            # Convert numpy array to PIL Image and save
            image = Image.fromarray(frame)
            image.save(filepath, quality=95)

            if config.DEBUG_MODE:
                print(f"Authorized face saved: {filename}")

            return filepath

        except Exception as e:
            print(f"Error saving authorized face: {e}")
            return None

    def cleanup_old_logs(self, max_count: int = config.MAX_LOG_PHOTOS):
        """
        Delete old log photos if count exceeds maximum

        Args:
            max_count: Maximum number of log photos to keep (0 = unlimited)
        """
        if max_count == 0:
            return

        try:
            # Get all log photos sorted by modification time
            log_files = []
            for filename in os.listdir(config.LOGS_DIR):
                if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    filepath = os.path.join(config.LOGS_DIR, filename)
                    log_files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x[1], reverse=True)

            # Delete files beyond max_count
            if len(log_files) > max_count:
                files_to_delete = log_files[max_count:]
                for filepath, _ in files_to_delete:
                    try:
                        os.remove(filepath)
                        if config.DEBUG_MODE:
                            print(f"Deleted old log: {os.path.basename(filepath)}")
                    except Exception as e:
                        print(f"Error deleting file {filepath}: {e}")

                if config.DEBUG_MODE:
                    print(f"Cleaned up {len(files_to_delete)} old log photos")

        except Exception as e:
            print(f"Error during log cleanup: {e}")

    def get_log_count(self) -> int:
        """
        Get the current number of log photos

        Returns:
            Number of log photos
        """
        try:
            count = 0
            for filename in os.listdir(config.LOGS_DIR):
                if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    count += 1
            return count
        except Exception as e:
            print(f"Error counting log photos: {e}")
            return 0

    def get_recent_logs(self, count: int = 10) -> list:
        """
        Get paths to recent log photos

        Args:
            count: Number of recent photos to retrieve

        Returns:
            List of photo paths (newest first)
        """
        try:
            # Get all log photos with modification times
            log_files = []
            for filename in os.listdir(config.LOGS_DIR):
                if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    filepath = os.path.join(config.LOGS_DIR, filename)
                    log_files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x[1], reverse=True)

            # Return requested number of files
            return [filepath for filepath, _ in log_files[:count]]

        except Exception as e:
            print(f"Error getting recent logs: {e}")
            return []


# Convenience function
def get_photo_logger() -> PhotoLogger:
    """Get a photo logger instance"""
    return PhotoLogger()
