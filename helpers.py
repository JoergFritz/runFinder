import urllib2
import json
import time
from secrets import get_Google_API_key

def geocode(search_term):
    API_KEY = get_Google_API_key()
    base_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}"
    query = base_url.format( urllib2.quote(search_term), API_KEY)
    resp = urllib2.urlopen(query)
    data = json.load(resp)
    formatted_address = data['results'][0]['formatted_address']
    geom = data['results'][0]['geometry']
    lat, lon = geom['location']['lat'], geom['location']['lng']
    return lat, lon, formatted_address, data

class timewith():
    def __init__(self, name=''):
        self.name = name
        self.start = time.time()

    @property
    def elapsed(self):
        return time.time() - self.start

    def checkpoint(self, name=''):
        print '{timer} {checkpoint} took {elapsed} seconds'.format(
            timer=self.name,
            checkpoint=name,
            elapsed=self.elapsed,
        ).strip()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.checkpoint('finished')
        pass