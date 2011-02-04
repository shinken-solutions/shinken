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
print "Detected module : Dummy module for Poller"


from shinken.basemodule import BaseModule


properties = {
    'type' : 'dummy_poller',
    'external' : False,
    'phases' : ['worker'],
    }


#called by the plugin manager to get a broker
def get_instance(mod_conf):
    print "Get a Dummy poller module for plugin %s" % mod_conf.get_name()
    instance = Dummy_poller(mod_conf)
    return instance



#Just print some stuff
class Dummy_poller(BaseModule):
    
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)


    # Called by poller to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the dummy poller module"



