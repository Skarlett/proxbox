from __init__ import Locator, Command
import time

USE = True


def online_cnt(parent):
  return parent.online()

def total_cnt(parent):
  return parent.total_proxies()

def uptime(parent):
  return parent.Utils.h_time(parent.uptime())

##
# Human stuff
###

def info(parent):
  try:
    msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: [%s] [%s]\nStatus: [%s]\nProviders: %d' % \
          (parent.total_cnt(), parent.online_cnt(), parent.mine_cnt, parent.uptime(),
           str(parent.last_scraped[0]),
           parent.Utils.h_time(time.time() - float(parent.last_scraped[1])), parent.current_task,
           len(parent.factory.providers))
  except:
    msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: None\nStatus: [%s]\nProviders: %d' % \
          (parent.total_proxies(), parent.online(), parent.mine_cnt, parent.uptime(), parent.current_task,
           len(parent.factory.providers))
  
  msg += '\n'
  for x in parent.Settings.collect_protocol:
    msg += '{}:{}\n'.format(x, parent._db.execute('SELECT COUNT(*) FROM PROXY_LIST WHERE PROTOCOL = ?',
                                                       (x.lower(),))[0][0] or 0)
  
  msg += '\nThreads: ' + str(len(parent._miners) + 3)
  
  return msg.strip()

def pinfo(parent, req):
  # get info about a specific proxy by uuid
  proxy = parent.Proxy(parent, *parent._db.execute('SELECT * FROM PROXY_LIST WHERE UUID = ?', (req,))[0])
  msg = 'UUID: ' + str(proxy.uuid) + '\n'
  msg += 'Online: %s\n' % str(proxy.online)
  msg += 'Reliance rate: %f alive\n' % float(proxy.reliance())
  msg += 'Address: %s//:%s:%d\n' % (proxy.protocol, proxy.ip, proxy.port)
  return msg

def get(parent, cnt=1, bot=False, check_alive=True,
        online=True, timeout=10, give_geo_info=True,
        protocol='nonspecific'):
  msg = ''
  if bot and give_geo_info:
    give_geo_info = False
  
  for i, proxy in enumerate(parent.get(cnt, check_alive=check_alive, online=online,
                                            timeout=timeout, protocol=protocol)):
    if not bot:
      msg += 'UUID: ' + str(proxy.uuid) + '\n'
      msg += 'Online: %s\n' % str(proxy.online)
      msg += 'Reliance rate: %f alive\n' % float(parent.Utils.percentage(proxy.alive_cnt, proxy.dead_cnt + proxy.alive_cnt))
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


def providers(parent):
    msg = ''
    for provider in parent.factory.providers:
      last_scrape, alive, dead = parent._db.provider_stats(provider)
      msg += provider.uuid + '\n\  Reliance: %f' \
                             '\n\  Alive: %d' \
                             '\n\  Dead: %d' \
                             '\n\  Contributed: %d' \
                             '\n\  Last scraped: %s' \
                             '\n---------------\n' % \
                             (parent.Utils.percentage(alive, alive + dead), alive, dead, alive + dead,
                              parent.Utils.h_time(time.time() - float(last_scrape)))
    return msg.strip()

def scrape(parent):
  return parent.scrape()

def setup(parent):
  parent.commands.extend([
    Command(get, ('-g',),
            param_map=(
              (1, ('-c', '--count')),
              (False, ('-b', '--bot')),
              (False, ('-nc', '--no-check')),
              (False, ('-o', '--online')),
              (10, ('-t',)),
              (False, ('--geo', '-g')),
              ('nonspecific', ('-p', '--protocol'))
            )),
    Command(info, ('-i',)),
    providers,
    scrape,
    pinfo
  ])