# Safety Features & Emergency Access Guide

## Critical Safety Information

This document describes all safety features and emergency access methods to prevent lockouts.

## 🚨 Emergency Access Methods

The system includes **multiple layers of safety** to ensure you never get locked out:

### 1. Physical Exit Button (PRIMARY SAFETY)

**Location**: GPIO Pin 22 (configured in [config.py](config.py))

**How it works**:
- Press the physical button connected to GPIO 22
- Door unlocks immediately for 5 seconds
- No camera or facial recognition required
- Works even if software crashes
- **ALWAYS install this button on the INSIDE of the door**

**Wiring**:
```
GPIO 22 ----[Button]---- GND
```

**Important**: This is your primary safety mechanism. The button should be easily accessible from inside.

### 2. Web Interface Emergency Unlock

**Access**: From any device on your network at http://192.168.20.203:5000

**How to use**:
1. Open the web interface on your phone/computer
2. Click the "🚨 Emergency Unlock" button in the header
3. Confirm the action
4. Door unlocks for 5 seconds

**Requirements**:
- Device must be on the same network as Raspberry Pi
- Web service must be running
- Works from anywhere in your house/network

**Network Access**:
- Save the web interface URL to your phone's home screen for quick access
- Bookmark it on all devices
- The URL is: http://[YOUR_PI_IP]:5000

### 3. SSH Remote Unlock

If you have SSH access to the Raspberry Pi:

```bash
# SSH into the Raspberry Pi
ssh guillaume@192.168.20.203

# Run Python command to unlock
cd ~/raspberry-pi-face-recognition-doorlock
python3 -c "from lock_controller import LockController; lock = LockController(); lock.unlock(); print('Door unlocked')"
```

### 4. Direct GPIO Access

As a last resort, if software has completely failed:

```bash
# SSH into the Raspberry Pi
ssh guillaume@192.168.20.203

# Manually set GPIO pin LOW to unlock (BCM pin 17)
sudo gpioset gpiochip0 17=0

# Wait 5 seconds

# Set back to HIGH to lock
sudo gpioset gpiochip0 17=1
```

### 5. Power Cycle Safety

**Important Hardware Choice**:
- Use a **NORMALLY OPEN (NO)** relay configuration
- When power fails, electromagnet releases → door unlocks
- This ensures you can exit during power outages

**Current Configuration** (from [lock_controller.py](lock_controller.py)):
- GPIO HIGH = Electromagnet ON = Locked
- GPIO LOW = Electromagnet OFF = Unlocked

**Power Failure Behavior**:
- If Raspberry Pi loses power → GPIO goes LOW → Door unlocks
- If electromagnet power supply fails → Door unlocks

## 🔧 Configuration Options

### Unlock Duration

Edit [config.py](config.py):

```python
# Time in seconds the lock stays unlocked
UNLOCK_DURATION = 5.0
```

You can increase this for more time to enter/exit.

### Test Mode (Hardware Testing)

Edit [config.py](config.py):

```python
# Enable test mode (simulates GPIO without actual hardware)
TEST_MODE = True
```

When enabled:
- No actual GPIO operations
- Prints simulation messages
- Safe for testing without hardware

### Debug Mode

Edit [config.py](config.py):

```python
# Enable debug mode (shows additional information)
DEBUG_MODE = True
```

When enabled:
- Detailed console output
- Helps troubleshoot issues
- Shows all detections and state changes

## 🛡️ Best Practices

### 1. Physical Security

- **Always install the inside exit button** (GPIO 22) in an accessible location
- Keep a physical key override on the electromagnetic lock (if supported by your lock model)
- Ensure the relay and Raspberry Pi are inside the secured area
- Use a UPS (Uninterruptible Power Supply) to prevent power-failure lockouts

### 2. Network Access

- Keep your phone connected to your home WiFi
- Bookmark the web interface URL on all devices
- Consider setting up VPN access for remote unlock when away from home

### 3. Testing

Before relying on the system:

```bash
# Test the exit button
# Press the physical button on GPIO 22 and verify door unlocks

# Test the web interface
# Click Emergency Unlock and verify door unlocks

# Test face recognition
# Stand in front of camera and verify automatic unlock

# Test power failure
# Unplug Raspberry Pi and verify door unlocks (if using NO relay)
```

### 4. Backup Plans

- Keep a traditional key as backup (if lock supports it)
- Have the SSH command saved on your phone's notes app
- Ensure at least one other person knows how to use the emergency unlock methods

## 📱 Quick Access Setup

### Save Web Interface to Phone Home Screen

**iPhone**:
1. Open http://192.168.20.203:5000 in Safari
2. Tap the Share button
3. Tap "Add to Home Screen"
4. Name it "Door Lock"

**Android**:
1. Open http://192.168.20.203:5000 in Chrome
2. Tap the menu (three dots)
3. Tap "Add to Home screen"
4. Name it "Door Lock"

## 🔍 Troubleshooting Emergency Access

### Web Interface Not Responding

1. Check if service is running:
   ```bash
   ssh guillaume@192.168.20.203
   sudo systemctl status doorlock-web.service
   ```

2. Restart the web service:
   ```bash
   sudo systemctl restart doorlock-web.service
   ```

3. Use SSH direct unlock method (see above)

### Physical Button Not Working

1. Check GPIO connection:
   ```bash
   ssh guillaume@192.168.20.203
   sudo gpioget gpiochip0 22
   ```
   Should show 1 when not pressed, 0 when pressed

2. Check button wiring - ensure one side connects to GPIO 22, other to GND

3. Use web interface or SSH unlock instead

### Completely Locked Out

If all software methods fail:

1. **Physical Power Cycle**:
   - Unplug the Raspberry Pi power supply
   - If using NO (Normally Open) relay, door should unlock
   - This should be your LAST RESORT

2. **Contact Support**:
   - Have someone inside press the exit button
   - Call someone who can SSH in remotely

3. **Traditional Key**:
   - Use physical key override if your lock has one

## 🏗️ Recommended Hardware Setup

For maximum safety:

1. **Electromagnetic Lock**:
   - Choose one with key override
   - 12V model recommended

2. **Relay Module**:
   - Use Normally Open (NO) configuration
   - Door unlocks when power is lost

3. **Power Supply**:
   - UPS (battery backup) for Raspberry Pi
   - Separate 12V supply for electromagnet
   - Both should be reliable

4. **Physical Button**:
   - Quality momentary push button
   - Mounted inside, easily accessible
   - Clearly labeled "EMERGENCY EXIT"

5. **Backup Access**:
   - Traditional key override
   - OR secondary entrance with traditional lock

## ⚠️ Important Notes

- **Never rely solely on facial recognition** for a sole entrance
- **Always have a backup exit method** (inside button is critical)
- **Test emergency methods regularly** (monthly recommended)
- **Keep web interface URL accessible** on all devices
- **Document your system** and share with household members
- **Use UPS** to prevent power-failure issues
- **Have traditional key backup** if possible

## 📞 Emergency Contacts

Keep this information handy:

```
Raspberry Pi IP: 192.168.20.203
Web Interface: http://192.168.20.203:5000
SSH Access: ssh guillaume@192.168.20.203

GPIO Pins:
- Lock Relay: GPIO 17
- Exit Button: GPIO 22
- Register Button: GPIO 27

Unlock Command:
python3 -c "from lock_controller import LockController; lock = LockController(); lock.unlock()"
```

## 🧪 Regular Maintenance Tests

Perform these tests monthly:

- [ ] Test physical exit button
- [ ] Test web interface emergency unlock
- [ ] Test facial recognition unlock
- [ ] Test SSH access
- [ ] Check all authorized faces are recognized
- [ ] Verify backup power (UPS) works
- [ ] Inspect all wire connections
- [ ] Test lock mechanism manually

Remember: **Your safety is more important than security**. When in doubt, design for safety over security.
