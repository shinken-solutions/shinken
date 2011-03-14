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
print "Detected module : Picle retention file for Broker"

import cPickle
import shutil


from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons' : ['broker'],
    'type' : 'pickle_retention_file_broker',
    'external' : False,
    'phases' : ['retention'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a pickle retention broker module for plugin %s" % plugin.get_name()
    path = plugin.path
    instance = Pickle_retention_broker(plugin, path)
    return instance



# Just print some stuff
class Pickle_retention_broker(BaseModule):
    def __init__(self, modconf, path):
        BaseModule.__init__(self, modconf)
        self.path = path
    
    # Ok, main function that is called in the retention creation pass
    def hook_save_retention(self, broker):#, log_mgr):
        log_mgr = logger
        print "[PickleRetentionBroker] asking me to update the retention objects"
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
            all_broks = broker.broks
            print "DBG"
            for b in all_broks:
                print "DBG : saving", b
            
            #for h in sched.hosts:
            #    d = {}
            #    running_properties = h.__class__.running_properties
            #    for prop, entry in running_properties.items():
            #        if entry.retention:
            #            d[prop] = getattr(h, prop)
            #    #f2 = open('/tmp/moncul2/'+h.host_name, 'wb')
            #    #cPickle.dump(d, f2)
            #    #f2.close()
            #    all_data['hosts'][h.host_name] = d

            #Now same for services
            #for s in sched.services:
            #    d = {}
            #    running_properties = s.__class__.running_properties
            #    for prop, entry in running_properties.items():
            #        if entry.retention:
            #            d[prop] = getattr(s, prop)
            #    #f2 = open('/tmp/moncul2/'+s.host_name+'__'+s.service_description, 'wb')
            #    #cPickle.dump(d, f2)
            #    #f2.close()
            #    all_data['services'][(s.host.host_name, s.service_description)] = d

            #s = cPickle.dumps(all_data)
            #s_compress = zlib.compress(s)
            cPickle.dump(all_broks, f, protocol=cPickle.HIGHEST_PROTOCOL)
            #f.write(s_compress)
            f.close()
            # Now move the .tmp fiel to the real path
            shutil.move(self.path+'.tmp', self.path)
        except IOError , exp:
            log_mgr.log("Error: retention file creation failed, %s" % str(exp))
            return
        log_mgr.log("Updating retention_file %s" % self.path)


    #Should return if it succeed in the retention load or not
    def hook_load_retention(self, broker):#, log_mgr):
        log_mgr = logger
        print "[PickleRetentionBroker] asking me to load the retention objects"

        #Now the old flat file way :(
        log_mgr.log("[PickleRetentionBroker]Reading from retention_file %s" % self.path)
        try:
            f = open(self.path, 'rb')
            all_broks = cPickle.load(f)
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

        for b in all_broks:
            print "Loading brok", b
        broker.broks.extend(all_broks)

        log_mgr.log("[PickleRetentionBroker] OK we've load data from retention file")
        
        return True
