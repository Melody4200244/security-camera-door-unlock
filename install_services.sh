#!/bin/bash
# Installation script for Door Lock System services
# Run this script to set up systemd services for automatic startup

set -e  # Exit on error

echo "============================================"
echo "Door Lock System - Service Installation"
echo "============================================"
echo ""

# Check if running as regular user (not root)
if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Do not run this script as root!"
    echo "Run as: ./install_services.sh"
    exit 1
fi

# Get the current user and directory
CURRENT_USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Current user: $CURRENT_USER"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Update service files with correct user and paths
echo "Updating service files with your username and paths..."

# Create temporary service files with correct paths
sed "s|User=guillaume|User=$CURRENT_USER|g; s|/home/guillaume/serrure_automatique|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/doorlock.service" > /tmp/doorlock.service

sed "s|User=guillaume|User=$CURRENT_USER|g; s|/home/guillaume/serrure_automatique|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/doorlock-web.service" > /tmp/doorlock-web.service

echo "✓ Service files updated"
echo ""

# Copy service files to systemd
echo "Installing systemd service files..."
sudo cp /tmp/doorlock.service /etc/systemd/system/
sudo cp /tmp/doorlock-web.service /etc/systemd/system/

echo "✓ Service files copied to /etc/systemd/system/"
echo ""

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
echo "✓ Systemd reloaded"
echo ""

# Enable services
echo "Enabling services to start on boot..."
sudo systemctl enable doorlock.service
sudo systemctl enable doorlock-web.service
echo "✓ Services enabled"
echo ""

# Show service status
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Services installed:"
echo "  • doorlock.service - Main door lock application (with display)"
echo "  • doorlock-web.service - Web interface (port 5000)"
echo ""
echo "To start the services now:"
echo "  sudo systemctl start doorlock.service"
echo "  sudo systemctl start doorlock-web.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status doorlock.service"
echo "  sudo systemctl status doorlock-web.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u doorlock.service -f"
echo "  sudo journalctl -u doorlock-web.service -f"
echo ""
echo "To stop the services:"
echo "  sudo systemctl stop doorlock.service"
echo "  sudo systemctl stop doorlock-web.service"
echo ""
echo "To disable auto-start on boot:"
echo "  sudo systemctl disable doorlock.service"
echo "  sudo systemctl disable doorlock-web.service"
echo ""
echo "Web interface will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
