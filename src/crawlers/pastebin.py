from __init__ import HREF_FIND, Provider
import requests
import logging

USE = False


class Pastebin_Settings:
  renewal = 4*60 # Every 4 Minutes
  onDieRenewal = 60*60 # An hour


class Pastebin(Provider):
  def __init__(self):
    r = range(1, 1000)
    r.remove(80)

    Provider.__init__(self, uuid="Pastebin.com", renewal=4*60, use=USE, badports=r)
    self._scrape = self.scrape
    
    def new_scrape():
      html_body = requests.get('https://pastebin.com/archive')
      bad_url_filters = ['/tools', '/api', '/trends', '/privacy', '/cookies', '/dmca',
                         '/pro', '/faq', '/contact', '/scraping', 'http', '/archive',
                         '/login', '/messages', '/settings', '/alerts', '/signup',
                         '/i/', '/favicon', 'mail']
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
        
      try:
        self._scrape()
      except Exception as e:
        logging.exception('Couldn\'t scrape Pastebin')
        self.renewal = Pastebin_Settings.onDieRenewal
      self.renewal = Pastebin_Settings.renewal
      self.urls = set()
    
    self.scrape = new_scrape

def setup(factory):
  factory.providers.add(Pastebin())

#
# paste = Pastebin()
# paste.scrape()
# print paste.proxies