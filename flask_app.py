from flask import Flask, render_template, redirect, url_for, request, make_response
import MySQLdb as mdb
import numpy as np
import json
import jinja2
from haversine import haversine
import gpxpy
import gpxpy.gpx

# User defined functions
from forms import LoginForm, ResultsForm
from helpers import geocode, timewith, getDistanceMeters, initializeWeights
import scoring_functions

# Basic configureation settings
app = Flask(__name__)
app.config.from_object('config')
dbName = "JoergFritz$runRoutesTest"

@app.route('/', methods = ['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        address = form.address.data
        distance = getDistanceMeters(form.distance.data)
        pro,pop,nat,asc,off,cir = initializeWeights()
        lat,lng,fullAdress,data = geocode(address)
        return redirect(url_for('results',lat=lat,lng=lng,distance=distance,pro=pro,pop=pop,nat=nat,asc=asc,off=off,cir=cir))
    return render_template('login.html', title = 'Run recommender', form = form)

@app.route('/slideshow')
def slideshow():
    return render_template('slideshow.html')

@app.route('/results/<lat>_<lng>_dist:<distance>_pr:<pro>_po:<pop>_na:<nat>_as:<asc>_of:<off>_ci:<cir>', methods = ['POST', 'GET'])
def results(lat,lng,distance,pro,pop,nat,asc,off,cir):

    # ensure proper format of variables
    runDist=float(distance)
    userLat=float(lat)
    userLng=float(lng)
    weightProximity=int(pro)
    weightPopularity=int(pop)
    weightNature=int(nat)
    weightAscent=int(asc)
    weightOffroad=int(off)
    weightCircularity=int(cir)

    # Hidden from to allow passing of weights back to python
    form = ResultsForm()
    if form.validate_on_submit():
        lat = form.userLat.data
        lng = form.userLng.data
        distance = form.runDist.data
        pro = form.weightProximity.data
        pop = form.weightPopularity.data
        nat = form.weightNature.data
        asc = form.weightAscent.data
        off = form.weightOffroad.data
        cir = form.weightCircularity.data
        return redirect(url_for('results',lat=lat,lng=lng,distance=distance,pro=pro,pop=pop,nat=nat,asc=asc,off=off,cir=cir))

    timer = timewith('results page')

    # Initialize database connection
    db=mdb.connect(host="mysql.server",user="JoergFritz", \
            db=dbName,passwd="you-wish")
    cursor=db.cursor()

    # find 5 closest cities to entered address
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
        dist[i] = haversine((float(cityLat),float(cityLng)),(userLat,userLng))
    # select three closest cities from the list
    for i in range(5):
        index_min = dist.argmin()
        closestCities.append(cityNames[index_min])
        dist[index_min] = max(dist)

    # read in all candidate routes
    distLow = runDist*0.85
    distHigh = runDist*1.15

    timer.checkpoint('find closest city')

    # initialize variables
    ascent={}
    circularity={}
    nature={}
    proximity={}
    popularity={}
    offroad={}
    overlap={}
    weightOverlap=0.2

    cursor.execute("SELECT MapMyRunId, Ascent, Circularity, Nature, Popularity, Offroad, StartLat, \
    StartLng, QuarterLat, QuarterLng, HalfLat, HalfLng, ThreeQuarterLat, \
    ThreeQuarterLng FROM Tracks WHERE (City IN (%s,%s,%s)) AND (Distance BETWEEN %s AND %s)",(closestCities[0],closestCities[1],closestCities[2],distLow,distHigh))
    rowsTracks = cursor.fetchall()
    for row in rowsTracks:
        ascent[row[0]] = row[1]
        circularity[row[0]] = row[2]
        nature[row[0]] = row[3]
        popularity[row[0]] = row[4]
        offroad[row[0]] = row[5]
        startLat = float(row[6])
        startLng = float(row[7])
        quarterLat = float(row[8])
        quarterLng = float(row[9])
        halfLat = float(row[10])
        halfLng = float(row[11])
        threeQuarterLat = float(row[12])
        threeQuarterLng = float(row[13])
        distStart = haversine((userLat,userLng),(startLat,startLng))
        distQuarter = haversine((userLat,userLng),(quarterLat,quarterLng))
        distHalf = haversine((userLat,userLng),(halfLat,halfLng))
        distThreeQuarter = haversine((userLat,userLng),(threeQuarterLat,threeQuarterLng))
        dists = [distStart,distQuarter,distHalf,distThreeQuarter]
        proximity[row[0]]=1000*min(dists)
        #print proximity[row[0]]
        overlap[row[0]]=0.0

    timer.checkpoint('select tracks')

    # compute scoring functions
    ascent_z = scoring_functions.zscore(ascent)
    circularity_z = scoring_functions.zscore(circularity)
    nature_z = scoring_functions.zscore(nature)
    proximity_z = scoring_functions.zscoreDist(proximity)
    popularity_z = scoring_functions.zscore(popularity)
    offroad_z = scoring_functions.zscore(offroad)
    overlap_z = scoring_functions.zscoreDist(overlap)

    route_scores = scoring_functions.routescore(ascent_z,circularity_z,nature_z,
        proximity_z,popularity_z,offroad_z,overlap_z,weightAscent,weightCircularity,
        weightNature,weightProximity,weightPopularity,weightOffroad,weightOverlap*weightProximity)

    timer.checkpoint('compute scoring functions')

    # select best route
    idBest = route_scores[0][0]
    cursor.execute("SELECT MapMyRunId, Lat, Lng FROM Points WHERE MapMyRunId = %s", (route_scores[0][0]))
    query_results=cursor.fetchall()
    path1=[]
    for result in query_results:
            path1.append(dict(id=result[0],lat=result[1],lng=result[2]))

    # resort other routes to minimize overlap
    cursor.execute("SELECT MapMyRunId, StartLat, StartLng, QuarterLat, QuarterLng, \
        HalfLat,HalfLng, ThreeQuarterLat, ThreeQuarterLng FROM Tracks WHERE MapMyRunId = %s", (route_scores[0][0]))
    query_results=cursor.fetchall()
    startLatBest = float(query_results[0][1])
    startLngBest = float(query_results[0][2])
    quarterLatBest = float(query_results[0][3])
    quarterLngBest = float(query_results[0][4])
    halfLatBest = float(query_results[0][5])
    halfLngBest = float(query_results[0][6])
    threeQuarterLatBest = float(query_results[0][7])
    threeQuarterLngBest = float(query_results[0][8])
    for row in rowsTracks:
        startLat = float(row[6])
        startLng = float(row[7])
        quarterLat = float(row[8])
        quarterLng = float(row[9])
        halfLat = float(row[10])
        halfLng = float(row[11])
        threeQuarterLat = float(row[12])
        threeQuarterLng = float(row[13])
        distStart = haversine((startLatBest,startLngBest),(startLat,startLng))
        distQuarter = haversine((quarterLatBest,quarterLngBest),(quarterLat,quarterLng))
        distHalf = haversine((halfLatBest,halfLngBest),(halfLat,halfLng))
        distThreeQuarter = haversine((threeQuarterLatBest,threeQuarterLngBest),(threeQuarterLat,threeQuarterLng))
        dists = [distStart,distQuarter,distHalf,distThreeQuarter]
        if sum(dists)==0:
            overlap[row[0]]=0
        else:
            overlap[row[0]]=1.0/sum(dists)

    overlap_z = scoring_functions.zscoreDist(overlap)
    route_scores = scoring_functions.routescore(ascent_z,circularity_z,nature_z,
        proximity_z,popularity_z,offroad_z,overlap_z,weightAscent,weightCircularity,
        weightNature,weightProximity,weightPopularity,weightOffroad,weightOverlap*weightProximity)

    # select 2nd best route
    idSecond = route_scores[1][0]
    cursor.execute("SELECT MapMyRunId, Lat, Lng FROM Points WHERE MapMyRunId = %s", (route_scores[1][0]))
    query_results=cursor.fetchall()
    path2=[]
    for result in query_results:
            path2.append(dict(id=result[0],lat=result[1],lng=result[2]))

    # resort other routes to minimize overlap with first and 2nd route
    cursor.execute("SELECT MapMyRunId, StartLat, StartLng, QuarterLat, QuarterLng, \
        HalfLat,HalfLng, ThreeQuarterLat, ThreeQuarterLng FROM Tracks WHERE MapMyRunId = %s", (route_scores[1][0]))
    query_results=cursor.fetchall()
    startLatBest = float(query_results[0][1])
    startLngBest = float(query_results[0][2])
    quarterLatBest = float(query_results[0][3])
    quarterLngBest = float(query_results[0][4])
    halfLatBest = float(query_results[0][5])
    halfLngBest = float(query_results[0][6])
    threeQuarterLatBest = float(query_results[0][7])
    threeQuarterLngBest = float(query_results[0][8])
    for row in rowsTracks:
        startLat = float(row[6])
        startLng = float(row[7])
        quarterLat = float(row[8])
        quarterLng = float(row[9])
        halfLat = float(row[10])
        halfLng = float(row[11])
        threeQuarterLat = float(row[12])
        threeQuarterLng = float(row[13])
        distStart = haversine((startLatBest,startLngBest),(startLat,startLng))
        distQuarter = haversine((quarterLatBest,quarterLngBest),(quarterLat,quarterLng))
        distHalf = haversine((halfLatBest,halfLngBest),(halfLat,halfLng))
        distThreeQuarter = haversine((threeQuarterLatBest,threeQuarterLngBest),(threeQuarterLat,threeQuarterLng))
        dists = [distStart,distQuarter,distHalf,distThreeQuarter]
        if sum(dists)==0:
            overlap[row[0]]=float(overlap[row[0]])+0
        else:
            overlap[row[0]]=float(overlap[row[0]])+1.0/sum(dists)

    overlap_z = scoring_functions.zscoreDist(overlap)
    route_scores = scoring_functions.routescore(ascent_z,circularity_z,nature_z,
        proximity_z,popularity_z,offroad_z,overlap_z,weightAscent,weightCircularity,
        weightNature,weightProximity,weightPopularity,weightOffroad,weightOverlap*weightProximity)

    # select 3rd best route
    idThird = route_scores[2][0]
    cursor.execute("SELECT MapMyRunId, Lat, Lng FROM Points WHERE MapMyRunId = %s", (route_scores[2][0]))
    query_results=cursor.fetchall()
    path3=[]
    for result in query_results:
            path3.append(dict(id=result[0],lat=result[1],lng=result[2]))


    timer.checkpoint('select best routes')

    # get info for n best routes
    routes_data = []
    bestRoutes=[idBest,idSecond,idThird]
    for i in range(3):
        cursor.execute("SELECT MapMyRunId, Distance, Ascent, Circularity, Nature, Popularity, Offroad FROM Tracks WHERE MapMyRunId = %s ;", (bestRoutes[i]))
        #print route_scores[i][0]
        query_results=cursor.fetchall()
        outDist=int(round(float(query_results[0][1]),0))
        outAscent=round(float(query_results[0][2]),2)
        outCircularity=round(float(query_results[0][3]),2)
        outNature=round(float(query_results[0][4]),2)
        outPopularity=round(float(query_results[0][5]),2)
        outOffroad=round(float(query_results[0][6]),2)
        routes_data.append(
            {'id':query_results[0][0],'distance':outDist,'ascent':outAscent,
            'circularity': outCircularity, 'nature': outNature,
            'popularity': outPopularity, 'offroad': outOffroad}
        )

    timer.checkpoint('get info for best routes')

    return render_template("results.html",
        title = 'Results',
        path1=path1,
        path2=path2,
        path3=path3,
        weightProximity=weightProximity,
        weightPopularity=weightPopularity,
        weightNature=weightNature,
        weightAscent=weightAscent,
        weightOffroad=weightOffroad,
        weightCircularity=weightCircularity,
        form=form,
        userLat=userLat,
        userLng=userLng,
        runDist=runDist,
        closestCity=closestCities[0],
        secondCity=closestCities[1],
        thirdCity=closestCities[2],
        routes_data = routes_data,
        jsonstr = json.dumps(routes_data)
        )

# This route will allow download of routes as gpx files
@app.route('/download/<downId>', methods = ['POST', 'GET'])
def download(downId):

    # connect to database
    dbDown=mdb.connect(host="mysql.server",user="JoergFritz", \
            db=dbName,passwd="you-wish")
    curDown=dbDown.cursor()

    curDown.execute("SELECT MapMyRunId, Lat, Lng FROM Points WHERE MapMyRunId = %s", (downId))
    query_results=curDown.fetchall()
    path=[]
    for result in query_results:
        path.append(dict(id=result[0],lat=result[1],lng=result[2]))

    # setup gpx file
    gpx = gpxpy.gpx.GPX()

    # create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = 'test'
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # write route points to gpx file
    points_count = len(path)
    points_range = range(points_count)
    for point_num in points_range:
        point = path[point_num]
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(point['lat'], point['lng']))

    # gpx is essentially xml format, so form proper response
    response = make_response(gpx.to_xml())
    response.headers["Content-Disposition"] = "attachment; filename=route.gpx"
    return response
