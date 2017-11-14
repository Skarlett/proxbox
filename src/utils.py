from math import *

#make a list of safe functions
safe_list = ['acos', 'asin', 'atan',
             'atan2', 'ceil', 'cos', 'cosh',
             'degrees', 'e', 'exp', 'fabs',
             'floor', 'fmod', 'frexp', 'hypot',
             'ldexp', 'log', 'log10', 'modf',
             'pi', 'pow', 'radians', 'sin',
             'sinh', 'sqrt', 'tan', 'tanh']


safe_dict = dict([(k, locals().get(k, None)) for k in safe_list ])
safe_dict['abs'] = abs


def safe_eval(string):
  return eval(string, {"__builtins__":None}, safe_dict)

def percentage(part, whole):
  try:
    return 100 * float(part) / float(whole)
  except ZeroDivisionError:
    return 0

def h_time(seconds):
  if 8640000 >= seconds:
    m, s = divmod(float(seconds), 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)
  else:
    return "+100 days"
