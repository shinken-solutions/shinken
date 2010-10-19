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
import imp
import sys
import traceback


from multiprocessing import Process, Queue, active_children

#modulepath = os.path.join(os.path.dirname(imp.find_module("pluginloader")[1]), "modules/")
#Thanks http://pytute.blogspot.com/2007/04/python-plugin-system.html

class ModulesManager(object):

    def __init__(self, modules_type, modules_path, modules):
        self.modules_path = modules_path
        self.modules_type = modules_type
        self.modules = modules
        self.allowed_types = [plug.module_type for plug in self.modules]


    #Lod all modules
    def load(self):
        #We get all modules file of our type (end with broker.py for example)
        modules_files = [fname[:-3] for fname in os.listdir(self.modules_path) if fname.endswith(self.modules_type+".py")]
        
        #And directories (no remove of .py but still with broker for example at the end)
        modules_files.extend([fname for fname in os.listdir(self.modules_path) if fname.endswith(self.modules_type)])
        
        #Now we try to load thems
        if not self.modules_path in sys.path:
            sys.path.append(self.modules_path)
        
        self.imported_modules = []
        for fname in modules_files:
            try:
                self.imported_modules.append(__import__(fname))
            except ImportError , exp:
                print "Warning :", exp

        self.modules_assoc = []
        for module in self.modules:
            module_type = module.module_type
            is_find = False
            for mod in self.imported_modules:
                if mod.properties['type'] == module_type:
                    self.modules_assoc.append((module, mod))
                    is_find = True
            if not is_find:
                #No module is suitable, we Raise a Warning
                print "Warning : the module type %s for %s was not found in modules!" % (module_type, module.get_name())
    

    #Get modules instance to give them after broks
    def get_instances(self):
        self.instances = []
        for (module, mod) in self.modules_assoc:
            try:
                inst = mod.get_instance(module)
                if inst != None: #None = Bad thing happened :)
                    #the instance need the properties of the module
                    inst.properties = mod.properties
                    self.instances.append(inst)
            except Exception , exp:
                print "Error : the module %s raised an exception %s, I remove it!" % (module.get_name(), str(exp))
                print "Back trace of this remove :"
                traceback.print_exc(file=sys.stdout)

        print "Load", len(self.instances), "module instances"

        to_del = []
        for inst in self.instances:
            try:
                if 'external' in inst.properties and inst.properties['external']:
                    print "Starting external process for instance", inst.get_name()
                    inst.properties['to_queue'] = Queue()
                    inst.properties['from_queue'] = Queue()
                    inst.init()
                    inst.properties['process'] = Process(target=inst.main, args=())
                    inst.properties['process'].start()
                else:
                    inst.properties['external'] = False
                    inst.init()
            except Exception , exp:
                print "Error : the instance %s raised an exception %s, I remove it!" % (inst.get_name(), str(exp))
                print "Back trace of this remove :"
                traceback.print_exc(file=sys.stdout)
                to_del.append(inst)


        for inst in to_del:
            self.instances.remove(inst)

        return self.instances

    def remove_instance(self, inst):
        #External instances need to be close before (process + queues)
        if inst.properties['external']:
            inst.properties['process'].terminate()
            inst.properties['process'].join(timeout=1)
            inst.properties['to_queue'].close()
            inst.properties['to_queue'].join_thread()
            inst.properties['from_queue'].close()
            inst.properties['from_queue'].join_thread()

        #Then do not listen anymore about it
        self.instances.remove(inst)


    def check_alive_instances(self):
        to_del = []
        #Only for external
        for inst in self.instances:
            if inst.properties['external'] and not inst.properties['process'].is_alive():
                print "Error : the external module %s goes down unexpectly!" % inst.get_name()
                to_del.append(inst)

        for inst in to_del:
            self.remove_instance(inst)


    def get_internal_instances(self, phase=None):
        return [inst for inst in self.instances if not inst.properties['external'] and (phase==None or phase in inst.properties['phases'])]


    def get_external_instances(self, phase=None):
        return [inst for inst in self.instances if inst.properties['external'] and (phase==None or phase in inst.properties['phases'])]


    def get_external_to_queues(self, phase=None):
        return [inst.properties['to_queue'] for inst in self.instances if inst.properties['external'] and (phase==None or phase in inst.properties['phases'])]


    def get_external_from_queues(self, phase=None):
        return [inst.properties['from_queue'] for inst in self.instances if inst.properties['external'] and (phase==None or phase in inst.properties['phases'])]


    def stop_all(self):
        for inst in self.get_external_instances():
            self.remove_instance(inst)
