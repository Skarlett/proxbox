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
import Settings
from cfscrape import create_scraper as CFscrape
from selenium.webdriver import PhantomJS
from os.path import isfile

drivers = {
  # driverName, Driver Object, Needs execution before use
  'phantomjs': (PhantomJS, True),
  'cfscrape':  (CFscrape, True),
  'requests': (requests, False)
}


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
    self.popBadUrls = True
    self.retry_limit = 3
    self.driver = None
    for k, v in kwargs.items():
      if hasattr(self, k):
        if not k == 'urls':
          setattr(self, k, v)
        else:
          for x in v:
            self.urls.add(x)
    self._scraped = False
    
    if self.driver.lower() in drivers:
      driver, execution = drivers[self.driver.lower()]
      if execution:
        driver = driver()
      self._driver = driver
    else: self._driver = requests
    
  def scrape(self, ignore_exceptions=Settings.safe_run):
    proxies = set()
    for url in list(self.urls):
      retries = 0
      
      while self.retry_limit >= retries:
        try:
          r = self._driver.get(url)
          if not hasattr(r, 'content'):
            r = Struct(ok=len(self._driver.page_source) > 0, content=self._driver.page_source, url=url)
          if r.ok:
            break
          else:
            retries += 1
        except (rexception.Timeout, rexception.ConnectionError):
          retries += 1
        
      if retries >= self.retry_limit:
        # If this is called, r isn't declared, so it will run into an exception anyway.
        logging.error(url + ' Failed to render.')

        if not ignore_exceptions:
          raise MaxRetry('Max url retries')
        
      if r.ok:
        for ip, port in proxyScrape(r.content):
          if not port in self.badports:
            proxies.add((ip, port))
      else:
        self.urls.remove(url)
        self.badUrls.append(url)

    for x in proxies:
      self.proxies.add(x)


if __name__ == '__main__':
  from sys import argv
  from os.path import split
  
  helpmsg = '%s [-u --url (-js) URL] [-a --author] [-h --help] [-d --data FILE]' \
            '\n\n' \
            'Example: python %s -u http://someplace.somehow/proxies http://moarproxies.net/pxy' % (split(__file__)[1], split(__file__)[1])
  
  try:
    if argv[1] in ['-u', '--url']:
      if not argv[2] == '-js':
        js_gen = False
        urls = argv[2:]
      else:
        js_gen = True
        urls = argv[3:]
      
      if len(urls) > 0:
        p = Provider(jsgen=js_gen)
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