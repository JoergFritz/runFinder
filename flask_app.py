
# A very simple Flask Hello World app for you to get started with...
from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
import MySQLdb as mdb
import sys
import numpy as np
import json
import scipy.stats
import jinja2

# User defined functions
from forms import LoginForm
from helpers import geocode
import db_functions
import scoring_functions

app = Flask(__name__)
app.config.from_object('config')

@app.route('/', methods = ['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        address = form.address.data
        distance = form.distance.data
        runFeatures = [1,2,3]
        print address, distance
        lat,lng,full_add,data = geocode(address)
        return redirect(url_for('results',lat=lat,lng=lng,distance=distance,runFeatures=runFeatures))
    return render_template('login.html', title = 'Run recommender', form = form)

@app.route('/slideshow')
def slideshow():
    return render_template('slideshow.html')

@app.route('/results/<lat>_<lng>_<distance>_<runFeatures>')
def results(lat,lng,distance,runFeatures):
# Map missing zip codes
    #zip1_orig = address
    #zip2_orig = distance
    # Get data from database
    db=mdb.connect(host="mysql.server",user="JoergFritz", \
            db="JoergFritz$runRoutesTest",passwd="you-wish")
    cursor=db.cursor()
    crime = db_functions.get_crime(cursor)
    walk = db_functions.get_walk(cursor)
    school = db_functions.get_school(cursor)
    sales = db_functions.get_sales(cursor)
    rent = db_functions.get_rent(cursor)
    city = db_functions.get_cities(cursor)
    # Calculate z_scores
    crime_z = scoring_functions.zscore(crime)
    walk_z = scoring_functions.zscore(walk)
    school_z = scoring_functions.zscore(school)
    sales_z = scoring_functions.zscore(sales)
    rent_z = scoring_functions.zscore(rent)
    zip_scores = scoring_functions.score_zips(crime_z,walk_z,school_z,sales_z,crime_z,crime_z)
    # Calculate percentiles
    score_pcntl = scoring_functions.percentile_score(zip_scores)
    school_pcntl = scoring_functions.percentile_high(school)
    walk_pcntl = scoring_functions.percentile_high(walk)
    crime_pcntl = scoring_functions.percentile_low(crime)
    safety = scoring_functions.calc_safety(crime)
    bestRoutesId=[478558214,22223,22224]
    #lat_test = db_functions.get_lat(cursor)
    #lng_test = db_functions.get_lng(cursor)
    cursor.execute("SELECT Lat,Lng FROM Points WHERE MapMyRunId=478558214 ORDER BY Id")
    rows = cursor.fetchall()
    lat_test = np.zeros(cursor.rowcount)
    lng_test = np.zeros(cursor.rowcount)
    trackPoints=[]
    n=0
    for row in rows:
        lat_test[n]=row[0]
        lng_test[n]=row[1]
        #trackPoints.append(dict('lat'=row[0], 'lng'=row[1]))
        n=n+1
    # Calculate job coordinates
    zip1_lnglat = [37.42565, 122.13535]
    zip2_lnglat = [37.42365, 122.13735]
    latTest=[37.42565,37.42865]
    lngTest=[-122.13535,-122.13535]
    # - Select Three random paths
    cursor.execute("SELECT MapMyRunId FROM Tracks ORDER BY RAND() LIMIT 3;")
    query_results=cursor.fetchall()
    bestFitId=np.zeros(3)
    n=0
    for result in query_results:
        bestFitId[n]=result[0]
        n=n+1

    path1String=["SELECT MapMyRunId,Lat,Lng,Id FROM Points WHERE MapMyRunId=",str(bestFitId[0])," ORDER BY Id;"]

    idNow=str(bestFitId[0])
    # - Select Three best Paths
    #cursor.execute("SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=176365802.0 ORDER BY Id;")
    cursor.execute("SELECT MapMyRunId,Lat,lng,Id FROM Points WHERE MapMyRunId = %s ORDER BY Id", (idNow))
    #cursor.execute(''.join(path1String))
    query_results=cursor.fetchall()
    path1=[]
    for result in query_results:
        path1.append(dict(id=result[0],lat=result[1],lng=result[2]))

    idNow=str(bestFitId[1])
    # - Select Three best Paths
    #cursor.execute("SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=176365802.0 ORDER BY Id;")
    cursor.execute("SELECT MapMyRunId,Lat,lng,Id FROM Points WHERE MapMyRunId = %s ORDER BY Id", (idNow))
    #cursor.execute(''.join(path1String))
    query_results=cursor.fetchall()
    path2=[]
    for result in query_results:
        path2.append(dict(id=result[0],lat=result[1],lng=result[2]))

    idNow=str(bestFitId[2])
    # - Select Three best Paths
    #cursor.execute("SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=176365802.0 ORDER BY Id;")
    cursor.execute("SELECT MapMyRunId,Lat,lng,Id FROM Points WHERE MapMyRunId = %s ORDER BY Id", (idNow))
    #cursor.execute(''.join(path1String))
    query_results=cursor.fetchall()
    path3=[]
    for result in query_results:
        path3.append(dict(id=result[0],lat=result[1],lng=result[2]))
    # Make json object
    zip_codes = []
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
        idNow=idNow,
        zip_codes = zip_codes,
        jsonstr = json.dumps(zip_codes),
        lat_test=lat_test,
        lng_test=lng_test,
        #tracksPoints=trackPoints;
        zip1_lng = zip1_lnglat[0],
        zip1_lat = zip1_lnglat[1],
        zip2_lng = zip2_lnglat[0],
        zip2_lat = zip2_lnglat[1])
