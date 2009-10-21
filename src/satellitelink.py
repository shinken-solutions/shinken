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


#SatelliteLink is a common Class for link to satellite for
#Arbiter with Conf Dispatcher.


import Pyro.core

from item import Item, Items
from util import to_int, to_bool

class SatelliteLink(Item):
    #id = 0 each Class will have it's own id
    #properties={'name' : {'required' : True },#, 'pythonize': None},
    #            'address' : {'required' : True},#, 'pythonize': to_bool},
    #            'port' : {'required':  True, 'pythonize': to_int},
    #            'spare' : {'required':  False, 'default' : '0', 'pythonize': to_bool},
    #            }
 
    #running_properties = {'is_active' : {'default' : False},
    #                      'con' : {'default' : None}
    #                      #self.is_alive = False
    #                      }
    #macros = {}


    #Clean? Really?
    def clean(self):
        pass


    def create_connexion(self):
        self.uri = "PYROLOC://"+self.address+":"+str(self.port)+"/ForArbiter"
        self.con = Pyro.core.getProxyForURI(self.uri)
        #Ok, set timeout to 5 sec
        self.con._setTimeout(5)


    def put_conf(self, conf):
        if self.con == None:
            self.create_connexion()
        #print "Connexion is OK, now we put conf", conf
            
        try:
            self.con.put_conf(conf)
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            #print self.name, "FUCK !!!!!!!!!!!!", exp
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            #print self.name, "FUCK !!!!!!!!!!!!", exp
            return False


    def is_alive(self):
        #print "Trying to see if ", self.address+":"+str(self.port), "is alive"
        try:
            if self.con == None:
                self.create_connexion()
            self.con.ping()
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            print exp
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            print exp
            return False


    def wait_new_conf(self):
        if self.con == None:
            self.create_connexion()
        #print "Connexion is OK, now we put conf", conf
            
        try:
            self.con.wait_new_conf()
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            #print self.name, "FUCK !!!!!!!!!!!!", exp
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            #print self.name, "FUCK !!!!!!!!!!!!", exp
            return False

    def have_conf(self):
        if self.con == None:
            self.create_connexion()
        #print "Connexion is OK, now we put conf", conf
            
        try:
            return self.con.have_conf()
        except Pyro.errors.URIError as exp:
            self.con = None
            #print self.name, "FUCK !!!!!!!!!!!!", exp
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            #print self.name, "FUCK !!!!!!!!!!!!", exp
            return False

