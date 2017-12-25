#!/usr/bin/python
import socket
import struct

from sys import version_info
if version_info.major == 2:
  range = xrange

def ips(start, end):
  start = struct.unpack('>I', socket.inet_aton(start))[0]
  end = struct.unpack('>I', socket.inet_aton(end))[0]
  return [socket.inet_ntoa(struct.pack('>I', i)) for i in range(start, end)]

def retBanner(ip, port):
  try:
    socket.setdefaulttimeout(2)
    s = socket.socket()
    s.connect((ip, port))
    banner = s.recv(1024)
    return banner
  except:
    return


ranges = {
  'socks': range(1080, 65535)
  
}

def scan(ip, rng=[]):

  portList = [21,22,25,80,110,443]
  for x in range(147, 150):
    ip = '192.168.95.' + str(x)
  for port in portList:
    banner = retBanner(ip, port)
  
    if banner:
      print '[+] ' + ip + ' : ' + banner

if __name__ == '__main__':
  main()