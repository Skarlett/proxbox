from sys_commands import Command
from exts import Extension
from utils import is_func
import socket
import struct
import threading
import settings
import errno
import logging

class InstanceRunning(Exception):
  '''
  Called when it is believed when two programs might be trying to run.
  '''
  pass

def find_in_args(args, data):
  for i, x in enumerate(args):
    if x == data:
       return i
  return None

class CommandsManager:
  def __init__(self):
    # ProxyFrame
    
    self.commands = [
      Command(CommandsManager.help, ('-h',)),
      Command(CommandsManager._reload, ('--reload',), self_name=False)
    ]
    self.exts = Extension(self, 'sys_commands')
    self.after_load()
  
  @staticmethod
  def _reload(parent):
    ''' reload extensions '''
    parent.reload()
    return 'Reloaded.'
  
  def after_load(self):
    temp = []
    for c in self.commands:
      if is_func(c):
        c = Command(c, ())
      temp.append(c)
    self.commands = temp
  
    
  def _pack(self, c, args):
    if c.param_map:
      data = []
      for v, aliases in c.param_map:
        location = [find_in_args(args, a) for a in aliases if a in args]
        if location:
            location = location[0]
            # print v, aliases
            if type(v) == bool:
              # print not(v)
              data.append(not(v))
            elif isinstance(v, int):
              data.append(int(args[location+1]))
            elif isinstance(v, str):
              data.append(args[location+1])
            else: data.append(v)
        else: data.append(v)
    else: data = args
    return data
  
  @staticmethod
  def help(parent):
      '''This displayed help message.'''
      return '\n'.join('['+' | '.join(x.aliases)+'] {}'.format(x.f.__doc__)
                       for x in parent.communicate.command_mgr.commands if x.help_menu)
  
  def sys_exec(self, *args):
    if args > 1:
      c = [c for c in self.commands if args[1] in c.aliases]
      if c:
        c = c[0]
        if len(args) > 1:
          return c, self._pack(c, args[2:])
        
        else:
          return c, tuple()
        
          
      
    
    
# fuck = Command(lambda: 'test', ('--superman', '-sm'), param_map=((False, ('-b', '--bot')), (False, ('-g', '--geo'))), self_name=False)
# fuckery = CommandsManager()
# print fuckery._pack(fuck, ('-g', '--geo', '-b', '--bot'))

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
      self.s.bind(settings.local_conn)
    except socket.error as serr:
      if serr.errno == errno.EADDRINUSE:
        raise InstanceRunning('It appears there is already an instance running on this port. [{}]'.format(settings.local_conn[1]))
      raise serr
    
    self.s.listen(settings.socket_backlog)
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

