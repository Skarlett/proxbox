import json
import logging
from os import walk, path
from cogs import Provider
from logic_interpreter import LogicInterpreter
import Settings

class Error(Exception): pass
class ProviderExists(Error): pass
class BadFormatProvider(Error): pass


class Factory():
  logic_interpreter = LogicInterpreter()
  
  def __init__(self, fp):
    self.fp = fp
    self.json = None
    self.providers = set()
    self.exts = []
    
    self.load()
    self.generate()
    self.load_ext()
    
  
  def load_ext(self):
    modules = []
    print path.join(path.split(__file__)[0], 'cogs')
    for root, dirs, files in walk(path.join(path.split(__file__)[0], 'cogs')):
      for x in files:
        if not x.startswith('__') and x.endswith('.py'):
          modules.append(x.split('.')[0])
      break
    for mod in modules:
      _mod = __import__("cogs." + mod).__dict__[mod]
      if hasattr(_mod, 'USE'):
        if _mod.USE:
          if hasattr(_mod, 'setup'):
            try:
              _mod.setup(self)
              self.exts.append(_mod)
            except Exception as e:
              logging.exception(mod+' Has failed to load due to ['+e.__class__.__name__+'] Being raised.')
          else:
            logging.warning(mod+' Has no setup function. Ignoring...')
      else:
        logging.warning(mod+' Has no USE flag, ignoring...')
      
  def load(self):
    with open(self.fp) as f:
      self.json = json.load(f)
    print len(self.json)
  
  def generate(self):
      for provider, settings in self.json['providers'].items():
        if settings['use']:
            urls = set()
            # try:
            types = []
            for specific_protocol in settings['types']:
              if specific_protocol in Settings.collect_protocol+['nonspecific']:
                types.append(specific_protocol)
                for url in settings['types'][specific_protocol]:
                  for nurl in self.logic_interpreter.generate(url):
                    urls.add(nurl)
            
            # except KeyError:
            #   raise BadFormatProvider(provider)
          
            if not 'driver' in settings:
              settings['driver'] = None
            
            if type(settings['renewal']) is str:
              settings['renewal'] = int(self.logic_interpreter.generate(settings['renewal']))
            
            if urls and type(settings['renewal']) is int:
              if not settings['driver']:
                settings['driver'] = 'requests'
              self.providers.add(Provider(provider, settings['renewal'], urls=urls, driver=settings['driver']))
            else:
              # print urls, settings['types']
              if types:
                logging.warn('Bad generation from '+provider)
      
        
  def save(self):
    with open(self.fp, 'wt') as f:
      json.dump(self.json, f, sort_keys=True, indent=4, separators=(',', ': '))
    
  def add(self, provider, typesetup, renewal_time, use=True, save=True, driver=None):
    if not provider in self.json['providers']:
      self.json['providers'][provider] = {
        'type': typesetup,
        'renewal': renewal_time,
        'use': use,
      }
      urls = set()
      for typ, v in typesetup.items():
        if typ in Settings.collect_protocol+['nonspecific']:
          for x in v:
            urls.add(x)
      
      self.providers.add(Provider(provider, renewal_time, use, urls=urls, driver=driver))
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
    
# a = Factory('../etc/data/providers.json')
# print a.providers