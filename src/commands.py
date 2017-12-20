from sys_commands import Command
from exts import Extension
from utils import is_func
import socket
import struct
import threading
import Settings
import errno
import logging

class InstanceRunning(Exception):
  '''
  Called when it is believed when two programs might be trying to run.
  '''
  pass

class CommandsManager:
  def __init__(self):
    # ProxyFrame
    self.commands = list()
    self.exts = Extension(self, 'sys_commands')
    temp = []
    for c in self.commands:
      if is_func(c):
        c = Command(c, ())
      temp.append(c)
    self.commands = temp
  
  def sys_exec(self, *args):
    c = [c for c in self.commands if args[1] in c.aliases]
    if c: c = c[0]
    else: return None
    return c, c.construct_from_sys_args(args[1:])
    
class User:
  def __init__(self, s, con, timeout=30):
    ''' super simple way of passing data basically way higher than you'd ever need'''
    self.s = s
    self.ip, self.port = con
    self.s.settimeout(timeout)
    self.msg = None
  
  def send(self, msg):
    '''i give you data'''
    msg = struct.pack('>I', len(str(msg))) + str(msg)
    self.s.sendall(msg)
  
  def recv(self):
    ''' i get gifted data'''
    raw_msglen = self._recv(4)
    if not raw_msglen:
      return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    return self._recv(msglen)
  
  def _recv(self, n):
    '''i do magic'''
    data = ''
    while len(data) < n:
      packet = self.s.recv(n - len(data))
      if not packet:
        return None
      data += packet
    return data

class Communicate_CLI(threading.Thread):
  def __init__(self, parent):
    ''' lets bind everything together and put it on a socket. It will communicate between the *main object*/parent
     and incoming queries/commands
     
     We litterally made a tiny ass server right now.
     I highly recommend making sure the port you used is not open.'''
    threading.Thread.__init__(self)
    self.parent = parent
    self.command_mgr = CommandsManager()
    self.s = socket.socket()
    try:
      self.s.bind(Settings.local_conn)
    except socket.error as serr:
      if serr.errno == errno.EADDRINUSE:
        raise InstanceRunning('It appears there is already an instance running on this port. [{}]'.format(Settings.local_conn[1]))
      raise serr
    
    self.s.listen(Settings.socket_backlog)
    self.running = False
    self.daemon = True
    self.start()
  
  def run(self):
    self.running = True
    while self.running:
      user = User(*self.s.accept())
      package = user.recv()
      if package:
        values = self.command_mgr.sys_exec(*[x for x in package.split(' ') if x])
        if values:
          c, args = values
          try:
            resp = c.execute(self.parent, *args)
            if resp:
              user.send(resp)
          except Exception:
            user.send('Error in Command.')
            logging.exception('Error raised on Command. {}, {} '.format(c, args))
        else:
          user.send('Not a command')
      else:
        user.send('Error.')
      user.s.close()

