import MySQLdb
import time

conn = MySQLdb.connect (host = "localhost", user = "root", passwd = "root",db = "merlin")
cursor = conn.cursor ()

t = time.time()
for i in xrange(1, 10000):
    cursor.execute ("UPDATE host SET max_check_attempts='%d' WHERE host_name='localhost'" % i)
    conn.commit ()
t2= time.time()

print "Diff =", t2 - t

cursor.close ()
conn.commit ()
conn.close ()
