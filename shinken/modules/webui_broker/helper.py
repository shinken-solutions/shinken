#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import time
try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error : you need the json or simplejson module"
        raise



class Helper(object):
    def __init__(self):
        pass

    def gogo(self):
        return 'HELLO'


    def act_inactive(self, b):
        if b:
            return 'Active'
        else:
            return 'Inactive'

    def yes_no(self, b):
        if b:
            return 'Yes'
        else:
            return 'No'

    def print_float(self, f):
        return '%.2f' % f

    def ena_disa(self, b):
        if b:
            return 'Enabled'
        else:
            return 'Disabled'

    # For a unix time return something like
    # Tue Aug 16 13:56:08 2011
    def print_date(self, t):
        if t == 0 or t == None:
            return 'N/A'
        return time.asctime(time.localtime(t))


    # For a time, print something like
    # 10m 37s  (just duration = True)
    # N/A if got bogus number (like 1970 or None)
    # 1h 30m 22s ago (if t < now)
    # Now (if t == now)
    # in 1h 30m 22s
    # Or in 1h 30m (no sec, if we ask only_x_elements=2, 0 means all)
    def print_duration(self, t, just_duration=False, x_elts=0):
        if t == 0 or t == None:
            return 'N/A'
        print "T", t
        # Get the difference between now and the time of the user
        seconds = int(time.time()) - int(t)
        
        # If it's now, say it :)
        if seconds == 0:
            return 'Now'

        in_future = False

        # Remember if it's in the future or not
        if seconds < 0:
            in_future = True
        
        # Now manage all case like in the past
        seconds = abs(seconds)
        print "In future?", in_future

        print "sec", seconds
        seconds = long(round(seconds))
        print "Sec2", seconds
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)
        months, weeks = divmod(weeks, 4)
        years, months = divmod(months, 12)
 
        minutes = long(minutes)
        hours = long(hours)
        days = long(days)
        weeks = long(weeks)
        months = long(months)
        years = long(years)
 
        duration = []
        if years > 0:
            duration.append('%dy' % years)
        else:
            if months > 0:
                duration.append('%dM' % months)
            if weeks > 0:
                duration.append('%dw' % weeks)
            if days > 0:
                duration.append('%dd' % days)
            if hours > 0:
                duration.append('%dh' % hours)
            if minutes > 0:
                duration.append('%dm' % minutes)
            if seconds > 0:
                duration.append('%ds' % seconds)

        print "Duration", duration
        # Now filter the number of printed elements if ask
        if x_elts >= 1:
            duration = duration[:x_elts]

        # Maybe the user just want the duration
        if just_duration:
            return ' '.join(duration)

        # Now manage the future or not print
        if in_future:
            return 'in '+' '.join(duration)
        else: # past :)
            return ' '.join(duration) + ' ago'


    # Need to create a X level higer and lower to teh element
    def create_json_dep_graph(self, elt, levels=2):
        t0 = time.time()
        # First we need ALL elements
        all_elts = self.get_all_linked_elts(elt, levels=levels)
        print "We got all our elements"
        dicts = []
        for i in all_elts:
            print "Elt", i.get_dbg_name()
            d = self.get_dep_graph_struct(i)
            dicts.append(d)
        j = json.dumps(dicts)
        print "Create json", j
        print "create_json_dep_graph::Json creation time", time.time() - t0
        return j

    # Return something like:
    #{
    #                  "id": "localhost",
    #                  "name": "localhost",
    #                  "data": {"$color":"red", "$dim": 5*2, "some other key": "some other value"},
    #                  "adjacencies": [{
    #                          "nodeTo": "main router",
    #                          "data": {
    #                              "$type":"arrow",
    #                              "$color":"gray",
    #                              "weight": 3,
    #                              "$direction": ["localhost", "main router"],
    #                          }
    #                      }
    #                      ]
    #              }
    # But as a python dict
    def get_dep_graph_struct(self, elt, levels=2):
        t = elt.__class__.my_type
        d = {'id' : elt.get_dbg_name(), 'name' : elt.get_dbg_name(),
             'data' : {'$dim': elt.business_impact*2},
             'adjacencies' : []
             }
        # Service got a 'star' type :)
        if t == 'service':
            d['data']["$type"] = "star"
            d['data']["$color"] = {0 : 'green', 1 : 'orange', 2 : 'red', 3 : 'gray'}.get(elt.state_id, 'red')
        else: #host
            d['data']["$color"] = {0 : 'green', 1 : 'red', 2 : 'orange', 3 : 'gray'}.get(elt.state_id, 'red')

        # Now put in adj our parents
        for p in elt.parent_dependencies:
            pd = {'nodeTo' : p.get_dbg_name(),
                  'data' : {"$type":"arrow", "$direction": [elt.get_dbg_name(), p.get_dbg_name()]}}
            # Naive way of looking at impact
            if elt.state_id != 0 and p.state_id != 0:
                pd['data']["$color"] = 'red'
            d['adjacencies'].append(pd)

        # The sons case is now useful, it will be done by our sons
        # that will link us

        return d
        

    def get_all_linked_elts(self, elt, levels=2):
        if levels == 0 :
            return set()

        my = set()
        for i in elt.child_dependencies:
            my.add(i)
            child_elts = self.get_all_linked_elts(i, levels=levels - 1)
            for c in child_elts:
                my.add(c)
        for i in elt.parent_dependencies:
            my.add(i)
            par_elts = self.get_all_linked_elts(i, levels=levels - 1)
            for c in par_elts:
                my.add(c)
            
        print "get_all_linked_elts::Give elements", my
        return my



    def get_button(self, text, img=None, id=None, cls=None):
        s = '<div class="buttons">\n'
        if cls and not id:
            s += '<button class="%s">\n' % cls
        elif id and not cls:
            s += '<button id="%s">\n' % id
        elif id and cls:
            s += '<button class="%s" id="%s">\n' % (cls, id)
        else:
            s += '<button>\n'
        if img:
            s += '<img src="%s" alt=""/>\n' % img
        s += "%s" % text
        s+= ''' </button>
            </div>\n'''
        return s


    
helper = Helper()
