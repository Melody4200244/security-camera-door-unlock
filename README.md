# Automatic Door Lock with Facial Recognition + AI Camera

An intelligent door lock system using **Raspberry Pi 4**, **Raspberry Pi AI Camera** with IMX500 onboard AI, and facial recognition. The system leverages hardware-accelerated person detection on the camera chip for optimal performance, automatically unlocking the door when it recognizes an authorized person.

## Features

- **🎯 IMX500 Onboard AI**: Person detection runs directly on camera chip (40-60% less CPU usage)
- **🔐 Hybrid Face Recognition**: IMX500 pre-detection + CPU face encoding for accuracy
- **📹 Continuous Monitoring**: Camera constantly monitors for faces with minimal CPU load
- **⚡ Automatic Unlock**: Door unlocks for 5 seconds when authorized person detected
- **🔘 Registration Button**: Physical button to register new authorized persons
- **🚪 Inside Exit Button**: Physical button to manually unlock from inside (safety feature)
- **🖥️ Display Interface**: Fullscreen GUI showing live camera feed, lock status, and recent activity
- **🌐 Web Interface**: Remote monitoring and access management via browser
- **🚨 Emergency Unlock**: Multiple failsafe methods including web button, SSH, and physical button
- **📊 Complete Logging**: All detections saved with photos and timestamps to SQLite database
- **🔒 Thread-Safe**: Prevents multiple simultaneous unlock operations

## ⚠️ Safety First

**This system includes multiple emergency access methods to prevent lockouts.**

Before installation, read the [SAFETY.md](SAFETY.md) document which covers:
- Physical exit button (primary safety mechanism)
- Web interface emergency unlock
- SSH remote unlock
- Power failure behavior
- Best practices and testing procedures

**Never rely on facial recognition as your only way to enter.** Always maintain backup access methods.

## System Architecture - Hybrid AI Approach

This system is **designed for the Raspberry Pi AI Camera** with Sony's IMX500 intelligent vision sensor. The hybrid AI architecture provides optimal performance:

### IMX500 Hybrid Mode (Recommended - Requires AI Camera)
1. **Person Detection** → Runs on IMX500 chip (hardware-accelerated, ~1ms)
2. **Face Detection** → Runs on Pi CPU, focused only on detected person regions
3. **Face Recognition** → Runs on Pi CPU for accurate encoding and matching

**Benefits:**
- ⚡ 40-60% reduction in CPU usage
- 🚀 Faster response time (0.5-1 second total)
- ❄️ Lower temperature/power consumption
- 🎯 Same face recognition accuracy

### Fallback Mode (Development/Testing Only)
- Face detection and recognition run entirely on Raspberry Pi CPU
- Slower (1-2 seconds) and higher CPU usage
- Automatically used if IMX500 not configured
- Useful for testing without hardware

## Hardware Requirements

### Essential Components

1. **Raspberry Pi 4** (2GB+ RAM recommended) or **Raspberry Pi 5**
2. **Raspberry Pi AI Camera** with IMX500 sensor (required for optimal performance)
3. **Electromagnet Lock** (12V recommended)
4. **Relay Module** (to control the electromagnet)
   - Suggested: 5V relay module compatible with Raspberry Pi GPIO
5. **Two Push Buttons**:
   - Registration button (to add new authorized persons)
   - Exit button (to unlock from inside)
6. **Display** (connected via HDMI)
7. **Power Supply**:
   - Raspberry Pi power supply (5V, 3A recommended)
   - Separate power supply for electromagnet (typically 12V)

### Optional Components

- Resistors for buttons (if not using internal pull-up)
- Case/enclosure for Raspberry Pi
- Mounting hardware for camera

## Wiring Diagram

### GPIO Connections (BCM numbering)

```
Raspberry Pi GPIO -> Component
─────────────────────────────────
GPIO 17             -> Relay IN (electromagnet control)
GPIO 27             -> Registration Button (one side)
GPIO 22             -> Exit Button (one side)
GND                 -> Buttons (other side) + Relay GND
5V                  -> Relay VCC
```

### Electromagnet Lock Connection

```
Power Supply +12V -> Relay COM
Relay NO          -> Electromagnet +
Electromagnet -   -> Power Supply GND
```

**Note**: The relay should be configured as Normally Open (NO). When GPIO is HIGH, the electromagnet is engaged (locked). When GPIO is LOW, the electromagnet releases (unlocked).

## Software Installation

### 1. System Preparation

Update your Raspberry Pi:

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install System Dependencies

```bash
# Install camera dependencies
sudo apt install -y python3-picamera2 python3-opencv

# Install build tools for dlib and face_recognition
sudo apt install -y build-essential cmake pkg-config
sudo apt install -y libopenblas-dev liblapack-dev
sudo apt install -y python3-dev python3-pip

# Install image libraries
sudo apt install -y libjpeg-dev libpng-dev libtiff-dev

# Install SDL for pygame (display)
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# Install GPIO libraries (modern libgpiod, not deprecated RPi.GPIO)
sudo apt install -y libgpiod-dev python3-libgpiod
```

### 3. Clone the Repository

```bash
cd ~
git clone https://github.com/Guiss-Guiss/raspberry-pi-face-recognition-doorlock.git
cd raspberry-pi-face-recognition-doorlock
```

Or if you prefer a shorter directory name:

```bash
cd ~
git clone https://github.com/Guiss-Guiss/raspberry-pi-face-recognition-doorlock.git doorlock
cd doorlock
```

### 4. Install Python Dependencies

```bash
cd ~/raspberry-pi-face-recognition-doorlock
pip3 install -r requirements.txt
```

**Note**: If you cloned with a different directory name, use that instead.

**Note**: Installing `dlib` and `face_recognition` may take 30-60 minutes on Raspberry Pi as they compile from source.

### 5. Configure GPIO Pins

Edit [config.py](config.py) to match your hardware setup:

```python
# Adjust these if you used different GPIO pins
RELAY_PIN = 17
REGISTER_BUTTON_PIN = 27
EXIT_BUTTON_PIN = 22
```

### 6. Install IMX500 Models for AI Camera

Install the IMX500 model zoo for hardware-accelerated person detection:

#### Install Models

```bash
# Install imx500-all package which includes model zoo
sudo apt install imx500-all

# Or install specific models
sudo apt install imx500-models
```

The models will be installed to `/usr/share/imx500-models/`.

#### Available Models for Person Detection

- **MobileNet SSD** (recommended): `imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk`
- **EfficientDet Lite**: Various sizes available
- Check `/usr/share/imx500-models/` for all available models

#### Configure IMX500 in config.py

Edit [config.py](config.py):

```python
# Enable IMX500 onboard AI
USE_IMX500 = True

# Set path to IMX500 model (.rpk file)
IMX500_MODEL_PATH = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

# Detection confidence threshold (0.0 to 1.0)
IMX500_CONFIDENCE_THRESHOLD = 0.5

# Person class ID for COCO models (person = 0)
IMX500_PERSON_CLASS_ID = 0
```

### 7. Verify Camera and IMX500 Setup

Test the AI Camera:

```bash
# Test basic camera functionality
libcamera-hello

# Verify IMX500 models are installed
ls -lh /usr/share/imx500-models/

# Test IMX500 with person detection
rpicam-hello --post-process-file /usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json
```

The system is now configured to use IMX500 hardware acceleration for person detection.

## Usage

### Starting the System

Run the application:

```bash
cd ~/raspberry-pi-face-recognition-doorlock
python3 app.py
```

The system will:
1. Initialize all components
2. Load authorized persons from database
3. Start the camera and display
4. Begin continuous monitoring

### Registering Authorized Persons

1. **Press the Registration Button** (GPIO 27)
2. A registration overlay will appear on the display
3. **Enter the person's name** using a connected keyboard
4. **Press ENTER** to save (or ESC to cancel)
5. The system will:
   - Detect the face in the current frame
   - Save the face encoding to the database
   - Save a photo to `data/authorized_faces/`
   - Reload the authorized persons list

**Important**: Only one person should be visible to the camera during registration.

### Unlocking from Inside

Press the **Exit Button** (GPIO 22) to unlock the door from inside. This is a safety feature allowing exit without face recognition.

### Normal Operation

- System continuously monitors for faces
- When an authorized person is detected:
  - Door unlocks for 5 seconds
  - Detection logged with photo and timestamp
  - Name displayed on screen
- When an unknown person is detected:
  - Door remains locked
  - Detection logged with photo and timestamp
  - "Unknown" displayed on screen

### Stopping the System

Press **Ctrl+C** to gracefully shut down the system. All components will be cleaned up properly.

## Web Interface

The system includes a web interface for remote monitoring and access management. The web interface runs independently from the main application and can be accessed from any device on your network.

### Features

- **📹 Live Camera Monitoring**: View live camera feed or snapshots
- **👥 Access Management**: Add and delete authorized persons remotely
- **📊 Detection Logs**: View recent detections with timestamps
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices

### Starting the Web Interface

Run the web server:

```bash
cd ~/raspberry-pi-face-recognition-doorlock
python3 web_app.py
```

The web interface will be available at:
- From Raspberry Pi: http://localhost:5000
- From other devices on network: http://192.168.20.203:5000 (use your Pi's IP)

**Optional arguments:**

```bash
python3 web_app.py --host 0.0.0.0 --port 5000 --debug
```

### Using the Web Interface

#### Emergency Unlock

**🚨 The most important feature for safety:**

1. Click the "🚨 Emergency Unlock" button in the header
2. Confirm the action
3. Door unlocks immediately for 5 seconds

**Use this when**:
- Face recognition fails
- Camera not working
- You need to let someone in remotely
- Emergency situations

**Tip**: Bookmark the web interface on your phone for quick access when needed.

#### Monitor Live Camera

- Click "Refresh Snapshot" to get a current frame
- Click "Toggle Stream" to view continuous video feed
- View current system status and authorized person count
- Lock status indicator shows if door is locked or unlocked

#### Add Authorized Person

1. Click "+ Add Person" button
2. Enter the person's name
3. Choose photo source:
   - **Use Current Camera Feed**: Captures from live camera
   - **Upload Photo**: Upload a photo from your device
4. Click "Add Person"

The system will detect the face and save it to the database.

#### Delete Authorized Person

1. Find the person in the "Authorized Persons" list
2. Click the "Delete" button next to their name
3. Confirm deletion

#### View Detection Logs

All recent detections appear in the "Recent Detections" section, showing:
- Photo of detected person
- Timestamp
- Authorization status (Authorized/Unknown)
- Person's name (if authorized)

### Running Web Interface at Startup

To run the web interface automatically on boot alongside the main app:

#### Using Systemd

Create a service file:

```bash
sudo nano /etc/systemd/system/doorlock-web.service
```

Add:

```ini
[Unit]
Description=Door Lock Web Interface
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspberry-pi-face-recognition-doorlock
ExecStart=/usr/bin/python3 /home/pi/raspberry-pi-face-recognition-doorlock/web_app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note**: Adjust paths if you used a different directory name.

Enable and start:

```bash
sudo systemctl enable doorlock-web.service
sudo systemctl start doorlock-web.service
sudo systemctl status doorlock-web.service
```

### Web Interface Security

**Important**: The web interface is designed for use on a trusted local network. For production use, consider:

1. **Enable HTTPS**: Use a reverse proxy (nginx) with SSL certificates
2. **Add Authentication**: Implement login system (Flask-Login)
3. **Firewall**: Restrict access to specific IP addresses
4. **Set Secret Key**: Set the `FLASK_SECRET_KEY` environment variable (see web_interface.py)

Example firewall rule (allow only local network):

```bash
sudo ufw allow from 192.168.20.0/24 to any port 5000
```

## Running at Startup (Recommended)

To automatically start both the main app and web interface on boot, use the provided installation script:

### Automatic Installation

```bash
cd ~/raspberry-pi-face-recognition-doorlock
chmod +x install_services.sh
./install_services.sh
```

This script will:
- Install systemd service files for both main app and web interface
- Configure them to start automatically on boot
- Set correct user and path settings

### Start Services Now

After installation:

```bash
# Start both services
sudo systemctl start doorlock.service
sudo systemctl start doorlock-web.service

# Check status
sudo systemctl status doorlock.service
sudo systemctl status doorlock-web.service

# View live logs
sudo journalctl -u doorlock.service -f
sudo journalctl -u doorlock-web.service -f
```

### Stop Services

```bash
sudo systemctl stop doorlock.service
sudo systemctl stop doorlock-web.service
```

### Disable Auto-Start

```bash
sudo systemctl disable doorlock.service
sudo systemctl disable doorlock-web.service
```

### Manual Service Installation

If you prefer to install manually, service files are provided:
- [doorlock.service](doorlock.service) - Main application
- [doorlock-web.service](doorlock-web.service) - Web interface

See the installation script for details

### Method 2: Desktop Autostart

For systems with a desktop environment:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/doorlock.desktop
```

Add:

```ini
[Desktop Entry]
Type=Application
Name=Door Lock System
Exec=/usr/bin/python3 /home/pi/raspberry-pi-face-recognition-doorlock/app.py
Terminal=false
```

**Note**: Adjust the path if you used a different directory name.

## Configuration

All settings can be adjusted in [config.py](config.py):

### Lock Behavior

```python
UNLOCK_DURATION = 5.0  # Seconds the lock stays unlocked
```

### Face Recognition

```python
FACE_MATCH_TOLERANCE = 0.6  # Lower = stricter (0.5-0.7 recommended)
FRAME_SKIP = 2  # Process every Nth frame (higher = faster but less responsive)
```

### Camera Settings

```python
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
```

### IMX500 AI Settings

```python
# Enable/disable IMX500 onboard AI
USE_IMX500 = True  # Enabled by default for AI Camera
IMX500_MODEL_PATH = None  # Path to .rpk model file
IMX500_CONFIDENCE_THRESHOLD = 0.5  # Detection confidence (0.0-1.0)
IMX500_PERSON_CLASS_ID = 0  # Class ID for person in model
```

### Display Settings

```python
DISPLAY_FULLSCREEN = True
FONT_SIZE_LARGE = 48
FONT_SIZE_MEDIUM = 32
FONT_SIZE_SMALL = 24
```

### Debug Mode

```python
DEBUG_MODE = True  # Enable detailed console output
TEST_MODE = False  # Simulate GPIO without hardware
```

## Database

The system uses SQLite to store:

### Authorized Persons

- ID, name, face encoding, photo path, registration timestamp

### Detection Logs

- Photo path, timestamp, authorized status, person ID

### Viewing Database

```bash
cd ~/raspberry-pi-face-recognition-doorlock
sqlite3 data/database.db

# View authorized persons
SELECT * FROM authorized_persons;

# View recent detections
SELECT * FROM detection_logs ORDER BY timestamp DESC LIMIT 10;

# Exit
.quit
```

## File Structure

```
raspberry-pi-face-recognition-doorlock/
├── app.py                      # Main application
├── web_app.py                  # Web interface launcher
├── web_interface.py            # Flask web server
├── config.py                   # Configuration
├── camera_module.py            # Camera handling
├── face_recognition_module.py  # Face recognition
├── lock_controller.py          # Lock control
├── database.py                 # Database operations
├── logger_module.py            # Photo logging
├── display_interface.py        # GUI display
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   └── index.html             # Web interface HTML
└── data/
    ├── database.db            # SQLite database
    ├── authorized_faces/      # Photos of authorized persons
    └── logs/                  # All detection photos
```

## Troubleshooting

### Camera Not Detected

```bash
# Test camera
libcamera-hello

# Check if camera is enabled
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

### GPIO Permission Denied

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Logout and login again
```

### Face Recognition Too Slow

In [config.py](config.py), increase `FRAME_SKIP`:

```python
FRAME_SKIP = 3  # Process every 3rd frame
```

Or reduce camera resolution:

```python
CAMERA_WIDTH = 480
CAMERA_HEIGHT = 360
```

### Display Issues

If running via SSH, ensure DISPLAY environment variable is set:

```bash
export DISPLAY=:0
python3 app.py
```

### Web Interface Not Accessible

If you can't access the web interface from another device:

```bash
# Check if web server is running
ps aux | grep web_app.py

# Check firewall (if enabled)
sudo ufw status

# Allow port 5000
sudo ufw allow 5000

# Find your Raspberry Pi IP address
hostname -I
```

Access using: http://YOUR_PI_IP:5000

### Port Already in Use

If port 5000 is already in use:

```bash
# Use a different port
python3 web_app.py --port 8080
```

## Security Considerations

1. **Physical Security**: Ensure the Raspberry Pi and relay are in a secure location
2. **Database Backup**: Regularly backup `data/database.db` and `data/authorized_faces/`
3. **Emergency Access**: Consider adding a physical key override
4. **Face Recognition Limits**: Face recognition can be fooled by photos - consider adding liveness detection for high-security applications
5. **Network Security**: If exposing any network services, use proper authentication

## Maintenance

### Regular Tasks

- Check database size: `du -h data/database.db`
- Check log photos: `du -h data/logs/`
- Clean old logs if needed (automatic cleanup can be enabled in config)

### Removing Authorized Persons

Currently, persons must be removed directly from the database:

```bash
sqlite3 data/database.db
DELETE FROM authorized_persons WHERE id = X;
.quit
```

Then restart the application to reload.

## Credits

Built using:
- [picamera2](https://github.com/raspberrypi/picamera2) - Raspberry Pi camera interface
- [face_recognition](https://github.com/ageitgey/face_recognition) - Face recognition library
- [pygame](https://www.pygame.org/) - Display interface
- [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) - GPIO control

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions, please check:
1. This README
2. Configuration in [config.py](config.py)
3. Console output when running with `DEBUG_MODE = True`
