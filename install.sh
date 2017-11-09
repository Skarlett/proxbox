#!/usr/bin/env bash
BASEDIR=$(dirname $0)


if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
echo "Starting..."

python -m pip install setuptools
python -m pip install sqlite3worker

chmod +x "$BASEDIR/src/pxf.py"
chmod +x "$BASEDIR/src/skeleton.py"
chmod +x "$BASEDIR/src/geo.py"
chmod +x "$BASEDIR/src/px"

echo "Attempting to install as a service/daemon on the system. Only works on linux."
echo "Adding user px..."
useradd -M px
deluser px sudo # No sudo for you

mkdir /opt/px

echo "Copying files to install directory"

cp -R "$BASEDIR/*" /opt/px/

echo "Creating soft links in /usr/sbin"

ln -s /opt/px/src/skeleton.py /usr/sbin/pxyscrape
echo "Made command pxyscrape"

ln -s /opt/px/src/geo.py /usr/sbin/geoip
echo "Made command geoip"

ln -s /opt/px/src/px /usr/sbin/px
echo "Made command px"

chown -R px:px /opt/px
chmod +x /opt/px

cp "$BASEDIR/px-daemon" "/etc/init.d/px-daemon"
chown root:root /etc/init.d/px-daemon
echo "copying files to init.d..."
cp "$BASEDIR/px-daemon" /etc/init.d/px-daemon
sh /etc/init.d/px-daemon start

echo "checking if it ran..."
if [ "$(sh /etc/init.d/px-daemon status)"=="Running" ]; then
  echo "Service installed correctly!"
else
  echo "Failed to install service"
fi

