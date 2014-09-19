import MySQLdb as mdb
#from geopy.geocoders import Nominatim
from helpers import geocode
import numpy as np
from haversine import haversine
import db_functions
import scoring_functions

db=mdb.connect(host="mysql.server",user="JoergFritz", \
            db="JoergFritz$runRoutesTest",passwd="you-wish")
cur=db.cursor()

address='260 Sheridan Ave, Palo Alto'
distance = 4200;

#geolocator = Nominatim()
#location = geolocator.geocode("175 5th Avenue NYC")
#g = geocoders.Google('AIzaSyBb2jxg7xdMbtQdJNCMgrtrOO6hbb6niEI')
#place, (lat, lng) = g.geocode(address)
lat,lng,full_add,data = geocode(address)

#print(lat, lng)

# - find 3 closest tracks

cur.execute("SELECT City,Lat,Lng from Cities")
rowsCities = cur.fetchall()
dist = np.zeros(len(rowsCities))
cityNames=[]
closestCities=[]

for i in range(len(rowsCities)):
    cityNames.append(rowsCities[i][0])
    cityLat = rowsCities[i][1]
    cityLng = rowsCities[i][2]
    dist[i] = haversine((cityLat,cityLng),(lat,lng))
index_min=dist.argmin()
closestCities.append(cityNames[index_min])

#print closestCity

dist[index_min] = max(dist)
index_min=dist.argmin()
closestCities.append(cityNames[index_min])

#print closestCities

dist[index_min] = max(dist)
index_min=dist.argmin()
closestCities.append(cityNames[index_min])

distLow = distance*0.90
distHigh = distance*1.10

# initialize variables
ascent={}
circularity={}
nature={}
proximity={}

cur.execute("SELECT MapMyRunId, Ascent, Circularity, Nature, StartLat, \
    StartLng FROM Tracks WHERE (City IN (%s,%s,%s)) AND (Distance BETWEEN %s AND %s)",(closestCities[0],closestCities[1],closestCities[2],distLow,distHigh))
rowsTracks = cur.fetchall()
for row in rowsTracks:
    ascent[row[0]] = row[1]
    circularity[row[0]] = row[2]
    nature[row[0]] = row[3]
    proximity[row[0]]=1000*haversine((lat,lng),(row[4],row[5]))
    #print proximity[row[0]]

#print len(rowsTracks)

# calculate scoring functions
ascent_z = scoring_functions.zscore(ascent)
circularity_z = scoring_functions.zscore(circularity)
nature_z = scoring_functions.zscore(nature)
proximity_z = scoring_functions.zscore(proximity)

#print proximity_z

route_scores = scoring_functions.routescore(ascent_z,circularity_z,nature_z,proximity_z)

#print route_scores

bestRoutePoints={}
for i in range(3):
    cur.execute("SELECT MapMyRunId, Lat, Lng FROM Points WHERE MapMyRunId = %s", (route_scores[i][0]))
    #print route_scores[i][0]
    query_results=cur.fetchall()
    path=[]
    for result in query_results:
        path.append(dict(id=result[0],lat=result[1],lng=result[2]))
    print path
    bestRoutePoints[route_scores[i][0]]=path

print bestRoutePoints

#print testArray
