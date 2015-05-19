#!/bin/bash

if [ "$1" = "" ]; then
	iface="wlan0"
else
	iface=$1
fi

# static ip for self
ifconfig ${iface} up 10.0.0.1 netmask 255.255.255.0
sleep 2

# start dhcpd
if [ "$(ps -e | grep dhcpd)" == "" ]; then
dhcpd ${iface} &
fi

# forward packet (not needed here)
sysctl -w net.ipv4.ip_forward=1

# hostapd handles the rest
hostapd /home/uninond/uninond/uninond/conf/hostapd.conf 1>/dev/null

# kill dhcp
killall dhcpd
