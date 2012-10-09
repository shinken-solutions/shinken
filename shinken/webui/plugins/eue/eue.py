#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Davif GUENAULT, david.guenault@gmail.com
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import time
import datetime
import json
import os
import mimetypes
import math

try:
    from shinken.webui.bottle import redirect
    from shinken.webui.bottle import static_file
    from shinken.webui.bottle import response
    from shinken.webui.bottle import get, post, request    
    from shinken.log import logger
except ImportError:
    print "Outside of bottle"

# Mongodb lib
try:
    import pymongo
    from pymongo.connection import Connection
    import gridfs
except ImportError:
    Connection = None


### Will be populated by the UI with it's own value
app = None
### TODO make this configurable START
media_path = '/usr/local/shinken/var/medias'
mongo_host = "localhost"
mongo_port = 27017
### TODO make this configurable END


def checkauth():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    else:
        return user

def getdb(dbname):
    con = None
    db = None

    try:
        con = Connection(mongo_host,mongo_port)
    except:
        return (  
            "Error : Unable to create mongo connection %s:%s" % (mongo_host,mongo_port),
            None
        )

    try:
        db = con[dbname]
    except:
        return (  
            "Error : Unable to connect to mongo database %s" % dbname,
            None
        )

    return (  
        "Connected to mongo database %s" % dbname,
        db
    )


def sparkline_data(eueid):
    message,db = getdb('shinken')
    if not db:
        return {
            "durations":None,
            "states":None,
            "message":message
        }


    parts = eueid.split(".")
    parts.pop(0)
    regex = "\d\.%s" % ("\.".join(parts))
    features = db.eue.find({'key':{'$regex' : regex }},sort=[("start_time",-1)],limit=50)

    durations = []
    states = []

    for feature in features:
        gduration = 0.0
        gstate = 1
        for scenario,scenario_data in feature["scenarios"].items():
            gduration+=float(scenario_data["duration"])
            if int(scenario_data["status"]) != 0:
                gstate = -1
        durations.append(str(gduration))
        states.append(str(gstate))

    durations.reverse()
    states.reverse()

    return {
        "durations":",".join(durations),
        "states":",".join(states),
        "message":""
    }


def feature_history(eueid):
    user = checkauth()    
    message,db = getdb('shinken')
    message,db2 = getdb('shinken')

    application = ""
    feature = ""
    platform = []
    history = []
    message = ""

    if not db:
        return {
            "message":message,
            "application":"",
            "feature":"",
            "platform":"",
            "filters":None,
            "history":[],
            "lastts" : None,
            "itempsperpage" : None
        }

    parts = eueid.split(".")
    parts.pop(0)
    id =  ".".join(parts)

    # base search parameters
    filters = {
        'key': { '$regex': id }
    }

    if app.request.GET.get('optionsStates', "both") == "failed":
        filters["state"] = 2
    elif app.request.GET.get('optionsStates', "both") == "succeed":
        filters["state"] = 0

    daterange = app.request.GET.get('daterangevalue',"4h")
    if daterange == "4h":
        daterangets = 4*60*60*1000
    elif daterange == "1h":
        daterangets = 1*60*60*1000
    elif daterange == "1d":
        daterangets = 24*60*60*1000
    elif daterange == "1w":
        daterangets = 7*24*60*60*1000
    else:
        daterangets = None

    # global application feature for this specific platform
    capplication = db2.eue.find({"key":eueid})[0]

    application = capplication["application"]
    feature_name = capplication["feature"]
    description = capplication["description"]
    platform = capplication["platform"]

    # history
    history=[]
    morris = []

    # for pagination
    itempsperpage = app.request.GET.get('itempsperpage', 20)
    
    # sort = app.request.GET.get("sort", "desc")
    # if sort == "desc":
    #     sortdirection = pymongo.DESCENDING
    # else:
    #     sortdirection = pymongo.ASCENDING

    lastts = app.request.GET.get('lastts', None)
    direction = app.request.GET.get('direction', "next")
    # if app.request.GET.get('direction', None) == "prev":
    #     diroperator = "$gt"
    # else:
    #     diroperator = "$lt"

    # if lastts:
    #     if sortdirection == pymongo.DESCENDING:
    #         filters["start_time"] = {diroperator:int(lastts)}
    #     elif sortdirection == pymongo.ASCENDING:
    #         filters["start_time"] = {diroperator:int(lastts)}

    if direction == "next":
        result = db.eue.find(filters).sort("start_time",-1).limit(itempsperpage)
    else:
        result = db.eue.find(filters).sort("start_time",1).limit(itempsperpage).sort("start_time",-1)

    date = None

    for feature in result:
        date = feature["start_time"]
        failed = 0
        succeed = 0
        duration = 0
        state = 0
        total = 0
        for scenario,scenario_data in feature["scenarios"].items():
            duration += scenario_data["duration"]
            if scenario_data["status"] == 0:
                succeed += 1
            else:
                state = 2                
                failed += 1

        total = succeed + failed

        morris.append({"period":int(date)*1000,"duration":"%0.2f" % float(duration)})

        data = {
            "timestamp" : int(date),
            "date" : datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M:%S'),
            "key": feature["key"],
            "duration" : duration,
            "state" : state,
            "succeed" : succeed,
            "failed" : failed,
            "total" : total
        }

        history.append(data)

    lastts = date

    return {
        "application":application,
        "feature":feature_name,
        "description":description,
        "platform":platform,
        "history":history,
        "message":"",
        "filters" : filters,
        "lastts" : int(lastts),
        "itempsperpage":itempsperpage,
        "eueid":eueid,
        "morris" : json.dumps(morris,indent=4)
    }



def create_media(media):
    if not os.path.exists("%s/%s" % (media_path,media)):

        message,db = getdb('euemedia')
        if not db:
            return False
        fs = gridfs.GridFS(db)

        data = fs.get_last_version(media).read()

        f = open("%s/%s" %(media_path,media), "wb")
        f.write(data)
        f.close()

    return True

def eue_media(media):

    user = checkauth()    

    header = dict()

    parts = media.split(".")
    ext = parts[len(parts)-1]

    if ext == ".ogg":
        mt = "application/ogg"
    elif ext == ".png":
        mt = "image/png"
    else:
        mt = "binary/octet-stream"

    response.set_header('Content-Type', mt)

    message,db = getdb('euemedia')
    if not db:
        return False

    fs = gridfs.GridFS(db)

    fh = fs.get_last_version(media)

    response.set_header('Content-Length', fh.length)

    data = fh.read()

    return data



def featuresbyapplication(application_code):
    message,db = getdb('shinken')
    if not db:
        return {
            "features":None,
            "message":message
        }


    result = db.eue.find({"application_code":application_code}).distinct("feature")

    return {
        "features" : result,
        "message" : ""
    }

def reporting(eueid=""):

    user = checkauth()

    message,db = getdb('shinken')
    if not db:
        return {
            "message":message,
            'app': app,
            'eue_data': None,
            'records': [],
            'durations' : None,
            'states' : None
        }


    eue_data = db.eue.find_one({'key': eueid})

    if not eue_data:
        eue_data = {}
        message = "Error : No matching feature test result available"

    records = ""
    # records = get_history(eueid)

    data = sparkline_data(eueid)


    return {
        'app': app,
        'eue_data': eue_data,
        'records': records,
        'message' : "",
        'durations' : data["durations"],
        'states' : data["states"]
    }


#### WIDGET ######
def eue_widget():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")

    wid = app.request.GET.get('wid', 'widget_system_' + str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    got_childs = (app.request.GET.get('got_childs', 'False') == 'True')
    key = app.request.GET.get('key', 1)

    options = {}

    problems = {}

    message,db = getdb('shinken')
    if not db:
        return {
            'app': app, 'user': user, 'wid': wid,
            'collapsed': collapsed, 'options': options,
            'base_url': '/widget/eue', 'title': 'Eue problems',
            'problems':problems        
        }


    return {'app': app, 'user': user, 'wid': wid,
            'collapsed': collapsed, 'options': options,
            'base_url': '/widget/eue', 'title': 'Eue problems',
            'problems':problems
    }


widget_desc = '''<h4>Eue problems</h4>'''

pages = {
    reporting: {'routes': ['/eue_report/:eueid'], 'view': 'eue_report', 'static': True},
    feature_history: {'routes': ['/eue_feature_history/:eueid'], 'view': 'eue_feature_history','static': True},
    eue_media: {'routes': ['/eue_media/:media'], 'view': None,'static': True},
    eue_widget: {'routes': ['/widget/eue'], 'view': 'eue_widget', 'static': True, 'widget': ['dashboard'], 'widget_desc': widget_desc, 'widget_name': 'eue', 'widget_picture': '/static/eue/img/widget_eue.png'}
    # eue_application: {'routes': ['/eue_application/:application'], 'view': 'eue_application','static': True}
}

