from __init__ import Or_Conjunction, Rule
from os import path, urandom
import struct
import socket

USE = True


ETC_DIR = path.join(path.split(path.split(path.split(__file__)[0])[0])[0], 'etc')
SERVER_KEY_FP = path.join(ETC_DIR, 'server.key')

if path.isfile(SERVER_KEY_FP):
  with open(SERVER_KEY_FP, 'rb') as f:
    SERVER_KEY = f.read()

else:
  SERVER_KEY = urandom(256)
  with open(SERVER_KEY_FP, 'wb') as f:
    f.write(SERVER_KEY)


class PrivateIP(Rule):
  def check(self, user):
    """
        Credited: Cuckoo package
        Check if the IP belongs to private network blocks.
        @param ip: IP address to verify.
        @return: boolean representing whether the IP belongs or not to
                 a private network block.
        """
    networks = [
      "0.0.0.0/8",
      "10.0.0.0/8",
      "100.64.0.0/10",
      "127.0.0.0/8",
      "169.254.0.0/16",
      "172.16.0.0/12",
      "192.0.0.0/24",
      "192.0.2.0/24",
      "192.88.99.0/24",
      "192.168.0.0/16",
      "198.18.0.0/15",
      "198.51.100.0/24",
      "203.0.113.0/24",
      "240.0.0.0/4",
      "255.255.255.255/32",
      "224.0.0.0/4",
    ]
  
    for network in networks:
      try:
        ipaddr = struct.unpack(">I", socket.inet_aton(user.ip))[0]
      
        netaddr, bits = network.split("/")
      
        network_low = struct.unpack(">I", socket.inet_aton(netaddr))[0]
        network_high = network_low | 1 << (32 - int(bits)) - 1
      
        if ipaddr <= network_high and ipaddr >= network_low:
          return True
      except Exception, err:
        continue
  
    return False


class Whitelist(Rule):
  def __init__(self):
    Rule.__init__(self)
    fp = path.join(ETC_DIR, 'whitelist.lst')
    self.white_list = []
    
    if not path.isfile(fp):
      with open(fp, 'w') as f:
        f.write('')
    
    with open(fp) as f:
      self.white_list.extend([x.replace('\n', '') for x in f])
    
  def check(self, user):
    if user.ip in self.white_list:
      return True
    else:
      return False

class Authenicate(Rule):
  def __init__(self):
    Rule.__init__(self)
    
  def check(self, user):
    if user.key == SERVER_KEY:
      user.s.send('OK')
      return True
    else:
      return False
    
def setup(NetworkManager):
  NetworkManager.mods.extend([
    Or_Conjunction('Access Denied.', Whitelist(), Authenicate(), PrivateIP()) # Server authenication
  ])