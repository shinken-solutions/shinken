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


#SatelliteLink is a common Class for link to satellite for
#Arbiter with Conf Dispatcher.


import shinken.pyro_wrapper
Pyro = shinken.pyro_wrapper.Pyro


from item import Item, Items
from util import to_int, to_bool

class SatelliteLink(Item):
    #id = 0 each Class will have it's own id
    #properties={'name' : {'required' : True },#, 'pythonize': None},
    #            'address' : {'required' : True},#, 'pythonize': to_bool},
    #            'port' : {'required':  True, 'pythonize': to_int},
    #            'spare' : {'required':  False, 'default' : '0', 'pythonize': to_bool},
    #            }
 
    #running_properties = {
    #                      'con' : {'default' : None}
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
        #URI are differents between 3 and 4
        if shinken.pyro_wrapper.pyro_version == 3:
            self.uri = 'PYROLOC://'+self.address+":"+str(self.port)+"/ForArbiter"
            self.con = Pyro.core.getProxyForURI(self.uri)            
            #Ok, set timeout to 5 sec
            self.con._setTimeout(5)
        else:
            self.uri = 'PYRO:ForArbiter@'+self.address+":"+str(self.port)
            self.con = Pyro.core.Proxy(self.uri)
            self.con._pyroTimeout = 5


    def put_conf(self, conf):
        if self.con == None:
            self.create_connexion()
        #print "Connexion is OK, now we put conf", conf
        #print "Try to put conf:", conf
        try:
            #Still fun with pyro 3 and 4...
            if shinken.pyro_wrapper.pyro_version == 3:
                self.con._setTimeout(120)
                self.con.put_conf(conf)
                self.con._setTimeout(5)
                return True
            else:
                self.con._pyroTimeout = 120
                self.con.put_conf(conf)
                self.con._pyroTimeout = 5
                return True
        except Pyro.errors.URIError , exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return False
        except TypeError , exp:
            print ''.join(Pyro.util.getPyroTraceback(exp))
        except Pyro.errors.CommunicationError , exp:
            self.con = None
            return False


    #Get and clean all of our broks
    def get_all_broks(self):
        res = self.broks
        self.broks = []
        return res


    def set_alive(self):
        was_alive = self.alive
        self.alive = True

        #We came from dead to alive
        #so we must add a brok update
        if not was_alive:
            b = self.get_update_status_brok()
            self.broks.append(b)


    def set_dead(self):
        was_alive = self.alive
        self.alive = False
        self.con = None

        #We are dead now. Must raise
        #a brok to say it
        if was_alive:
            b = self.get_update_status_brok()
            self.broks.append(b)



    def ping(self):
        try:
            if self.con == None:
                self.create_connexion()
            self.con.ping()
            self.set_alive()
        except Pyro.errors.ProtocolError , exp:
            self.set_dead()
        except Pyro.errors.URIError , exp:
            print exp
            self.set_dead()
        #Only pyro 4 but will be ProtocolError in 3
        except Pyro.errors.CommunicationError , exp:
            #print "Is not alive!", self.uri
            self.set_dead()
        except Pyro.errors.DaemonError , exp:
            print exp
            self.set_dead()


    def wait_new_conf(self):
        if self.con == None:
            self.create_connexion()
        try:
            self.con.wait_new_conf()
            return True
        except Pyro.errors.URIError , exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return False


    #To know if the satellite have a conf (magic_hash = None)
    #OR to know if the satellite have THIS conf (magic_hash != None)
    def have_conf(self, magic_hash=None):
        if self.con == None:
            self.create_connexion()
            
        try:
            if magic_hash == None:
                return self.con.have_conf()
            else:
                return self.con.have_conf(magic_hash)
        except Pyro.errors.URIError , exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return False


    def remove_from_conf(self, sched_id):
        if self.con == None:
            self.create_connexion()
        try:
            self.con.remove_from_conf(sched_id)
            return True
        except Pyro.errors.URIError , exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return False

    def what_i_managed(self):
        if self.con == None:
            self.create_connexion()
        try:
            return self.con.what_i_managed()
        except Pyro.errors.URIError , exp:
            self.con = None
            return []
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return []


    def push_broks(self, broks):
        if self.con == None:
            self.create_connexion()
        try:
            return self.con.push_broks(broks)
        except Pyro.errors.URIError , exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return False
        except AttributeError , exp:
            print exp
            return False


    def get_external_commands(self):
        if self.con == None:
            self.create_connexion()
        try:
            return self.con.get_external_commands()
        except Pyro.errors.URIError , exp:
            self.con = None
            return []
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return []
        except AttributeError , exp:
            print exp
            return []



    def prepare_for_conf(self):
        self.cfg = { 'global' : {}, 'schedulers' : {}, 'arbiters' : {}}
        #cfg_for_satellite['modules'] = satellite.modules
        properties = self.__class__.properties
        for prop in properties:
            if 'to_send' in properties[prop] and properties[prop]['to_send']:
                self.cfg['global'][prop] = getattr(self, prop)

    #Some parameters for satellites are not defined in the satellites conf
    #but in the global configuration. We can pass them in the global
    #property
    def add_global_conf_parameters(self, params):
        for prop in params:
            print "Add global parameter", prop, params[prop]
            self.cfg['global'][prop] = params[prop]


    def get_my_type(self):
        return self.__class__.my_type


    #Here for poller and reactionner. Scheduler have it's own function
    def give_satellite_cfg(self):
        return {'port' : self.port, 'address' : self.address, 'name' : self.get_name(), 'instance_id' : self.id, 'active' : True}



class SatelliteLinks(Items):
    #name_property = "name"
    #inner_class = SchedulerLink

    #We must have a realm property, so we find our realm
    def linkify(self, realms, modules):
        self.linkify_s_by_p(realms)
        self.linkify_s_by_plug(modules)

        
    def linkify_s_by_p(self, realms):
        for s in self:
            p_name = s.realm.strip()
            p = realms.find_by_name(p_name)
            s.realm = p
            if p is not None:
                print "Me", s.get_name(), "is linked with realm", s.realm.get_name()
                s.register_to_my_realm()


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

