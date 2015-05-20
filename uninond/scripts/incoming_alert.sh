#!/bin/bash

cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# play the siren sound
aplay ../static/alert-siren.wav &

# wake up screen
DISPLAY=:0 xdotool key alt && DISPLAY=:0 xdotool key alt && DISPLAY=:0 xdotool key alt
