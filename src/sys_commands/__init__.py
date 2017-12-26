import json
import requests


class InstanceRunning(Exception):
  '''
  Called when it is believed when two programs might be trying to run.
  '''
  pass

class NoAlias(Exception):
  '''
  This happens when a function tries to be assigned with no call sign, such as --command
  '''

class Locator:
  def __init__(self, ip):
    self.ip = ip
    self._request = requests.get('http://ip-api.com/json/'+self.ip)
    self._data = json.loads(self._request.content)
    assert self._request.ok
    for k, v in self._data.items():
      setattr(self, k, v)


class Command:
  def __init__(self, f, aliases=tuple(), param_map=list(), self_name=True, show_help=True):
    self.f = f
    if self_name:
      self.aliases = aliases+('--'+f.__name__,)
    else:
      if len(aliases) > 0:
        self.aliases = aliases
      else:
        raise NoAlias(str(f)+' was assigned with no command attached eg. "--flag"')
    self.param_map = param_map
    self.help_menu = show_help
  
  def execute(self, *args, **kwargs):
    return self.f(*args, **kwargs)
    