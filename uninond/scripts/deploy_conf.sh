#!/bin/bash
set -e  # exit script on any failure

# install configuration files on the system. must be run as root

if [ "$EUID" -ne 0 ]
	then echo "Please run as root"
 	exit 1
fi	

SCRIPTS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${SCRIPTS_DIR}

HOMED=/home/uninond

# ACPI
cp -v ../conf/acpi_low_battery /etc/acpi/events/low_battery
cp -v ../conf/acpi_powerbtn /etc/acpi/events/powerbtn
chmod 644 /etc/acpi/events/{low_battery,powerbtn}

# home
cp -v ../conf/dot_fehbg ${HOMED}/.fehbg
chmod 664 ${HOMED}/.fehbg
cp -v ../conf/dot_xinitrc ${HOMED}/.xinitrc
chmod 744 ${HOMED}/.fehbg
cp -v ../conf/fluxbox_overlay ${HOMED}/.fluxbox/overlay
cp -v ../conf/fluxbox_apps ${HOMED}/.fluxbox/apps
cp -v ../conf/fluxbox_init ${HOMED}/.fluxbox/init
cp -v ../conf/fluxbox_menu ${HOMED}/.fluxbox/menu
cp -v ../conf/fluxbox_lastwallpaper ${HOMED}/.fluxbox/lastwallpaper
chmod 664 ${HOMED}/.fluxbox/{apps,overlay,menu,init,lastwallpaper}
cp -v ../conf/fluxbox_startup ${HOMED}/.fluxbox/startup
chmod 744 ${HOMED}/.fluxbox/startup
chown -R uninond:uninond /home/uninond/.fluxbox
chown uninond:uninond /home/uninond/{.xinitrc,.fehbg}

# uninond crontab
cp -v ../conf/uninond_crontab /var/spool/cron/crontabs/uninond
chown uninond:crontab /var/spool/cron/crontabs/uninond
chmod 600 /var/spool/cron/crontabs/uninond

# tty1 for autologin
cp -v ../conf/tty1.conf /etc/init/tty1.conf
chmod 644 /etc/init/tty1.conf

# udev
cp -v ../conf/udev_10-usbmount.rules /etc/udev/rules.d/10-usbmount.rules
chmod 644 /etc/udev/rules.d/10-usbmount.rules

# disable systemd handling of acpi power button
cp -v ../conf/systemd_logind.conf /etc/systemd/logind.conf
chmod 644 /etc/systemd/logind.conf

# root crontab
cp -v ../conf/root_crontab /etc/crontab

# sudoers for shutdown and mount
cat ../conf/sudoers >> /etc/sudoers
sudo -h # check if sudo is not broken
