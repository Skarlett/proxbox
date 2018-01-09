#!/usr/bin/env bash
BASEDIR=$(dirname $0)

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "installing binaries needed"
add-apt-repository ppa:maxmind/ppa
apt update
apt-get install python-pip python-virtualenv libmaxminddb0 libmaxminddb-dev mmdb-bin

echo "Making user..."
useradd -r -m -s /bin/false -g px px
echo "Moving files to new user home"
mv * /home/px
chown -R px:px /home/px


echo "setting up virtualenv"
mkdir /home/px/venv
virtualenv venv
source venv/bin/activate
echo "installing python dependencies"
pip install -r /home/px/requirements.txt

echo "Checking dependencies"
if [ "$(python -c "import sqlite3worker, requests, cfscrape, maxminddb, selenium;print(True)")" == "True" ]; then
  echo "Test completed successfully."
else
  echo "Test failed. Stopping installation"
  exit 1
fi
chmod +x /home/px/sys_tools/*
echo "Setting up soft links to /usr/sbin"
ln -s /home/px/sys_tools/px /usr/sbin/px
ln -s /home/px/sys_tools/geo /usr/sbin/geo
ln -s /home/px/sys_tools/pxyscrape /usr/sbin/pxyscrape
echo "Setting up system service"

mv /home/px/etc/px-daemon /etc/init.d/px-daemon
echo "starting service..."
sh /etc/init.d/px-daemon start
