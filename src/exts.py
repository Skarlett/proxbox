from os import walk, path
import logging
# import Settings

class Extension:
  ''' Dynamic object carrying for objects to hold extensions '''
  def __init__(self, parent, folder, load_func='setup', load=True, exclusions=[]):
    self.folder = folder
    self.parent = parent
    self.load_func = load_func
    self.loaded = set()
    self.exclusions = exclusions
    if load:
      self.load_ext()
  
  def load_ext(self):
    ''' gimme moar stuff '''
    modules = []
    #                        walk(Settings.soure_folder, ...
    for root, dirs, files in walk(path.join(path.dirname(__file__), self.folder)):
      for x in files:
        if not x.startswith('__') and x.endswith('.py') and x not in self.exclusions:
          modules.append(x.split('.')[0])
      
      if not '__init__.py' in files:
        with open(path.join(root, '__init__.py'), 'wb') as f:
          f.write('')
      break
    
    for mod in modules:
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

