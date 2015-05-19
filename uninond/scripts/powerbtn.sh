#!/bin/sh

# Initiates a shutdown when the power putton has been pressed.

if [ "$1" = "" ];
then
	MSG = "Power button pressed"
else
	MSG = $1
fi

# close firefox nicely
DISPLAY=:0 sudo -u uninond xdotool key alt+F4 && sleep 1
sudo -u uninond kill -1 `pgrep -f firefox` && sleep 1

# Skip if we just in the middle of resuming.
test -f /var/lock/acpisleep && exit 0

# If all else failed, just initiate a plain shutdown.
/sbin/shutdown -h now ${MSG}
