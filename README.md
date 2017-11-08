# px
This tool is used for collecting, storing and checking proxy servers.
What it does, what it doesn't.

## What it do
  + It scrapes proxies off webpages, you can find this etc/data/providers.json, the command line too also allows easy adding and removing
  + It collects, sorts, and checks these proxies for us in the background
  + It uses some fancy regex to dismantle data and find IP and Port Patterns.
  + It only takes an IP and port Pair and the rest is done inside of the system.
  + Its pretty configurable, theres still lots of stuff to add.

## What it don't
  - It can't scan proxies with authenification enabled.

## What we've tested
  + It runs on linux
  + It can run as a service/daemon
  + Its fine with huge amounts of shell calls

## What we've added and never tried testing
  + We added phantomjs for the fact that some web pages will generate via javascript. Never tried using it.
  + Numerous amounts of commands written into `px` and connected to `commands.py`

## Bugs
  + Sometimes theres a weird Provider Object bug that says theres no proxies to be found from that provider. Still working on it.
  
## Known risks
  + Its probably common knowledge, but we never explicitly hardcoded each commands, so it's probably more than possible for a raw injection of python into the implementation of the socket structure that communicates `px` and `pxf.py/px-daemon`

## Implementation of install
  So I figured that the safest way to do this was to make a user called `px` and then make no files actually owned by it, but go ahead and run the daemon as that user so if there were to an injection in `px-daemon` then, it would atleast miminalize the fact they no longer have root privelleges.
