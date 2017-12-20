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
  def __init__(self, f, aliases, param_map=list(), self_name=True):
    self.f = f
    if self_name:
      self.aliases = aliases+('--'+f.__name__,)
    else:
      if len(aliases) > 0:
        self.aliases = aliases
      else:
        raise NoAlias(str(f)+' was assigned with no command attached eg. "--flag"')
    self.param_map = param_map

  def check(self, *args):
    if len(args) == len(self.param_map):
      for i, x in args:
        if i != 0:
          if not isinstance(x, self.param_map[i]) or self.param_map[i] != type(x):
            return False
      return True
    return False
  
  def construct_from_sys_args(self, *args):
    execute_values = []
    for p in self.param_map:
      value = p[0]
      aliases = p[1:]

      if isinstance(value, bool) and aliases in args:
        execute_values.append(value)
      else:
        if str(value).isdigit() and not isinstance(value, bool): value = int(value)
        execute_values.append(value)
    return execute_values
  
  def execute(self, *args, **kwargs):
    return self.f(*args, **kwargs)
    