#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2011 :
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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



import os
import time
import sys
import traceback
import cStringIO

from shinken.basemodule import BaseModule
from shinken.log import logger

class ModulesManager(object):
    """This class is use to manage modules and call callback"""
    
    
    def __init__(self, modules_type, modules_path, modules):
        self.modules_path = modules_path
        self.modules_type = modules_type
        self.modules = modules
        self.allowed_types = [ plug.module_type for plug in modules ]
        self.imported_modules = []
        self.modules_assoc = []
        self.instances = []
        self.to_restart = []
        self.max_queue_size = 0
        self.manager = None


    def load_manager(self, manager):
        self.manager = manager


    # Set the modules requested for this manager
    def set_modules(self, modules):
        self.modules = modules
        self.allowed_types = [ mod.module_type for mod in modules ]


    def set_max_queue_size(self, max_queue_size):
        self.max_queue_size = max_queue_size


    # Import, instanciate & "init" the modules we have been requested
    def load_and_init(self):
        self.load()
        self.get_instances()


    # Try to import the requested modules ; put the imported modules in self.imported_modules.
    # The previous imported modules, if any, are cleaned before.
    def load(self):
        now = int(time.time())
        # We get all modules file with .py
        modules_files = [ fname[:-3] for fname in os.listdir(self.modules_path) 
                         if fname.endswith(".py") ]

        # And directories
        modules_files.extend([ fname for fname in os.listdir(self.modules_path)
                               if os.path.isdir(os.path.join(self.modules_path, fname)) ])

        # Now we try to load thems
        # So first we add their dir into the sys.path
        if not self.modules_path in sys.path:
            sys.path.append(self.modules_path)

        # We try to import them, but we keep only the one of
        # our type
        del self.imported_modules[:]
        for fname in modules_files:
            #print "Try to load", fname
            try:
                m = __import__(fname)
                if not hasattr(m, 'properties'):
                    continue

                # We want to keep only the modules of our type
                if self.modules_type in m.properties['daemons']:
                    self.imported_modules.append(m)
            except Exception , exp:
                logger.log("Warning in importing module : %s" % exp)

        del self.modules_assoc[:]
        for mod_conf in self.modules:
            module_type = mod_conf.module_type
            is_find = False
            for module in self.imported_modules:
                if module.properties['type'] == module_type:
                    self.modules_assoc.append((mod_conf, module))
                    is_find = True
                    break
            if not is_find:
                # No module is suitable, we Raise a Warning
                logger.log("Warning : the module type %s for %s was not found in modules!" % (module_type, mod_conf.get_name()))


    # Try to "init" the given module instance. 
    # Returns: True on successfull init. False if instance init method raised any Exception.
    def try_instance_init(self, inst):
        try:
            logger.log("Trying to init module : %s" % inst.get_name())
            inst.init_try += 1
            # Maybe it's a retry
            if inst.init_try > 1:
                # Do not try until 5 sec, or it's too loopy
                if inst.last_init_try > time.time() - 5:
                    return False
            inst.last_init_try = time.time()

            # If it's an external, create/update Queues()
            if inst.is_external:
                inst.create_queues(self.manager)

            inst.init()
        except Exception, e:
            logger.log("Error : the instance %s raised an exception %s, I remove it!" % (inst.get_name(), str(e)))
            output = cStringIO.StringIO()
            traceback.print_exc(file=output)
            logger.log("Back trace of this remove : %s" % (output.getvalue()))
            output.close()
            return False
        return True

    # Request to "remove" the given instances list or all if not provided
    def clear_instances(self, insts=None):
        if insts is None:
            insts = self.instances[:] # have to make a copy of the list
        for i in insts:
            self.remove_instance(i)
    

    # Put an instance to the restart queue
    def set_to_restart(self, inst):
        self.to_restart.append(inst)



    # actually only arbiter call this method with start_external=False..
    # Create, init and then returns the list of module instances that the caller needs.
    # If an instance can't be created or init'ed then only log is done. 
    # That instance is skipped. The previous modules instance(s), if any, are all cleaned.
    def get_instances(self):
        self.clear_instances()
        for (mod_conf, module) in self.modules_assoc:
            try:
                mod_conf.properties = module.properties.copy()
                inst = module.get_instance(mod_conf)
                if inst is None: # None = Bad thing happened :)
                    logger.log("get_instance for module %s returned None !" % (mod_conf.get_name()))
                    continue
                assert(isinstance(inst, BaseModule))
                self.instances.append(inst)
            except Exception , exp:
                s = str(exp)
                if isinstance(s, str):
                    s = s.decode('UTF-8', 'replace')
                logger.log("Error : the module %s raised an exception %s, I remove it!" % (mod_conf.get_name(), s))
                output = cStringIO.StringIO()
                traceback.print_exc(file=output)
                logger.log("Back trace of this remove : %s" % (output.getvalue()))
                output.close()

        for inst in self.instances:
            # External are not init now, but only when they are started
            if not inst.is_external and not self.try_instance_init(inst):
                # If the init failed, we put in in the restart queue
                logger.log("Warning : the module '%s' failed to init, I will try to restart it later" % inst.get_name())
                self.to_restart.append(inst)

        return self.instances


    # Launch external instaces that are load corectly
    def start_external_instances(self):
        for inst in [inst for inst in self.instances if inst.is_external]:
            # But maybe the init failed a bit, so bypass this ones from now
            if not self.try_instance_init(inst):
                logger.log("Warning : the module '%s' failed to init, I will try to restart it later" % inst.get_name())
                self.to_restart.append(inst)
                continue
            
            # ok, init succeed
            logger.log("Info : Starting external module %s" % inst.get_name())
            inst.start()



    # Request to cleanly remove the given instance. 
    # If instance is external also shutdown it cleanly 
    def remove_instance(self, inst):

        # External instances need to be close before (process + queues)
        if inst.is_external:
            print "Info : Ask stop process for", inst.get_name()
            inst.stop_process()
            print "Info : Stop process done"
        
        inst.clear_queues(self.manager)

        # Then do not listen anymore about it
        self.instances.remove(inst)


    def check_alive_instances(self):
        # Only for external
        for inst in self.instances:
            if not inst in self.to_restart:
                if inst.is_external and not inst.process.is_alive():
                    logger.log("Error : the external module %s goes down unexpectly!" % inst.get_name())
                    logger.log("Info : Setting the module %s to restart" % inst.get_name())
                    # We clean its queues, they are no more useful
                    inst.clear_queues(self.manager)
                    self.to_restart.append(inst)
                    # Ok, no need to look at queue size now
                    continue

                # Now look for man queue size. If above value, the module should got a huge problem
                # and so bailout. It's not a perfect solution, more a watchdog
                # If max_queue_size is 0, don't check this
                if self.max_queue_size == 0:
                    continue
                # Ok, go launch the dog!
                queue_size = 0
                try:
                    queue_size = inst.to_q.qsize()
                except Exception, exp:
                    pass
                if queue_size > self.max_queue_size:
                    logger.log("Error : the external module %s got a too high brok queue size (%s > %s)!" % (inst.get_name(), queue_size, self.max_queue_size))
                    logger.log("Info : Setting the module %s to restart" % inst.get_name())
                    # We clean its queues, they are no more useful
                    inst.clear_queues(self.manager)
                    self.to_restart.append(inst)




                
    def try_to_restart_deads(self):
        to_restart = self.to_restart[:]
        del self.to_restart[:]
        for inst in to_restart:
            print "Info : I should try to reinit", inst.get_name()
            if self.try_instance_init(inst):
                print "Info : Good, I try to restart",  inst.get_name()
                # If it's an external, it will start it
                inst.start()
                # Ok it's good now :)
            else:
                self.to_restart.append(inst)
                

    # Do not give to others inst that got problems
    def get_internal_instances(self, phase=None):
        return [ inst for inst in self.instances if not inst.is_external and phase in inst.phases and inst not in self.to_restart]


    def get_external_instances(self, phase=None):
        return [ inst for inst in self.instances if inst.is_external and phase in inst.phases and inst not in self.to_restart]


    def get_external_to_queues(self):
        return [ inst.to_q for inst in self.instances if inst.is_external and inst not in self.to_restart]


    def get_external_from_queues(self):
        return [ inst.from_q for inst in self.instances if inst.is_external and inst not in self.to_restart]


    def stop_all(self):
        #Ask internal to quit if they can
        for inst in self.get_internal_instances():
            if hasattr(inst, 'quit') and callable(inst.quit):
                inst.quit()
        
        self.clear_instances([ inst for inst in self.instances if inst.is_external])

