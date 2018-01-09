from standard import online_cnt, total_cnt, geo, Command, Alias
from json import dumps

USE = False

def status(parent):
  d = {'onlinecount': online_cnt(parent), 'total_cnt': total_cnt(parent)}
  return dumps(d)
  
def jget(parent, count=1):
  d = {}
  for x in parent.get(cnt=count):
    d[x.uuid] = dumps(x)
    d[x.uuid].pop('uuid')
    d[x.uuid]['geo'] = geo(parent, x.ip)
  return d

def setup(parent):
  parent.commands.extend([
    Command(jget, ('--g',), param_map=(Alias(1, aliases=('-c', '--count'), help_desc='Amount of proxies to collect.'))),
    status
  ])
