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


    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['realm']
        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    print self.get_name(), " : I do not have", prop
                    state = False #Bad boy...
        #Ok now we manage special cases...
        if not hasattr(self, 'realm') or  hasattr(self, 'realm') and self.realm == None:
            print self.get_name()," : I do not have a valid realm"
            state = False
        return state



    def create_connexion(self):
        self.uri = "PYROLOC://"+self.address+":"+str(self.port)+"/ForArbiter"
        self.con = Pyro.core.getProxyForURI(self.uri)
        #Ok, set timeout to 5 sec
        self.con._setTimeout(60)


    def put_conf(self, conf):
        if self.con == None:
            self.create_connexion()
        #print "Connexion is OK, now we put conf", conf
            
        try:
            self.con.put_conf(conf)
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            return False


    def is_alive(self):
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
        try:
            self.con.wait_new_conf()
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            return False

    def have_conf(self):
        if self.con == None:
            self.create_connexion()
            
        try:
            return self.con.have_conf()
        except Pyro.errors.URIError as exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            return False

    def remove_from_conf(self, sched_id):
        if self.con == None:
            self.create_connexion()
        try:
            self.con.remove_from_conf(sched_id)
            return True
        except Pyro.errors.URIError as exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            return False

    def what_i_managed(self):
        if self.con == None:
            self.create_connexion()
        try:
            return self.con.what_i_managed()
        except Pyro.errors.URIError as exp:
            self.con = None
            return []
        except Pyro.errors.ProtocolError as exp:
            self.con = None
            return []


    def prepare_for_conf(self):
        self.cfg = {'schedulers' : {}} #i : {'port' : sched.port, 'address' : sched.address, 'name' : sched.name, 'instance_id' : sched.id, 'active' : sched.conf!=None}


    def get_my_type(self):
        return self.__class__.my_type


class SatelliteLinks(Items):
    #name_property = "name"
    #inner_class = SchedulerLink

    #We must have a realm property, so we find our realm
    def linkify(self, realms, plugins):
        self.linkify_s_by_p(realms)
        self.linkify_s_by_plug(plugins)

        
    def linkify_s_by_p(self, realms):
        for s in self:
            p_name = s.realm.strip()
            p = realms.find_by_name(p_name)
            s.realm = p
            if p is not None:
                print "Me", s.get_name(), "is linked with realm", s.realm.get_name()
                s.register_to_my_realm()


    def linkify_s_by_plug(self, plugins):
        for s in self:
            new_plugins = []
            for plug_name in s.plugins:
                plug = plugins.find_by_name(plug_name.strip())
                if plug != None:
                    new_plugins.append(plug)
                else:
                    print "Error : the plugin %s is unknow for %s" % (plug_name, s.get_name())
            s.plugins = new_plugins

