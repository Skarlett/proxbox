# px
This tool is used for collecting, storing and checking proxy servers.
Current Version: 1.0.5
### Change list
  + Added sqlite3worker

### Todo
    [X] Safe run
    [ ] Add dynamic logging handle for debugging outside of development
    [X] Add support for http proxies
    [ ] determine if http proxy is protected by ssl/tsl or whatever new variant.
    [ ] Add support for socks4 proxies
    [X] add support for selecting which proxies to collect
    [X] Add command line support for specifying proxy protocol
    [X] Add support for "special" providers that are specific to the proxy protocol
      Example socks24.org is special to socks 5, so if we only want to scrape http proxies,
      that shouldn't be scraped
    [X] add phantomjs for scraping pages generated by JS
    [ ] seperate settings into a .conf file in etc/
    [ ] add regex pattern reference in add providers | right now it uses global ip and port find regex
    [ ] add filters (transparent, obscured, elite) for searching and collecting | sooner or later
    [X] Make set-up file
    [X] auto back up & compress
    [ ] add json output to get
    [X] directly connect skeleton.py to commands
    [X] enforce uuid in command add providers
    [X] converge factory and proxyframe so both providers file and database are purged
    [X] switch over to sqlite3worker eventually, maybe a modified version.
    [ ] massscan le internet, once i figure out how to collect banners.
    [ ] optimize scanning ips in providers



### What it do
  + It scrapes proxies off webpages, you can find this etc/data/providers.json, the command line too also allows easy adding and removing
  + It collects, sorts, and checks these proxies for us in the background
  + It uses some fancy regex to dismantle data and find IP and Port Patterns.
  + It only takes an IP and port Pair and the rest is done inside of the system.
  + Its pretty configurable, theres still lots of stuff to add.

### What it don't
  - It can't scan proxies with authenification enabled.
  - It currently cannot determine anonminity level for http proxies
  
### What we've tested
  + It runs on linux. Debian like distros. Modify it how you please to run on your own system
  + It can run as a service/daemon (Atleast it did on ubuntu and debian)
  + Its fine with huge amounts of shell calls on `px`

### What we've added and never tried testing
  + We added phantomjs for the fact that some web pages will generate via javascript. Never tried using it.
  + Numerous amounts of commands written into `px` and connected to `commands.py`
     - Here's a list of all the buggy ones we know of
     - `px -sc -f`
     - `px -a`

### Bugs
  + Sometimes theres a weird Provider Object bug that says theres no proxies to be found from that provider. Still working on it.
  
### Known risks
  + Its probably common knowledge, but we never explicitly hardcoded each commands, so it's probably more than possible for a raw injection of python into the implementation of the socket structure that communicates `px` and `pxf.py/px-daemon`

### Implementation of install
  So I figured that the safest way to do this was to make a user called `px` and then make `/opt/px` owned by it, but go ahead and run the daemon as that user so if there were to an injection in `px-daemon` then, it would atleast miminalize the fact they no longer have root privelleges. Further more since it would be a socket injection it is highly recommended to run this on local host, with the port its listening on closed. ( Later on I need to make px-daemon.py owned by root and give perms to only read and exec)


#### Configuration
You will find in `src/Settings.py` configuration for the program, these options are yet to be documented due to the fact they are ever changing. Until further notice, there will be no efforts to document them other than their describing names.

#### Global Installation (Linux)
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
    [--reload-providers] reload providers.json

After starting the `px-daemon` service or running `src/pxf.py` It will attempt to fill the database with proxies from the providers list. 
Any provider you add during it's runtime will delayed shortly before scraped, while at boot time will be appended immdiately and soon after will be scraped.

To start the `px-daemon` just in case it stopped you can run the following.
This is also the case you should use if `px` ever returns `"ProxyMiner isn't online."`

    sh /etc/init.d/px-daemon start


### Providers.json
This file is unique in some ways, it contains all the places as to where to get the proxies from. Including keywords...

`renewal (int)` which is how often the proxy source should be scraped, **counted in seconds.**
`use (bool)` Which specifies if this proxy srouce should be used
`type (socks5|http|nonspecific)` This contains the protocol, if a source specifically gives a certain protocol, this should be specified. In unpredictable enviorments, `nonspecific` should be used instead of a protocol.

In the url list field under `types`, there is logic the can be applied to quickly generate predictable url strings.
The current implied syntax is currently as following.

###### Range Operator
This specific operator will yield multiple urls from a single one, by iterating the place `{` and `}` and replacing it with a number between its iterations.

    http://myproxies.com/page/{0-20}/


A single entry example of this would be...

        "xroxy.com": {
            "renewal": 86400,
            "types": {
              "socks5": [
                "http://www.xroxy.com/proxylist.php?port=&type=Socks5&pnum={0-9}#table"
              ],
              "http": [
                "http://www.xroxy.com/proxylist.php?port=&type=All_http&ssl=&country=&latency=&reliability=&sort=reliability&desc=true&pnum={0-149}#table"
             ]
            },
            "jsgen":false,
            "use": true
        }

##### Errors and output
  + Errors: `/var/log/px-daemon.err`
  + stdout: `/var/log/px-daemon.log`


##### Notes
Keep in mind this project is still in development and should be considered "as is" with no warranty of operation.
