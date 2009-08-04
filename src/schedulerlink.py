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


import Pyro.core

from item import Item, Items
from util import to_int, to_char, to_split, to_bool

class SchedulerLink(Item):
    id = 0
    properties={'name' : {'required' : True },#, 'pythonize': None},
                'address' : {'required' : True},#, 'pythonize': to_bool},
                'port' : {'required':  True, 'pythonize': to_int},
                'spare' : {'required':  False, 'default' : '0', 'pythonize': to_bool},
                }
 
    running_properties = {'is_active' : False,
                          'con' : None
                          #self.is_alive = False
                          }
    macros = {}


    def clean(self):
        pass


    def create_connexion(self):
        self.uri = "PYROLOC://"+self.address+":"+str(self.port)+"/ForArbiter"
        self.con = Pyro.core.getProxyForURI(self.uri)


    def put_conf(self, conf):
        if self.con == None:
            self.create_connexion()

        self.con.put_conf(conf)

    def run_external_command(self, command):
        if self.con == None:
            self.create_connexion()
        if not self.is_alive():
            return None
        self.con.run_external_command(command)


    def is_alive(self):
        print "Trying to see if ", self.address+":"+str(self.port), "is alive"
        try:
            if self.con == None:
                self.create_connexion()
            self.con.ping()
            return True
        except Pyro.errors.URIError as exp:
            print exp
            return False
        except Pyro.errors.ProtocolError as exp:
            print exp
            return False


class SchedulerLinks(Items):
    name_property = "name"
    inner_class = SchedulerLink

#    def find_spare
#    def sort(self, f):
#        self.items.sort(f)
