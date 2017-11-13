import socket
import time
import Settings
from scanner import discover_protocol
from utils import percentage


class Proxy:
  def __init__(self, parent, uuid, ip, port, user,
               password, protocol, last_mined,
               last_mined_success, online,
               dead, alive_cnt, dead_cnt, provider, ):
    
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
  
  def mine(self, timeout=5):
    self.parent.mine_cnt += 1
    if not self.protocol:
      protocol = discover_protocol(self.ip, self.port, timeout=timeout)
      if protocol:
        self.parent._db.modify(self.uuid, 'PROTOCOL', protocol)
        self.checked(True)
      else:
        self.checked(False,)
    else:
      if self.is_alive(timeout=timeout):
        self.checked(True)
      else:
        self.checked(False)
    self.parent._db.modify(self.uuid, 'LAST_MINED', str(time.time()))
    
    if Settings.remove_when_total <= self.alive_cnt + self.dead_cnt:
      if float(self.reliance()) <= Settings.remove_by_reliance:
        self.die()
  
  def die(self):
    self.parent._db.modify(self.uuid, 'REMOVE', 1)
    self.parent._db.execute('UPDATE RENEWAL SET DEAD_CNT = DEAD_CNT + %d WHERE UUID = ?' % self.dead_cnt, (self.provider,))
    
  def is_alive(self, timeout=30):
    s = socket.socket()
    s.settimeout(timeout)
    try:
      s.connect((self.ip, self.port))
    except:
      return False
    s.close()
    return True
  
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