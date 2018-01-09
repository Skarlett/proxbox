from os import walk, path, mkdir
import logging

etc_folder = path.join(path.join(path.split(path.dirname(__file__))[0], 'etc'), 'ext')

class Extension:
  ''' Dynamic object carrying for objects to hold extensions '''
  def __init__(self, parent, folder, load_func='setup', load=True, exclusions=[]):
    self.folder = folder
    self.parent = parent
    self.load_func = load_func
    self.loaded = set()
    self.available = list()
    self.exclusions = exclusions
    
    self.etc_data = path.join(etc_folder, self.folder)
    if not path.isdir(self.etc_data):
      mkdir(self.etc_data)
    
    if load:
      self.load_ext()
    
    for x in self.loaded:
      etc_file = path.join(self.etc_data, x.__name__.split('.')[1]+ '.json')
      if path.isfile(etc_file):
        pass
      else:
        with open(etc_file, 'w') as f:
           f.write('')
      #print path.isfile(etc_file)
      
      #if not path.isfile(etc_folder):
      
    
  def find_files(self):
    for root, dirs, files in walk(path.join(path.dirname(__file__), self.folder)):
      for x in files:
        if not x.startswith('__') and x.endswith('.py') and x not in self.exclusions:
          yield x.split('.')[0]
    
      if not '__init__.py' in files:
        with open(path.join(root, '__init__.py'), 'wb') as f:
          f.write('pass')
      break
  
  def reload_setup_hooks(self):
    loaded = [x.__name__ for x in self.loaded]
    for f in self.find_files():
      needs_containment = False
      if f in loaded:
        mod = [x for x in self.loaded if x.__name__ == f][0]
      else:
        needs_containment = True
        mod = __import__(self.folder + '.' + f).__dict__[f]
      
      if hasattr(mod, 'USE'):
        if mod.USE:
          if hasattr(mod, self.load_func):
            try:
              getattr(mod, self.load_func)(self.parent)
            except Exception as e:
              logging.exception(mod.__name__ + ' Has failed to load due to [' +e.__class__. __name__ +'] Being raised.')
          else:
            logging.warning(mod.__name__ +' Has no setup function. Ignoring...')
      else:
        logging.warning(mod.__name__ +' Has no USE flag, ignoring...')
      
      if needs_containment:
        self.loaded.add(mod)

  def load_ext(self):
    ''' gimme moar stuff '''
    #                        walk(Settings.soure_folder, ...
    fs = list(self.find_files())
    
    for mod in fs:
      _mod = __import__(self.folder + '.' + mod).__dict__[mod]
        
      if hasattr(_mod, 'USE'):
        if _mod.USE:
          if hasattr(_mod, self.load_func):
            try:
              getattr(_mod, self.load_func)(self.parent)
              self.loaded.add(_mod)
            except Exception as e:
              logging.exception(mod + ' Has failed to load due to [' +e.__class__. __name__ +'] Being raised.')
          else:
            logging.warning(mod +' Has no setup function. Ignoring...')
      else:
        logging.warning(mod +' Has no USE flag, ignoring...')
