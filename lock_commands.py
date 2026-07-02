"""
Lock command interface for communication between web interface and main app
"""
import os
import time
import json
import config

COMMAND_FILE = "/tmp/doorlock_command.json"
LOCK_STATE_FILE = "/tmp/doorlock_state.json"

class LockCommands:
    """Handle lock commands via file-based IPC"""
    
    @staticmethod
    def request_unlock(duration=config.UNLOCK_DURATION):
        """Request door unlock from web interface"""
        command = {
            'action': 'unlock',
            'duration': duration,
            'timestamp': time.time()
        }
        try:
            with open(COMMAND_FILE, 'w') as f:
                json.dump(command, f)
            return True
        except Exception as e:
            print(f"Error writing unlock command: {e}")
            return False
    
    @staticmethod
    def get_lock_state():
        """Get current lock state"""
        try:
            if os.path.exists(LOCK_STATE_FILE):
                with open(LOCK_STATE_FILE, 'r') as f:
                    state = json.load(f)
                    return state.get('is_locked', True)
            return True  # Default to locked
        except Exception as e:
            print(f"Error reading lock state: {e}")
            return True
    
    @staticmethod
    def update_lock_state(is_locked):
        """Update lock state file (called by main app)"""
        state = {
            'is_locked': is_locked,
            'timestamp': time.time()
        }
        try:
            with open(LOCK_STATE_FILE, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error writing lock state: {e}")
    
    @staticmethod
    def check_command():
        """Check for pending commands (called by main app)"""
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r') as f:
                    command = json.load(f)
                
                # Remove command file after reading
                os.remove(COMMAND_FILE)
                
                # Check if command is recent (within last 5 seconds)
                if time.time() - command.get('timestamp', 0) < 5:
                    return command
            return None
        except Exception as e:
            print(f"Error checking command: {e}")
            return None
