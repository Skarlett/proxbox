#!/usr/bin/env bash
BASEDIR=$(dirname $0)


if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
echo "Starting..."

apt-get install python-pip
# apt-get install phantomjs

echo "Installing dependencies"
python -m pip install setuptools
python -m pip install sqlite3worker
python -m pip install requests
python -m pip install cfscrape
python -m pip install selenium
echo "Checking dependencies"
if [ "$(python -c "import sqlite3worker;import requests;import cfscrape;import selenium;print(True)")" == "True" ]; then
  echo "Test completed successfully."
else
  echo "Test failed. Stopping installation"
fi

chmod +x "$BASEDIR/src/pxf.py"
chmod +x "$BASEDIR/src/skeleton.py"
chmod +x "$BASEDIR/src/geo.py"
chmod +x "$BASEDIR/src/px"

echo "Install PhantomJS"
if [ -f /usr/bin/phantomjs ]; then [:]
else
  if [ "$(uname -m)"=="x86_64" ]; then
    phantom_download="https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2"
  else
    phantom_download="https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-i686.tar.bz2"
  fi
  phantomTar=$(tempfile)
  phantomDir=$(tempfile)
  mkdir $phantomDir
  wget "$phantom_download" -O $phantomTar
  tar xjvf $phantomTar -C $phantomDir
  cp "$phantomDir/bin/phantomjs" /usr/bin/phantomjs
  # Cleanup
  rm $phantomTar
  rm -rf $phantomDir
fi

if [ "$1" == "global" ]; then
    echo "Attempting to install as a service/daemon on the system. Only works on linux."
    echo "Adding user px..."
    useradd -M -s /bin/false px

    mkdir /opt/px

    echo "Copying files to install directory"

    cp -R "$BASEDIR/src/" /opt/px/
    cp -R "$BASEDIR/etc/" /opt/px/

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
    if [ -f "/etc/init.d/px-daemon" ]
    then
        #echo "$file found."
        if [ "$(sh /etc/init.d/px-daemon status)"!="Running" ]; then
          sh /etc/init.d/px-daemon start
        fi
    else
        cp "$BASEDIR/px-daemon" /etc/init.d/px-daemon
        sh /etc/init.d/px-daemon start
    fi

    if [ "$(sh /etc/init.d/px-daemon status)"=="Running" ]; then
      echo "Service installed correctly!"
    else
      echo "Failed to install service"
    fi
fi

echo "Done"