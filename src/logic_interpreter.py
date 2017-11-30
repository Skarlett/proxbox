import re, Settings, logging
from utils import safe_eval
from os import path, walk

class Exception(Exception): pass
class NotImplemented(Exception): pass
class ProgrammingError(Exception): pass
class SyntaxError(ProgrammingError): pass


class LogicInterpreter:
  __logic_interpreter = re.compile('(?<={)(.*?)(?=})')
  
  @staticmethod
  def range(x, y, **kwargs):
    return range(int(x), int(y), **kwargs)
  
  def __init__(self):
    self.passive_funcs = set()
    self.active_funcs = set([LogicInterpreter.range, safe_eval])
    self.startup()

  def startup(self):
    modules = []
    for root, dirs, files in walk(path.join(path.split(__file__)[0], 'factory_mods')):
      for x in files:
        if not x.startswith('__') and x.endswith('.py'):
          modules.append(x.split('.')[0])
      break
    # print modules
    for mod in modules:
      self.add_mod(mod)


  def add_mod(self, mod):
    _mod = __import__("factory_mods." + mod).__dict__[mod]
    if hasattr(_mod, 'USE'):
      if hasattr(_mod, 'setup'):
        _mod.setup(self)
      else:
        logging.error('Failed to load cogs.' + mod)
    else:
      logging.warning(mod + ' Has no USE flag, ignoring...')
    
  
  def generate(self, url):
    iteratives = []
    logic_syntax = set(self.__logic_interpreter.findall(url.replace(' ', '')))
    
    for command in list(logic_syntax):
      if not '%' in command:
        funcname = command.split('(')[0]
        args = [arg for arg in command.split('(')[1].split(')')[0].replace(' ', '').split(',') if arg]
        # print [x.__name__ for x in self.active_funcs], funcname
        try:
          func = [x for x in self.active_funcs if x.__name__ == funcname ][0]
        except IndexError:
          raise NotImplemented('Function "{}" was not loaded into Active_funcs'.format(funcname))
        
        # TODO: Document this
        # self - changes the command variable to the url
        # fragment - changes the command to a raw version of the command? Was I fucked up?
        # for special_arg, replacement in [("self", url), ("fragment", command)]:
        #   if special_arg in args:
        #     for i,x in enumerate(args):
        #       if x == special_arg:
        #         args[i] = replacement
        #
        
        if Settings.safe_run:
          try:
            resp = func(*args)
          except:
            logging.exception(funcname+' Has failed to generate')
        else:
          resp = func(*args)
        
        if hasattr(resp, '__iter__'):
            iteratives.append(resp)
        else:
            url = url.replace('{'+command+'}', str(resp))
            logic_syntax.remove(command)
        
      else:
        if not '(' in command or not ')' in command:
          for passive_func in self.passive_funcs:
            url = passive_func(url)
            logic_syntax.remove(command)
        else:
          raise SyntaxError('May not use subsitutes and passive funcs in the same argument')

    if len(iteratives) > 0:
      urls = []
      for i, lst in enumerate(iteratives):
        for x in lst:
          urls.append(url.replace('{'+list(logic_syntax)[i]+'}', str(x)))
    else:
      urls = [url]
    
    return [x.replace('{', '').replace('}', '') for x in urls]


