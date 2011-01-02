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
print "Detected module : Picle retention file for Scheduler"


import cPickle
import shutil


properties = {
    'type' : 'pickle_retention_file',
    'external' : False,
    'phases' : ['retention'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a pickle retention scheduler module for plugin %s" % plugin.get_name()
    path = plugin.path
    instance = Pickle_retention_scheduler(plugin.get_name(), path)
    return instance



#Just print some stuff
class Pickle_retention_scheduler:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    #Called by Scheduler to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the Pickle file retention scheduler module"
        #self.return_queue = self.properties['from_queue']


    def get_name(self):
        return self.name


    #Ok, main function that is called in the retention creation pass
    def update_retention_objects(self, sched, log_mgr):
        print "[PickleRetention] asking me to update the retention objects"
        #Now the flat file method
        try:
            # Open a file near the path, with .tmp extension
            # so in cae or problem, we do not lost the old one
            f = open(self.path+'.tmp', 'wb')
            #Just put hosts/services becauses checks and notifications
            #are already link into
            #all_data = {'hosts' : sched.hosts, 'services' : sched.services}

            # We create a all_data dict with lsit of dict of retention useful
            # data of our hosts and services
            all_data = {'hosts' : {}, 'services' : {}}
            for h in sched.hosts:
                d = {}
                running_properties = h.__class__.running_properties
                for prop in running_properties:
                    entry = running_properties[prop]
                    if entry.retention:
                        d[prop] = getattr(h, prop)
#                        if prop == 'notifications_in_progress':
#                            v = getattr(h, prop)
#                            if v != {}:
#                                print "DUMP", getattr(h, prop)
#                                for n in v.values():
#                                    print n.__dict__
                all_data['hosts'][h.host_name] = d

            #Now same for services
            for s in sched.services:
                d = {}
                running_properties = s.__class__.running_properties
                for prop in running_properties:
                    entry = running_properties[prop]
                    if entry.retention:
                        d[prop] = getattr(s, prop)
                all_data['services'][(s.host.host_name, s.service_description)] = d

            #s = cPickle.dumps(all_data)
            #s_compress = zlib.compress(s)
            cPickle.dump(all_data, f)
            #f.write(s_compress)
            f.close()
            # Now move the .tmp fiel to the real path
            shutil.move(self.path+'.tmp', self.path)
        except IOError , exp:
            log_mgr.log("Error: retention file creation failed, %s" % str(exp))
            return
        log_mgr.log("Updating retention_file %s" % self.path)




    #Should return if it succeed in the retention load or not
    def load_retention_objects(self, sched, log_mgr):
        print "[PickleRetention] asking me to load the retention objects"

        #Now the old flat file way :(
        log_mgr.log("[PickleRetention]Reading from retention_file %s" % self.path)
        try:
            f = open(self.path, 'rb')
            all_data = cPickle.load(f)
            f.close()
        except EOFError , exp:
            print exp
            return False
        except ValueError , exp:
            print exp
            return False
        except IOError , exp:
            print exp
            return False
        except IndexError , exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            log_mgr.log(s)
            return False
        except TypeError , exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            log_mgr.log(s)
            return False


        #Now load interesting properties in hosts/services
        #Taging retention=False prop that not be directly load
        #Items will be with theirs status, but not in checking, so
        #a new check will be launch like with a normal begining (random distributed
        #scheduling)

        ret_hosts = all_data['hosts']
        for ret_h_name in ret_hosts:
            #We take the dict of our value to load
            d = all_data['hosts'][ret_h_name]
            h = sched.hosts.find_by_name(ret_h_name)
            if h != None:
                running_properties = h.__class__.running_properties
                for prop in running_properties:
                    entry = running_properties[prop]
                    if entry.retention:
                        # Mayeb the save was not with this value, so
                        # we just bypass this
                        if prop in d:
                            setattr(h, prop, d[prop])
                for a in h.notifications_in_progress.values():
#                    print "AA,", a.__dict__
                    a.ref = h
                    sched.add(a)
                h.update_in_checking()
                #And also add downtimes and comments
                for dt in h.downtimes:
                    dt.ref = h
                    dt.extra_comment.ref = h
                    sched.add(dt)
                for c in h.comments:
                    c.ref = h
                    sched.add(c)


        ret_services = all_data['services']
        for (ret_s_h_name, ret_s_desc) in ret_services:
            #We take the dict of our value to load
            d = all_data['services'][(ret_s_h_name, ret_s_desc)]
            s = sched.services.find_srv_by_name_and_hostname(ret_s_h_name, ret_s_desc)
            if s != None:
                running_properties = s.__class__.running_properties
                for prop in running_properties:
                    entry = running_properties[prop]
                    if entry.retention:
                        # Mayeb the save was not with this value, so
                        # we just bypass this
                        if prop in d:
                            setattr(s, prop, d[prop])
                for a in s.notifications_in_progress.values():
                    a.ref = s
                    sched.add(a)
                s.update_in_checking()
                #And also add downtimes and comments
                for dt in s.downtimes:
                    dt.ref = s
                    dt.extra_comment.ref = s
                    sched.add(dt)
                for c in s.comments:
                    c.ref = s
                    sched.add(c)

        log_mgr.log("[PickleRetention] OK we've load data from retention file")

        return True
