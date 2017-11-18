#!/usr/bin/python

from __init__ import ProxyFrame, Settings

if __name__ == '__main__':
  pxf = ProxyFrame(Settings.database, Settings.threads)
  
  try:
    pxf.fast_miner()
  except KeyboardInterrupt:
    pxf.shutdown()
  
    