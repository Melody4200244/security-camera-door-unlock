#!/usr/bin/env python3
"""
Automatic Door Lock with Facial Recognition
Main Application

Controls an electromagnet door lock using facial recognition.
Features:
- Continuous face recognition monitoring
- Automatic unlock for authorized persons
- Registration button for adding new authorized persons
- Inside exit button for manual unlock
- Display interface showing camera feed and status
- Complete logging of all detections
"""

import sys
import signal
import time
from datetime import datetime
import pygame
import config

# Import custom modules
from camera_module import Camera
from face_recognition_module import FaceRecognizer
from lock_controller import LockController
from database import Database
from logger_module import PhotoLogger
from display_interface import DisplayInterface
from shared_frame_buffer import SharedFrameBuffer
from lock_commands import LockCommands

# Import GPIO (modern gpiod 2.x library)
try:
    import gpiod
    from gpiod import LineSettings
    from gpiod.line import Direction, Value, Bias, Edge
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    print("WARNING: gpiod not available. Button functions disabled.")
    GPIO_AVAILABLE = False


class DoorLockSystem:
    """Main door lock system controller"""

    def __init__(self):
        """Initialize all system components"""
        print("Initializing Automatic Door Lock System...")

        # Initialize components
        self.camera = Camera()

        # Initialize face recognizer with IMX500 awareness
        use_imx500 = self.camera.is_using_imx500()
        self.recognizer = FaceRecognizer(use_imx500=use_imx500)

        if use_imx500:
            print("IMX500 AI Camera detected - using onboard AI for person detection")
        else:
            print("Using CPU-based face detection")

        self.lock = LockController()
        self.database = Database()
        self.logger = PhotoLogger()
        self.display = DisplayInterface()

        # System state
        self.running = True
        self.frame_count = 0
        self.last_unlock_time = 0
        self.unlock_cooldown = 3.0  # Prevent rapid repeated unlocks

        # Button state tracking
        self.chip = None
        self.button_lines = None
        self.register_button = None
        self.exit_button = None
        self.last_register_press = 0
        self.last_exit_press = 0
        self.button_debounce = config.BUTTON_DEBOUNCE_MS / 1000.0  # Convert to seconds

        # Load authorized faces from database
        self._load_authorized_faces()

        # Setup GPIO buttons
        self._setup_buttons()

        print("System initialized successfully!")

    def _load_authorized_faces(self):
        """Load all authorized faces from database"""
        try:
            authorized_persons = self.database.get_all_authorized_persons()
            self.recognizer.load_known_faces(authorized_persons)
            print(f"Loaded {len(authorized_persons)} authorized person(s)")
        except Exception as e:
            print(f"Error loading authorized faces: {e}")

    def _setup_buttons(self):
        """Setup GPIO button handlers using gpiod 2.x"""
        if not GPIO_AVAILABLE or config.TEST_MODE:
            print("Buttons disabled (GPIO not available or TEST_MODE)")
            return

        try:
            # Open GPIO chip
            self.chip = gpiod.Chip('/dev/gpiochip0')

            # Configure button lines as inputs with pull-up resistors (gpiod 2.x API)
            button_settings = LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP
            )

            # Request both button lines together
            line_config = {
                config.REGISTER_BUTTON_PIN: button_settings,
                config.EXIT_BUTTON_PIN: button_settings
            }

            self.button_lines = self.chip.request_lines(
                consumer="door_buttons",
                config=line_config
            )

            # Keep references to the line request object
            self.register_button = self.button_lines
            self.exit_button = self.button_lines

            print("GPIO buttons configured using gpiod 2.x")

        except Exception as e:
            print(f"Error setting up buttons: {e}")

    def _check_buttons(self):
        """Poll button states (called in main loop)"""
        if not GPIO_AVAILABLE or config.TEST_MODE or not self.button_lines:
            return

        try:
            current_time = time.time()

            # Check register button (active low - pressed = 0)
            # In gpiod 2.x, get_value() requires the line offset
            if self.button_lines.get_value(config.REGISTER_BUTTON_PIN) == Value.INACTIVE:
                if current_time - self.last_register_press > self.button_debounce:
                    self.last_register_press = current_time
                    self._on_register_button()

            # Check exit button (active low - pressed = 0)
            if self.button_lines.get_value(config.EXIT_BUTTON_PIN) == Value.INACTIVE:
                if current_time - self.last_exit_press > self.button_debounce:
                    self.last_exit_press = current_time
                    self._on_exit_button()

        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error checking buttons: {e}")

    def _check_web_commands(self):
        """Check for web interface unlock commands"""
        try:
            command = LockCommands.check_command()
            if command and command.get('action') == 'unlock':
                duration = command.get('duration', config.UNLOCK_DURATION)
                print(f"Web interface unlock request: {duration} seconds")
                self.lock.unlock(duration)
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error checking web commands: {e}")

    def _on_register_button(self):
        """Handle registration button press"""
        print("Registration button pressed")
        self.display.start_registration()

    def _on_exit_button(self):
        """Handle inside exit button press"""
        print("Exit button pressed - unlocking door")
        self.lock.unlock()

    def _process_registration(self, frame):
        """
        Process new person registration

        Args:
            frame: Current camera frame
        """
        try:
            # Get the name from display
            name = self.display.get_registration_name()

            if not name or len(name.strip()) == 0:
                print("Registration cancelled: No name entered")
                self.display.cancel_registration()
                return

            print(f"Registering new person: {name}")

            # Detect face in frame
            face_locations = self.recognizer.detect_faces(frame)

            if len(face_locations) == 0:
                print("No face detected. Please try again.")
                self.display.cancel_registration()
                return

            if len(face_locations) > 1:
                print("Multiple faces detected. Please ensure only one person is visible.")
                self.display.cancel_registration()
                return

            # Get face encoding
            face_encoding = self.recognizer.encode_face(frame, face_locations[0])

            if face_encoding is None:
                print("Failed to encode face. Please try again.")
                self.display.cancel_registration()
                return

            # Add to database (this will generate person_id)
            person_id = self.database.add_authorized_person(
                name=name.strip(),
                face_encoding=face_encoding,
                photo_path=""  # Temporary, will update after saving photo
            )

            # Save photo
            photo_path = self.logger.save_authorized_face(frame, person_id, name.strip())

            # Update database with actual photo path
            self.database.update_person_photo_path(person_id, photo_path)

            print(f"Successfully registered: {name} (ID: {person_id})")

            # Reload authorized faces
            self._load_authorized_faces()

            # Cancel registration mode
            self.display.cancel_registration()

        except Exception as e:
            print(f"Error during registration: {e}")
            self.display.cancel_registration()

    def _process_frame(self, frame, imx500_inference=None):
        """
        Process a single frame for face recognition

        Args:
            frame: Camera frame as numpy array
            imx500_inference: Optional IMX500 inference results
        """
        try:
            # Perform face recognition (with or without IMX500)
            if imx500_inference and self.recognizer.use_imx500:
                # Parse IMX500 detections
                imx500_detections = self.camera.get_detections_from_inference(imx500_inference)
                # Use hybrid processing
                results = self.recognizer.process_frame_with_imx500(frame, imx500_detections)
            else:
                # Standard CPU-based processing
                results = self.recognizer.process_frame(frame)

            # Process each detected face
            for result in results:
                is_authorized = result['is_match']
                person_id = result['person_id']
                name = result['name']
                encoding = result['encoding']

                # Log the detection
                photo_path = self.logger.save_detection_photo(frame, person_id)
                self.database.log_detection(
                    photo_path=photo_path,
                    is_authorized=is_authorized,
                    person_id=person_id,
                    face_encoding=encoding
                )

                # Update display with last detection
                self.display.set_last_detection({
                    'name': name,
                    'timestamp': datetime.now().isoformat()
                })

                # Unlock door if authorized
                if is_authorized:
                    # Check cooldown to prevent rapid unlocks
                    current_time = time.time()
                    if current_time - self.last_unlock_time >= self.unlock_cooldown:
                        print(f"Authorized person detected: {name}")
                        self.lock.unlock()
                        self.last_unlock_time = current_time
                    else:
                        print(f"Unlock cooldown active ({name})")
                else:
                    print(f"Unauthorized person detected")

            return results

        except Exception as e:
            print(f"Error processing frame: {e}")
            return []

    def run(self):
        """Main application loop"""
        print("Starting main loop...")
        print("Press Ctrl+C to exit")

        try:
            # Start camera
            self.camera.start()

            while self.running:
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                    # Handle keyboard input for registration
                    if self.display.registration_mode:
                        if self.display.handle_keyboard_input(event):
                            # Registration confirmed
                            frame = self.camera.capture_frame()
                            if frame is not None:
                                self._process_registration(frame)

                # Capture frame (with IMX500 inference if available)
                if self.camera.is_using_imx500():
                    frame, imx500_inference = self.camera.capture_frame_with_inference()
                else:
                    frame = self.camera.capture_frame()
                    imx500_inference = None

                if frame is None:
                    print("Failed to capture frame")
                    time.sleep(0.1)
                    continue

                # Write frame to shared buffer for web interface access
                # Write more frequently for smoother video stream
                # Note: Convert BGR to RGB for proper color display
                if self.frame_count % 2 == 0:  # Every 2 frames for smoother stream
                    # Picamera2 RGB888 format is actually BGR, swap channels
                    frame_rgb = frame[:, :, ::-1]  # BGR to RGB
                    SharedFrameBuffer.write_frame(frame_rgb)

                # Check button states
                self._check_buttons()

                # Check for web interface commands
                self._check_web_commands()

                # Process frame (skip frames based on config)
                recognition_results = []
                if not self.display.registration_mode:
                    if self.frame_count % config.FRAME_SKIP == 0:
                        recognition_results = self._process_frame(frame, imx500_inference)

                # Get recent detections for display
                recent_detections = self.database.get_recent_detections(limit=8)

                # Update display
                self.display.update(
                    frame=frame,
                    lock_state=self.lock.get_state(),
                    recent_detections=recent_detections,
                    recognition_results=recognition_results
                )

                # Increment frame counter
                self.frame_count += 1

                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nShutdown signal received")
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()

    def shutdown(self):
        """Cleanup and shutdown all components"""
        print("Shutting down system...")

        self.running = False

        # Cleanup components
        try:
            self.camera.close()
            print("Camera closed")
        except:
            pass

        try:
            self.lock.cleanup()
            print("Lock controller cleaned up")
        except:
            pass

        try:
            self.database.close()
            print("Database closed")
        except:
            pass

        try:
            self.display.close()
            print("Display closed")
        except:
            pass

        # Cleanup GPIO buttons
        if GPIO_AVAILABLE and not config.TEST_MODE:
            try:
                if hasattr(self, 'button_lines') and self.button_lines:
                    self.button_lines.release()
                if hasattr(self, 'chip') and self.chip:
                    self.chip.close()
                print("GPIO buttons cleaned up")
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"Error cleaning up GPIO: {e}")

        # Cleanup shared frame buffer
        try:
            SharedFrameBuffer.cleanup()
            print("Shared frame buffer cleaned up")
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error cleaning up shared buffer: {e}")

        print("Shutdown complete")


def signal_handler(sig, frame):
    """Handle system signals for graceful shutdown"""
    print("\nSignal received, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run the system
    try:
        system = DoorLockSystem()
        system.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
