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

def getDistanceMeters(input_string):
    distList = input_string.split(' ')
    numTerms = len(distList)
    if numTerms==1:
        distance = 1609.34*float(distList[0])
    if numTerms==2:
        unit = distList[1].lower()
        if unit=='miles' or unit=='mile':
            distance = 1609.34*float(distList[0])
        elif unit=='k' or unit=='km' or unit=='kms':
            distance = 1000.0*float(distList[0])
        elif unit=='m':
            if (distList[0])<100:
                # the user probably meant miles
                distance = 1609.34*float(distList[0])
            else:
                # the user meant meters
                distance = float(distList[0])
        elif unit=='meter' or unit=='meters' or unit=='metres':
            distance = float(distList[0])
        else:
            # assume miles
            distance = 1609.34*float(distList[0])
    return distance