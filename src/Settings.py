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


# data_folder = path.join(etc_folder, 'data')
# log_folder = path.join(etc_folder, 'logs')
# ext_folder = path.join(etc_folder, 'ext')

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
 
#exit(1)

version = "1.1.0"
_version = 0


#################
# Configuration #
#################

safe_run = False
backup_at = 60*60*24*7 # 7 days
keep_unregonized_protocols = False

##
# Collection policies
###
collect_protocol = [
  'socks5',
  'socks4'
  'https'
  'http'
]

##
# Remove policies
# Proxies...
###
remove_by_reliance = .10
remove_when_total = 25  # Greater than
remove_when_time_kept = (60 ** 2) * 24 * 2  # 2 days


##
# Proxy mining
###
mine_wait_time = 60 * 60  # 1 hour

# Connection info
global_timeout = 30
socket_backlog = 1
max_sql_queue_size = 1000
local_conn = ('127.0.0.1', 52312)

##
# Advanced features - ps don't touch if you don't know what is
###
raw_sql_exec = False
threads = 4
allow_thread_sleeping = True
threading_sleep_time = 60 * 5
thread_sleep_threshold = 10
