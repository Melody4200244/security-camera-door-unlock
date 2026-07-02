"""
Display interface module using pygame for GUI
"""

import pygame
import numpy as np
from typing import List, Optional
from datetime import datetime
import config


class DisplayInterface:
    """Manages the pygame display interface"""

    def __init__(self):
        """Initialize pygame and create display"""
        pygame.init()
        self.screen = None
        self.clock = pygame.time.Clock()
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.running = False
        self._setup_display()
        self._load_fonts()

        # State variables
        self.current_status = "Locked"
        self.last_detection = None
        self.recent_activity = []
        self.registration_mode = False
        self.registration_name = ""

    def _setup_display(self):
        """Setup the pygame display"""
        try:
            # Get display info
            display_info = pygame.display.Info()

            if config.DISPLAY_FULLSCREEN:
                # Fullscreen mode
                self.width = display_info.current_w
                self.height = display_info.current_h
                self.screen = pygame.display.set_mode(
                    (self.width, self.height),
                    pygame.FULLSCREEN
                )
            else:
                # Windowed mode
                self.width = config.DISPLAY_WIDTH or 1024
                self.height = config.DISPLAY_HEIGHT or 600
                self.screen = pygame.display.set_mode((self.width, self.height))

            pygame.display.set_caption("Automatic Door Lock")
            self.running = True

            if config.DEBUG_MODE:
                print(f"Display initialized: {self.width}x{self.height}")

        except Exception as e:
            print(f"Error setting up display: {e}")
            raise

    def _load_fonts(self):
        """Load fonts for display"""
        try:
            self.font_large = pygame.font.Font(None, config.FONT_SIZE_LARGE)
            self.font_medium = pygame.font.Font(None, config.FONT_SIZE_MEDIUM)
            self.font_small = pygame.font.Font(None, config.FONT_SIZE_SMALL)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            raise

    def update(self, frame: np.ndarray, lock_state: bool,
               recent_detections: List[dict], recognition_results: List[dict] = None):
        """
        Update the display with current information

        Args:
            frame: Current camera frame (numpy array, RGB)
            lock_state: Current lock state (True = locked, False = unlocked)
            recent_detections: List of recent detection dictionaries from database
            recognition_results: Optional list of current frame recognition results
        """
        try:
            # Fill background
            self.screen.fill(config.COLOR_BACKGROUND)

            # Draw camera feed
            self._draw_camera_feed(frame, recognition_results)

            # Draw status panel
            self._draw_status_panel(lock_state)

            # Draw recent activity
            self._draw_recent_activity(recent_detections)

            # Draw instructions
            self._draw_instructions()

            # Draw registration mode overlay if active
            if self.registration_mode:
                self._draw_registration_overlay()

            # Update display
            pygame.display.flip()

            # Control frame rate
            self.clock.tick(config.CAMERA_FPS)

        except Exception as e:
            print(f"Error updating display: {e}")

    def _draw_camera_feed(self, frame: np.ndarray, recognition_results: List[dict] = None):
        """Draw the camera feed on the left side"""
        if frame is None:
            return

        try:
            # Calculate camera feed dimensions (left 60% of screen)
            feed_width = int(self.width * 0.6)
            feed_height = self.height

            # Convert numpy array to pygame surface
            # Picamera2 RGB888 format is actually BGR, swap channels
            frame_rgb = frame[:, :, ::-1]  # BGR to RGB
            # Rotate and flip to correct orientation
            frame_surface = pygame.surfarray.make_surface(
                np.rot90(np.fliplr(frame_rgb))
            )

            # Scale to fit display
            scaled_frame = pygame.transform.scale(frame_surface, (feed_width, feed_height))

            # Draw frame
            self.screen.blit(scaled_frame, (0, 0))

            # Draw face boxes if recognition results provided
            if recognition_results:
                self._draw_face_boxes_on_display(recognition_results, feed_width, feed_height)

        except Exception as e:
            print(f"Error drawing camera feed: {e}")

    def _draw_face_boxes_on_display(self, results: List[dict],
                                    display_width: int, display_height: int):
        """Draw face detection boxes on the display"""
        try:
            # Calculate scale factors
            scale_x = display_width / config.CAMERA_WIDTH
            scale_y = display_height / config.CAMERA_HEIGHT

            for result in results:
                top, right, bottom, left = result['location']
                is_match = result['is_match']
                name = result['name']

                # Scale coordinates
                scaled_left = int(left * scale_x)
                scaled_top = int(top * scale_y)
                scaled_right = int(right * scale_x)
                scaled_bottom = int(bottom * scale_y)

                # Choose color
                color = config.COLOR_UNLOCKED if is_match else config.COLOR_LOCKED

                # Draw rectangle
                pygame.draw.rect(self.screen, color,
                               (scaled_left, scaled_top,
                                scaled_right - scaled_left,
                                scaled_bottom - scaled_top), 3)

                # Draw label
                label = name if is_match else "Unknown"
                label_surface = self.font_small.render(label, True, config.COLOR_TEXT)
                label_bg = pygame.Surface((label_surface.get_width() + 10,
                                          label_surface.get_height() + 4))
                label_bg.fill(color)
                self.screen.blit(label_bg, (scaled_left, scaled_bottom - 30))
                self.screen.blit(label_surface, (scaled_left + 5, scaled_bottom - 28))

        except Exception as e:
            print(f"Error drawing face boxes: {e}")

    def _draw_status_panel(self, lock_state: bool):
        """Draw the status panel on the right side"""
        try:
            # Status panel area (right 40% of screen)
            panel_x = int(self.width * 0.6)
            panel_width = self.width - panel_x
            panel_height = int(self.height * 0.3)

            # Draw panel background
            pygame.draw.rect(self.screen, (30, 30, 40),
                           (panel_x, 0, panel_width, panel_height))

            # Draw lock status
            status_text = "LOCKED" if lock_state else "UNLOCKED"
            status_color = config.COLOR_LOCKED if lock_state else config.COLOR_UNLOCKED

            status_surface = self.font_large.render(status_text, True, status_color)
            status_rect = status_surface.get_rect(
                center=(panel_x + panel_width // 2, 60)
            )
            self.screen.blit(status_surface, status_rect)

            # Draw current time
            current_time = datetime.now().strftime("%H:%M:%S")
            time_surface = self.font_medium.render(current_time, True, config.COLOR_TEXT)
            time_rect = time_surface.get_rect(
                center=(panel_x + panel_width // 2, 120)
            )
            self.screen.blit(time_surface, time_rect)

            # Draw last detection info
            if self.last_detection:
                name = self.last_detection.get('name', 'Unknown')
                timestamp = self.last_detection.get('timestamp', '')

                detection_text = f"Last: {name}"
                detection_surface = self.font_small.render(
                    detection_text, True, config.COLOR_TEXT
                )
                detection_rect = detection_surface.get_rect(
                    center=(panel_x + panel_width // 2, 180)
                )
                self.screen.blit(detection_surface, detection_rect)

        except Exception as e:
            print(f"Error drawing status panel: {e}")

    def _draw_recent_activity(self, recent_detections: List[dict]):
        """Draw recent activity list"""
        try:
            # Activity panel area
            panel_x = int(self.width * 0.6)
            panel_y = int(self.height * 0.3)
            panel_width = self.width - panel_x
            panel_height = int(self.height * 0.5)

            # Draw panel background
            pygame.draw.rect(self.screen, (25, 25, 35),
                           (panel_x, panel_y, panel_width, panel_height))

            # Draw title
            title_surface = self.font_medium.render("Recent Activity", True, config.COLOR_TEXT)
            self.screen.blit(title_surface, (panel_x + 20, panel_y + 10))

            # Draw activity list
            y_offset = panel_y + 50
            line_height = 35

            for i, detection in enumerate(recent_detections[:8]):  # Show last 8
                name = detection.get('name', 'Unknown')
                timestamp = detection.get('timestamp', '')
                is_authorized = detection.get('is_authorized', False)

                # Parse timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8] if len(timestamp) >= 8 else timestamp

                # Format line
                line_text = f"{time_str} - {name}"
                color = config.COLOR_UNLOCKED if is_authorized else config.COLOR_LOCKED

                line_surface = self.font_small.render(line_text, True, color)
                self.screen.blit(line_surface, (panel_x + 20, y_offset))

                y_offset += line_height

        except Exception as e:
            print(f"Error drawing recent activity: {e}")

    def _draw_instructions(self):
        """Draw instructions panel at the bottom"""
        try:
            panel_x = int(self.width * 0.6)
            panel_y = int(self.height * 0.8)
            panel_width = self.width - panel_x
            panel_height = self.height - panel_y

            # Draw panel background
            pygame.draw.rect(self.screen, (35, 35, 45),
                           (panel_x, panel_y, panel_width, panel_height))

            # Draw instructions
            instructions = [
                "Press REGISTER button",
                "to add new person",
                "",
                "Press EXIT button",
                "to unlock from inside"
            ]

            y_offset = panel_y + 15
            for instruction in instructions:
                text_surface = self.font_small.render(instruction, True, config.COLOR_TEXT)
                self.screen.blit(text_surface, (panel_x + 20, y_offset))
                y_offset += 25

        except Exception as e:
            print(f"Error drawing instructions: {e}")

    def _draw_registration_overlay(self):
        """Draw registration mode overlay"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            # Registration box
            box_width = 600
            box_height = 300
            box_x = (self.width - box_width) // 2
            box_y = (self.height - box_height) // 2

            pygame.draw.rect(self.screen, (50, 50, 60),
                           (box_x, box_y, box_width, box_height))
            pygame.draw.rect(self.screen, config.COLOR_UNLOCKED,
                           (box_x, box_y, box_width, box_height), 3)

            # Title
            title = "Register New Person"
            title_surface = self.font_large.render(title, True, config.COLOR_TEXT)
            title_rect = title_surface.get_rect(
                center=(self.width // 2, box_y + 50)
            )
            self.screen.blit(title_surface, title_rect)

            # Instruction
            instruction = "Enter name using keyboard:"
            instruction_surface = self.font_medium.render(
                instruction, True, config.COLOR_TEXT
            )
            instruction_rect = instruction_surface.get_rect(
                center=(self.width // 2, box_y + 120)
            )
            self.screen.blit(instruction_surface, instruction_rect)

            # Name input
            name_text = self.registration_name or "_"
            name_surface = self.font_large.render(name_text, True, config.COLOR_UNLOCKED)
            name_rect = name_surface.get_rect(
                center=(self.width // 2, box_y + 180)
            )
            self.screen.blit(name_surface, name_rect)

            # Footer
            footer = "Press ENTER to save, ESC to cancel"
            footer_surface = self.font_small.render(footer, True, config.COLOR_TEXT)
            footer_rect = footer_surface.get_rect(
                center=(self.width // 2, box_y + 250)
            )
            self.screen.blit(footer_surface, footer_rect)

        except Exception as e:
            print(f"Error drawing registration overlay: {e}")

    def set_last_detection(self, detection: dict):
        """Set the last detection for display"""
        self.last_detection = detection

    def start_registration(self):
        """Start registration mode"""
        self.registration_mode = True
        self.registration_name = ""

    def cancel_registration(self):
        """Cancel registration mode"""
        self.registration_mode = False
        self.registration_name = ""

    def get_registration_name(self) -> Optional[str]:
        """Get the entered registration name"""
        if self.registration_name:
            return self.registration_name
        return None

    def handle_keyboard_input(self, event) -> bool:
        """
        Handle keyboard input for registration

        Returns:
            True if registration should be saved, False otherwise
        """
        if not self.registration_mode:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Save registration
                return True
            elif event.key == pygame.K_ESCAPE:
                # Cancel registration
                self.cancel_registration()
            elif event.key == pygame.K_BACKSPACE:
                # Delete last character
                self.registration_name = self.registration_name[:-1]
            else:
                # Add character
                if len(self.registration_name) < 20:  # Max 20 characters
                    self.registration_name += event.unicode

        return False

    def close(self):
        """Close the display"""
        pygame.quit()
        self.running = False

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience function
def get_display_interface() -> DisplayInterface:
    """Get a display interface instance"""
    return DisplayInterface()
