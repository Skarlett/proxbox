from os.path import isfile
from cogs import Provider, proxyScrape

__author__ = "https://github.com/Skarlett"

if __name__ == '__main__':
  from sys import argv
  from os.path import split
  
  helpmsg = '%s [-u --url (-js) URL] [-a --author] [-h --help] [-d --data FILE]' \
            '\n\n' \
            'Example: python %s -u http://someplace.somehow/proxies http://moarproxies.net/pxy' % (split(__file__)[1], split(__file__)[1])
  
  try:
    if argv[1] in ['-u', '--url']:
      if not argv[2] == '-js':
        js_gen = False
        urls = argv[2:]
      else:
        js_gen = True
        urls = argv[3:]
      
      if len(urls) > 0:
        p = Provider(jsgen=js_gen)
        for x in urls:
          if not x.startswith('http'):
            x = 'http://'+x
          p.urls.add(x)
        p.scrape()
        
        if len(p.proxies) > 0:
          for ip, port in p.proxies:
            print(':'.join((ip, port)))
            
        else: print("No proxies found")
      else:
        print('Example: python %s -u http://someplace.somehow/proxies http://moarproxies.net/pxy ')
    
    elif argv[1] in ['--author', '-a']:
      print(__author__)
    
    elif argv[1] in ['-d', '--data']:
      if len(argv) > 2:
        for f in argv[2:]:
          if isfile(f):
            try:
              with open(f) as reader:
                for line in reader:
                  for ip, port in proxyScrape(line):
                    print(ip+':'+str(port))
            except:
              print("Could not read "+f)
      else:
        print('Example: %s -d file1 file2 file3' % split(__file__)[1])
        
    elif argv[1] in ['--help', '-h']:
       print(helpmsg)
    
    else: print("argument not recognized.")
    
  except IndexError:
    print(helpmsg)