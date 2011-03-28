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


#This class is use to manage modules and call callback

import os
import time
import sys
import traceback
import cStringIO

from shinken.basemodule import BaseModule
from shinken.log import logger

class ModulesManager(object):

    def __init__(self, modules_type, modules_path, modules):
        self.modules_path = modules_path
        self.modules_type = modules_type
        self.modules = modules
        self.allowed_types = [ plug.module_type for plug in modules ]
        self.imported_modules = []
        self.modules_assoc = []
        self.instances = []
        self.to_restart = []


    def set_modules(self, modules):
        """ Set the modules requested for this manager """
        self.modules = modules
        self.allowed_types = [ mod.module_type for mod in modules ]


    def load_and_init(self, start_external=True):
        """ Import, instanciate & "init" the modules we have been requested """
        self.load()
        self.get_instances(start_external)


    def load(self):
        now = int(time.time())
        """ Try to import the requested modules ; put the imported modules in self.imported_modules.
The previous imported modules, if any, are cleaned before. """ 
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
            print "Try to load", fname
            try:
                m = __import__(fname)
                if not hasattr(m, 'properties'):
                    continue

                # We want to keep only the modules of our type
                if self.modules_type in m.properties['daemons']:
                    self.imported_modules.append(m)
            except ImportError , exp:
                print "Warning :", exp        

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


    def try_instance_init(self, inst):
        """ Try to "init" the given module instance. 
Returns: True on successfull init. False if instance init method raised any Exception. """ 
        try:
            print "Trying to init module", inst.get_name()
            inst.init_try += 1
            # Maybe it's a retry, so do not create queues again
            if inst.init_try == 1:
                # We setup the inst queues before its 'init' method is called.
                # So that it can eventually get ref to the queues.
                inst.create_queues()
            else:
                # do not try until 5 sec, or it's too loopy
                if inst.last_init_try > time.time() - 5:
                    return False

            inst.last_init_try = time.time()
            inst.init()
        except Exception, e:
            logger.log("Error : the instance %s raised an exception %s, I remove it!" % (inst.get_name(), str(e)))
            output = cStringIO.StringIO()
            traceback.print_exc(file=output)
            logger.log("Back trace of this remove : %s" % (output.getvalue()))
            output.close()
            return False
        return True


    def clear_instances(self, insts=None):
        """ Request to "remove" the given instances list or all if not provided """
        if insts is None:
            insts = self.instances[:] # have to make a copy of the list
        for i in insts:
            self.remove_instance(i)
    

    # actually only arbiter call this method with start_external=False..
    def get_instances(self, start_external=True):
        """ Create, init and then returns the list of module instances that the caller needs.
By default (start_external=True) also start the execution of the instances that are "external".
If an instance can't be created or init'ed then only log is done. That instance is skipped.
The previous modules instance(s), if any, are all cleaned. """ 
        self.clear_instances()
        for (mod_conf, module) in self.modules_assoc:
            try:
                mod_conf.properties = module.properties.copy()
                inst = module.get_instance(mod_conf)
                if inst is None: #None = Bad thing happened :)
                    logger.log("get_instance for module %s returned None !" % (mod_conf.get_name()))
                    continue
                assert(isinstance(inst, BaseModule))
                self.instances.append(inst)
            except Exception , exp:
                logger.log("Error : the module %s raised an exception %s, I remove it!" % (mod_conf.get_name(), str(exp)))
                output = cStringIO.StringIO()
                traceback.print_exc(file=output)
                logger.log("Back trace of this remove : %s" % (output.getvalue()))
                output.close()

        print "Loaded", len(self.instances), "module instances"

        for inst in self.instances:
            if not self.try_instance_init(inst):
                # If the init failed, we put in in the restart queue
                logger.log("Warning : the module '%s' failed to init, I will try to restart it later" % inst.get_name())
                self.to_restart.append(inst)

        #self.clear_instances(to_del)

        # We only start the external instances once they all have been "init" called 
        if start_external:
            self.__start_ext_instances()

        return self.instances


    #Launch external instaces that are load corectly
    def __start_ext_instances(self):
        for inst in self.instances:
            if inst not in self.to_restart:
                print "Starting external module %s" % inst.get_name()
                inst.start()


    # actually only called by arbiter... because it instanciate its modules before going daemon
    # TODO: but this actually leads to a double "init" call.. maybe a "uninit" would be needed ? 
    def init_and_start_instances(self):
        #for inst in self.instances:
        #    if not self.try_instance_init(inst):
        #        # damn..
        #        logger.log("Module instance %s could not be init" % inst.get_name())
        #        self.to_restart.append(inst)
        self.__start_ext_instances()

     
    def remove_instance(self, inst):
        """ Request to cleanly remove the given instance. 
If instance is external also shutdown it cleanly """
        # External instances need to be close before (process + queues)
        if inst.is_external:
            print "Ask stop process for", inst.get_name()
            inst.stop_process()
            print "Stop process done"
        
        inst.clear_queues()

        # Then do not listen anymore about it
        self.instances.remove(inst)


    def check_alive_instances(self):
        #to_del = []
        #Only for external
        for inst in self.instances:
            if not inst in self.to_restart:
                if inst.is_external and not inst.process.is_alive():
                    logger.log("Error : the external module %s goes down unexpectly!" % inst.get_name())
                    logger.log("Setting the module %s to restart" % inst.get_name())
                    self.to_restart.append(inst)

                
    def try_to_restart_deads(self):
        to_restart = self.to_restart[:]
        del self.to_restart[:]
        for inst in to_restart:
            print "I should try to reinit", inst.get_name()
            if self.try_instance_init(inst):
                print "Good, I try to restart",  inst.get_name()
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


    def get_external_to_queues(self, phase=None):
        return [ inst.to_q for inst in self.instances if inst.is_external and phase in inst.phases and inst not in self.to_restart]


    def get_external_from_queues(self, phase=None):
        return [ inst.from_q for inst in self.instances if inst.is_external and phase in inst.phases and inst not in self.to_restart]


    def stop_all(self):
        #Ask internal to quit if they can
        for inst in self.get_internal_instances():
            if hasattr(inst, 'quit') and callable(inst.quit):
                inst.quit()
        
        self.clear_instances([ inst for inst in self.instances if inst.is_external])
