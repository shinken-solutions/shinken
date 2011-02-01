#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#This class is use to mnager modules and call callback


import os
import os.path
import sys
import traceback


from multiprocessing import Process, Queue

#modulepath = os.path.join(os.path.dirname(imp.find_module("pluginloader")[1]), "modules/")
#Thanks http://pytute.blogspot.com/2007/04/python-plugin-system.html

from basemodule import Module

class ModulesManager(object):

    def __init__(self, modules_type, modules_path, modules):
        self.modules_path = modules_path
        self.modules_type = modules_type
        self.modules = modules
        self.allowed_types = [ plug.module_type for plug in modules ]
        self.imported_modules = []
        self.modules_assoc = []
        self.instances = []


    #Lod all modules
    def load(self):
        #We get all modules file of our type (end with broker.py for example)
        modules_files = [ fname[:-3] for fname in os.listdir(self.modules_path) 
                         if fname.endswith(self.modules_type+".py") ]

        #And directories (no remove of .py but still with broker for example at the end)
        modules_files.extend([ fname for fname in os.listdir(self.modules_path)
                               if fname.endswith(self.modules_type) ])

        # Now we try to load thems
        if not self.modules_path in sys.path:
            sys.path.append(self.modules_path)

        del self.imported_modules[:]
        for fname in modules_files:
            try:
                print("importing %s" % (fname))
                self.imported_modules.append(__import__(fname))
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
                #No module is suitable, we Raise a Warning
                print "Warning : the module type %s for %s was not found in modules!" % (module_type, mod_conf.get_name())


    def try_instance_init(self, inst):
        """ Try to "init" the given module instance. 
Returns: True on successfull init. False if instance init method raised any Exception. """ 
        try:
            inst.init()
        except Exception as e:
            print "Error : the instance %s raised an exception %s, I remove it!" % (inst.get_name(), str(e))
            print "Back trace of this remove :"
            traceback.print_exc(file=sys.stdout)    
            return False
        return True

    def clear_instances(self, insts=None):
        if insts is None:
            insts = self.instances[:]
        for i in insts:
            self.remove_instance(i)
    
    # actually only arbiter call this method with start_external=False..
    def get_instances(self, start_external=True):
        """ Create, init and then returns the list of module instances that the caller needs.
By default (start_external=True) also start the execution of the instances that are "external".
If an instance can't be created or init'ed then only log is done. That instance is skipped. """ 
        self.clear_instances()
        for (mod_conf, module) in self.modules_assoc:
            try:
                mod_conf.properties = module.properties.copy()
                inst = module.get_instance(mod_conf)
                if inst is None: #None = Bad thing happened :)
                    continue
                ## TODO: temporary for back comptability with previous modules :
                if not isinstance(inst, Module):
                    print("Notice: module %s is old module style (not instance of basemodule.Module)" % (mod_conf.get_name()))
                    inst.props = inst.properties = mod_conf.properties.copy()
                    inst.is_external = inst.props['external'] = inst.props.get('external', False)
                    inst.phases = inst.props.get('phases', [])  ## though a module defined with no phase is quite useless ..
                    inst.phases.append(None) ## to permit simpler get_*_ methods
                    ## end temporary
                self.instances.append(inst)
            except Exception , exp:
                print "Error : the module %s raised an exception %s, I remove it!" % (mod_conf.get_name(), str(exp))
                print "Back trace of this remove :"
                traceback.print_exc(file=sys.stdout)

        print "Load", len(self.instances), "module instances"

        to_del = []
        for inst in self.instances:
            if not self.try_instance_init(inst):
                to_del.append(inst)
                continue

        for inst in to_del:
            self.instances.remove(inst)

        if start_external:
            self.__start_ext_instances()

        return self.instances

    def __start_ext_instances(self):
        for inst in self.instances:
            if inst.is_external:
                self.__set_ext_inst_queues(inst)
                print("Starting external process for instance %s" % (inst.name))
                p = inst.process = Process(target=inst.main, args=())
                inst.properties['process'] = p  ## TODO: temporary
                p.start()
                print("%s is now started ; pid=%d" % (inst.name, p.pid))

    def __set_ext_inst_queues(self, inst):
        if isinstance(inst, Module):
            inst.create_queues()
        else:
            Module.create_queues__(inst)
            ## TODO: temporary until new style module is used by every shinken module:
            inst.properties['to_queue'] = inst.to_q
            inst.properties['from_queue'] = inst.from_q

    # actually only called by arbiter...
    # TODO: but this actually leads to a double "init" call.. maybe a "uninit" would be needed ? 
    def init_and_start_instances(self):
        for inst in self.instances:
            inst.init()
        self.__start_ext_instances()

    def close_inst_queues(self, inst):
        """ Release the resources associated with the queues from the given module instance """
        for q in (inst.to_q, inst.from_q):
            if q is None: continue
            q.close()
            q.join_thread()
        inst.to_q = inst.from_q = None
        
    def remove_instance(self, inst):
        # External instances need to be close before (process + queues)
        if inst.is_external:
            inst.process.terminate()
            inst.process.join(timeout=1)
            self.close_inst_queues(inst)
        # Then do not listen anymore about it
        self.instances.remove(inst)


    def check_alive_instances(self):
        to_del = []
        #Only for external
        for inst in self.instances:
            if inst.is_external and not inst.process.is_alive():
                print "Error : the external module %s goes down unexpectly!" % inst.get_name()
                to_del.append(inst)

        for inst in to_del:
            self.remove_instance(inst)


    def get_internal_instances(self, phase=None):
        return [ inst for inst in self.instances if not inst.is_external and phase in inst.phases ]


    def get_external_instances(self, phase=None):
        return [ inst for inst in self.instances if inst.is_external and phase in inst.phases ]


    def get_external_to_queues(self, phase=None):
        return [ inst.to_q for inst in self.instances if inst.is_external and phase in inst.phases ]


    def get_external_from_queues(self, phase=None):
        return [ inst.from_q for inst in self.instances if inst.is_external and phase in inst.phases ]


    def stop_all(self):
        #Ask internal to quit if they can
        for inst in self.get_internal_instances():
            if hasattr(inst, 'quit') and callable(inst.quit):
                inst.quit()
        for inst in self.get_external_instances():
            self.remove_instance(inst)
