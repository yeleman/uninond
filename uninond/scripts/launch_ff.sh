#!/bin/bash

pgrep -f firefox
if [ $? -ne 0 ];
then
	# launch firefox in french
	# then emulate a touch on F11 to go fullscreen
    LC_ALL=fr_FR.UTF-8 firefox --display :0 && sleep 3 && DISPLAY=:0 xdotool key F11
fi
