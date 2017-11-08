#!/usr/bin/python
# Python2 maybe 3
# --------
# Author: github.com/Skarlett
# This is a library used to scrape proxies off of sites using regex.
# Shout out to the project "ProxyBroker" for the awesome regex.

__author__ = 'https://github.com/Skarlett'

import re, requests
import requests.exceptions as rexception
import logging
from os.path import isfile
import Settings

if Settings.enable_js_gen:
  from selenium.webdriver import PhantomJS



class Struct:
  def __init__(self, **entries):
    self.__dict__.update(entries)
  def update(self, **entries):
    self.__dict__.update(entries)


IPPattern = re.compile(
    r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)')

IPPortPatternLine = re.compile(
    r'^.*?(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)).*?(?P<port>\d{2,5}).*$',
    flags=re.MULTILINE)

IPPortPatternGlobal = re.compile(
    r'(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))'
    r'(?=.*?(?:(?:(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?P<port>\d{2,5})))',
    flags=re.DOTALL)

class Error(Exception): pass
class MaxRetry(Error): pass

def strip_chars(data, chars):
  for x in chars:
    data = data.replace(x, '')
  return data

def proxyScrape(data):
  data = IPPortPatternGlobal.findall(data)
  for thing in data:
    if len(thing) == 2:
      ip, port = thing
      ip = strip_chars(ip, chars='\t\n ')
      port = strip_chars(port, chars='\t\n ')
      yield ip, port
      

class Provider:
  '''
  Parent object for inheritence over other scrape proxy sources
  '''
  
  def __init__(self, **kwargs):
    self.urls = set()
    self.proxies = set()
    self.badUrls = []
    self.badports = []
    self.retry_limit = 3
    self._scraped = False
    self._retries = 0
    self.jsgen = False
    
    for k, v in kwargs.items():
      if hasattr(self, k):
        if not k == 'urls':
          setattr(self, k, v)
        else:
          for x in v:
            self.urls.add(x)
    
    
    wrapper_scrape = lambda driver: self._scrape(driver)
    
    
    if self.jsgen and Settings.enable_js_gen:
      self.scrape = wrapper_scrape(PhantomJS)
    else:
      self.scrape = wrapper_scrape(requests)
    
  def _scrape(self, driver, ignore_exceptions=False):
    proxies = set()
    for url in list(self.urls):
      while self.retry_limit >= self._retries:
        try:
          r = driver.get(url)
          if not hasattr(r, 'content'):
            r = Struct(ok=len(driver.page_source) > 0, content=driver.page_source, url=url)
          
          self._retries = 0
          if r.ok:
            break
        except rexception.Timeout:
          self._retries += 1
        
      if self._retries > self.retry_limit:
        # If this is called, r isn't declared, so it will run into an exception anyway.
        logging.error(url + ' Failed to render.')

        if not ignore_exceptions:
          raise MaxRetry('Max url retries')
        
      if r.ok:
        for ip, port in proxyScrape(r.content):
          if not port in self.badports:
            proxies.add((ip, port))
      else:
        self.urls.remove(r.url)
        self.badUrls.append(r.url)

    for x in proxies:
      self.proxies.add(x)


if __name__ == '__main__':
  from sys import argv
  from os.path import split
  
  helpmsg = '%s [-u --url URL] [-a --author] [-h --help] [-d --data FILE]' \
            '\n\n' \
            'Example: python %s -u http://someplace.somehow/proxies http://moarproxies.net/pxy' % (split(__file__)[1], split(__file__)[1])
  
  try:
    if argv[1] in ['-u', '--url']:
      urls = argv[2:]
      if len(urls) > 0:
        p = Provider()
        
        for x in urls:
          if not x.startswith('http'):
            x = 'http://'+x
          p.urls.add(x)
        p.scrape()
        
        if len(p.proxies) > 0:
          for ip, port in p.proxies:
            print(':'.join((ip, port)))
            
        else: print("No proxies found")
      else:
        print('Example: python %s -u http://someplace.somehow/proxies http://moarproxies.net/pxy ')
    
    elif argv[1] in ['--author', '-a']:
      print(__author__)
    
    elif argv[1] in ['-d', '--data']:
      if len(argv) > 2:
        for f in argv[2:]:
          if isfile(f):
            try:
              with open(f) as reader:
                for line in reader:
                  for ip, port in proxyScrape(line):
                    print(ip+':'+str(port))
            except:
              print("Could not read "+f)
      else:
        print('Example: %s -d file1 file2 file3' % split(__file__)[1])
        
    elif argv[1] in ['--help', '-h']:
       print(helpmsg)
    
    else: print("argument not recognized.")
    
  except IndexError:
    print(helpmsg)