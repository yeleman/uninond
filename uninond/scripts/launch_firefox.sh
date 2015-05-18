#!/bin/bash

# sleep first so fluxbox has time to load
sleep 1

# check for firefox process
# launch firefox on first display
pgrep -f firefox || firefox --display :0 

sleep 3

# emulate a touch on F11 to go fullscreen
xdotool key F11
