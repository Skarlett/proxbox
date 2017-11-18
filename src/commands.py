from proxy import Proxy
from requests import get
from cogs import IPPortPatternGlobal, IPPortPatternLine
from geo import Locator
from os import path
from utils import percentage, h_time
import time
import Settings


class commands():
  def __init__(self, parent):
    # ProxyFrame
    self.__parent = parent # probably a raw injection exploit here,
    # should sub class
    # should implement private variable functionality in some way
    # but instead i use the hidden pretext wrapper in the python language.
    # i guess that works for now,
    # ps https://stackoverflow.com/questions/1641219/does-python-have-private-variables-in-classes
    # TODO
    
    if Settings.raw_sql_exec:
      self.execute = lambda req: self.__parent._db.execute(req)
    else:
      self.execute = lambda _: []
      
  ##
  # Utils
  ###
  def online_cnt(self):
    return self.__parent.online()
  
  def total_cnt(self):
    return self.__parent.totalProxies()

  def uptime(self):
    return h_time(self.__parent.uptime())

  def geo(self, ip):
    return '\n'.join(unicode(k) + ': ' + unicode(v) for k, v in Locator(ip)._data.items())
  
  ##
  # Human stuff
  ###
  def info(self):
    try:
      msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: [%s] [%s]\nStatus: [%s]' %\
           (self.total_cnt(), self.online_cnt(), self.__parent.mine_cnt, self.uptime(), str(self.__parent.last_scraped[0]),
            h_time(time.time()-float(self.__parent.last_scraped[1])), self.__parent.current_task)
    except:
      msg = 'Total \ Online\n%d \ %d\nMine iterations: %d\n uptime: %s\nLast scraped: None\nStatus: [%s]' %\
           (self.total_cnt(), self.online_cnt(), self.__parent.mine_cnt, self.uptime(), self.__parent.current_task)
    
    msg += '\n'
    for x in Settings.collect_protocol:
      msg += '\n'+x+': '+str(self.__parent._db.execute('SELECT COUNT(*) FROM PROXY_LIST WHERE PROTOCOL = ?', (x,))[0][0])

    msg += '\nThreads: '+str(len(self.__parent._miners)+3)
    
    return msg
  
  def pinfo(self, req):
    # get info about a specific proxy by uuid
    proxy = Proxy(self.__parent, *self.__parent._db.execute('SELECT * FROM PROXY_LIST WHERE UUID = ?', (req,))[0])
    msg = 'UUID: ' + str(proxy.uuid) + '\n'
    msg += 'Online: %s\n' % str(proxy.online)
    msg += 'Reliance rate: %f alive\n' % float(proxy.reliance())
    msg += 'Address: %s//:%s:%d\n' % (proxy.protocol, proxy.ip, proxy.port)
    return msg
  
  def get(self, cnt=1, bot=False, check_alive=True, online=True, timeout=10, give_geo_info=True, protocol='nonspecific'):
    msg = ''
    if bot and give_geo_info:
      give_geo_info = False
    
    for i, proxy in enumerate(self.__parent.get(cnt, check_alive=check_alive, online=online,
                                              timeout=timeout, protocol=protocol)):
      if not bot:
        msg += 'UUID: '+str(proxy.uuid)+'\n'
        msg += 'Online: %s\n' % str(proxy.online)
        msg += 'Reliance rate: %f alive\n' % float(percentage(proxy.alive_cnt, proxy.dead_cnt+proxy.alive_cnt))
        msg += 'Address: %s://%s:%d' % (proxy.protocol, proxy.ip, proxy.port)
          
        if give_geo_info:
            msg += '\n'+self.geo(proxy.ip)
          
        if cnt > 1:
          msg += '\n'+'-'*25+'\n'
        
      else:
        msg += '%s://%s:%d' % (proxy.protocol, proxy.ip, proxy.port)
        if cnt > 1 and i <= cnt-1:
          msg += '\n'
    return msg
  
  def scrape(self):
    return self.__parent.scrape()
  
  def add(self, *args):
    if args:
      for req in args:
        if req.startswith('http'):
          data = get(req).content
          for ip, port in IPPortPatternGlobal.findall(data):
            self.__parent._db.add(ip, port, provider=req.split('/')[2])
          
        else:
          if path.isfile(req):
            with open(req) as f:
              for l in f:
                for ip, port in IPPortPatternLine.findall(l):
                  self.__parent._db.add(ip, port, provider="local_system")
            
      return 'Added.'
    else: return 'Needs more args.'
  
  ##
  # Provider tools
  ###
  
  def providers(self):
    msg = ''
    for provider in self.__parent.factory.providers:
      last_scrape, alive, dead, permadead = self.__parent._db.provider_stats(provider)
      msg += provider.uuid+'\n\  Reliance: %f' \
                           '\n\  Alive: %d' \
                           '\n\  Dead: %d' \
                           '\n\  Contributed: %d' \
                           '\n\  Last scraped: %s' \
                           '\n\  PermaDead: %d' \
                           '\n---------------\n' % \
                           (percentage(alive, alive+dead),alive, dead, alive+dead+permadead,
                            h_time(time.time()-float(last_scrape)), permadead)
      
    
    return msg.strip()

  def add_provider(self, renewal, jsgen=False, *urls):
    if urls:
      try:
        provider = urls[0].split(':')[2:].split('/', 1)[0]
      except:
        provider = urls[0]
      metaurl = {'nonspecific': list(urls)}
      self.__parent.factory.add(provider=provider, urls=metaurl, renewal=renewal, jsgen=jsgen)
      self.__parent.factory.save()
      return 'Added.'
    else:
      return 'Needs more args.'

  def del_provider(self, *provider):
    msg = ''
    for x in provider:
      msg += x+':'+str(self.__parent.factory.remove(x, save=False))
      self.__parent._db.execute('DELETE FROM RENEWAL WHERE UUID = ?', (x,))
    self.__parent.factory.save()
    return msg
  
  def reload_providers(self):
    self.__parent.factory.load()
    self.__parent.factory.generate()
    return "done."