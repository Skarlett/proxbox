from skeleton import Provider as Skeleton
from logic_interpreter import LogicInterpreter
import Settings
import json
import requests
import re
import logging

url_pattern = re.compile(r'href=[\'"]?([^\'" >]+)')


class Error(Exception):
  pass


class ProviderExists(Exception):
  pass


class BadFormatProvider(Exception):
  pass


class Provider(Skeleton):
  def __init__(self, uuid=None, renewal=0, use=True, **kwargs):
    Skeleton.__init__(self, **kwargs)
    if not Settings.safe_run:
      assert uuid and renewal
    self.uuid = uuid
    self.use = use
    self.renewal = renewal


class live_socks(Provider):
  def __init__(self):
    Provider.__init__(self, uuid="live-socks.com", renewal=60*60*24, use=False)
    for x in url_pattern.findall(requests.get('http://www.live-socks.net/search/label/Socks%205').content):
      x = x[::-1].split('#', 1)[0][::-1]
      if 'socks-5' in x:
        self.urls.add(x)
  
  
class socks24(Provider):
  def __init__(self):
    Provider.__init__(self, uuid="socks24.org", renewal=60*60*24, use=False)
    for x in url_pattern.findall(requests.get('http://www.socks24.org/').content):
      if 'socks' in '/'.join([y for y in x.split('/') if y and not '#' in y][2:]):
        self.urls.add(x)
    
  
class Factory():
  def __init__(self, fp):
    self.fp = fp
    self.json = None
    self.providers = set()
    temp = [live_socks, socks24]
    for x in temp:
      x = x()
      if x.use:
        self.providers.add(x)
    
    self.logic_interpreter = LogicInterpreter()
    
    self.load()
    self.generate()
    
  def load(self):
    with open(self.fp) as f:
      self.json = json.load(f)
  
  def generate(self):
      for provider, settings in self.json['providers'].items():
        if settings['use']:
          urls = set()
          try:
            for specific_protocol in settings['types']:
              if specific_protocol in Settings.collect_protocol+['nonspecific']:
                for url in settings['types'][specific_protocol]:
                  for nurl in self.logic_interpreter.generate(url):
                    urls.add(nurl)
            
          except KeyError:
            raise BadFormatProvider(provider)
          
          if not 'driver' in settings:
            settings['driver'] = None
          
          if urls:
            self.providers.add(Provider(provider, settings['renewal'], urls=urls, jsgen=settings['driver']))
          else:
            logging.warn('Bad generation from '+provider)
    
        
  def save(self):
    with open(self.fp, 'wt') as f:
      json.dump(self.json, f, sort_keys=True, indent=4, separators=(',', ': '))
    
  def add(self, provider, typesetup, renewal_time, use=True, save=True, jsgen=False):
    
    if not provider in self.json['providers']:
      self.json['providers'][provider] = {
        'type': typesetup,
        'renewal': renewal_time,
        'use': use,
        'jsgen': jsgen
      }
      urls = set()
      for typ, v in typesetup.items():
        if typ in Settings.collect_protocol+['nonspecific']:
          for x in v:
            urls.add(x)
      
      self.providers.add(Provider(provider, renewal_time, use, urls=urls, jsgen=jsgen))
      if save:
        self.save()
    else:
      raise ProviderExists('Provider %s is already in database')
  
  def remove(self, provider, save=True):
    try:
      for x in list(self.providers):
        if x.uuid == provider:
          self.providers.remove(x)
      
      if provider in self.json:
        self.json.pop(provider)
      if save:
        self.save()
      return 'Removed.'
    
    except Exception as e:
      return 'Error. '+str(e)+'\n'+e.message+'\n'+e.__class__.__name__
    
    