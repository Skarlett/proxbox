from __init__ import Settings
from datetime import datetime
from os import path
import time

USE = True


def backup(pxf):
  ''' Backup Data extension'''
  lb = path.join(Settings.etc_folder, 'last_backup')
  if not path.isfile(lb):
    with open(lb, 'wb') as f:
      f.write(str(time.time()))
  
  with open(lb, 'rb') as f:
    if float(f.read().strip()) + Settings.backup_at >= time.time():
      pxf._db.backup(path.join(Settings.backup_folder, '%s_%s_%s_backup.db.gz' % (
        str(datetime.month), str(datetime.day), str(datetime.year))))


def setup(pxf):
  pxf.tasks.append(backup)