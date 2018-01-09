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


class Alias:
  '''Extra layer of abstraction to be used by the help menu'''
  def __init__(self, default_val, help_desc=None, aliases=tuple()):
    self.default_val = default_val
    self.aliases = aliases
    self.help = help_desc
    self.type = type(self.default_val)
    
  def format_param_help(self):
    if not self.type == bool:
      val_needed = '<{}>'.format(type(str()))[7:][:-2]
    else: val_needed = None
    return '[{}] ' + val_needed if val_needed else '' + ' {}'.format(' | '.join(self.aliases), self.help)

class Command:
  '''Layer of abstraction that contains functions and Alias objects in param_map'''
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
