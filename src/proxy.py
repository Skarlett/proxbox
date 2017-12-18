import socket
import time
import Settings
import requests
import json
from scanner import discover_protocol
from utils import percentage
from crawlers import IPPattern

# TODO: Make this horrible thing work dynamically
def rank(proxy):
  if proxy.protocol in ['socks5', 'socks4']:
    return 'Elite'
  else:
    resp = requests.get(proxy.protocol+'://httpbin.org/get?show_env',
                 proxies={
                   proxy.protocol: proxy.protocol+'://'+proxy.ip+':'+proxy.port
                 },
                 headers={'User-Agent':'Test'})

    try:
      content = json.loads(resp.content)
    except: return False
    
    ips = IPPattern.findall(resp.content)

    user_agent = False
    proxy_net = False
    obsurce = False
    transparent = False
    
    if not proxy.ip in ips and not content['origin'] == proxy.ip:
      proxy_net = True
    elif Settings.public_ip in ips:
      return 'Transparent'
    else:
      obsurce = True
    
    if content['User-Agent'] == 'Test':
      user_agent = True
    
    if proxy_net:
      return 'Elite'
    elif user_agent or obsurce:
      return 'Obscured'
    elif transparent:
      'Transparent'
    

class Proxy:
  def __init__(self, parent, uuid, ip, port, user,
               password, protocol, last_mined,
               last_mined_success, online,
               dead, alive_cnt, dead_cnt, provider,
               anonlvl, speed, first_added):
    
    
    self.parent = parent
    self.uuid = int(uuid)
    self.ip = ip
    self.port = int(port)
    self.protocol = protocol
    
    self.user = user
    self.password = password
    self.last_mined = float(last_mined) or float()
    self.alive_cnt = alive_cnt or 0
    self.dead_cnt = dead_cnt or 0
    self.dead = bool(int(dead))
    self.online = bool(int(online))
    self.last_mined_success = float(last_mined_success)
    self.provider = provider
    self.first_added = first_added
    if not anonlvl:
      load_anonlvl = True
      self.anonlvl = 'Elite' if self.protocol and self.protocol.startswith('socks') else anonlvl
    else:
      load_anonlvl = False
      self.anonlvl = anonlvl
    self.speed = speed
    
    if load_anonlvl and self.anonlvl and self.anonlvl == 'Elite':
      self.parent._db.modify(self.uuid, 'ANONLVL', 'Elite')
  
  def mine(self, timeout=5):
    self.parent.mine_cnt += 1
    
    if not self.protocol:
      self.protocol, self.speed = discover_protocol(self, timeout=timeout)
      if self.protocol and self.speed:
        self.parent._db.modify(self.uuid, 'PROTOCOL', self.protocol)
        self.parent._db.modify(self.uuid, 'SPEED', str(self.speed))
        self.checked(True)
      else:
        self.checked(False)
    else:
      start = time.time()
      alive = self.is_alive(timeout=timeout)
      if alive:
        self.speed = time.time()-start
      self.checked(alive)
    
    self.parent._db.modify(self.uuid, 'SPEED', str(self.speed)) if self.speed else None
    self.parent._db.modify(self.uuid, 'LAST_MINED', str(time.time()))
    
    if not self.anonlvl and self.protocol:
      self.anonlvl = rank(self)
      self.parent._db.modify(self.uuid, 'ANONLVL', self.anonlvl)
    self.die()
  
  def die(self, check_policy=True):
    if check_policy and not self.check_policy():
      return
    self.parent._db.modify(self.uuid, 'REMOVE', 1)
    
    
  def is_alive(self, timeout=Settings.global_timeout):
    s = socket.socket()
    s.settimeout(timeout)
    reply = False
    try:
      s.connect((self.ip, self.port))
      reply = True
    except Exception:
      pass
    s.close()
    return reply
  
  def checked(self, result):
    '''
    Adds dead or alive count to db
    :param result: bool
    :return: none
    '''
    
    if result:
      method = 'ALIVE_CNT'
      if not self.online:
        self.parent._db.modify(self.uuid, 'ONLINE', 1)
        self.online = True
    else:
      method = 'DEAD_CNT'
      if self.online:
        self.parent._db.modify(self.uuid, 'ONLINE', 0)
        self.online = False
      
    self.parent._db.execute('UPDATE PROXY_LIST SET %s = %s + 1 WHERE UUID = ?' % (method, method), (self.uuid,))
    
  def reliance(self):
    try:
      return percentage(self.alive_cnt, self.dead_cnt+self.alive_cnt)
    except ZeroDivisionError:
      return 0
  
  def check_policy(self):
    return Settings.remove_when_total <= self.alive_cnt + self.dead_cnt and \
    float(self.reliance()) <= float(Settings.remove_by_reliance) and \
    time.time() >= float(self.first_added)+Settings.remove_when_time_kept
