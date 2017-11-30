# !/usr/bin/python
# Python2 maybe 3
# --------
# Author: github.com/Skarlett
# This is a library used to scrape proxies off of sites using regex.
# Shout out to the project "ProxyBroker" for the awesome regex.

__author__ = 'https://github.com/Skarlett'

import sys
sys.path.append('..')
import re, requests
import requests.exceptions as rexception
import logging
from cfscrape import create_scraper as CFscrape
from selenium.webdriver import PhantomJS
import Settings
from utils import Struct



drivers = {
  # driverName, Driver Object, Needs execution before use
  'phantomjs': (PhantomJS, True),
  'cfscrape': (CFscrape, True),
  'requests': (requests, False)
}
HREF_FIND = re.compile(r'href=[\'"]?([^\'" >]+)')


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
      if ip and port:
        yield ip, port


class Skeleton:
  '''
  Parent object for inheritence over other scrape proxy sources
  '''
  # fake = False
  
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
    
    if type(self.driver) is str and self.driver.lower() in drivers:
      driver, execution = drivers[self.driver.lower()]
      if execution:
        driver = driver()
      self._driver = driver
    else:
      self._driver = requests
  
  def scrape(self, ignore_exceptions=True):
    proxies = set()
    for url in list(self.urls):
      retries = 0
      
      while self.retry_limit >= retries:
        try:
          try:
            r = self._driver.get(url)
          except:
            r = Struct(ok=False, content=None)
          if not hasattr(r, 'content'):
            r = Struct(ok=len(self._driver.page_source) > 0, content=self._driver.page_source, url=url)
          if r.ok:
            break
          else:
            retries += 1
        except Exception as err:
          retries += 1
          if not err in [rexception.Timeout, rexception.ConnectionError, rexception.RetryError]:
            logging.exception('Unhandled exception '+err.__class__.__name__)
      
      if retries >= self.retry_limit:
        logging.error(url + ' Failed to render.')
        if not ignore_exceptions:
          raise MaxRetry('Max url retries')
        else:
          r = None
      
      if r:
        if r.ok:
          for ip, port in proxyScrape(r.content):
            if not int(port) in self.badports:
              proxies.add((ip, int(port)))
        else:
          self.urls.remove(url)
          self.badUrls.append(url)
      
      
    if hasattr(self._driver, 'close'):
      self._driver.close()
      
    for x in proxies:
      self.proxies.add(x)

class Provider(Skeleton):
  def __init__(self, uuid=None, renewal=0, use=True, **kwargs):
    Skeleton.__init__(self, **kwargs)
    assert uuid and renewal
    self.uuid = uuid
    self.use = use
    self.renewal = renewal

