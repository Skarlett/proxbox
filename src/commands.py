from sys_commands import Command
from exts import Extension
from utils import is_func
import socket
import struct
import threading
import settings
import errno
import logging
from time import gmtime, strftime


class InstanceRunning(Exception):
  '''
  Called when it is believed when two programs might be trying to run.
  '''
  pass


class ProtocolLog:
  def __init__(self, fp):
    self.fp = fp
  
  def log(self, user, msg):
    with open(self.fp, 'a') as f:
      f.write(':'.join([user.ip, strftime('%m-%d-%Y %H:%M:%S', gmtime()), msg]))

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
    print self.commands
  
  @staticmethod
  def _reload(parent):
    ''' reload extensions '''
    parent.reload()
    return 'Reloaded.'
  
  def loaded_in(self, CommandObject, all_aliases=None):
    if not all_aliases:
      all_aliases = [x.aliases for x in self.commands if not is_func(x)]

    for x in CommandObject.aliases:
      if x in all_aliases:
        if x in all_aliases:
          return True
    return False
  
  def after_load(self):
    aliases = []
    temp = []
    for c in self.commands:
      if is_func(c):
        default_flag = '--'+c.__name__
        if default_flag in aliases:
          logging.warning('Conflicting aliases {}, already loaded'.format(default_flag))
        c = Command(c, ())
        aliases.append(default_flag)
        
      else:
        if self.loaded_in(c, aliases):
          logging.warning('Conflicting Aliases {}, already loaded'.format(c.aliases))
          c = None
      if c:
        aliases.extend(c.aliases)
        temp.append(c)
    self.commands = temp
    
  def _pack(self, c, args):
    if c.param_map:
      data = []
      # Handles flagged / aliased statements
      for flag in c.param_map:
        location = [find_in_args(args, a) for a in flag.aliases if a in args]
        if location:
            location = location[0]
            # print v, aliases
            if flag.type is bool:
              data.append(not(flag.default_value))
            elif flag.type is int:
              data.append(int(args[location+1]))
            elif flag.type is str:
              data.append(args[location+1])
            else:
              data.append(flag.default_value)
        else:
          data.append(flag.default_value)
    else: data = args
    return data
  
  @staticmethod
  def help(parent):
      '''This displayed help message.'''
      msg = ''
      for cmd in parent.communicate.command_mgr.commands:
        msg += '[ '+ ' | '.join(cmd.aliases)+' ]\n'
        msg += '\t'+str(cmd.__doc__)
        if cmd.param_map:
          msg += '\t\n'.join(x.format_param_help() for x in cmd.param_map)
      
      return msg
      
      
  def sys_exec(self, *args):
    if args > 1:
      c = [c for c in self.commands if args[1] in c.aliases]
      if c:
        c = c[0]
        if len(args) > 1:
          return c, self._pack(c, args[2:])
        else:
          return c, tuple()
        
        
class User(threading.Thread):
  def __init__(self, s, con, parent, cmd_mgr, timeout=30):
    ''' Threaded response server '''
    threading.Thread.__init__(self)
    self.daemon = True
    self.parent = parent
    self.cmd_mgr = cmd_mgr
    self.s = s
    self.ip, self.port = con
    self.s.settimeout(timeout)
    self.msg = None
    self.key = self.s.recv(256)
  
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
  
  def run(self):
    package = self.recv()
    if package:
      values = self.cmd_mgr.sys_exec(*[x for x in package.split(' ') if x])
      if values:
        c, args = values
        try:
          resp = c.execute(self.parent, *args)
          if resp:
            self.send(resp)
        except Exception:
          self.send('Error in Command.')
          logging.exception('Error raised on Command. {}, {} '.format(c, args))
      else:
        self.send('Not a command')
    else:
      self.send('Error.')
    self.s.close()

class NetworkManager:
  def __init__(self):
    self.mods = list()
    self.exts = Extension(self, 'networking_mods')
        
  def check_user(self, user):
    for rule in self.mods:
      if not rule.check(user):
        return False, rule
    return True, None

class Communicate_CLI(threading.Thread):
  def __init__(self, parent):
    ''' lets bind everything together and put it on a socket. It will communicate between the *main object*/parent
     and incoming queries/commands
     
     We litterally made a tiny ass server right now.
     I highly recommend making sure the port you used is not open.'''
    threading.Thread.__init__(self)
    self.parent = parent
    self.command_mgr = CommandsManager()
    self.networking_rules = NetworkManager()
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
      s, con = self.s.accept()
      user = User(s, con, self.parent, self.command_mgr)
      auth, r = self.networking_rules.check_user(user)
      if auth:
        user.s.send('OK')
        user.start()
      else:
        user.s.send(r.fail_reason)
        user.s.close()
      

