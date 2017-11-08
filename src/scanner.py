import struct, socket
from requests import get, exceptions
from json import loads as jloads
import Settings


#class Error(Exception): pass


def discover_protocol(ip, port, timeout=Settings.global_timeout):
  protocols = {
    'socks5': isSocks5Protocol,
    'http': ishttpProxy
  }
  for t, f in protocols.items():
    if t in Settings.collect_protocol and f(ip, port, timeout):
      return t
  

def isSocks5Protocol(server, port, timeout=Settings.global_timeout):
  sen = struct.pack('BBB', 0x05, 0x01, 0x00)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(timeout)
  try:
    s.connect((server, int(port)))
  except socket.error as e:
    return None
  s.sendall(sen)
  try:
    data = s.recv(2)
  except socket.error as serr:
    return None
  s.close()
  try:
    # version, auth
    version, _ = struct.unpack('BB', data)
    version = int(version)
  except:
    version = None
  
  if version == 5:
    return True

def ishttpProxy(ip, port, timeout=Settings.global_timeout):
  try:
    pi = jloads(get('http://httpbin.org/get', proxies={
      'http': 'http://%s:%d' % (ip, port),
      #'https': 'https://%s:%d' % (ip, port),
    }, timeout=Settings.global_timeout).content)
  except (exceptions.Timeout,
          exceptions.ProxyError,
          exceptions.ConnectionError,
          ValueError # Sometimes proxies change the content,
          # and since we're expecting json it will throw an error for anything else
          ) as e:
    return False
  
  if not pi['origin'] == Settings.public_ip:
    return None
  else:
    return True


