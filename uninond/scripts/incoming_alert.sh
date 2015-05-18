#!/bin/bash

cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# play the siren sound
aplay ../static/alert-siren.wav &

# wake up screen
xdotool key alt && xdotool key alt && xdotool key alt
