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


#This Class is a plugin for the Shinken Arbiter. It connect to
#a GLPI with webservice (xmlrpc, SOAP is garbage) and take all
#hosts. Simple way from now

import json

#This text is print at the import
print "Detected module : Hot dependencies modules for Arbiter"


properties = {
    'type' : 'hot_dependencies',
    'external' : False,
    'phases' : ['late_configuration'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Hot dependencies module for arbiter with plugin %s" % plugin.get_name()
    mapping_file = getattr(plugin, 'mapping_file', '')
    mapping_command = getattr(plugin, 'mapping_command', '')
    mapping_file_history = getattr(plugin, 'mapping_file_history', '')
    mapping_command_interval = int(getattr(plugin, 'mapping_command_interval', '60'))

    instance = Hot_dependencies_arbiter(plugin.get_name(), mapping_file, mapping_command, mapping_file_history, mapping_command_interval)
    return instance



# Get hosts and/or services dep by launching a command
# or read a flat file as json format taht got theses links
class Hot_dependencies_arbiter:
    def __init__(self, name, mapping_file, mapping_command, mapping_file_history, mapping_command_interval):
        self.name = name
        self.mapping_file = mapping_file
        self.mapping_command = mapping_command
        self.mapping_file_history = mapping_file_history
        self.mapping_command_interval = mapping_command_interval


    #Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "I open the HOT dependency module"
        # Remember what we add
        


    def get_name(self):
        return self.name


    #Ok, main function that will load dep from a json file
    def hook_late_configuration(self, arb):
        # We will return external commands to the arbiter, so
        # it can jsut manage it easily and in a generic way
        ext_cmds = []
        f = open(self.mapping_file, 'rb')
        r = json.loads(f.read())
        f.close()
        print "Rules :", r

        for (father_k, son_k) in r:
            son_type, son_name = son_k
            father_type, father_name = father_k
            print son_name, father_name
            if son_type == 'host' and father_type == 'host':
                son = arb.conf.hosts.find_by_name(son_name)
                father = arb.conf.hosts.find_by_name(father_name)
                if son != None and father != None:
                    print "finded!", son_name, father_name
                    if not son.is_linked_with_host(father):
                        print "Doing simple link between", son.get_name(), 'and', father.get_name()
                        # Add a dep link between the son and the father
                        son.add_host_act_dependancy(father, ['w', 'u', 'd'], None, True)
                else:
                    print "Missing one of", son_name, father_name
