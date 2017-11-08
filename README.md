# px
This tool is used for collecting, storing and checking proxy servers.
Current Version: 1.0.3

### What it do
  + It scrapes proxies off webpages, you can find this etc/data/providers.json, the command line too also allows easy adding and removing
  + It collects, sorts, and checks these proxies for us in the background
  + It uses some fancy regex to dismantle data and find IP and Port Patterns.
  + It only takes an IP and port Pair and the rest is done inside of the system.
  + Its pretty configurable, theres still lots of stuff to add.

### What it don't
  - It can't scan proxies with authenification enabled.

### What we've tested
  + It runs on linux
  + It can run as a service/daemon
  + Its fine with huge amounts of shell calls

### What we've added and never tried testing
  + We added phantomjs for the fact that some web pages will generate via javascript. Never tried using it.
  + Numerous amounts of commands written into `px` and connected to `commands.py`

### Bugs
  + Sometimes theres a weird Provider Object bug that says theres no proxies to be found from that provider. Still working on it.
  
### Known risks
  + Its probably common knowledge, but we never explicitly hardcoded each commands, so it's probably more than possible for a raw injection of python into the implementation of the socket structure that communicates `px` and `pxf.py/px-daemon`

### Implementation of install
  So I figured that the safest way to do this was to make a user called `px` and then make no files actually owned by it, but go ahead and run the daemon as that user so if there were to an injection in `px-daemon` then, it would atleast miminalize the fact they no longer have root privelleges.

#### Global Installation
This will install the script under /etc/init.d/px-daemon, run it through a user named PX and install utility commands like `px`, `geoip`, and `pxyscrape` into `/usr/sbin`

    sudo ./install.sh
    px -i

#### Local run
    cd /path/to/dir
    python src/pxf.py &
    ./px -i

#### Command line tools
    [-h --help]
    [-g --get,
      ( -b | --bot Formats for easy scraping)
      (-nc | --no-check Doesnt check proxies for being online before giving them)
      (-a | --all Doesnt check proxies are marked as online before giving them)
      (-t | --time-out [int] inserts timeout value)
    ]
    [-i --info] shows current state of program 
    [-p --pinfo (UUID)] shows information on a proxy based on UUID
    [-sc --scrape (-f | --force) Forces a proxy scrape] scrape your provider sources, and add them to the db
    [-t --total] get total number of proxies in data
    [-oc --online-count] returns number of proxies marked alive
    [--uptime] returns the time at which the service was last rebooted
    [-a --add (URL/FilePath)] scrapes and adds to proxies in database
    [-ap --add-provider (scrape time) (URL)] adds URLs to providers list
    [-dp --del-provider (UUID)] removes URL to providers list
    [--providers] Shows statistics on each provider

After starting the `px-daemon` service or running `src/pxf.py` It will attempt to fill the database with proxies from the providers list. 
Any provider you add during it's runtime will delayed shortly before scraped, while at boot time will be appended immdiately and soon after will be scraped.

To start the `px-daemon` just in case it stopped you can run the following.
This is also the case you should use if `px` ever returns `"ProxyMiner isn't online."`

    sh /etc/init.d/px-daemon start

##### Errors and output
  + Errors: `/var/log/px-daemon.err`
  + stdout: `/var/log/px-daemon.log`


##### Notes
Keep in mind this project is still in development and should be considered "as is" with no warranty of operation, use or responsibility to it's use. Further more, I wish you all a good day.
