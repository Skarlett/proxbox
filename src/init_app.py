from Settings import *
from os import mkdir, path

def check_dirs():
  for d in [etc_folder, bin_folder, data_folder, backup_folder]:
    if not path.isdir(d):
      logging.info('made directory: '+str(d))
      mkdir(d)

def check_provider():
  if not path.isfile(providers):
    logging.info('retrieving providers.json into '+str(providers))
    try:
      urlretrieve('https://raw.githubusercontent.com/Skarlett/px/master/etc/data/providers.json', providers)
    except:
      print "Fatal error. Couldn\'t recieve providers.json"