from sys import path
from __init__ import Locator, Command
path.append('..')
from utils import h_time, percentage
from proxy import Proxy
import Settings
import time

USE = True

def online_cnt(cmds):
  return cmds.parent.online()

def total_cnt(cmds):
  return cmds.parent.totalProxies()

def uptime(cmds):
  return h_time(cmds.parent.uptime())

##
# Human stuff
###

def info(cmds):
  try:
    msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: [%s] [%s]\nStatus: [%s]\nProviders: %d' % \
          (cmds.total_cnt(), cmds.online_cnt(), cmds.parent.mine_cnt, cmds.uptime(),
           str(cmds.parent.last_scraped[0]),
           h_time(time.time() - float(cmds.parent.last_scraped[1])), cmds.parent.current_task,
           len(cmds.parent.factory.providers))
  except:
    msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: None\nStatus: [%s]\nProviders: %d' % \
          (cmds.total_cnt(), cmds.online_cnt(), cmds.parent.mine_cnt, cmds.uptime(), cmds.parent.current_task,
           len(cmds.parent.factory.providers))
  
  msg += '\n'
  for x in Settings.collect_protocol:
    msg += '{}:{}\n'.format(x, cmds.parent._db.execute('SELECT COUNT(*) FROM PROXY_LIST WHERE PROTOCOL = ?',
                                                       (x.lower(),))[0][0] or 0)
  
  msg += '\nThreads: ' + str(len(cmds.parent._miners) + 3)
  
  return msg.strip()

def pinfo(cmds, req):
  # get info about a specific proxy by uuid
  proxy = Proxy(cmds.parent, *cmds.parent._db.execute('SELECT * FROM PROXY_LIST WHERE UUID = ?', (req,))[0])
  msg = 'UUID: ' + str(proxy.uuid) + '\n'
  msg += 'Online: %s\n' % str(proxy.online)
  msg += 'Reliance rate: %f alive\n' % float(proxy.reliance())
  msg += 'Address: %s//:%s:%d\n' % (proxy.protocol, proxy.ip, proxy.port)
  return msg

def get(cmds, cnt=1, bot=False, check_alive=True,
        online=True, timeout=10, give_geo_info=True,
        protocol='nonspecific'):
  msg = ''
  if bot and give_geo_info:
    give_geo_info = False
  
  for i, proxy in enumerate(cmds.parent.get(cnt, check_alive=check_alive, online=online,
                                            timeout=timeout, protocol=protocol)):
    if not bot:
      msg += 'UUID: ' + str(proxy.uuid) + '\n'
      msg += 'Online: %s\n' % str(proxy.online)
      msg += 'Reliance rate: %f alive\n' % float(percentage(proxy.alive_cnt, proxy.dead_cnt + proxy.alive_cnt))
      msg += 'Address: %s://%s:%d' % (proxy.protocol, proxy.ip, proxy.port)
      
      if give_geo_info:
        msg += '\n' + '\n'.join(unicode(k) + ': ' + unicode(v) for k, v in Locator(proxy.ip)._data.items())
      
      if cnt > 1:
        msg += '\n' + '-' * 25 + '\n'
    
    else:
      msg += '%s://%s:%d' % (proxy.protocol, proxy.ip, proxy.port)
      if cnt > 1 and i <= cnt - 1:
        msg += '\n'
  return msg


def providers(cmds):
    msg = ''
    for provider in cmds.parent.factory.providers:
      last_scrape, alive, dead = cmds.parent._db.provider_stats(provider)
      msg += provider.uuid + '\n\  Reliance: %f' \
                             '\n\  Alive: %d' \
                             '\n\  Dead: %d' \
                             '\n\  Contributed: %d' \
                             '\n\  Last scraped: %s' \
                             '\n---------------\n' % \
                             (percentage(alive, alive + dead), alive, dead, alive + dead,
                              h_time(time.time() - float(last_scrape)))
    return msg.strip()

def scrape(cmds):
  return cmds.parent.scrape()

def setup(cmds):
  cmds.commands.extend([
    Command(get, ('-g',),
            param_map=((1, '-c', '--count'), (False, '-b', '--bot'),
                      (False, '-nc', '--no-check'), (False, '-a', '--all'),
                      (10, '-t'), (False, '--geo'),
                      ('nonspecific', '-p', '--protocol'))
            ),
    Command(info, ('-i',)),
    providers,
    scrape,
    pinfo
  ])