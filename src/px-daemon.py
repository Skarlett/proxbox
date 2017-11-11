#!/usr/bin/python
import gzip
import shutil
import errno
import struct
import time
import logging
import socket
from sqlite3worker import Sqlite3Worker
from datetime import datetime
from threading import Thread
from os import path

from proxy import Proxy
import Settings
import commands
import providers

RUNNING = True

__version__ = Settings.version

# logging = logging.Logger('main.log', 10)

###
#            Todo ... fml
# [X] Safe run
# [ ] Add dynamic logging handle for debugging outside of development
# [X] Add support for http proxies
# [ ] Add support for socks4 proxies
# [X] add support for selecting which proxies to collect
# [X] Add command line support for specifying proxy protocol
# [X] Add support for "special" providers that are specific to the proxy protocol
#     Example socks24.org is special to socks 5, so if we only want to scrape http proxies,
#     that shouldn't be scraped
# [X] add phantomjs for scraping pages generated by JS
# [ ] seperate settings into a .conf file in etc/
# [ ] add regex pattern reference in add providers | right now it uses global ip and port find regex
# [ ] add filters (transparent, obscured, elite) for searching and collecting | sooner or later
# [X] Make set-up file
# [X] auto back up & compress
# [ ] add json output to get
# [X] directly connect skeleton.py to commands
# [X] enforce uuid in command add providers
# [X] converge factory and proxyframe so both providers file and database are purged
# [X] switch over to sqlite3worker eventually, maybe a modified version.
# [ ] massscan le internet, once i figure out how to collect banners.
# [ ] optimize scanning ips in providers

class Error(Exception):
  '''
  Globalized error for easy rejection in modular use.
  '''

class InstanceRunning(Error):
  '''
  Called when it is believed when two programs might be trying to run.
  '''
  pass


class User():
  def __init__(self, s, con, timeout=30):
    self.s = s
    #print "client"
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
    #print "recv"
    data = ''
    while len(data) < n:
      packet = self.s.recv(n - len(data))
      if not packet:
        return None
      data += packet
    return data
    
class Communicate_CLI(Thread):
  def __init__(self, parent):
    Thread.__init__(self)
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
 
class ProxyFrameDB(Sqlite3Worker):
  def __init__(self, fp):
    self.fp = fp
    Sqlite3Worker.__init__(self, fp)
    r = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PROXY_LIST';")
    if not r:
      self.execute('''CREATE TABLE PROXY_LIST(
        UUID INTEGER PRIMARY KEY,
        IP TEXT,
        PORT INTEGER,
        USER TEXT,
        PASSWORD TEXT,
        PROTOCOL TEXT,
        LAST_MINED TEXT,
        LAST_MINED_SUCCESS TEXT,
        ONLINE INTEGER,
        REMOVE INTEGER,
        ALIVE_CNT INTEGER,
        DEAD_CNT INTEGER,
        PROVIDER TEXT,
        /*NOOBTERM TEXT,*/
        UNIQUE(IP, PORT) ON CONFLICT REPLACE
      )''')
      self.execute('''
      CREATE TABLE RENEWAL(
        UUID TEXT,
        EPOCH TEXT,
        DEAD_CNT
      );
      ''')
      
      self.first_run = True
    else:
      self.first_run = False
      
  def getTotal(self):
    r = self.execute('SELECT Count(*) FROM PROXY_LIST')
    return int(r[0][0])
  
  def add(self, ip, port, protocol=None, user=None, pw=None, alive_cnt=0, dead_cnt=0,
          online=False, provider=None):
      if ip and port:
        self.execute(
          '''INSERT INTO PROXY_LIST(
            IP, PORT, USER, PASSWORD, PROTOCOL,
            LAST_MINED, LAST_MINED_SUCCESS,
            REMOVE, ONLINE, ALIVE_CNT, DEAD_CNT, PROVIDER)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
          ''',
            (
              ip, int(port), user, pw, protocol, 0, 0, 0,
              int(online), alive_cnt, dead_cnt, provider
            )
          )
        
          
   
    
  def remove(self, uuid):
    self.execute('DELETE FROM PROXY_LIST WHERE UUID=?;', (uuid,))
      
  
  def provider_stats(self, provider):
    dead = alive = 0
    for x in self.execute('SELECT * FROM PROXY_LIST WHERE PROVIDER = ?', (provider.uuid,)):
      p = Proxy(self, *x)
      dead += p.dead_cnt
      alive += p.alive_cnt
    prev, epoch = self.execute('SELECT DEAD_CNT, EPOCH FROM RENEWAL WHERE UUID = ?', (provider.uuid,))[0]
    
    return epoch, alive, dead
    
    
  def modify(self, uuid, var, value):
    self.execute(
      '''
      UPDATE PROXY_LIST
      SET %s = ?
      WHERE UUID = ?;''' % var.upper(),
      (value, uuid)
    )
    
  
  def backup(self, to):
    try:
      with open(self.fp, 'rb') as f_in, gzip.open(to, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
        return True
    except: return False
  
class ProxyFrame:
  def __init__(self, proxyDbLoc):
    self._db = ProxyFrameDB(proxyDbLoc)
    
    # Extra stuff
    self.mine_cnt = 0
    self._start_time = time.time()
    self.factory = providers.Factory(Settings.providers)
    self.last_scraped = self.find_last_scraped()
    
    self._tasks = [
      self.scrape,
      self.backup
    ]
    
    self.commands = commands.commands(self)
    self.communicate = Communicate_CLI(self)
    # start up and check database for first run.
    self.current_task = "init"
    
    
    if self._db.first_run or self._db.getTotal() <= 0:
      logging.error('Not enough proxies in DB, running proxy scrape first.')
      self.scrape(True)
  
    #################
    #     Utils
  
  def find_last_scraped(self):
    '''
    searches database providers to find the latest one scraped
    :return: tuple (uuid, epoch)
    '''
    latest_epoch = 0
    provider = None
    for row in self._db.execute('SELECT * FROM RENEWAL'):
      uuid, epoch, deadcnt = row
      if epoch > latest_epoch:
        latest_epoch = epoch
        provider = uuid
    return provider, latest_epoch
    
  def uptime(self):
    '''
    :return: int; Seconds elapsed from start up
    '''
    return time.time() - self._start_time

  def totalProxies(self):
    '''
    :return: int; returns total number of proxies in database.
    '''
    return self._db.getTotal()

  def online(self):
    '''
    :return: int; returns total number of proxies marked as online in the database
    '''
    return self._db.execute('SELECT Count(*) FROM PROXY_LIST WHERE ONLINE = 1')[0][0]

  def reload(self):
    '''
    reloads all the cool stuff that should be adjustments by the user
    :return: None
    '''
    for m in [Settings, commands]:
      reload(m)
    self.commands = commands.commands(self)

  def shutdown(self):
    ''' Nicely shuts everything down for us '''
    global RUNNING
    RUNNING = False
    self.communicate.running = False
    self.communicate.s.close()

    #################
    # Functionality #

  def backup(self):
    lb = path.join(Settings.data_folder, 'last_backup')
    if not path.isfile(lb):
      with open(lb, 'wb') as f:
        f.write(str(time.time()))
    
    with open(lb, 'rb') as f:
      if float(f.read().strip())+Settings.backup_at >= time.time():
        self._db.backup(path.join(Settings.backup_folder, '%s_%s_%s_backup.db.gz' % (
          str(datetime.month), str(datetime.day), str(datetime.year))))
    

  def scrape(self, force=False):
    '''
    Iterates through Settings.providers and keeps a database of time based
    on their last scrape
    :param force: boolean; Ignores time parameter
    :return: int amount of added entries
    '''
    logging.info('Preparing self_update...')
    ctr = 0
    print('preparing self update')
    self.current_task = "scraping"
    for result in self.factory.providers:
      data = self._db.execute('SELECT * FROM RENEWAL WHERE UUID = ?', (result.uuid,))[0]
      
      if data and len(data) > 2:
        _, epoch, _ = data
        epoch = float(epoch)
      else:
        logging.info('Adding %s to db' % result.uuid)
        self._db.execute('INSERT INTO RENEWAL(UUID, EPOCH, DEAD_CNT) VALUES(?, ?, ?)', (result.uuid, 0, 0))
        epoch = 0
      
      if force or time.time() >= epoch+result.renewal:
        if Settings.safe_run:
          try:
            result.scrape()
          except:
            logging.exception('Scraping %s failed.' % result.uuid)
            if hasattr(result, 'use'):
              result.use = False
            else: # It should, but in case of glitches and subclasses, we'll assert it will have it if it fails.
              setattr(result, 'use', False)
        else:
          result.scrape()
        
        if len(result.proxies) > 0 and result.use:
          ctr += len(result.proxies)
          for ip, port in result.proxies:
            self._db.add(ip, port, provider=result.uuid)
        else:
          logging.warn('Failed provider [{}] Dumping object into logs.\n{}\n'.format(result.uuid.upper(), vars(result)))
          

        self._db.execute('UPDATE RENEWAL SET EPOCH = ? WHERE UUID = ?', (time.time(), result.uuid))
        self.last_scraped = (result.uuid, time.time())
    logging.info('Added %d to PXFrame.' % ctr)
    return ctr
  
  def do_tasks(self):
    #print "doing tasks"
    for x in self._tasks:
      if Settings.safe_run:
        try:
          x()
        except:
          logging.exception('Failed to do task '+str(x))
      else:
        x()
    
    
  def get(self, cnt=1, check_alive=True, online=True, timeout=10, protocol='nonspecific'):
    '''
    receive proxies :D
    :param cnt: int; How many proxies would you like it to yield
    :param check_alive: bool; Should proxies be checked if alive before yielded
    :param online: bool; only get proxies marked as online from the database to yield
    :param timeout: int; if check_alive; timeout session
    :return: proxy.Proxy instances
    '''
    assert cnt > 0
    valid_response = 0
    
    while valid_response <= cnt:
      sql = 'SELECT * FROM PROXY_LIST'
      if online:
        sql += ' WHERE ONLINE = 1'
        if not protocol == 'nonspecific':
          sql += ' AND WHERE PROTOCOL = '+protocol.lower()
      sql += ' ORDER BY RANDOM() LIMIT '+str(cnt)
      
      data = self._db.execute(sql)
      for row in data:
        if row:
          proxy = Proxy(self, *row)
          if check_alive:
            if proxy.is_alive(timeout):
              proxy.checked(True)
              valid_response += 1
              yield proxy
            else:
              proxy.checked(False)
          else:
            valid_response += 1
            yield proxy
        if valid_response >= cnt:
          break
      if valid_response >= cnt:
        break
    
  def miner(self, chunk=100, find_method='ALIVE_CNT', order_method='ASC', force=False, include_online=True, timeout=5,
            do_tasks=True):
    '''
    :param chunk: Query size or None
    :param find_method: ALIVE_CNT or DEAD_CNT
    :return:
    '''
    #print "mining."
    self.current_task = "mining"
    query = 'SELECT * FROM PROXY_LIST'
  
    if not include_online:
      query += ' WHERE ONLINE = 0'
  
    query += ' ORDER BY ' + find_method.upper() + ', CAST(LAST_MINED as INTEGER) '+order_method
  
    if not chunk in [None, 0] and type(chunk) is int:
      query += ' LIMIT %d' % chunk
      
    for row in self._db.execute(query):
      proxy = Proxy(self, *row)
      #try:
      if not proxy.dead:
          if force or time.time() - proxy.last_mined >= Settings.mine_wait_time:
            proxy.mine(timeout)
          else:
            self.current_task = "chilling"
      else:
          self._db.remove(proxy.uuid)
      # except ValueError:
      #   self._db.remove(proxy.uuid)
      self.do_tasks()
    
    

if __name__ == '__main__':
  print "loading from "+Settings.data_folder
  pxf = ProxyFrame(Settings.database)
  while RUNNING:
    try:
      if Settings.safe_run:
        try:
          pxf.miner(0)
        except Exception: pass
      else:
        pxf.miner(0)
    except KeyboardInterrupt:
      pxf.shutdown()
      break
      
