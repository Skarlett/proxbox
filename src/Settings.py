####
# Default stuff
####
from os import path, mkdir
from urllib import urlretrieve
import logging
import requests
##############################
# Application configuration  #
##############################

##
# Directory setup
###

maindir = path.split(path.split(__file__)[0])[0]
etc_folder = path.join(maindir, 'etc')
bin_folder = path.join(etc_folder, 'bin')
data_folder = path.join(etc_folder, 'data')
backup_folder = path.join(data_folder, 'backups')
# log_folder = path.join(etc_folder, 'logs')

for d in [etc_folder, bin_folder, data_folder, backup_folder]:
  if not path.isdir(d):
    logging.info('made directory: '+str(d))
    mkdir(d)


###
# Constants
####
public_ip = requests.get('http://ipv4bot.whatismyipaddress.com/').content.strip()
version = "1.0.3"
_version = 0

##
# File setup
###

database = path.join(data_folder, 'main.db')
providers = path.join(data_folder, 'providers.json')
log = path.join(maindir, 'main.log')


##
# Phantomjs stuff.
###
enable_js_gen = False
phantomjs_binary = path.join(bin_folder, 'phantomjs')


if not path.isfile(providers):
  logging.info('retrieving providers.json into '+str(providers))
  urlretrieve('https://raw.githubusercontent.com/Skarlett/px/master/etc/data/providers.json', providers)

#################
# Configuration #
#################

safe_run = False
backup_at = 60*60*24*7 # 7 days
##
# Remove policies
###

remove_by_reliance = .02
remove_when_total = 25 # Greater than
collect_protocol = ['socks5', 'http']

##
# Proxy mining
###
mine_wait_time = 60 * 60  # 1 hour

# Connection info
global_timeout = 30
socket_backlog = 1
local_conn = ('127.0.0.1', 52313)

##
# Advanced features - ps don't touch if you don't know what is
###
raw_sql_exec = False
