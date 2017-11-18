from __init__ import HREF_FIND, Provider, Settings
import requests


USE = False

class Pastebin(Provider):
  def __init__(self):
    r = range(1, 1000)
    if 'http' in Settings.collect_protocol:
      for i in [80, 81]:
        r.remove(i)
    
    Provider.__init__(self, uuid="Pastebin.com", renewal=4*60, use=False, badports=r)
    self._scrape = self.scrape
    
    def new_scrape():
      html_body = requests.get('https://pastebin.com/archive')
      bad_url_filters = ['/tools', '/api', '/trends', '/privacy', '/cookies', '/dmca',
                         '/pro', '/faq', '/contact', '/scraping', 'http', '/archive',
                         '/login', '/messages', '/settings', '/alerts', '/signup',
                         '/i/', '/favicon']
      for url in HREF_FIND.findall(html_body.content):
        live_or_die = True
        for badthing in bad_url_filters:
          if url.startswith(badthing):
            live_or_die = False
            break
    
        if live_or_die:
          if not url.startswith('http'):
            url = 'https://pastebin.com'+url
          self.urls.add(url)
      
      self._scrape()
      self.urls = set()
    
    self.scrape = new_scrape

def setup(factory):
  factory.providers.add(Pastebin())

#
# paste = Pastebin()
# paste.scrape()
# print paste.proxies