from standard import online_cnt, uptime, total_cnt
from __init__ import Command

USE = True

#def sql(parent, *args):
#  return parent._db.execute(' '.join(args))

def say(_, *args):
  return ' '.join(args)

def _eval(parent, *args):
 return eval(' '.join(args))

def test(_):
  ''' Test for response'''
  print "did you hear that..?"
  return "Someone, Finally!" # Callback

def setup(cmd):
  cmd.commands.extend([
   Command(online_cnt, ('-oc',), self_name=False),
   Command(total_cnt, ('-tc',), self_name=False),
   Command(_eval, ('--eval',), self_name=False),
   uptime,
   test,
   say
  ])
