import re
from time import gmtime, strftime
from utils import safe_eval


class Exception(Exception):
  pass


class ProgrammingError(Exception):
  pass


class SyntaxError(ProgrammingError):
  pass

class LogicInterpreter:
  __logic_interpreter = re.compile('(?<={)(.*?)(?=})')
  
  def __dates(self, string):
    return strftime(string, gmtime())
  
  def range(self, start, end):
    return [i for i in xrange(int(start), int(end))]
  
  def eval(self, string):
    return safe_eval(string)
  
  def generate(self, url):
    iteratives = []
    logic_syntax = set(self.__logic_interpreter.findall(url.replace(' ', '')))

    for command in list(logic_syntax):
      func = command.split('(')[0]
      
      if hasattr(self, func):
        
        args = command.split('(')[1].split(')')[0].replace(' ', '').split(',')
        resp = getattr(self, func)(*args)
        if hasattr(resp, '__iter__'):
          iteratives.append(resp)
        else:
          url = url.replace('{'+command+'}', str(resp))
          logic_syntax.remove(command)
      else:
        oldurl = url
        url = self.__dates(url)
        if oldurl == url:
          raise SyntaxError(url+' contains syntax error')
        logic_syntax.remove(command)


    if len(iteratives) > 0:
      urls = []
      for i, lst in enumerate(iteratives):
        for x in lst:
          urls.append(url.replace('{'+list(logic_syntax)[i]+'}', str(x)))
    else:
      urls = [url]
    
    return [x.replace('{', '').replace('}', '') for x in urls]

#

# Generate urls for factory
# interpret logic
# use iteratives last

