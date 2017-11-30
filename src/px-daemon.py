#!/usr/bin/python

from __init__ import *
import init_app

if __name__ == '__main__':
  init_app.check_dirs()
  pxf = ProxyFrame(Settings.database, Settings.threads)
  
  try:
    pxf.start()
  except KeyboardInterrupt:
    pxf.shutdown()
  
    