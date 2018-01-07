###
# Our libs
##
from exts import Extension               # tiny extension framework
from extended_providers import MaxRetry, IPPattern  # An exception, a re pattern
from utils import MiningQueue            # set queue
from commands import Communicate_CLI     # threaded communication and command framework
from scanner import discover_protocol
from commands import CommandsManager, Command
import settings                          # config
import providers_factory                 # providers stuff
import utils
###
# External libs
##
from sqlite3worker import Sqlite3Worker # Threaded sqlite response
import requests

###
# builtins
##
import gzip
import shutil
import time
import logging
import threading
import json
import socket

__version__ = settings.version


###
#            Todo ... fml
# [ ] Add support for "special" providers that are specific to the proxy protocol
#     Example socks24.org is special to socks 5, so if we only want to scrape http proxies,
#     that shouldn't be scraped
# [ ] seperate settings into a .conf file in etc/
# [ ] add regex pattern reference in add providers | right now it uses global ip and port find regex
# [ ] add filters (transparent, obscured, elite) for searching and collecting | sooner or later
# [ ] massscan le internet, once i figure out how to collect banners.


class Error(Exception):
  '''
  Globalized error for easy rejection in modular use.
  '''


class Extra_miner(threading.Thread):
  def __init__(self, parent, timeout=5):
    threading.Thread.__init__(self)
    self.daemon = True
    self.parent = parent
    self.timeout = timeout
    self.status= 'init'
  
  def run(self):
    while self.parent.running:
      if not self.parent._container.empty():
        self.parent.current_task = 'mining'
        self.status = 'ClinkClink.'
        proxy = Proxy(self.parent, *self.parent._container.get())
        if not proxy.dead:
          if time.time() - proxy.last_mined >= settings.mine_wait_time:
            proxy.mine(self.timeout)
        else:
          self.parent._db.remove(proxy.uuid)
        self.parent._container.task_done()
  
      else:
        self.status = 'chilling'
        time.sleep(5)
      


class Proxy:
  def __init__(self, parent, uuid, ip, port, protocol, last_mined,
               last_mined_success, online, dead, alive_cnt, dead_cnt, provider,
               anonlvl, speed, first_added):
    
    self.parent = parent
    self.uuid = int(uuid)
    self.ip = ip
    self.port = int(port)
    self.protocol = protocol
    self.last_mined = float(last_mined) or float()
    self.alive_cnt = alive_cnt or 0
    self.dead_cnt = dead_cnt or 0
    self.dead = bool(int(dead))
    self.online = bool(int(online))
    self.last_mined_success = float(last_mined_success)
    self.provider = provider
    self.first_added = first_added
    
    
    if not anonlvl:
      load_anonlvl = True
      self.anonlvl = 'Elite' if self.protocol and self.protocol.startswith('socks') else anonlvl
    else:
      load_anonlvl = False
      self.anonlvl = anonlvl
    self.speed = speed
    
    if load_anonlvl and self.anonlvl and self.anonlvl == 'Elite':
      self.parent._db.modify(self.uuid, 'ANONLVL', 'Elite')
  
  def mine(self, timeout=5):
    self.parent.mine_cnt += 1
    
    if not self.protocol:
      self.protocol, self.speed = discover_protocol(self, timeout=timeout)
      if self.protocol and self.speed:
        self.parent._db.modify(self.uuid, 'PROTOCOL', self.protocol)
        self.parent._db.modify(self.uuid, 'SPEED', str(self.speed))
        self.checked(True)
      else:
        self.checked(False)
    else:
      start = time.time()
      alive = self.is_alive(timeout=timeout)
      if alive:
        self.speed = time.time() - start
      self.checked(alive)
    
    self.parent._db.modify(self.uuid, 'SPEED', str(self.speed)) if self.speed else None
    self.parent._db.modify(self.uuid, 'LAST_MINED', str(time.time()))
    
    if not self.anonlvl and self.protocol:
      self.anonlvl = self.rank()
      self.parent._db.modify(self.uuid, 'ANONLVL', self.anonlvl)
    self.die()
  
  def die(self, check_policy=True, force_policy=False):
    if check_policy and not self.check_policy(force_policy):
      return
    self.parent._db.modify(self.uuid, 'REMOVE', 1)
  
  def rank(self):
    if self.protocol in ['socks5', 'socks4']:
      return 'Elite'
    else:
      try:
        resp = requests.get(self.protocol + '://httpbin.org/get?show_env',
                          proxies={
                            self.protocol: self.protocol + '://' + self.ip + ':' + str(self.port)
                          },
                          headers={'User-Agent': 'Test'})
      except:
        return False
      
      try:
        content = json.loads(resp.content)
      except:
        return False
      
      ips = IPPattern.findall(resp.content)
      
      user_agent = False
      proxy_net = False
      obsurce = False
      transparent = False
      
      if not self.ip in ips and not content['origin'] == self.ip:
        proxy_net = True
      elif settings.public_ip in ips:
        return 'Transparent'
      else:
        obsurce = True
      
      if 'User-Agent' in content:
        if content['User-Agent'] == 'Test':
          user_agent = True
      
      if proxy_net:
        return 'Elite'
      elif user_agent or obsurce:
        return 'Obscured'
      elif transparent:
        'Transparent'
  
  def is_alive(self, timeout=settings.global_timeout):
    s = socket.socket()
    s.settimeout(timeout)
    reply = False
    try:
      s.connect((self.ip, self.port))
      reply = True
    except Exception:
      pass
    s.close()
    return reply
  
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
      return utils.percentage(self.alive_cnt, self.dead_cnt + self.alive_cnt)
    except ZeroDivisionError:
      return 0
  
  def check_policy(self, force=False):
    return force or settings.remove_when_total <= self.alive_cnt + self.dead_cnt and \
           float(self.reliance()) <= float(settings.remove_by_reliance) and \
           time.time() >= float(self.first_added) + settings.remove_when_time_kept


class ProxyFrameDB(Sqlite3Worker):
  def __init__(self, fp, queue_size=settings.max_sql_queue_size):
    self.fp = fp
    Sqlite3Worker.__init__(self, fp, max_queue_size=queue_size)
    r = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PROXY_LIST';")
    if not r:
      self.execute('''CREATE TABLE PROXY_LIST(
        UUID INTEGER PRIMARY KEY,
        IP TEXT,
        PORT INTEGER,
        PROTOCOL TEXT,
        LAST_MINED TEXT,
        LAST_MINED_SUCCESS TEXT,
        ONLINE INTEGER,
        REMOVE INTEGER,
        ALIVE_CNT INTEGER,
        DEAD_CNT INTEGER,
        PROVIDER TEXT,
        ANONLVL TEXT,
        SPEED TEXT,
        FIRST_ADDED TEXT,
        UNIQUE(IP, PORT) ON CONFLICT REPLACE
      )''')
      self.execute('''
      CREATE TABLE RENEWAL(
        UUID TEXT,
        EPOCH TEXT,
        UNIQUE(UUID) ON CONFLICT REPLACE
      );
      ''')
      
      self.first_run = True
    else:
      self.first_run = False
  
  def getTotal(self):
    r = self.execute('SELECT Count(*) FROM PROXY_LIST')
    return int(r[0][0])
  
  def add(self, ip, port, protocol=None, alive_cnt=0, dead_cnt=0,
          online=False, provider=None):
    if ip and port:
      self.execute(
        '''INSERT INTO PROXY_LIST(
          IP, PORT, PROTOCOL,
          LAST_MINED, LAST_MINED_SUCCESS,
          REMOVE, ONLINE, ALIVE_CNT, DEAD_CNT, PROVIDER, FIRST_ADDED)
          VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''',
        (
          ip, int(port), protocol, 0, 0, 0,
          int(online), alive_cnt, dead_cnt, provider, time.time()
        )
      )
  
  def remove(self, uuid):
    self.execute('DELETE FROM PROXY_LIST WHERE UUID=?;', (uuid,))
  
  def provider_stats(self, provider):
    dead = alive = 0
    for a, b in self.execute('SELECT DEAD_CNT, ALIVE_CNT FROM PROXY_LIST WHERE PROVIDER = ?', (provider.uuid,)):
      dead += a
      alive += b
    
    epoch = self.execute('SELECT EPOCH FROM RENEWAL WHERE UUID = ?', (provider.uuid,))[0][0]
    
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
    except:
      return False


class ProxyFrame:
  Proxy = Proxy # Carried for extensions
  Settings = settings # Settings carried for other shit
  Utils = utils
  
  def __init__(self, proxyDbLoc, threads=Settings.threads):
    '''
    
    TODO: Elaborate this objects functionality without having to call private variables outside of it.
    :param proxyDbLoc:
    :param threads:
    '''
    ###
    # Main
    ##
    self._db = ProxyFrameDB(proxyDbLoc)
    self._start_time = time.time()
    self._container = None
    self._miners = []
    self.tasks = [ProxyFrame._scrape]
    
    ###
    # Extensions
    ##
    self.factory = providers_factory.Factory()
    self.communicate = Communicate_CLI(self)
    self.exts = Extension(self, 'tasks')
    
    ###
    # sugar
    ##
    self.mine_cnt = 0
    self.current_task = "init"
    self.running = True
    self.threads = threads
    
    self.last_scraped = self.find_last_scraped()
    # start up and check database for first run.
    if self._db.first_run or self._db.getTotal() <= 0:
      logging.error('Not enough proxies in DB, running proxy scrape first.')
      self.scrape(True)
      
      #################
      #     Utils
  
  
  def reload_crawlers(self):
    ''' reload crawlers'''
    for m in self.factory.exts.loaded:
      reload(m)
    self.factory.providers = set()
    self.factory._load()
    self.factory.exts.reload_setup_hooks()
  
  def reload_interpreter(self):
    '''reload json interpretation '''
    for m in self.factory.logic_interpreter.exts.loaded:
      reload(m)
    self.factory.logic_interpreter.passive_funcs = set()
    self.factory.logic_interpreter.active_funcs = set([self.factory.logic_interpreter.range, utils.safe_eval])
    self.factory.logic_interpreter.exts.reload_setup_hooks()
  
  def reload_commands(self):
    '''reloads sys_commands'''
    for m in self.communicate.command_mgr.exts.loaded:
      reload(m)
    
    self.communicate.command_mgr.commands = [
      Command(CommandsManager.help, ('-h',)),
      Command(CommandsManager._reload, ('--reload',), self_name=False)

    ]
    
    self.communicate.command_mgr.exts.reload_setup_hooks()
    self.communicate.command_mgr.after_load()
    #print self.communicate.command_mgr.commands
  
  def reload_tasks(self):
    ''' reloads tasks'''
    for m in self.exts.loaded:
      reload(m)
    
    self.tasks = [ProxyFrame._scrape]
    self.exts.reload_setup_hooks()

  def reload(self, reload_funcs=None):
    '''reloads all extensible code, and forces a json provider reload'''
    reload_funcs = reload_funcs or [self.reload_tasks, self.reload_crawlers,
                                    self.reload_commands, self.reload_interpreter]
    for x in reload_funcs:
      x()
    
  def scrape(self, force=False):
    return ProxyFrame._scrape(self, force=force)
  
  @staticmethod
  def _scrape(pxf, force=False):
    '''
    Iterates through * and keeps a database of time based
    on their last scrape
    :param force: boolean; Ignores time parameter
    :return: int amount of added entries
    '''
    logging.info('Preparing self_update...')
    ctr = 0
    for result in pxf.factory.providers:
      data = pxf._db.execute('SELECT * FROM RENEWAL WHERE UUID = ?', (result.uuid,))
      if data and data[0]:
        _, epoch = data[0]
        epoch = float(epoch)
      else:
        logging.info('Adding [%s] to db' % result.uuid)
        pxf._db.execute('INSERT INTO RENEWAL(UUID, EPOCH) VALUES(?, ?)', (result.uuid, 0))
        epoch = 0
    
      if force or time.time() >= epoch + result.renewal:
        pxf.current_task = "scraping"
        if settings.safe_run:
          try:
            result.scrape()
          except KeyboardInterrupt:
            break
            
          except Exception:
            logging.exception('Scraping %s failed.' % result.uuid)
            result.use = False
        else:
          try:
            result.scrape()
          except MaxRetry:
            pass
      
        if len(result.proxies) > 0:
          if result.use:
            ctr += len(result.proxies)
            for ip, port in result.proxies:
              pxf._db.add(ip, port, provider=result.uuid)
        else:
          logging.warn('Failed provider [{}] Dumping object into logs.\n{}\n'.format(result.uuid.upper(), vars(result)))
      
        pxf._db.execute('UPDATE RENEWAL SET EPOCH = ? WHERE UUID = ?', (str(time.time()), result.uuid))
        pxf.last_scraped = (result.uuid, time.time())
  
    logging.info('Added %d to PXFrame.' % ctr)
    return ctr

  def find_last_scraped(self):
    '''
    searches database providers to find the latest one scraped
    :return: tuple (uuid, epoch)
    '''
    latest_epoch = 0
    provider = None
    for row in self._db.execute('SELECT * FROM RENEWAL'):
      uuid, epoch = row
      if epoch > latest_epoch:
        latest_epoch = epoch
        provider = uuid
    return provider, latest_epoch
  
  def uptime(self):
    '''
    :return: int; Seconds elapsed from start up
    '''
    return utils.h_time(time.time() - self._start_time)
  
  def total_proxies(self):
    '''
    :return: int; returns total number of proxies in database.
    '''
    return self._db.getTotal()
  
  def online(self):
    '''
    :return: int; returns total number of proxies marked as online in the database
    '''
    return self._db.execute('SELECT Count(*) FROM PROXY_LIST WHERE ONLINE = 1')[0][0]
  
  
  def shutdown(self):
    ''' Nicely shuts everything down for us '''
    self.running = False
    self.communicate.running = False
    self.communicate.s.close()
    
    #################
    # Functionality #
  
  
  def do_tasks(self):
    # print "doing tasks"
    for x in self.tasks:
      try:
        x(self)
      except KeyboardInterrupt:
        self.shutdown()
      except Exception:
        self.tasks.remove(x)
        logging.exception('Failed to do task ' + str(x.__name__))
  
  
  def get(self, cnt=1, check_alive=True,
          online=True, protocol='nonspecific',
          order_by='RANDOM()'):
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
          sql += ' AND WHERE PROTOCOL = ' + protocol.lower()
      
      sql += ' ORDER BY '+order_by+' LIMIT ' + str(cnt)
      
      data = self._db.execute(sql)
      for row in data:
        if row:
          proxy = self.Proxy(self, *row)
          if check_alive:
            if proxy.is_alive(settings.global_timeout):
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
  
  def miner(self, chunk=100, find_method='ALIVE_CNT', order_method='ASC', force=False, include_online=True, timeout=5):
    '''
    :param chunk: Query size or None
    :param find_method: ALIVE_CNT or DEAD_CNT
    :return:
    '''
    query = 'SELECT * FROM PROXY_LIST WHERE %d-LAST_MINED > %d' % (int(time.time()), settings.mine_wait_time)
    
    if not include_online:
      query += ' AND WHERE ONLINE = 0'
    
    query += ' ORDER BY ' + find_method.upper() + ', CAST(LAST_MINED as INTEGER) ' + order_method
    
    if not chunk in [None, 0] and type(chunk) is int:
      query += ' LIMIT %d' % chunk
    
    for row in self._db.execute(query):
      proxy = self.Proxy(self, *row)
      if not proxy.dead:
        if force or time.time() - proxy.last_mined >= settings.mine_wait_time:
          self.current_task = "mining"
          proxy.mine(timeout)
        else:
          self.current_task = "chilling"
      else:
        self._db.remove(proxy.uuid)
  
  def start(self, find_method='ALIVE_CNT', order_method='ASC', include_online=True, timeout=settings.global_timeout):
    if self.threads == 0:
      while self.running:
        self.miner(0)
        self.do_tasks()
    else:
      self._container = MiningQueue(1000)
      self._miners = [Extra_miner(self, timeout) for _ in xrange(settings.threads)]
      for b in self._miners:
        b.start()
      
      while self.running:
        if self._container.empty():
          query = 'SELECT * FROM PROXY_LIST WHERE %d-LAST_MINED > %d' % (int(time.time()), settings.mine_wait_time)
          if not include_online:
            query += ' AND WHERE ONLINE = 0'
          
          query += ' ORDER BY ' + find_method.upper() + ', CAST(LAST_MINED as INTEGER) ' + order_method
          
          resp = self._db.execute(query)
          if len(resp) > 0:
            for row in resp:
              self._container.put(row)
          else:
            time.sleep(5)
            # print self._container.unfinished_tasks
        self.do_tasks()

