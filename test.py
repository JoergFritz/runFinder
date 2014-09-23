import MySQLdb as mdb
#from geopy.geocoders import Nominatim
from helpers import geocode, timewith
from mapmyfitness import MapMyFitness
import numpy as np
from haversine import haversine
import db_functions
import scoring_functions

timer = timewith('results page')

db=mdb.connect(host="mysql.server",user="JoergFritz", \
            db="JoergFritz$runTracks",passwd="you-wish")
cursor=db.cursor()

# connect to apis
mmf = MapMyFitness(api_key='4h968vgnddc5r5kswxdpf7tnuat7h8sk', access_token='6cf8fc4094b30b31b49990083c3c25ad3fcfdefc')

address='260 Sheridan Ave, Palo Alto'
runDist = 4200;

#geolocator = Nominatim()
#location = geolocator.geocode("175 5th Avenue NYC")
#g = geocoders.Google('AIzaSyBb2jxg7xdMbtQdJNCMgrtrOO6hbb6niEI')
#place, (lat, lng) = g.geocode(address)
userLat,userLng,full_add,data = geocode(address)

#print(lat, lng)

# find 3 closest cities to entered address
cursor.execute("SELECT City,Lat,Lng from Cities")
rowsCities = cursor.fetchall()
dist = np.zeros(len(rowsCities))
cityNames=[]
closestCities=[]
# get distance from address to all cities
for i in range(len(rowsCities)):
    cityNames.append(rowsCities[i][0])
    cityLat = rowsCities[i][1]
    cityLng = rowsCities[i][2]
    #dist[i] = haversine((cityLat,cityLng),(lat,lng))
    dist[i] = haversine((float(cityLat),float(cityLng)),(userLat,userLng))
    #dist[i] = haversine((12.3,1.3),(12.4,1.2))
# select three closest cities from the list
for i in range(3):
    index_min = dist.argmin()
    closestCities.append(cityNames[index_min])
    #closestCities.append('Palo Alto, CA')
    dist[index_min] = max(dist)

# read in all candidate routes
distLow = runDist*0.95
distHigh = runDist*1.05

timer.checkpoint('find closest city')

# initialize variables
ascent={}
circularity={}
nature={}
proximity={}

cursor.execute("SELECT MapMyRunId, Ascent, Circularity, Nature, StartLat, \
StartLng FROM Tracks WHERE (City IN (%s,%s,%s)) AND (Distance BETWEEN %s AND %s)",(closestCities[0],closestCities[1],closestCities[2],distLow,distHigh))
rowsTracks = cursor.fetchall()
for row in rowsTracks:
    ascent[row[0]] = row[1]
    circularity[row[0]] = row[2]
    nature[row[0]] = row[3]
    proximity[row[0]]=1000*haversine((userLat,userLng),(float(row[4]),float(row[5])))
    #print proximity[row[0]]

timer.checkpoint('select tracks')

# compute scoring functions
ascent_z = scoring_functions.zscore(ascent)
circularity_z = scoring_functions.zscore(circularity)
nature_z = scoring_functions.zscore(nature)
proximity_z = scoring_functions.zscore(proximity)

route_scores = scoring_functions.routescore(ascent_z,circularity_z,nature_z,proximity_z,4,0,4,4)

timer.checkpoint('compute scoring functions')

#route = mmf.route.find(536019642)
#routes_paginator = mmf.route.search(route=348949363)
#route = mmf.route.find(route_scores[i][0])
#print(route.name)  # '4 Mile Lunch Run'

# select n best routes
bestRoutePoints={}
for i in range(3):
    cursor.execute("SELECT MapMyRunId, Lat, Lng FROM Points WHERE MapMyRunId = %s", (route_scores[i][0]))
    #print route_scores[i][0]
    query_results=cursor.fetchall()
    path=[]
    for result in query_results:
        path.append(dict(id=result[0],lat=result[1],lng=result[2]))
    #print path
    bestRoutePoints[route_scores[i][0]]=path
    if i==0:
        path1=path
    if i==1:
        path2=path
    if i==2:
        path3=path

timer.checkpoint('select best routes')

# get info for n best routes
zip_codes = []
for i in range(3):
    cursor.execute("SELECT MapMyRunId, Distance, Ascent, Circularity, Nature FROM Tracks WHERE MapMyRunId = %s ;", (route_scores[i][0]))
    #print route_scores[i][0]
    query_results=cursor.fetchall()
    zip_codes.append(
        {'zip':query_results[0][0],'city':query_results[0][1],'commute1_mins':query_results[0][2],
        'commute2_mins': query_results[0][3], 'nature': query_results[0][4]}
    )

timer.checkpoint('get info for best routes')

weights=[1,1,1]
print weights[0]

#for zip_code in zip_codes:
    #print zip_code['zip']
#print bestRoutePoints
#print zip_codes[0]['zip']

#print testArray
