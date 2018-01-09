from __init__ import Command, Alias
import time

USE = True

def online_cnt(parent):
  '''online count'''
  return parent.online()

def total_cnt(parent):
  '''total proxies in db'''
  return parent.total_proxies()

def uptime(parent):
  '''up time.'''
  return parent.uptime()

def alive():
  return True

##
# Human stuff
###
def geo(parent, ip):
  return parent.geo_lookup.get(ip)


def info(parent):
  '''general application runtime stats'''
  try:
    msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: [%s] [%s]\nStatus: [%s]\nProviders: %d' % \
          (parent.total_cnt(), parent.online_cnt(), parent.mine_cnt, uptime(parent),
           str(parent.last_scraped[0]),
           parent.Utils.h_time(time.time() - float(parent.last_scraped[1])), parent.current_task,
           len(parent.factory.providers))
  except:
    msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: None\nStatus: [%s]\nProviders: %d' % \
          (parent.total_proxies(), parent.online(), parent.mine_cnt, parent.uptime(), parent.current_task,
           len(parent.factory.providers))
  
  msg += '\n'
  for x in parent.Settings.collect_protocol:
    resp = int(parent._db.execute('SELECT COUNT(*) FROM PROXY_LIST WHERE PROTOCOL = ?', (x.lower(),))[0][0])
    msg += '{}:{}\n'.format(x, resp or 0)
  
  msg += '\nThreads: ' + str(len(parent._miners) + 3)
  working = 0
  sleeping = 0
  for x in parent._miners:
    if x.status[0] == 'C':
      working+=1
    else:
      sleeping+=1
  
  msg += '\nMiner Queues: [ Working: {}] [Chilling: {}]'.format(working, sleeping)
  
  #msg += '\n\t'.join('[= {} =]'.format(x.status) for x in parent._miners)
  return msg.strip()

def pinfo(parent, req):
  '''info about proxy by uuid'''
  # get info about a specific proxy by uuid
  proxy = parent.Proxy(parent, *parent._db.execute('SELECT * FROM PROXY_LIST WHERE UUID = ?', (req,))[0])
  msg = 'UUID: ' + str(proxy.uuid) + '\n'
  msg += 'Online: %s\n' % str(proxy.online)
  msg += 'Reliance rate: %f alive\n' % float(proxy.reliance())
  msg += 'Address: %s//:%s:%d\n' % (proxy.protocol, proxy.ip, proxy.port)
  return msg

def get(parent, cnt=1, bot=False, check_alive=True,
        online=True, give_geo_info=True,
        protocol='nonspecific'):
  '''fetches proxies for you'''
  msg = ''
  if bot and give_geo_info:
    give_geo_info = False
  
  for i, proxy in enumerate(parent.get(cnt, check_alive=check_alive, online=online, protocol=protocol)):
    if not bot:
      msg += 'UUID: ' + str(proxy.uuid) + '\n'
      msg += 'Online: %s\n' % str(proxy.online)
      msg += 'Reliance rate: %f alive\n' % float(parent.Utils.percentage(proxy.alive_cnt, proxy.dead_cnt + proxy.alive_cnt))
      msg += 'Address: %s://%s:%d' % (proxy.protocol, proxy.ip, proxy.port)
      
      if give_geo_info:
        msg += '\n' + '\n'.join(unicode(k) + ': ' + unicode(v) for k, v in geo(parent, proxy.ip))
      
      if cnt > 1:
        msg += '\n' + '-' * 25 + '\n'
    
    else:
      msg += '%s://%s:%d' % (proxy.protocol, proxy.ip, proxy.port)
      if cnt > 1 and i <= cnt - 1:
        msg += '\n'
  return msg


def providers(parent):
    '''stats for providers loaded.'''
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


def setup(parent):
  parent.commands.extend([
    Command(get, ('-g',),
            param_map=(
              Alias(1, aliases=('-c', '--count'), help_desc='Amount of proxies to collect.'),
              Alias(False, aliases=('-b', '--bot'), help_desc='List out put format'),
              Alias(False, aliases=('-ch', '--check'), help_desc='Check proxies before giving them,'),
              Alias(False, aliases=('-o', '--online'), help_desc='Asserts proxy\'s online'),
              Alias(False, aliases=('--geo', '-g'), help_desc='Gathers Location data.'),
              Alias('nonspecific', aliases=('-p', '--protocol'), help_desc='Specifies protocol for selection')
            )),
    Command(info, ('-i',)),
    Command(alive, show_help=False),
    providers,
    pinfo,
    geo,
  ])