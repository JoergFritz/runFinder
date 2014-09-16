import numpy as np

def get_crime(cursor):
	crime = {}
	cursor.execute("SELECT MapMyRunId,Distance from Tracks")
	rows = cursor.fetchall()
	for row in rows:
		crime[row[0]] = row[1]
	return crime

def get_cities(cursor):
	city = {}
	cursor.execute("SELECT MapMyRunId,Distance from Tracks")
	rows = cursor.fetchall()
	for row in rows:
		city[row[0]] = row[1]
	return city

def get_walk(cursor):
	walk = {}
	cursor.execute("SELECT MapMyRunId,Distance from Tracks")
	rows = cursor.fetchall()
	for row in rows:
		walk[row[0]] = row[1]
	return walk

def get_school(cursor):
	school = {}
	cursor.execute("SELECT MapMyRunId,Distance from Tracks")
	rows = cursor.fetchall()
	for row in rows:
		school[row[0]] = row[1]
	return school

def get_sales(cursor):
	sales = {}
	cursor.execute("SELECT MapMyRunId,Ascent from Tracks")
	rows = cursor.fetchall()
	for row in rows:
		sales[row[0]] = row[1]
	return sales

def get_rent(cursor):
	rent = {}
	cursor.execute("SELECT MapMyRunId,Distance from Tracks")
	rows = cursor.fetchall()
	for row in rows:
		rent[row[0]] = row[1]
	return rent

def get_lat(cursor):
	cursor.execute("SELECT Lat FROM Points WHERE MapMyRunId=478558214 ORDER BY Id")
	rows = cursor.fetchall()
	numRows = cursor.rowcount
	lat = np.zeros(numRows)
	n=0
	for row in rows:
		lat[n] = row['Lat']
		n=n+1
	return lat

def get_latMod(cursor):
	cursor.execute("SELECT Lat FROM Points WHERE MapMyRunId=478558214 ORDER BY Id")
	rows = cursor.fetchall()
	numRows = cursor.rowcount
	lat = {}
	n=0
	for row in rows:
		lat[n] = row['Lat']
		n=n+1
	return lat

def get_lng(cursor):
	cursor.execute("SELECT Lng FROM Points WHERE MapMyRunId=478558214 ORDER BY Id")
	rows = cursor.fetchall()
	numRows = cursor.rowcount
	lng = np.zeros(numRows)
	n=0
	for row in rows:
		lng[n] = row['Lng']
		n=n+1
	return lng