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

import socket

from satellitelink import SatelliteLink, SatelliteLinks
from util import to_int, to_bool, to_split
from item import Items

class ArbiterLink(SatelliteLink):
    id = 0
    my_type = 'arbiter'
    properties={'arbiter_name' : {'required' : True },
                'host_name' : {'required' : True},
                'address' : {'required' : True},
                'port' : {'required':  False, 'default' : '7770', 'pythonize': to_int},
                'spare' : {'required':  False, 'default' : '0', 'pythonize': to_bool},
#                'manage_sub_realms' : {'required':  False, 'default' : '1', 'pythonize': to_bool},
#                'manage_arbiter' : {'required':  False, 'default' : '0', 'pythonize': to_bool},
                'modules' : {'required':  False, 'default' : '', 'pythonize' : to_split, 'to_send' : True},
#                'polling_interval': {'required':  False, 'default' : '1', 'pythonize': to_int, 'to_send' : True},
                'manage_arbiters' : {'required' : False, 'default' : '0', 'pythonize' : to_int},
                }
 
    running_properties = {'is_active' : {'default' : False},
                          'con' : {'default' : None},
                          }

    macros = {}
    
    
    def get_name(self):
        return self.arbiter_name
    

    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        for prop in cls.properties:
            if not hasattr(self, prop) and cls.properties[prop]['required']:
                print self.get_name(), " : I do not have", prop
                state = False #Bad boy...
        return state

    
    def is_me(self):
        print "Hostname:%s, gethostname:%s" % (self.host_name, socket.gethostname())
        return self.host_name == socket.gethostname()
    
    
    def give_satellite_cfg(self):
        return {'port' : self.port, 'address' : self.address, 'name' : self.arbiter_name}


    def do_not_run(self):
        if self.con == None:
            self.create_connexion()
        try:
            self.con.do_not_run()
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            return False



class ArbiterLinks(SatelliteLinks):
    name_property = "name"
    inner_class = ArbiterLink

    
    #We must have a realm property, so we find our realm
    def linkify(self, modules):
        self.linkify_s_by_plug(modules)
 

    def linkify_s_by_plug(self, modules):
        for s in self:
            new_modules = []
            for plug_name in s.modules:
                plug = modules.find_by_name(plug_name.strip())
                if plug != None:
                    new_modules.append(plug)
                else:
                    print "Error : the module %s is unknow for %s" % (plug_name, s.get_name())
            s.modules = new_modules

