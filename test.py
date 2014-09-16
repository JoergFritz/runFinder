import MySQLdb as mdb
#from geopy.geocoders import Nominatim
from helpers import geocode

db=mdb.connect(host="mysql.server",user="JoergFritz", \
            db="JoergFritz$runRoutesTest",passwd="you-wish")
cursor=db.cursor()

address='260 Sheridan Ave, Palo Alto'

#geolocator = Nominatim()
#location = geolocator.geocode("175 5th Avenue NYC")
#g = geocoders.Google('AIzaSyBb2jxg7xdMbtQdJNCMgrtrOO6hbb6niEI')
#place, (lat, lng) = g.geocode(address)
lat,lng,full_add,data = geocode(address)

print(lat, lng)

