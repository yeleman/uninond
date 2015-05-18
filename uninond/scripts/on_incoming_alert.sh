#!/bin/bash

# wake up screen
DISPLAY=:0 xdotool key alt && xdotool key alt && xdotool key alt

# play incoming alert siren
aplay ../static/alert-siren.wav
