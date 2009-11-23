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


#This class is use to mnager plugins and call callback


import os
import os.path
import imp
import sys

#pluginpath = os.path.join(os.path.dirname(imp.find_module("pluginloader")[1]), "plugins/")
#Thanks http://pytute.blogspot.com/2007/04/python-plugin-system.html

class PluginsManager():

    def __init__(self, plugins_type, plugins_path):
        self.plugins_path = plugins_path
        self.plugins_type = plugins_type


    #Lod all plugins
    def load(self):
        #We get all plugins file of our type (end with broker.py for example)
        plugins_files = [fname[:-3] for fname in os.listdir(self.plugins_path) if fname.endswith(self.plugins_type+".py")]
        
        #Now we try to load thems
        if not self.plugins_path in sys.path:
            sys.path.append(self.plugins_path)
        self.imported_modules = [__import__(fname) for fname in plugins_files]
    
    
    #Get broker instance to five them after broks
    def get_brokers(self):
        brokers = []
        for mod in self.imported_modules:
            b = mod.get_broker()
            brokers.append(b)
        return brokers
