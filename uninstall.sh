#!/usr/bin/env bash
sh /etc/init.d/px-daemon stop
rm /etc/init.d/px-daemon /usr/sbin/px /usr/sbin/pxyscrape /usr/sbin/geoip
rm -rf /opt/px
userdel -r px
