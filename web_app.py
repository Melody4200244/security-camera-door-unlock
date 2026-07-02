#!/usr/bin/env python3
"""
Web Application Launcher for Door Lock System
Run this to start the web interface on port 5000

This can run alongside the main app.py or standalone.
"""

import sys
import argparse
from web_interface import run_server

def main():
    parser = argparse.ArgumentParser(description='Door Lock Web Interface')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host to bind to (default: 0.0.0.0 for all interfaces)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to listen on (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')

    args = parser.parse_args()

    print("=" * 60)
    print("Door Lock System - Web Interface")
    print("=" * 60)
    print(f"Starting web server on http://{args.host}:{args.port}")
    print(f"Access from your network: http://192.168.20.203:{args.port}")
    print()
    print("Features:")
    print("  - Live camera monitoring")
    print("  - Add/delete authorized persons")
    print("  - View detection logs")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
