from flask import Flask, render_template, flash, redirect, url_for, request, jsonify, make_response
import MySQLdb as mdb
import sys
import numpy as np
import json
import scipy.stats
import jinja2
from haversine import haversine
import gpxpy
import gpxpy.gpx

# User defined functions
from forms import LoginForm, ResultsForm
from helpers import geocode, timewith
import db_functions
import scoring_functions

# basic configureation settings
app = Flask(__name__)
app.config.from_object('config')
dbName = "JoergFritz$runRoutesTest"

@app.route('/', methods = ['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        address = form.address.data
        distance = float(form.distance.data)
        # change to SI units
        distance = 1609.34*distance
        #weights = ["0","1","2","3","4","5"]
        #weights = {'pr': 1, 'po': 2, 'na': 3, 'as': 4, 'of': 5, 'ci': 6}
        pro = 8
        pop = 5
        nat = 2
        asc = 5
        off = 2
        cir = 8
        print address, distance
        lat,lng,full_add,data = geocode(address)
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

    form = ResultsForm()
    if form.validate_on_submit():
        lat = form.userLat.data
        #lat = '37.4038194'
        lng = form.userLng.data
        #lng = '-122.081267'
        distance = form.runDist.data
        pro = form.weightProximity.data
        pop = form.weightPopularity.data
        nat = form.weightNature.data
        asc = form.weightAscent.data
        off = form.weightOffroad.data
        cir = form.weightCircularity.data
        #weights = ["0","1","2","3","4","5"]
        #weights = {'pr': 1, 'po': 2, 'na': 3, 'as': 4, 'of': 5, 'ci': 6}
        return redirect(url_for('results',lat=lat,lng=lng,distance=distance,pro=pro,pop=pop,nat=nat,asc=asc,off=off,cir=cir))

    timer = timewith('results page')

    # Get data from database
    db=mdb.connect(host="mysql.server",user="JoergFritz", \
            db=dbName,passwd="you-wish")
    cursor=db.cursor()

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
    distLow = runDist*0.85
    distHigh = runDist*1.15

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

    route_scores = scoring_functions.routescore(ascent_z,circularity_z,nature_z,proximity_z,weightAscent,weightCircularity,weightNature,weightProximity)

    timer.checkpoint('compute scoring functions')

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

# print bestRoutePoints


#    crime = db_functions.get_crime(cursor)
#    walk = db_functions.get_walk(cursor)
#    school = db_functions.get_school(cursor)
#    sales = db_functions.get_sales(cursor)
#    rent = db_functions.get_rent(cursor)
#    city = db_functions.get_cities(cursor)
    # Calculate z_scores
#    crime_z = scoring_functions.zscore(crime)
#    walk_z = scoring_functions.zscore(walk)
#    school_z = scoring_functions.zscore(school)
#    sales_z = scoring_functions.zscore(sales)
#    rent_z = scoring_functions.zscore(rent)
#    zip_scores = scoring_functions.score_zips(crime_z,walk_z,school_z,sales_z,crime_z,crime_z)
    # Calculate percentiles
#    score_pcntl = scoring_functions.percentile_score(zip_scores)
#    school_pcntl = scoring_functions.percentile_high(school)
#    walk_pcntl = scoring_functions.percentile_high(walk)
#    crime_pcntl = scoring_functions.percentile_low(crime)
#    safety = scoring_functions.calc_safety(crime)
#    bestRoutesId=[478558214,22223,22224]
    #lat_test = db_functions.get_lat(cursor)
    #lng_test = db_functions.get_lng(cursor)
#    cursor.execute("SELECT Lat,Lng FROM Points WHERE MapMyRunId=478558214 ORDER BY Id")
#    rows = cursor.fetchall()
#    lat_test = np.zeros(cursor.rowcount)
#    lng_test = np.zeros(cursor.rowcount)
#    trackPoints=[]
#    n=0
#    for row in rows:
#        lat_test[n]=row[0]
#        lng_test[n]=row[1]
#        #trackPoints.append(dict('lat'=row[0], 'lng'=row[1]))
#        n=n+1
    # Calculate job coordinates
    zip1_lnglat = [37.42565, 122.13535]
    zip2_lnglat = [37.42365, 122.13735]
    latTest=[37.42565,37.42865]
    lngTest=[-122.13535,-122.13535]
    # - Select Three random paths
    #cursor.execute("SELECT MapMyRunId FROM Points ORDER BY RAND() LIMIT 3;")
    #cursor.execute("SELECT MapMyRunId FROM Points LIMIT 3;")
    #query_results=cursor.fetchall()
    bestFitId=np.zeros(3)
    n=0
    for result in query_results:
        bestFitId[n]=result[0]
        n=n+1

#    bestFitId[0]=362895605
#    bestFitId[1]=53858614
#    bestFitId[2]=46670374

    path1String=["SELECT MapMyRunId,Lat,Lng,Id FROM Points WHERE MapMyRunId=",str(bestFitId[0])," ORDER BY Id;"]

#    idNow=str(bestFitId[0])
#    # - Select Three best Paths
#    #cursor.execute("SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=176365802.0 ORDER BY Id;")
#    cursor.execute("SELECT MapMyRunId,Lat,lng, Id FROM Points WHERE MapMyRunId = %s ORDER BY Id", (idNow))
#    #cursor.execute(''.join(path1String))
#    query_results=cursor.fetchall()
#    path1=[]
#    for result in query_results:
#        path1.append(dict(id=result[0],lat=result[1],lng=result[2]))

#    idNow=str(bestFitId[1])
#    # - Select Three best Paths
#    #cursor.execute("SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=176365802.0 ORDER BY Id;")
#    cursor.execute("SELECT MapMyRunId,Lat,lng,Id FROM Points WHERE MapMyRunId = %s ORDER BY Id", (idNow))
#    #cursor.execute(''.join(path1String))
#    query_results=cursor.fetchall()
#    path2=[]
#    for result in query_results:
#        path2.append(dict(id=result[0],lat=result[1],lng=result[2]))

#    idNow=str(bestFitId[2])
#    # - Select Three best Paths
#    #cursor.execute("SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=176365802.0 ORDER BY Id;")
#    cursor.execute("SELECT MapMyRunId,Lat,lng,Id FROM Points WHERE MapMyRunId = %s ORDER BY Id", (idNow))
#    #cursor.execute(''.join(path1String))
#    query_results=cursor.fetchall()
#    path3=[]
#    for result in query_results:
#        path3.append(dict(id=result[0],lat=result[1],lng=result[2]))

    # make fake variables
#    path1=[]
#    path2=[]
#    path3=[]
#    idNow=[]

    # Make json object
#    zip_codes = []
    #for i in range(0,222):
    for i in range(0,3):
        #zip = zip_scores[i][0]
        #zip = bestRoutesId(i)
        commute1_mins = int(20/60)
        commute2_mins = int(20/60)
        #zip_codes.append(
        #    {'zip':result[0]}
        #)
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
        idNow=[],
        userLat=userLat,
        userLng=userLng,
        runDist=runDist,
        zip_codes = zip_codes,
        jsonstr = json.dumps(zip_codes),
        #tracksPoints=trackPoints;
        zip1_lng = zip1_lnglat[0],
        zip1_lat = zip1_lnglat[1],
        zip2_lng = zip2_lnglat[0],
        zip2_lat = zip2_lnglat[1])

# This route will prompt a file download with the csv lines
@app.route('/download')
def download():
    downId = '37426726'

    # Connect to database
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
    # Create first track in our GPX:
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


    csv = """"REVIEW_DATE","AUTHOR","ISBN","DISCOUNTED_PRICE"
        "1985/01/21","Douglas Adams",0345391802,5.95
        "1990/01/12","Douglas Hofstadter",0465026567,9.95
        "1998/07/15","Timothy ""The Parser"" Campbell",0968411304,18.99
        "1999/12/03","Richard Friedman",0060630353,5.95
        "2004/10/04","Randel Helms",0879755725,4.50"""
    # We need to modify the response, so the first thing we
    # need to do is create a response out of the CSV string
    response = make_response(gpx.to_xml())
    #response = gpx.to_xml()
    # This is the key: Set the right header for the response
    # to be downloaded, instead of just printed on the browser
    response.headers["Content-Disposition"] = "attachment; filename=route.gpx"
    return response
