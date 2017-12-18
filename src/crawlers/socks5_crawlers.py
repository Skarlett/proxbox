from __init__ import Provider, requests, HREF_FIND

USE = False

class live_socks(Provider):
  def __init__(self):
    Provider.__init__(self, uuid="live-socks.com", renewal=60 * 60 * 24, use=USE)
    for x in HREF_FIND.findall(requests.get('http://www.live-socks.net/search/label/Socks%205').content):
      x = x[::-1].split('#', 1)[0][::-1]
      if 'socks-5' in x:
        self.urls.add(x)
    
class socks24(Provider):
  def __init__(self):
    Provider.__init__(self, uuid="socks24.org", renewal=60 * 60 * 24, use=USE)
    for x in HREF_FIND.findall(requests.get('http://www.socks24.org/').content):
      if 'socks' in '/'.join([y for y in x.split('/') if y and not '#' in y][2:]):
        self.urls.add(x)

def setup(factory):
  for m in [socks24(), live_socks()]:
    factory.providers.add(m)
