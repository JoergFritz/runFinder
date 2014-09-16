import MySQLdb as mdb
import db_functions
import numpy as np

con=mdb.connect(host="mysql.server",user="JoergFritz", \
            db="JoergFritz$runRoutesTest",passwd="you-wish")
cursor = con.cursor(mdb.cursors.DictCursor)

cursor.execute("SELECT MapMyRunId FROM Tracks ORDER BY RAND() LIMIT 3;")
query_results=cursor.fetchall()
bestFitId=np.zeros(3)
n=0
for result in query_results:
    bestFitId[n]=result['MapMyRunId']
    n=n+1

print bestFitId

path1String=["SELECT MapMyRunId,Lat,Lng FROM Points WHERE MapMyRunId=",str(bestFitId[0])," ORDER BY Id;"]

print ''.join(path1String)


