"""
Lock controller module for electromagnet GPIO control
Uses modern gpiod library (libgpiod) for GPIO access
"""

import threading
import time
import config

# Import lock commands for state sharing
try:
    from lock_commands import LockCommands
    LOCK_COMMANDS_AVAILABLE = True
except ImportError:
    LOCK_COMMANDS_AVAILABLE = False

# Import GPIO library (modern gpiod 2.x)
try:
    import gpiod
    from gpiod import LineSettings
    from gpiod.line import Direction, Value
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    print("WARNING: gpiod not available. Running in simulation mode.")
    GPIO_AVAILABLE = False


class LockController:
    """Controls the electromagnet lock via GPIO relay using gpiod"""

    def __init__(self):
        """Initialize GPIO and lock state"""
        self.is_locked = True
        self.unlock_timer = None
        self.lock = threading.Lock()  # Thread safety
        self.chip = None
        self.relay_line = None
        self._setup_gpio()

    def _setup_gpio(self):
        """Setup GPIO pins for relay control using gpiod"""
        if not GPIO_AVAILABLE or config.TEST_MODE:
            if config.DEBUG_MODE:
                print("GPIO: Running in simulation mode")
            return

        try:
            # Open GPIO chip and request relay line (gpiod 2.x API)
            self.chip = gpiod.Chip('/dev/gpiochip0')

            # Request the relay pin as output with initial value HIGH (locked)
            # In gpiod 2.x, we use request_lines() method
            line_settings = gpiod.LineSettings(
                direction=Direction.OUTPUT,
                output_value=Value.ACTIVE  # HIGH = locked
            )

            line_config = {config.RELAY_PIN: line_settings}
            self.relay_line = self.chip.request_lines(
                consumer="door_lock",
                config=line_config
            )

            self.is_locked = True

            if config.DEBUG_MODE:
                print(f"GPIO initialized: Relay on pin {config.RELAY_PIN} using gpiod 2.x")

        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            raise

    def unlock(self, duration: float = config.UNLOCK_DURATION):
        """
        Unlock the door for a specified duration

        Args:
            duration: Time in seconds to keep the door unlocked
        """
        with self.lock:
            # Cancel any existing timer
            if self.unlock_timer and self.unlock_timer.is_alive():
                if config.DEBUG_MODE:
                    print("Existing unlock timer cancelled")
                return  # Already unlocking

            # Unlock the door
            self._set_lock_state(False)

            # Start timer to automatically lock after duration
            self.unlock_timer = threading.Timer(duration, self._auto_lock)
            self.unlock_timer.start()

            if config.DEBUG_MODE:
                print(f"Door unlocked for {duration} seconds")

    def _auto_lock(self):
        """Automatically lock the door (called by timer)"""
        with self.lock:
            self._set_lock_state(True)

            if config.DEBUG_MODE:
                print("Door automatically locked")

    def lock(self):
        """Manually lock the door immediately"""
        with self.lock:
            # Cancel any existing timer
            if self.unlock_timer and self.unlock_timer.is_alive():
                self.unlock_timer.cancel()

            self._set_lock_state(True)

            if config.DEBUG_MODE:
                print("Door manually locked")

    def _set_lock_state(self, locked: bool):
        """
        Set the physical lock state

        Args:
            locked: True to lock, False to unlock
        """
        self.is_locked = locked

        # Update shared lock state file for web interface
        if LOCK_COMMANDS_AVAILABLE:
            try:
                LockCommands.update_lock_state(locked)
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"Error updating shared lock state: {e}")

        if GPIO_AVAILABLE and not config.TEST_MODE and self.relay_line:
            try:
                if locked:
                    # HIGH = electromagnet engaged = locked
                    self.relay_line.set_value(config.RELAY_PIN, Value.ACTIVE)
                else:
                    # LOW = electromagnet released = unlocked
                    self.relay_line.set_value(config.RELAY_PIN, Value.INACTIVE)
            except Exception as e:
                print(f"Error setting GPIO state: {e}")
        else:
            # Simulation mode
            state = "LOCKED" if locked else "UNLOCKED"
            print(f"[SIMULATION] Door state: {state}")

    def get_state(self) -> bool:
        """
        Get current lock state

        Returns:
            True if locked, False if unlocked
        """
        return self.is_locked

    def cleanup(self):
        """Cleanup GPIO resources"""
        # Cancel any running timer
        if self.unlock_timer and self.unlock_timer.is_alive():
            self.unlock_timer.cancel()

        # Ensure door is locked before cleanup
        if GPIO_AVAILABLE and not config.TEST_MODE and self.relay_line:
            try:
                self.relay_line.set_value(config.RELAY_PIN, Value.ACTIVE)  # Lock
            except:
                pass

        # Release GPIO lines
        if self.relay_line:
            try:
                self.relay_line.release()
                if config.DEBUG_MODE:
                    print("GPIO lines released")
            except Exception as e:
                print(f"Error releasing GPIO lines: {e}")

        # Close chip
        if self.chip:
            try:
                self.chip.close()
                if config.DEBUG_MODE:
                    print("GPIO chip closed")
            except Exception as e:
                print(f"Error closing GPIO chip: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

    def __del__(self):
        """Destructor - ensure cleanup"""
        self.cleanup()


# Convenience function
def get_lock_controller() -> LockController:
    """Get a lock controller instance"""
    return LockController()
