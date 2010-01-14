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


#This class is use to mnager modules and call callback


import os
import os.path
import imp
import sys

#modulepath = os.path.join(os.path.dirname(imp.find_module("pluginloader")[1]), "modules/")
#Thanks http://pytute.blogspot.com/2007/04/python-plugin-system.html

class ModulesManager():

    def __init__(self, modules_type, modules_path, modules):
        self.modules_path = modules_path
        self.modules_type = modules_type
        self.modules = modules
        self.allowed_types = [plug.module_type for plug in self.modules]


    #Lod all modules
    def load(self):
        #We get all modules file of our type (end with broker.py for example)
        modules_files = [fname[:-3] for fname in os.listdir(self.modules_path) if fname.endswith(self.modules_type+".py")]
        
        #And directories (no remove of .py)
        modules_files.extend([fname for fname in os.listdir(self.modules_path) if fname.endswith(self.modules_type)])
        
        #Now we try to load thems
        if not self.modules_path in sys.path:
            sys.path.append(self.modules_path)
        
        self.imported_modules = []
        for fname in modules_files:
            try:
                self.imported_modules.append(__import__(fname))
            except ImportError as exp:
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
    

    #Get broker instance to five them after broks
    def get_instances(self):
        brokers = []
        for (module, mod) in self.modules_assoc:
            b = mod.get_broker(module)
            if b != None: #None = Bad thing happened :)
                #the instance need the properties of the module
                b.properties = mod.properties
                brokers.append(b)

        print "Load", len(brokers), "module instances"

#        for inst in brokers:
#            print "Doing mod instance", inst, inst.__dict__
#            if hasattr(inst, 'is_external') and callable(inst.is_external) and inst.is_external():
#                print "Is external!"
#                q = Queue()
#                self.external_queues.append(q)
#                inst.init(q)
#                p = Process(target=inst.main, args=())
#                p.start()
#                inst._process = p
#                inst._queue = q
#                self.external_process.append(p)
#            else:
#                inst.init()

        return brokers
