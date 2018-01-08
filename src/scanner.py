import settings
import logging
import time
import errno
import struct
import socket
from requests import get, exceptions
from json import loads as jloads

class InvalidData(Exception): pass
class NeedsAuth(InvalidData): pass


def isSocks5Protocol(server, port, timeout=settings.global_timeout):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(timeout)
  data = None
  try:
    s.connect((server, int(port)))
    s.sendall(struct.pack('BBB', 0x05, 0x01, 0x00))
    data = s.recv(2)
    s.close()
  except socket.error as serr:
    s.close()
    return False
  
  if data and len(data) > 1:
    unpacked = struct.unpack('BB', data)
    return unpacked[0] == 5 and unpacked[1] == 0
  return False


def isSocks4Protocol(ip, port, timeout=settings.global_timeout):
  bip = socket.inet_aton(ip)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.settimeout(timeout)
  s.connect((ip, port))
  s.send(struct.pack('>BBH', 4, 1, port) + bip + struct.pack('B', 0))
  try:
    _d = s.recv(2)
  except:
    return False
  
  if _d:
    resp = struct.unpack('BB', _d)
    if len(resp) > 1:
      return resp[0] == 0 and resp[1] == 90
  return False

def _http_wrapper(method, ip, port, timeout=settings.global_timeout):
  try:
    pi = jloads(get(method+'://httpbin.org/get', proxies={
      method: method+'://%s:%d' % (ip, port),
    }, timeout=timeout).content)
    
  except (exceptions.Timeout,
          exceptions.ProxyError,
          exceptions.ConnectionError,
          ValueError  # Sometimes proxies change the content,
          ) as e:
    return False
  
  return not pi['origin'] == settings.public_ip
  

supported_protocols = {
  'socks5': isSocks5Protocol,
  'socks4': isSocks4Protocol,
  'https': lambda *a, **k: _http_wrapper('https', *a, **k),
  'http': lambda *a, **k: _http_wrapper('http', *a, **k),
  
}

def discover_protocol(proxy, timeout=settings.global_timeout):
  if proxy.port > 0 and proxy.port <= 65535:  # Port check
    for t, f in supported_protocols.items():
      if t in settings.collect_protocol:
        start = time.time()
        try:
          if f(proxy.ip, proxy.port, timeout):
            return t, time.time()-start
        
        except socket.timeout:
          pass
        
        except socket.error as e:
          if hasattr(e, 'errno'):
            if not e.errno in (errno.ETIMEDOUT, errno.ECONNABORTED, errno.ECONNREFUSED, errno.EHOSTUNREACH):
              logging.exception('Exception raised in '+t+' '+e.__class__.__name__)
          else:
            logging.exception('Exception raised in ' + t + ' ' + e.__class__.__name__)

        # except Exception as e:
        #   if hasattr(e, 'errno'):
        #     if not e.errno in (errno.ETIMEDOUT, errno.ECONNABORTED, errno.ECONNREFUSED, errno.EHOSTUNREACH):
        #       logging.exception('Exception raised in '+t+' '+e.__class__.__name__)
        #   else:
        #     logging.exception('Exception raised in ' + t + ' ' + e.__class__.__name__)
  
    
    # if not Settings.keep_unregonized_protocols and not error:
    #   proxy.die()
  else:
    proxy.die(False)
  
  return None, None
