# -*- coding: utf-8 -*-
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


""" This python module contains the class Module that shinken modules will subclass """


import os
import signal
from multiprocessing import Queue

 

## TODO: use a class for defining the module "properties" instead of plain dict ??  Like:
"""
class ModuleProperties(object):
    def __init__(self, type, phases, external=False)
        self.type = type
        self.phases = phases
        self.external = external
"""
## and  have the new modules instanciate this like follow :
"""
properties = ModuleProperties('the_module_type', the_module_phases, is_mod_ext)
"""
## 
""" The `properties´ dict defines what the module can do and if it's an external module or not. """
properties = {
    # name of the module type ; to distinguish between them:
    'type': None,
    
    # is the module "external" (external means here a daemon module) ?
    'external': True,
    
    # Possible configuration phases where the module is involved :
    'phases' : [ 'configuration', 'late_configuration', 'running', 'retention' ], 
    }


class ModulePhases:
## TODO: why not use simply integers instead of string to represent the different phases ??    
    CONFIGURATION       = 1
    LATE_CONFIGURATION  = 2
    RUNNING             = 4 
    RETENTION           = 8
    
    

class Module(object):
    """ This is the base class for the shinken modules.
Modules can be used by the different shinken daemons/services for different tasks.
Example of task that a shinken module can do:
 - load additional configuration objects.
 - recurrently save hosts/services status/perfdata informations in different format.
 - ...
 """

    def __init__(self, mod_conf):
        """ `name´ is the name given to this module instance. There can be many instance of the same type.
`props´ is the properties dict of this module. dict that defines at what phases the module is involved. """
        self.myconf = mod_conf
        self.name = mod_conf.get_name()
        self.props = mod_conf.properties
        self.properties = self.props
        self.interrupted = False
        self.is_external = self.props.get('external', False)
        self.phases = self.props.get('phases', [])  ## though a module defined with no phase is quite useless ..
        self.phases.append(None)
        
    def create_queues(self):
        self.create_queues__(self)
        
    @staticmethod
    def create_queues__(obj):
        obj.from_q = Queue()
        obj.to_q = Queue()

    def init(self):
        """ Handle this module "post" init ; just before it'll be started. 
Like just open necessaries file(s), database(s), or whatever the module will need. """
        pass

    def get_name(self):
        return self.name

    def has(self, prop):
        """ The classic has : do we have a prop or not? """
        return hasattr(self, prop)

    def get_objects(self):
        """ Called during arbiter configuration phase. Return a dict to the objects that the module provides.
Possible objects are Host, Service, Timeperiod, etc .. 
Examples of valid return:
    h1 = { 'host_name': "server1", register=0 }
    return { 'hosts': [ h1 ] } """
        raise NotImplementedError()

    
    def update_retention_objects(self, sched, log_mgr):
        """ Update the retention objects of this module.
Called recurrently by scheduler. Also during stop of scheduler. """
        raise NotImplementedError()


    def hook_late_configuration(self, conf):
        """ Hook for the module "late configuration" : Called by arbiter after the configuration has been fully loaded & built """
        raise NotImplementedError()


    def manage_brok(self, brok):
        """ Request the module to manage the given brok.
There a lot of different possible broks to manage. """
        manage = getattr(self, 'manage_' + brok.type + '_brok', None)
        if manage:
            return manage(brok)


    def manage_signal(self, sig, frame):
        self.interrupted = True

    def set_signal_handler(self, sigs=None):
        if sigs is None:
            sigs = (signal.SIGINT, signal.SIGTERM)
            
        for sig in sigs:
            signal.signal(sig, self.manage_signal)
    
    set_exit_handler = set_signal_handler
    
    def do_stop(self):
        pass
    
    def do_loop_turn(self):
        raise NotImplementedError()
    
    def main(self):
        self.set_signal_handler()
        print("[%s[%d]]: Now running.." % (self.name, os.getpid()))
        while not self.interrupted:
            self.do_loop_turn()
        self.do_stop()
        print("[%s]: exiting now.." % (self.name))
