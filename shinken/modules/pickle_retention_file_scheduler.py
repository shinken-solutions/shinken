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


import time
from shinken.external_command import ExternalCommand



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
        print "Initilisation of the dummy scheduler module"
        #self.return_queue = self.properties['from_queue']


    def get_name(self):
        return self.name


    #Ok, main function that is called in the retention creation pass
    def update_retention_objects(self, sched):
        print "[PickleRetention] asking me to update the retention objects"


    #Should return if it succeed in the retention load or not
    def load_retention_objects(self, sched):
        print "[PickleRetention] asking me to load the retention objects"
        return False

