# px
This tool is a daemon with (over sockets) CLI tools. used for collecting (Sqlite3), storing and checking proxy servers.

Current Version: 1.1.0

### Change list
  **-----1.1.0 or older -----**
    + Added sqlite3worker (1.0.3)
    + Added multithreaded proxy scanning (1.0.4)
    + Added portable mods for adding custom website crawls (1.0.5)
    + Added logic expressions in `etc/data/provider.json` (1.0.5)
    + Added portable moddable logical expressions (1.0.7)
    + Added portable mods for sys_commands (1.1.0)
    + Added portable mods for tasks (1.1.0)
    +! Command outline change (1.1.0)
  
### What it don't
  - It can't scan proxies with authenification enabled.
  - It currently cannot determine anonminity level for http proxies
  
### What we've tested
  + It runs on linux. Debian like distros. Modify it how you please to run on your own system
  + It can run as a service/daemon (Atleast it did on ubuntu and debian)
  + Its fine with huge amounts of shell calls on `px`

### Bugs
  None Found.
  
### Known risks
  All risks appear to be interal threats if implemented correctly.

### Configuration
You will find in `src/Settings.py` configuration for the program, these options are yet to be documented due to the fact they are ever changing. Until further notice, there will be no efforts to document them other than their describing names.


### Running it
    cd /path/to/dir
    python src/px-daemon.py &
    ./px -i


### px   

Command line interface for `px-daemon`, this interacts with storing, collecting, and scanning proxies.

    [-h | --help] 
      This displayed help message.
      
    [-g | --get] receives proxy(s) for you
    [-i | --info] general application runtime stats
    [--providers] stats for providers loaded.
    [--scrape] force parent to scrape
    [--pinfo] info about proxy by uuid


