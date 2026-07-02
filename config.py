"""
Configuration file for Raspberry Pi Automatic Door Lock System
"""

import os

# ==================== GPIO Configuration ====================
# GPIO pin assignments (BCM numbering)

# Electromagnet relay control (lock/unlock)
RELAY_PIN = 17

# Registration button - press to save new authorized person
REGISTER_BUTTON_PIN = 27

# Inside exit button - press to unlock from inside
EXIT_BUTTON_PIN = 22

# Button debounce time in milliseconds
BUTTON_DEBOUNCE_MS = 300

# ==================== Lock Behavior ====================
# Time in seconds the lock stays unlocked
UNLOCK_DURATION = 5.0

# ==================== Face Recognition ====================
# Tolerance for face matching (lower = more strict, higher = more lenient)
# Recommended: 0.6 (default), stricter: 0.5, more lenient: 0.7
FACE_MATCH_TOLERANCE = 0.6

# Number of times a face must be detected before processing (reduces false positives)
MIN_DETECTION_COUNT = 2

# Process every Nth frame to reduce CPU load
FRAME_SKIP = 2

# ==================== Camera Settings ====================
# Camera resolution (lower = faster processing)
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Camera frame rate
CAMERA_FPS = 30

# ==================== IMX500 AI Camera Settings ====================
# IMX500 model path (.rpk file)
# This system is designed for the Raspberry Pi AI Camera with IMX500
# MobileNet SSD is recommended for person detection
IMX500_MODEL_PATH = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

# Enable IMX500 onboard AI (set to False only for testing/development without AI Camera)
USE_IMX500 = True

# IMX500 detection confidence threshold
IMX500_CONFIDENCE_THRESHOLD = 0.5

# IMX500 person/face class ID (depends on model)
# For COCO models: person = 0
IMX500_PERSON_CLASS_ID = 0

# ==================== Display Settings ====================
# Display resolution (set to None for auto-detect)
DISPLAY_WIDTH = None
DISPLAY_HEIGHT = None

# Display mode (fullscreen)
DISPLAY_FULLSCREEN = True

# Font sizes
FONT_SIZE_LARGE = 48
FONT_SIZE_MEDIUM = 32
FONT_SIZE_SMALL = 24

# Colors (R, G, B)
COLOR_BACKGROUND = (20, 20, 30)
COLOR_TEXT = (255, 255, 255)
COLOR_LOCKED = (220, 50, 50)
COLOR_UNLOCKED = (50, 220, 50)
COLOR_DETECTING = (255, 200, 50)

# ==================== File Paths ====================
# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory
DATA_DIR = os.path.join(BASE_DIR, "data")

# Database file
DATABASE_PATH = os.path.join(DATA_DIR, "database.db")

# Authorized persons photos directory
AUTHORIZED_FACES_DIR = os.path.join(DATA_DIR, "authorized_faces")

# Detection logs photos directory
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# ==================== Logging ====================
# Maximum number of log photos to keep (0 = unlimited)
MAX_LOG_PHOTOS = 10000

# Log photo filename format
LOG_PHOTO_FORMAT = "%Y%m%d_%H%M%S_{person_id}.jpg"

# ==================== System Settings ====================
# Enable debug mode (shows additional information)
DEBUG_MODE = False

# Enable test mode (simulates GPIO without actual hardware)
TEST_MODE = False
