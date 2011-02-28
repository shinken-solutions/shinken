#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


#This Class is an example of an Scheduler module
#Here for the configuration phase AND running one


#This text is print at the import
print "Detected module : Memcache retention file for Scheduler"


import memcache


from shinken.basemodule import BaseModule


properties = {
    'type' : 'memcache_retention',
    'external' : False,
    'phases' : ['retention'],
    }


#called by the plugin manager to get a broker
def get_instance(modconf):
    print "Get a memcache retention scheduler module for plugin %s" % modconf.get_name()
    instance = Memcache_retention_scheduler(modconf)
    return instance



#Just print some stuff
class Memcache_retention_scheduler(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.server = mod_conf.server
        self.port = mod_conf.port

    #Called by Scheduler to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the memcache module"
        #self.return_queue = self.properties['from_queue']
        self.mc = memcache.Client(['%s:%s' % (self.server, self.port)], debug=0)


    #Ok, main function that is called in the retention creation pass
    def update_retention_objects(self, sched, log_mgr):
        print "[MemcacheRetention] asking me to update the retention objects"
        #Now the flat file method
        for h in sched.hosts:
            key = "HOST-%s" % h.host_name
            self.mc.set(key, h)

        for s in sched.services:
            key = "SERVICE-%s,%s" % (s.host.host_name, s.service_description)
            #space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            #print "Using key", key
            self.mc.set(key, s)
        log_mgr.log("Retention information updated in Memcache")



    #Should return if it succeed in the retention load or not
    def load_retention_objects(self, sched, log_mgr):
        print "[MemcacheRetention] asking me to load the retention objects"

        #Now the old flat file way :(
        log_mgr.log("[MemcacheRetention] asking me to load the retention objects")

        #We got list of loaded data from retention server
        ret_hosts = []
        ret_services = []

        #Now the flat file method
        for h in sched.hosts:
            key = "HOST-%s" % h.host_name
            val = self.mc.get(key)
            if val is not None:
                ret_hosts.append(val)

        for s in sched.services:
            key = "SERVICE-%s,%s" % (s.host.host_name, s.service_description)
            #space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            #print "Using key", key
            val = self.mc.get(key)
            if val is not None:
                ret_services.append(val)


        #Now load interesting properties in hosts/services
        #Taging retention=False prop that not be directly load
        #Items will be with theirs status, but not in checking, so
        #a new check will be launch like with a normal begining (random distributed
        #scheduling)

#        ret_hosts = all_data['hosts']
        for ret_h in ret_hosts:
            h = sched.hosts.find_by_name(ret_h.host_name)
            if h is not None:
                running_properties = h.__class__.running_properties
                for prop, entry in running_properties.items():
                    if 'retention' in entry and entry['retention']:
                        setattr(h, prop, getattr(ret_h, prop))
                        for a in h.notifications_in_progress.values():
                            a.ref = h
                            sched.add(a)
                        h.update_in_checking()

#        ret_services = all_data['services']
        for ret_s in ret_services:
            s = sched.services.find_srv_by_name_and_hostname(ret_s.host_name, ret_s.service_description)
            if s is not None:
                running_properties = s.__class__.running_properties
                for prop, entry in running_properties.items():
                    if 'retention' in entry and entry['retention']:
                        setattr(s, prop, getattr(ret_s, prop))
                        for a in s.notifications_in_progress.values():
                            a.ref = s
                            sched.add(a)
                        s.update_in_checking()

        log_mgr.log("[MemcacheRetention] OK we've load data from memcache server")

        return True
