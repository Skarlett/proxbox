from time import gmtime, strftime

USE = True

def dates(string):
    return strftime(string, gmtime())

def lower(string):
  return string.lower()

def upper(string):
  return string.upper()

def capitalize(string):
  return string.capitalize()

def setup(interpreter):
  interpreter.passive_funcs.add(dates)
  for x in [upper, capitalize, lower]:
    interpreter.active_funcs.add(x)