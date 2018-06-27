import requests
from urllib.parse import parse_qsl, urljoin
from bs4 import BeautifulSoup
import re
import json

home = 'http://www.youtube.com'

user_agent = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'}
ajax = {'X-Requested-With': 'XMLHttpRequest'}
ajax.update(user_agent)

pats = {
    'config': re.compile(b'ytplayer[.]config.*?(\{.*?\});'),
    'type': re.compile(r'(?P<type>\w+?)/(?P<comp>\w+).*?codecs="(?P<codec>.*?)"'),
    'size': re.compile(r'(\d{2,4}).*(\d{2,4})'),
    'itag': re.compile(r'((\d{1,3})/(\d{2,4}).*(\d{2,4}))'),
    'playlist': re.compile(b'(\{"responseContext".*?.*?\});')
}

class Video:
    def __init__(self,url):
        self._html = requests.get(url, headers=user_agent).content
        self._config = self._yt_config()
        self._itag_to_size = self._fmt_map()

    def _yt_config(self):
        match = pats['config'].search(self._html).group(1)
        config = json.loads(match)
        return config

    def _fmt_map(self):
        fmts = self._config['args']['fmt_list'].split(',')
        itag_size = [fmt.split('/') for fmt in fmts]
        itag_to_size = {
            itag : pats['size'].search(size).groups()
            for itag,size in itag_size
        }
        return itag_to_size

    def _parse_fmts(self, kind):
        qs_s = self._config['args'][kind].split(',')
        fmts = [dict(parse_qsl(qs)) for qs in qs_s]
        return fmts

    @property
    def adaptive_fmts(self):
        fmts = self._parse_fmts('adaptive_fmts')
        pretty_fmts = [self._pretty_ad(fmt) for fmt in fmts]
        return pretty_fmts

    @property
    def usable_fmts(self):
        fmts = self._parse_fmts('url_encoded_fmt_stream_map')
        pretty_fmts = [self._pretty_us(fmt) for fmt in fmts]
        return pretty_fmts

    def _pretty_ad(self,fmt):
        pretty_fmt = {
            'len' : int(fmt.get('clen',0)),
            'bitrate' : int(fmt['bitrate']),
            'fps' : int(fmt['fps']),
            'quality' : fmt['quality_label'],
            'type': pats['type'].search(fmt['type']).groupdict(),
            'size': pats['size'].search(fmt['size']).groups(),
            'url': fmt['url']
        }

        return pretty_fmt

    def _pretty_us(self,fmt):
        pretty_fmt = {
            'size': self._itag_to_size[fmt['itag']],
            'type': pats['type'].search(fmt['type']).groupdict(),
            'quality': fmt['quality'],
            'url': fmt['url']
        }

        return pretty_fmt

class Playlist:
    def __init__(self,url,workers=5):
        self._html = requests.get(url).text
        self._soup = BeautifulSoup(self._html,'html.parser')
        self.items = self._playlist_items()
        
    def _playlist_items(self):
        a_s = self._soup.find_all('a',class_='pl-video-title-link')
        #items = [dict(parse_qsl(urlparse(a['href']).query)) for a in a_s]
        items = [urljoin(home,a['href']) for a in a_s]
        return items

    def __iter__(self):
        for item in self.items:
            video = Video(item)
            yield video
