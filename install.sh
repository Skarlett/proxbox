#!/usr/bin/env bash
BASEDIR=$(dirname $0)

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
echo "Making user..."
useradd -r -g -m -s /bin/false px px
echo "Moving files to new user home"
mv * /home/px
chown -R px:px /home/px
mkdir /home/px/venv
apt-get install python-pip python-virtualenv

virtualenv venv
source venv/bin/activate
pip install -r /home/px/requirements.txt

echo "Checking dependencies"
if [ "$(python -c "import sqlite3worker, requests, cfscrape, maxminddb, selenium;print(True)")" == "True" ]; then
  echo "Test completed successfully."
else
  echo "Test failed. Stopping installation"
  exit 1
fi

mv /home/px/etc/px-daemon /etc/init.d/px-daemon
sh /etc/init.d/px-daemon start
