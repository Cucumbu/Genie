#!/bin/bash
set -e
cd "$(dirname "$0")/.."
Xvfb :99 -screen 0 1280x720x24 &
export DISPLAY=:99
pulseaudio --start || true
pactl load-module module-null-sink sink_name=virtual_speaker || true
pactl load-module module-loopback source=virtual_speaker.monitor || true
export PULSE_SINK=virtual_speaker
python3 main.py