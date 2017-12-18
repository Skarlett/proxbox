#!/usr/bin/python
from sys_commands import Locator

if __name__ == "__main__":
  from sys import argv
  if len(argv) > 1 and not argv[1] in ['-h', '--help']:
    for k, v in Locator(argv[1])._data.items():
      print(str(k)+': '+str(v))
  else:
    print('geoip [ip]')
    