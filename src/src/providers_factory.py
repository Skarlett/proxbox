from os import walk, path
from extended_providers import Provider
from logic_interpreter import LogicInterpreter
from exts import Extension
import json
import logging
import settings

class Error(Exception): pass
class ProviderExists(Error): pass
class BadFormatProvider(Error): pass


class Factory():
  directory = settings.providers_folder
  
  def __init__(self):
    self.logic_interpreter = LogicInterpreter()
    self.json = dict()
    self.providers = set()
    self._load()
    self.exts = Extension(self, 'extended_providers')
  
  
  def _load(self):
    for root, _, files in walk(settings.providers_folder):
      for _file in files:
        with open(path.join(root, _file)) as f:
          jsonfile = json.load(f)
          if jsonfile['use']:
            self.json[_file.split('.')[0]] = jsonfile['providers']
    self.generate()
  
  def generate(self):
    for fileName, dictionary in self.json.items():
      for provider, data in dictionary.items():
        if data['use']:
          urls = set()
          for proto in data['types']:
            if proto.lower() in settings.collect_protocol+['nonspecific']:
              for url in data['types'][proto]:
                for nurl in self.logic_interpreter.generate(url):
                  urls.add(nurl)

          if not 'driver' in data:
            data['driver'] = 'requests'
              
          if type(data['renewal']) is str:
            data['renewal'] = int(self.logic_interpreter.generate(data['renewal']))
              
          if urls and type(data['renewal']) is int or str(data['renewal']).isdigit():
            self.providers.add(Provider(provider, int(data['renewal']), urls=urls,
                                            driver=data['driver'],
                                            file=fileName))
          else:
            logging.warning('Failed to render ['+provider+'] from ['+fileName+']')

