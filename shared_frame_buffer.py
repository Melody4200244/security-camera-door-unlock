"""
Shared Frame Buffer for camera frame sharing between processes
Allows main app to write frames and web interface to read them
"""

import os
import time
import fcntl
import numpy as np
from PIL import Image
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SharedFrameBuffer')

class SharedFrameBuffer:
    """Thread-safe frame buffer using file system"""

    FRAME_PATH = "/tmp/doorlock_current_frame.jpg"
    TIMESTAMP_PATH = "/tmp/doorlock_frame_timestamp.txt"
    MAX_FRAME_AGE = 5.0  # seconds

    @classmethod
    def write_frame(cls, frame: np.ndarray):
        """
        Write a frame to the shared buffer

        Args:
            frame: numpy array (RGB format)
        """
        try:
            logger.debug(f"Writing frame: shape={frame.shape}, dtype={frame.dtype}")

            # Convert to PIL Image (expects RGB)
            img = Image.fromarray(frame, mode='RGB')

            # Write to temporary file first (atomic operation)
            temp_path = f"{cls.FRAME_PATH}.tmp"
            img.save(temp_path, format='JPEG', quality=85)

            # Atomic rename
            os.replace(temp_path, cls.FRAME_PATH)

            # Update timestamp
            with open(cls.TIMESTAMP_PATH, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(str(time.time()))
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            logger.debug("Frame written successfully")

        except Exception as e:
            logger.error(f"Error writing shared frame: {e}", exc_info=True)

    @classmethod
    def read_frame(cls) -> tuple:
        """
        Read the latest frame from the shared buffer

        Returns:
            tuple: (frame as numpy array in RGB format, age in seconds) or (None, None) if unavailable
        """
        try:
            # Check if frame file exists
            if not os.path.exists(cls.FRAME_PATH):
                logger.debug("Frame file does not exist")
                return None, None

            # Check frame age
            if os.path.exists(cls.TIMESTAMP_PATH):
                with open(cls.TIMESTAMP_PATH, 'r') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    timestamp = float(f.read().strip())
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                age = time.time() - timestamp

                # Frame too old
                if age > cls.MAX_FRAME_AGE:
                    logger.warning(f"Frame too old: {age:.2f}s")
                    return None, age
            else:
                age = 0

            # Read the frame
            img = Image.open(cls.FRAME_PATH)
            frame = np.array(img)

            logger.debug(f"Read frame: shape={frame.shape}, age={age:.3f}s")

            return frame, age

        except Exception as e:
            logger.error(f"Error reading shared frame: {e}", exc_info=True)
            return None, None

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if a recent frame is available

        Returns:
            bool: True if a recent frame exists
        """
        frame, age = cls.read_frame()
        return frame is not None and age is not None and age < cls.MAX_FRAME_AGE

    @classmethod
    def cleanup(cls):
        """Remove shared frame files"""
        try:
            if os.path.exists(cls.FRAME_PATH):
                os.remove(cls.FRAME_PATH)
                logger.info("Removed frame file")
            if os.path.exists(cls.TIMESTAMP_PATH):
                os.remove(cls.TIMESTAMP_PATH)
                logger.info("Removed timestamp file")
        except Exception as e:
            logger.error(f"Error cleaning up shared frames: {e}", exc_info=True)
