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


""" This python module contains the class BaseModule that shinken modules will subclass """


import os
import signal
import time
from multiprocessing import Queue, Process

from shinken.log import logger
 

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
    
    

class BaseModule(object):
    """ This is the base class for the shinken modules.
Modules can be used by the different shinken daemons/services for different tasks.
Example of task that a shinken module can do:
 - load additional configuration objects.
 - recurrently save hosts/services status/perfdata informations in different format.
 - ...
 """

    def __init__(self, mod_conf):
        """ Instanciate a new module. There can be many instance of the same type.
`mod_conf´ is module configuration object for this new module instance. """
        self.myconf = mod_conf
        self.name = mod_conf.get_name()
        # We can have sub modules
        self.modules = getattr(mod_conf, 'modules', [])
        self.props = mod_conf.properties.copy()
        self.properties = self.props # TODO: choose between 'props' or 'properties'..
        self.interrupted = False
        self.is_external = self.props.get('external', False)
        self.phases = self.props.get('phases', [])  # though a module defined with no phase is quite useless ..
        self.phases.append(None)
        self.to_q = None # the queue the module will receive data to manage
        self.from_q = None # the queue the module will put its result data
        self.process = None
        self.init_try = 0


    def init(self):
        """ Handle this module "post" init ; just before it'll be started. 
Like just open necessaries file(s), database(s), or whatever the module will need. """
        pass

    # The manager is None on android, but a true Manager() elsewhere
    def create_queues(self, manager=None):
        """ Create the shared queues that will be used by shinken daemon process and this module process.
But clear queues if they were already set before recreating new one.  """
        self.clear_queues(manager)
        # If no Manager() object, go with classic Queue()
        if not manager:
            self.from_q = Queue()
            self.to_q = Queue()
        else:
            self.from_q = manager.Queue()
            self.to_q = manager.Queue()


    def clear_queues(self, manager):
        """ Release the resources associated with the queues of this instance """
        for q in (self.to_q, self.from_q):
            if q is None: continue
            # If we gotno manager, we direct call the clean
            if not manager:
                q.close()
                q.join_thread()
#            else:
#                q._callmethod('close')
#                q._callmethod('join_thread')
        self.to_q = self.from_q = None


    def start(self):
        """ Start this module process if it's external. if not -> donothing """
        if not self.is_external:
            return
        self.stop_process()
        logger.log("Starting external process for instance %s" % (self.name))
        p = Process(target=self.main, args=())

        # Under windows we should not call a start on an object that got
        # it's process as object, so we remove it it we set it in a earlier
        # start
        try:
          del self.properties['process']
        except:
          pass

        p.start()
        # We save the process data AFTER the fork()
        self.process = p
        self.properties['process'] = p  ## TODO: temporary
        logger.log("%s is now started ; pid=%d" % (self.name, p.pid))


    # Sometime terminate() is not enough, we must "help"
    # external modules to die...
    def __kill(self):
        if os.name == 'nt':
            self.process.terminate()
        else:
            # Ok, let him 1 second before really KILL IT
            os.kill(self.process.pid, 15)
            time.sleep(1)
            # You do not let me another choice guy...
            if self.process.is_alive():
                os.kill(self.process.pid, 9)


    def stop_process(self):
        """ Request the module process to stop and release it """
        if self.process:
            logger.log("I'm stopping module '%s' process pid:%s " % (self.get_name(), self.process.pid))
            self.process.terminate()
            self.process.join(timeout=1)
            if self.process.is_alive():
                logger.log("The process is still alive, I help it to die")
                self.__kill()
            self.process = None



    ## TODO: are these 2 methods really needed ?
    def get_name(self):
        return self.name
    def has(self, prop):
        """ The classic has : do we have a prop or not? """
        return hasattr(self, prop)

#    def get_objects(self):
#        """ Called during arbiter configuration phase. Return a dict to the objects that the module provides.
##Possible objects are Host, Service, Timeperiod, etc .. 
#Examples of valid return:
#    h1 = { 'host_name': "server1", register=0 }
#    return { 'hosts': [ h1 ] } """
#        raise NotImplementedError()

    
#    def update_retention_objects(self, sched, log_mgr):
#        """ Update the retention objects of this module.
#Called recurrently by scheduler. Also during stop of scheduler. """
#        raise NotImplementedError()


#    def hook_late_configuration(self, conf):
#        """ Hook for the module "late configuration" : Called by arbiter after the configuration has been fully loaded & built """
#        raise NotImplementedError()


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
        """ Called just before the module will exit
Put in this method all you need to cleanly release all open resource used by your module """ 
        pass
    
    def do_loop_turn(self):
        """ For external modules only: implement in this method the body of you main loop """
        raise NotImplementedError()
    
    def main(self):
        """ module "main" method. Only used by external modules. """
        self.set_signal_handler()
        logger.log("[%s[%d]]: Now running.." % (self.name, os.getpid()))
        while not self.interrupted:
            self.do_loop_turn()
        self.do_stop()
        logger.log("[%s]: exiting now.." % (self.name))
        
    work = main # TODO: apparently some modules would uses "work" as the main method ??

