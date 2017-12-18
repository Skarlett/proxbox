###
# Our libs
##
from exts import Extension             # tiny extension framework
from crawlers import MaxRetry          # An exception
from proxy import Proxy                # Proxy mold object that represents the the query results
from utils import MiningQueue          # set queue
from commands import Communicate_CLI   # threaded communication and command framework
import Settings                        # config
import factory                         # providers stuff

###
# External libs
##
from sqlite3worker import Sqlite3Worker # Threaded sqlite response

###
# builtins
##
import gzip
import shutil
import time
import logging
import threading

__version__ = Settings.version


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
  
  def run(self):
    while self.parent.running:
      if not self.parent._container.empty():
        self.parent.current_task = 'mining'
        proxy = Proxy(self.parent, *self.parent._container.get())
        if not proxy.dead:
          if time.time() - proxy.last_mined >= Settings.mine_wait_time:
            proxy.mine(self.timeout)
        else:
          self.parent._db.remove(proxy.uuid)
        self.parent._container.task_done()
      else:
        time.sleep(5)
  

class ProxyFrameDB(Sqlite3Worker):
  def __init__(self, fp, queue_size=Settings.max_sql_queue_size):
    self.fp = fp
    Sqlite3Worker.__init__(self, fp, max_queue_size=queue_size)
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
        ANONLVL TEXT,
        SPEED TEXT,
        FIRST_ADDED TEXT,
        UNIQUE(IP, PORT) ON CONFLICT REPLACE
      )''')
      self.execute('''
      CREATE TABLE RENEWAL(
        UUID TEXT,
        EPOCH TEXT
        /* DEAD_CNT INTEGER removed */
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
          REMOVE, ONLINE, ALIVE_CNT, DEAD_CNT, PROVIDER, FIRST_ADDED)
          VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''',
        (
          ip, int(port), user, pw, protocol, 0, 0, 0,
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
  def __init__(self, proxyDbLoc, threads=Settings.threads):
    '''
    
    TODO: Elaborate this objects functionality without having to call private variables outside of it.
    :param proxyDbLoc:
    :param threads:
    '''
    self._db = ProxyFrameDB(proxyDbLoc)
    self._start_time = time.time()
    self._container = None
    self._miners = []
    self.tasks = [ProxyFrame._scrape]

    # Stuff we made
    self.factory = factory.Factory()
    self.communicate = Communicate_CLI(self)
    self.exts = Extension(self, 'tasks')
    
    # Extra stuff
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
        if Settings.safe_run:
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
          online=True, timeout=10, protocol='nonspecific',
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
  
  def miner(self, chunk=100, find_method='ALIVE_CNT', order_method='ASC', force=False, include_online=True, timeout=5):
    '''
    :param chunk: Query size or None
    :param find_method: ALIVE_CNT or DEAD_CNT
    :return:
    '''
    query = 'SELECT * FROM PROXY_LIST WHERE %d-LAST_MINED > %d' % (int(time.time()), Settings.mine_wait_time)
    
    if not include_online:
      query += ' AND WHERE ONLINE = 0'
    
    query += ' ORDER BY ' + find_method.upper() + ', CAST(LAST_MINED as INTEGER) ' + order_method
    
    if not chunk in [None, 0] and type(chunk) is int:
      query += ' LIMIT %d' % chunk
    
    for row in self._db.execute(query):
      proxy = Proxy(self, *row)
      if not proxy.dead:
        if force or time.time() - proxy.last_mined >= Settings.mine_wait_time:
          self.current_task = "mining"
          proxy.mine(timeout)
        else:
          self.current_task = "chilling"
      else:
        self._db.remove(proxy.uuid)
  
  def start(self, find_method='ALIVE_CNT', order_method='ASC', include_online=True, timeout=5, threads=Settings.threads):
    if 0 in [self.threads, threads]:
      while self.running:
        self.miner(0)
        self.do_tasks()
    else:
      self._container = MiningQueue(1000000)
      self._miners = [Extra_miner(self, timeout) for _ in xrange(Settings.threads)]
      for b in self._miners:
        b.start()
      
      while self.running:
        if self._container.empty():
          query = 'SELECT * FROM PROXY_LIST WHERE %d-LAST_MINED > %d' % (int(time.time()), Settings.mine_wait_time)
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

