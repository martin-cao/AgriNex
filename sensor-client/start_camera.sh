#!/bin/bash

# AgriNex Camera Sensor Client Startup Script
# 启动摄像头传感器客户端

echo "=== AgriNex Camera Sensor Client ==="
echo "Starting camera sensor client..."

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Check if config exists
if [ ! -f "config/camera_client.json" ]; then
    echo "Config file not found, creating default config..."
    mkdir -p config
fi

# Default arguments
ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --simulation)
            ARGS="$ARGS --simulation"
            echo "Simulation mode enabled"
            shift
            ;;
        --image)
            ARGS="$ARGS --capture-type image"
            echo "Image capture mode"
            shift
            ;;
        --video)
            ARGS="$ARGS --capture-type video"
            echo "Video capture mode"
            shift
            ;;
        --interval)
            ARGS="$ARGS --interval $2"
            echo "Capture interval: $2 seconds"
            shift 2
            ;;
        --no-auto)
            ARGS="$ARGS --no-auto-capture"
            echo "Automatic capture disabled"
            shift
            ;;
        --camera)
            ARGS="$ARGS --camera-index $2"
            echo "Camera index: $2"
            shift 2
            ;;
        --duration)
            ARGS="$ARGS --video-duration $2"
            echo "Video duration: $2 seconds"
            shift 2
            ;;
        --debug)
            ARGS="$ARGS --log-level DEBUG"
            echo "Debug logging enabled"
            shift
            ;;
        --mqtt-host)
            ARGS="$ARGS --mqtt-host $2"
            echo "MQTT host: $2"
            shift 2
            ;;
        --mqtt-port)
            ARGS="$ARGS --mqtt-port $2"
            echo "MQTT port: $2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --simulation          Enable simulation mode (no real camera)"
            echo "  --image               Capture images"
            echo "  --video               Capture videos"
            echo "  --interval SECONDS    Capture interval in seconds"
            echo "  --no-auto             Disable automatic capture"
            echo "  --camera INDEX        Camera device index (default: 0)"
            echo "  --duration SECONDS    Video duration in seconds"
            echo "  --debug               Enable debug logging"
            echo "  --mqtt-host HOST      MQTT broker host"
            echo "  --mqtt-port PORT      MQTT broker port"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --simulation --image --interval 30"
            echo "  $0 --video --duration 15 --camera 1"
            echo "  $0 --no-auto --debug"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Start the camera client
echo "Starting camera sensor client with arguments: $ARGS"
echo "Press Ctrl+C to stop..."
echo ""

exec python3 camera_main.py "$ARGS"

echo ""
echo "Camera sensor client stopped."
