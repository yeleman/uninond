#!/bin/bash

# cw to django folder
cd /home/uninond/uninond

# debug dump of udev env to a file
# set 2>1 >> /tmp/usbdevinfo

# play the please-wait sound
aplay ./uninond/static/please-wait.wav

# mount the device in auto mode
sudo mount -o uid=uninond,gid=users,fmask=113,dmask=002 ${DEVNAME}1 /mnt || { aplay ./uninond/static/export-failed.wav; exit 1; }

# actually write report on media
pew in uninondenv ./manage.py export_xls -f /mnt || { aplay ./uninond/static/export-failed.wav; exit 1; }

# unmount the device
sleep 3
sudo umount /mnt || { aplay ./uninond/static/export-failed.wav; exit 1; }

# play the success sound
aplay ./uninond/static/export-complete.wav
