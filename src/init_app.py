from Settings import *
from os import mkdir, path

def check_dirs():
  for d in [etc_folder, bin_folder, backup_folder, providers_folder]:
    if not path.isdir(d):
      logging.info('made directory: '+str(d))
      mkdir(d)

