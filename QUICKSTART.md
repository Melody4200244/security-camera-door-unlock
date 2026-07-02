# Quick Start Guide

Get your door lock system running in minutes!

## Prerequisites Checklist

- [ ] Raspberry Pi 4 connected to network (IP: 192.168.20.203)
- [ ] Raspberry Pi AI Camera installed and working
- [ ] Electromagnet lock installed
- [ ] Relay module wired to GPIO 17
- [ ] Exit button wired to GPIO 22
- [ ] Register button wired to GPIO 27
- [ ] Display connected via HDMI
- [ ] IMX500 models installed (`imx500-all` package)

## 1. Install System Services

```bash
cd ~/raspberry-pi-face-recognition-doorlock
chmod +x install_services.sh
./install_services.sh
```

This installs and enables both services to start on boot.

## 2. Start the Services

```bash
# Start main application (with display)
sudo systemctl start doorlock.service

# Start web interface
sudo systemctl start doorlock-web.service

# Check they're running
sudo systemctl status doorlock.service
sudo systemctl status doorlock-web.service
```

## 3. Access the Web Interface

On any device on your network:
- Open browser to: **http://192.168.20.203:5000**
- Bookmark this URL on your phone!

## 4. Register Your First Authorized Person

### Method A: Physical Button
1. Stand in front of camera
2. Press the registration button (GPIO 27)
3. Type your name on connected keyboard
4. Press ENTER

### Method B: Web Interface
1. Go to http://192.168.20.203:5000
2. Click "+ Add Person"
3. Enter name
4. Choose "Use Current Camera Feed" or "Upload Photo"
5. Click "Add Person"

## 5. Test the System

### Test Automatic Unlock
1. Step in front of the camera
2. Wait 1-2 seconds
3. Door should unlock for 5 seconds
4. Check the display or web interface for confirmation

### Test Emergency Unlock Methods

**Physical Exit Button**:
- Press the button on GPIO 22
- Door unlocks immediately

**Web Interface Emergency Unlock**:
- Go to http://192.168.20.203:5000
- Click "🚨 Emergency Unlock" button
- Confirm action
- Door unlocks

## 6. Save Emergency Access

### On Your Phone
1. **Bookmark the web interface**: http://192.168.20.203:5000
2. **Add to home screen** for quick access
3. **Test the emergency unlock button**

### Important Numbers
```
Raspberry Pi IP: 192.168.20.203
Web Interface: http://192.168.20.203:5000
SSH: ssh guillaume@192.168.20.203
```

## Common Tasks

### View Live Logs
```bash
# Main app logs
sudo journalctl -u doorlock.service -f

# Web interface logs
sudo journalctl -u doorlock-web.service -f
```

### Restart Services
```bash
sudo systemctl restart doorlock.service
sudo systemctl restart doorlock-web.service
```

### Stop Services
```bash
sudo systemctl stop doorlock.service
sudo systemctl stop doorlock-web.service
```

### Add More Authorized Persons
- Use physical button method (see above)
- Or use web interface "+ Add Person" button

### View Detection History
- Check the display interface (shows last 8 detections)
- Or open web interface and scroll to "Recent Detections"

### Delete Authorized Person
1. Go to web interface
2. Find person in "Authorized Persons" list
3. Click "Delete" button
4. Confirm

## Configuration

Edit `~/raspberry-pi-face-recognition-doorlock/config.py` to customize:

```python
# Unlock duration (seconds)
UNLOCK_DURATION = 5.0

# Face matching strictness (0.5 = strict, 0.7 = lenient)
FACE_MATCH_TOLERANCE = 0.6

# GPIO pins
RELAY_PIN = 17
REGISTER_BUTTON_PIN = 27
EXIT_BUTTON_PIN = 22
```

After changes, restart services:
```bash
sudo systemctl restart doorlock.service doorlock-web.service
```

## Troubleshooting

### Camera Not Working
```bash
# Test camera
libcamera-hello

# Check IMX500 models
ls -lh /usr/share/imx500-models/

# View logs
sudo journalctl -u doorlock.service -n 50
```

### Web Interface Not Accessible
```bash
# Check if running
sudo systemctl status doorlock-web.service

# Check firewall
sudo ufw allow 5000

# Restart service
sudo systemctl restart doorlock-web.service
```

### Lock Not Responding
```bash
# Test GPIO manually
sudo gpioget gpiochip0 17

# Check relay connection
# Verify wiring: GPIO 17 → Relay IN
```

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u doorlock.service -n 50

# Run manually to see errors
cd ~/raspberry-pi-face-recognition-doorlock
python3 app.py
```

## Safety Reminders

**🚨 CRITICAL: Always maintain multiple ways to unlock!**

1. **Physical exit button** (GPIO 22) - works always
2. **Web interface** emergency unlock - works from any device
3. **SSH access** - remote unlock via command line
4. **Power failure** - door unlocks when power lost (if using NO relay)

**Read [SAFETY.md](SAFETY.md) for complete safety information!**

## Next Steps

- **Test all emergency unlock methods** - Don't wait for an emergency!
- **Share web interface URL** with household members
- **Set up UPS** for power backup
- **Schedule monthly tests** of all systems
- **Keep traditional key** as ultimate backup

## Getting Help

1. Check logs: `sudo journalctl -u doorlock.service -f`
2. Read [README.md](README.md) for detailed documentation
3. Read [SAFETY.md](SAFETY.md) for emergency access
4. Check configuration in `config.py`

## Success Checklist

After setup, you should have:

- [ ] Main app running and displaying camera feed
- [ ] Web interface accessible at http://192.168.20.203:5000
- [ ] At least one authorized person registered
- [ ] Tested automatic unlock (face recognition)
- [ ] Tested physical exit button
- [ ] Tested web emergency unlock
- [ ] Bookmarked web interface on your phone
- [ ] Services set to start on boot
- [ ] Read SAFETY.md document

**All checked? You're ready to use your smart door lock! 🎉**
