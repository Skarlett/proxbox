#!/usr/bin/python

import json
import requests

class Locator():
  def __init__(self, ip):
    self.ip = ip
    self._request = requests.get('http://ip-api.com/json/'+self.ip)
    self._data = json.loads(self._request.content)
    assert self._request.ok
    for k, v in self._data.items():
      setattr(self, k, v)

if __name__ == "__main__":
  from sys import argv
  if len(argv) > 1:
    for k, v in Locator(argv[1])._data.items():
      print(k, v)
    
