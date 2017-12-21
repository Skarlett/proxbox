import re, Settings, logging
from exts import Extension


class Exception(Exception): pass
class NotImplemented(Exception): pass
class ProgrammingError(Exception): pass
class SyntaxError(ProgrammingError): pass


def safe_eval(string, dirs={}):
  dirs["__builtins__"] = dirs or None
  return eval(string, dirs)


class LogicInterpreter:
  __logic_interpreter = re.compile('(?<={)(.*?)(?=})')
  
  @staticmethod
  def range(x, y, **kwargs):
    return range(int(x), int(y), **kwargs)
  
  def __init__(self):
    self.passive_funcs = set()
    self.active_funcs = set([LogicInterpreter.range, safe_eval])
    self.exts = Extension(self, 'factory_mods')
    
  
  def generate(self, url):
    iteratives = []
    logic_syntax = set(self.__logic_interpreter.findall(url.replace(' ', '')))
    
    for command in list(logic_syntax):
      if not '%' in command:
        
        # TODO: Cleanup
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

# Testing your logic.
# print LogicInterpreter().generate("http://proxy-daily.com{/%Y/%m/%d-%m-%Y}-proxy-list-{range(0,5)}/")