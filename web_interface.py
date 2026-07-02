#!/usr/bin/env python3
"""
Web Interface for Automatic Door Lock System
Provides remote monitoring and access management via Flask web server
"""

import os
import io
import base64
import json
import logging
import traceback
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, send_from_directory
from PIL import Image
import numpy as np
import config
from database import Database
from face_recognition_module import FaceRecognizer
from logger_module import PhotoLogger
from shared_frame_buffer import SharedFrameBuffer
from lock_commands import LockCommands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('WebInterface')

app = Flask(__name__)
# Secret key for session management - change in production!
# Set via environment variable: export FLASK_SECRET_KEY='your-random-secret'
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global instances (shared with main app via database and shared frame buffer)
# NOTE: We don't use a single global Database instance in Flask due to threading issues
# Instead, we create a new connection for each request using get_db()
photo_logger = PhotoLogger()
recognizer = None

def get_db():
    """Get a database instance for the current request"""
    # Create a new database connection for each request to avoid threading issues
    return Database()


def init_recognizer():
    """Initialize face recognizer without camera (for processing uploaded images)"""
    global recognizer
    if recognizer is None:
        try:
            log.info("Initializing face recognizer for web interface...")
            # Initialize recognizer without camera dependency
            recognizer = FaceRecognizer(use_imx500=False)
            log.info("Face recognizer initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize face recognizer: {e}", exc_info=True)
            raise
    return recognizer


# Removed init_lock() - web interface uses command file instead of direct GPIO control


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current system status"""
    db = None
    try:
        db = get_db()
        # Use info method to avoid unpickling face encodings (prevents SEGV crashes)
        authorized_count = len(db.get_all_authorized_persons_info())
        recent_logs = db.get_recent_detections(limit=1)

        last_activity = None
        if recent_logs:
            last_activity = {
                'timestamp': recent_logs[0]['timestamp'],
                'is_authorized': recent_logs[0]['is_authorized']
            }

        # Get lock state from shared state file
        is_locked = LockCommands.get_lock_state()
        lock_state = 'locked' if is_locked else 'unlocked'

        return jsonify({
            'success': True,
            'authorized_count': authorized_count,
            'last_activity': last_activity,
            'camera_active': SharedFrameBuffer.is_available(),
            'lock_state': lock_state
        })
    except Exception as e:
        log.error(f"Error in get_status: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/unlock', methods=['POST'])
def emergency_unlock():
    """Emergency manual unlock endpoint"""
    try:
        # Get optional duration from request
        data = request.get_json() or {}
        duration = data.get('duration', config.UNLOCK_DURATION)

        # Send unlock command to main app via command file
        if LockCommands.request_unlock(duration):
            log.info(f"Unlock command sent: {duration} seconds")
            return jsonify({
                'success': True,
                'message': f'Door unlock requested for {duration} seconds',
                'duration': duration
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to send unlock command'}), 500
    except Exception as e:
        log.error(f"Error requesting unlock: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/camera/snapshot')
def get_snapshot():
    """Get current camera snapshot from shared frame buffer"""
    try:
        log.info("Camera snapshot requested")

        # Read frame from shared buffer (main app writes to it)
        frame, age = SharedFrameBuffer.read_frame()

        if frame is None:
            log.warning("No camera frame available")
            return jsonify({'success': False, 'error': 'No camera frame available. Main app may not be running.'}), 503

        log.info(f"Got frame: shape={frame.shape}, age={age:.3f}s")

        # Convert frame to JPEG (PIL expects RGB)
        img = Image.fromarray(frame, mode='RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        # Encode to base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        log.info("Snapshot encoded successfully")

        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_base64}',
            'timestamp': datetime.now().isoformat(),
            'frame_age': age
        })
    except Exception as e:
        log.error(f"Error getting snapshot: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/camera/stream')
def video_stream():
    """MJPEG video stream endpoint using shared frame buffer"""
    def generate():
        import time
        log.info("Video stream started")
        frame_count = 0
        max_errors = 10
        error_count = 0

        while error_count < max_errors:
            try:
                # Read from shared buffer
                frame, age = SharedFrameBuffer.read_frame()

                if frame is not None and frame.size > 0:
                    # Convert to JPEG (PIL expects RGB)
                    img = Image.fromarray(frame, mode='RGB')
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=75)

                    if buffer.tell() > 0:  # Check if data was written
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.getvalue() + b'\r\n')
                        frame_count += 1
                        error_count = 0  # Reset error count on success

                    buffer.close()

                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)

            except GeneratorExit:
                log.info(f"Video stream closed by client after {frame_count} frames")
                break
            except Exception as e:
                error_count += 1
                log.error(f"Error in video stream (error {error_count}/{max_errors}): {e}", exc_info=True)
                time.sleep(1)

        if error_count >= max_errors:
            log.error(f"Video stream terminated after {max_errors} consecutive errors")

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/authorized')
def get_authorized():
    """Get list of all authorized persons"""
    db = None
    try:
        log.info("Getting authorized persons list")
        db = get_db()
        # Use info method to avoid unpickling face encodings (prevents SEGV crashes)
        persons = db.get_all_authorized_persons_info()
        log.info(f"Found {len(persons)} authorized person(s)")

        log.info(f"Returning {len(persons)} person(s)")
        return jsonify({'success': True, 'persons': persons})
    except Exception as e:
        log.error(f"Error getting authorized persons: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        if db:
            db.close()


@app.route('/api/authorized/<int:person_id>', methods=['DELETE'])
def delete_authorized(person_id):
    """Delete an authorized person"""
    db = None
    try:
        db = get_db()
        # Get person info before deleting (use info method to avoid unpickling)
        persons = db.get_all_authorized_persons_info()
        person = next((p for p in persons if p['id'] == person_id), None)

        if not person:
            return jsonify({'success': False, 'error': 'Person not found'}), 404

        # Delete from database
        db.delete_authorized_person(person_id)

        # Delete photo file if exists
        photo_path = person.get('photo_path')
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)

        return jsonify({'success': True, 'message': f'Deleted person ID {person_id}'})
    except Exception as e:
        log.error(f"Error deleting authorized person: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/authorized', methods=['POST'])
def add_authorized():
    """Add a new authorized person (from uploaded photo or current camera frame)"""
    db = None
    try:
        log.info("Add authorized person request received")
        data = request.get_json()
        name = data.get('name', '').strip()

        if not name:
            log.warning("Name not provided")
            return jsonify({'success': False, 'error': 'Name is required'}), 400

        # Check if image is provided (base64) or should use camera
        use_camera = data.get('use_camera', False)

        if use_camera:
            log.info("Using camera feed for registration")
            # Capture from shared frame buffer
            frame, age = SharedFrameBuffer.read_frame()
            if frame is None:
                log.error("No camera frame available for registration")
                return jsonify({'success': False, 'error': 'No camera frame available. Main app may not be running.'}), 503
            log.info(f"Got camera frame: shape={frame.shape}, age={age:.3f}s")
        else:
            log.info("Using uploaded image for registration")
            # Get from uploaded base64 image
            image_data = data.get('image')
            if not image_data:
                log.warning("No image data provided")
                return jsonify({'success': False, 'error': 'Image data required'}), 400

            # Decode base64 image
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            img_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_bytes))
            frame = np.array(img)
            log.info(f"Decoded uploaded image: shape={frame.shape}")

        # Detect face (initialize recognizer without camera if needed)
        init_recognizer()
        log.info("Detecting faces...")
        face_locations = recognizer.detect_faces(frame)
        log.info(f"Found {len(face_locations)} face(s)")

        if len(face_locations) == 0:
            log.warning("No face detected")
            return jsonify({'success': False, 'error': 'No face detected in image'}), 400

        if len(face_locations) > 1:
            log.warning("Multiple faces detected")
            return jsonify({'success': False, 'error': 'Multiple faces detected. Please ensure only one person is visible'}), 400

        # Encode face
        log.info("Encoding face...")
        face_encoding = recognizer.encode_face(frame, face_locations[0])

        if face_encoding is None:
            log.error("Failed to encode face")
            return jsonify({'success': False, 'error': 'Failed to encode face'}), 500

        # Add to database
        log.info(f"Adding {name} to database...")
        db = get_db()
        person_id = db.add_authorized_person(
            name=name,
            face_encoding=face_encoding,
            photo_path=""
        )

        # Save photo
        photo_path = photo_logger.save_authorized_face(frame, person_id, name)

        # Update database with actual photo path
        db.update_person_photo_path(person_id, photo_path)

        log.info(f"Successfully registered {name} (ID: {person_id})")

        return jsonify({
            'success': True,
            'person_id': person_id,
            'name': name,
            'message': f'Successfully registered {name}'
        })

    except Exception as e:
        log.error(f"Error adding authorized person: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        if db:
            db.close()


@app.route('/api/detections')
def get_detections():
    """Get recent detection logs"""
    db = None
    try:
        db = get_db()
        limit = request.args.get('limit', 50, type=int)
        detections = db.get_recent_detections(limit=limit)

        # database.get_recent_detections already returns dictionaries with all needed fields
        result = []
        for detection in detections:
            result.append({
                'photo_path': detection['photo_path'],
                'timestamp': detection['timestamp'],
                'is_authorized': detection['is_authorized'],
                'person_id': detection['person_id'],
                'person_name': detection['name']
            })

        return jsonify({'success': True, 'detections': result})
    except Exception as e:
        log.error(f"Error getting detections: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/photo/<path:filename>')
def get_photo(filename):
    """Serve detection or authorized face photos"""
    try:
        # Check in logs directory
        logs_path = os.path.join(config.DATA_DIR, 'logs', filename)
        if os.path.exists(logs_path):
            return send_from_directory(os.path.join(config.DATA_DIR, 'logs'), filename)

        # Check in authorized_faces directory
        auth_path = os.path.join(config.DATA_DIR, 'authorized_faces', filename)
        if os.path.exists(auth_path):
            return send_from_directory(os.path.join(config.DATA_DIR, 'authorized_faces'), filename)

        # Try full path if provided
        if os.path.exists(filename):
            directory = os.path.dirname(filename)
            basename = os.path.basename(filename)
            return send_from_directory(directory, basename)

        return jsonify({'success': False, 'error': 'Photo not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def cleanup():
    """Cleanup resources"""
    pass  # No cleanup needed - lock controlled by main app


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask web server"""
    try:
        log.info(f"Starting web interface on http://{host}:{port}")
        app.run(host=host, port=port, debug=debug, threaded=True)
    except Exception as e:
        log.error(f"Error running web server: {e}", exc_info=True)
        raise
    finally:
        cleanup()


if __name__ == '__main__':
    run_server(debug=config.DEBUG_MODE)
