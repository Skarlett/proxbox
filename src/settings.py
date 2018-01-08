####
# Default stuff
####
from os import path
import logging
import requests
##############################
# Application configuration  #
##############################

##
# Directory setup
###

maindir = path.split(path.split(__file__)[0])[0]
source_folder = path.split(__file__)[0]
etc_folder = path.join(maindir, 'etc')
bin_folder = path.join(etc_folder, 'bin')
backup_folder = path.join(etc_folder, 'backups')
providers_folder = path.join(etc_folder, 'providers')
ext_folder = path.join(etc_folder, 'ext')

##
# Files
###
database = path.join(etc_folder, 'proxies.sqlite3')
log = path.join(maindir, 'main.log')


public_ip = None

try:
  public_ip = requests.get('http://ipv4bot.whatismyipaddress.com/').content.strip()
except:
  logging.error("No internet Connection.")
 

version = "1.1.5"


#################
# Configuration #
#################
threads = 4


##
# Proxy Collection Configuration
###
# Protocols to collect
collect_protocol = [
  'socks5',
  'socks4',
  'https',
  'http',
]

# Remove proxy policies
remove_by_reliance = .10
remove_when_total = 25  # Greater than
remove_when_time_kept = (60 ** 2) * 24 * 2  # 2 days
mine_wait_time = 3600  # 1 hour


##
# Connection info
###
global_timeout = 5
socket_backlog = 5
max_sql_queue_size = 1000
local_conn = ('127.0.0.1', 52312)
