#!/bin/bash

# sleep first so fluxbox has time to load
# sleep 1

# check for firefox process
# launch firefox on first display
pgrep -f firefox || LC_ALL=fr_FR.UTF-8 firefox --display :0 

sleep 3

# emulate a touch on F11 to go fullscreen
DISPLAY=:0 xdotool key F11
