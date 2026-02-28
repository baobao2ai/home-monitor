#!/bin/bash
# test_stream.sh — Test the full pipeline using your phone as a camera.
#
# BEFORE CAMERAS ARRIVE: Use this to validate Frigate + GPU + digest scripts.
#
# Instructions:
#   1. Install "IP Webcam" on Android (or "Camo" on iPhone)
#   2. Start the stream on your phone → note the IP address shown
#   3. Run this script: ./scripts/test_stream.sh <phone_ip>
#
# Example:
#   ./scripts/test_stream.sh 192.168.1.50

set -e

PHONE_IP="${1:-}"

if [ -z "$PHONE_IP" ]; then
  echo "Usage: $0 <phone_ip>"
  echo "Example: $0 192.168.1.50"
  echo ""
  echo "Instructions:"
  echo "  Android: Install 'IP Webcam' app, start server, note the IP"
  echo "  iPhone:  Install 'Camo' or 'EpocCam' app"
  exit 1
fi

RTSP_URL="rtsp://${PHONE_IP}:8554/video"
echo "[+] Testing stream: $RTSP_URL"

# Test 1: Can ffmpeg reach the stream?
echo ""
echo "── Test 1: Stream connectivity ──"
ffprobe -v quiet -print_format json -show_streams "$RTSP_URL" 2>&1 | head -20 && echo "✓ Stream OK" || {
  echo "✗ Cannot reach stream. Check:"
  echo "  - Phone and computer on same WiFi?"
  echo "  - IP Webcam app is running?"
  echo "  - Try: rtsp://${PHONE_IP}:8080/video (alternate port)"
  exit 1
}

# Test 2: Write a temp Frigate config with phone stream
echo ""
echo "── Test 2: Generating test Frigate config ──"
cat > /tmp/test_config.yml << EOF
mqtt:
  enabled: false

detectors:
  tensorrt:
    type: tensorrt
    device: 0

cameras:
  test_phone:
    enabled: true
    ffmpeg:
      inputs:
        - path: ${RTSP_URL}
          roles:
            - detect
            - record
    detect:
      width: 1280
      height: 720
      fps: 5

objects:
  track:
    - person
    - dog
    - cat

record:
  enabled: true
  retain:
    days: 1
    mode: motion

snapshots:
  enabled: true
EOF

echo "✓ Test config written to /tmp/test_config.yml"

# Test 3: Launch Frigate with test config
echo ""
echo "── Test 3: Launching Frigate with phone stream ──"
echo "Press Ctrl+C to stop"
echo ""

docker run --rm \
  --name frigate-test \
  --gpus all \
  --shm-size=128m \
  -p 5000:5000 \
  -v /tmp/test_config.yml:/config/config.yml \
  -v /tmp/frigate-test-storage:/media/frigate \
  ghcr.io/blakeblackshear/frigate:stable

echo ""
echo "── Test complete ──"
echo "If Frigate started, open http://localhost:5000 to see your phone feed."
echo "Walk in front of it to trigger detection."
echo "Then run the digest script to test end-to-end:"
echo "  python3 scripts/daily_digest.py --dry-run"
