#!/usr/bin/env bash
sh /etc/init.d/px-daemon stop
rm /etc/init.d/px-daemon /usr/sbin/px /usr/sbin/pxyscrape /usr/sbin/geoip
rm -rf /home/px
userdel -r -f px
apt remove libmaxminddb0 libmaxminddb-dev mmdb-bin
