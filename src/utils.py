import Queue

def safe_eval(string, dirs={}):
  dirs["__builtins__"] = dirs or None
  return eval(string, dirs)


def percentage(part, whole):
  try:
    return 100 * float(part) / float(whole)
  except ZeroDivisionError:
    return 0

def h_time(seconds):
  if 8640000 >= seconds:
    m, s = divmod(float(seconds), 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)
  else:
    return "+100 days"

class MiningQueue(Queue.Queue):
  def _init(self, maxsize):
    self.queue = set()
  
  def _put(self, item):
    self.queue.add(item)
  
  def _get(self):
    return self.queue.pop()
  
  def __contains__(self, item):
    with self.mutex:
      return item in self.queue
    
def is_func(func):
  def _blank(): pass
  return type(func) == type(_blank)