from time import gmtime, strftime
from urllib import quote, quote_plus

USE = True

def dates(string):
    return strftime(string, gmtime())

def setup(interpreter):
  interpreter.passive_funcs.add(dates)
  for x in [quote, quote_plus]:
    interpreter.active_funcs.add(x)