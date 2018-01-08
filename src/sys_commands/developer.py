from standard import online_cnt, uptime, total_cnt
from __init__ import Command
from os import system

USE = False

def scrape(parent):
  '''force parent to scrape'''
  return parent.scrape()

def sql(parent, *args):
  ''' sql injection '''
  return parent._db.execute(' '.join(args))

def clear(_):
  ''' clear console '''
  system("clear")

def say(_, *args):
  '''repeats what you say '''
  return ' '.join(args)

def _eval(_, *args):
  '''Evaluate something '''
  return eval(' '.join(args))

def test(_):
  ''' Test for response'''
  print "did you hear that..?"
  return "Someone, Finally!" # Callback

def kill(parent):
  ''' Kills process '''
  parent.shutdown()


def setup(cmd):
  cmd.commands.extend([
   Command(online_cnt, ('-oc',), self_name=False),
   Command(total_cnt, ('-tc',), self_name=False),
   Command(_eval, ('--eval',), self_name=False),
   uptime,
   test,
   say,
   clear,
   kill,
  ])
