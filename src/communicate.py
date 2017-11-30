import socket, struct, threading, Settings, errno



class InstanceRunning(Exception):
  '''
  Called when it is believed when two programs might be trying to run.
  '''
  pass

class User():
  def __init__(self, s, con, timeout=30):
    self.s = s
    # print "client"
    self.ip, self.port = con
    self.s.settimeout(timeout)
    self.msg = None
  
  def send_msg(self, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    self.s.sendall(msg)
  
  def recv_msg(self):
    # Read message length and unpack it into an integer
    raw_msglen = self.recvall(4)
    if not raw_msglen:
      return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return self.recvall(msglen)
  
  def recvall(self, n):
    # Helper function to recv n bytes or return None if EOF is hit
    # print "recv"
    data = ''
    while len(data) < n:
      packet = self.s.recv(n - len(data))
      if not packet:
        return None
      data += packet
    return data


class Communicate_CLI(threading.Thread):
  def __init__(self, parent):
    threading.Thread.__init__(self)
    self.parent = parent
    self.s = socket.socket()
    try:
      self.s.bind(Settings.local_conn)
    except socket.error as serr:
      if serr.errno == errno.EADDRINUSE:
        raise InstanceRunning('It appears there is already an instance running on this machine.')
      raise serr
    
    self.s.listen(Settings.socket_backlog)
    self.running = False
    self.daemon = True
    self.start()
  
  def run(self):
    self.running = True
    while self.running:
      user = User(*self.s.accept())
      l = user.recv_msg().split(':::')
      cmd = l[0]
      args = l[1:] or list()
      
      for i, x in enumerate(args):
        if x.lower() == 'true':
          args[i] = True
        elif x.lower() == 'false':
          args[i] = False
        
        elif x.isdigit():
          args[i] = int(x)
      
      args = tuple(args)
      
      if not cmd.lower() == 'reload':
        if hasattr(self.parent.commands, cmd):
          resp = getattr(self.parent.commands, cmd)(*args)
          if type(resp) in [str, unicode]:
            resp = resp.encode('ascii', 'ignore')
          else:
            resp = str(resp)
          user.send_msg(resp.strip())
      user.s.close()