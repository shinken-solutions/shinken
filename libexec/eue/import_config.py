#!/usr/bin/pyhon
from pymongo import MongoClient
import ConfigParser, os, io, sys, getopt

# display cli usage
def usage():
    print "usage : import_config.py {-i|--inifile=}/path/to/inifile  {-d|--database=}localhost:port/db/collection"
    sys.exit(2)

# arguments
try:                                  
    opts, args = getopt.getopt(sys.argv[1:], "i:d:", ["inifile=","database="]) 
except getopt.GetoptError:           
    usage()                          
    sys.exit(2)           

host=""
database=""
collection=""

for opt,arg in opts:
    if opt in ("-i","--inifile"):
        inifile = arg
    elif opt in ("-d","--database"):
        database = arg
    else:
        print "Unknown argument\n"
        usage()

if database == "" or inifile == "":
    print "database and inifile are required! \n"
    usage()
    sys.exit(2)

# make a mongo connection
host,database,collection = database.split("/")

if not ":" in "host":
    port = 27017
else:
    host,port = port.split(":")
try:
    con = MongoClient(host,port)
    db = con[database]
    col = db[collection]
except:
    print "Unexpected error:", sys.exc_info()[0]
    print "host : %s" % (host)
    print "port : %s" % (port)
    print "database : %s" % (database)
    print "collection : %s" % (collection)
    sys.exit(2)


if not os.path.isfile(inifile):
    print "inifile does not exist \n"
    sys.exit(2)

# load config file
try:

    data = {
        "media" : {
            "path" : "/usr/local/shinlen/var/medias",
            "capturevideo" : 0,
            "capture" : 0,
            "capture_level" : "scenario",
            "videocodec" : "libtheora -vsync 0 -r 24 -b 2496k -bt 1024k",
            "videoextension" : "ogg"
        "security" : {
            "hidepatterns" : "le mot de passe (\"[^\"]*\");the password (\"[^\"]*\")",
            "patternseparator" : ";",
        },
        "application" : {
            "name" : "Application GLPI",
            "robot",
            "env" : "prod",
            "name" : "poller-eue-spain",
            "os" : "linux",
            "localization" : "spain",
        },
        "browser" : {
            "name" : "firefox",
            "path" : "/usr/local/firefox/bin/firefox",
            "browser" : "firefox",
            "profile" : "auto",
            "use_proxy" : "0",
            "proxy_host" : "",
            "proxy_port" : "",
            "proxy_autourl" : "",
        },
        "execution" : {
            "mode" : "visible",
            "resolution" : "1280x1024x24",
            "display" : "999",
        },
        "sikuli" : {
            "enabled" : "false",
            "redirect" : "/tmp/sikuli.log",
            "java" : "/usr/bin/java",
            "path" : "/opt/Sikuli-IDE",
            "project" : "cacoo.sikuli",
            "host" : "localhost",
            "port" : "1339",
            "timeout" : "60",
        },
        "shinken" : {
            "base_uri" : "http://192.168.122.206:7767/eue_report",
        },
        "mongo" : {
            "host" : "localhost",
            "port" : "27017",
            "db" : "shinken",
            "collection" : "eue",
            "dbgrid" : "euemedia",
            "user" : "",
            "password" : "",
            "dateformat" : "timestamp",
        }
    }

    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.read(inifile)
except:
    print "Unexpected error:", sys.exc_info()[0]
    print "host : %s" % (host)
    print "port : %s" % (port)
    print "database : %s" % (database)
    print "collection : %s" % (collection)
    sys.exit(2)

