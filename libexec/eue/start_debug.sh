#!/bin/bash
export DISPLAY=:999
echo "Starting Xvfb and vncserver on display on $DISPLAY"
Xvfb -screen 0 1280x1024x24 $DISPLAY &
sleep 5
x11vnc -display $DISPLAY &
sleep 2
echo "ready"
