import requests
from urllib.parse import parse_qsl
from bs4 import BeautifulSoup
import re
import json

home = 'http://www.youtube.com'

pats = {
    'config': re.compile(b'ytplayer[.]config.*?(\{.*?\});'),
    'type': re.compile(r'(?P<type>\w+?)/(?P<comp>\w+).*?codecs="(?P<codec>.*?)"'),
    'size': re.compile(r'(\d{2,4}).*(\d{2,4})'),
    'itag': re.compile(r'((\d{1,3})/(\d{2,4}).*(\d{2,4}))'),
    'playlist': re.compile(b'(\{"responseContext".*?.*?\});')
}

