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

class Plugins():

    def __init__(self, pluginpath):
        self.pluginpath = pluginpath


    #Lod all plugins
    def load(self):
        #We get all plugins names
        #pluginpath = "./plugins"
        pluginfiles = [fname[:-3] for fname in os.listdir(self.pluginpath) if fname.endswith(".py")]
        
        #Now we try to load thems
        if not self.pluginpath in sys.path:
            sys.path.append(self.pluginpath)
        self.imported_modules = [__import__(fname) for fname in pluginfiles]

    #def init(self):
    #    for mod in self.imported_modules:
    #        mod.init()


    #Get broker instance to five them after broks
    def get_brokers(self):
        brokers = []
        for mod in self.imported_modules:
            b = mod.get_broker()
            brokers.append(b)
        return brokers
