#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

from shinken.satellitelink import SatelliteLink, SatelliteLinks
from shinken.property import BoolProp, IntegerProp, StringProp, ListProp
import shinken.pyro_wrapper as pyro
Pyro = pyro.Pyro

from shinken.log import logger

class ArbiterLink(SatelliteLink):
    id = 0
    my_type = 'arbiter'
    properties = SatelliteLink.properties.copy()
    properties.update({
        'arbiter_name':    StringProp(),
        'host_name':       StringProp(default=socket.gethostname()),
        'port':            IntegerProp(default='7770'),
    })

    def get_name(self):
        return self.arbiter_name


    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        for prop, entry in cls.properties.items():
            if not hasattr(self, prop) and entry.required:
                print self.get_name(), " : I do not have", prop
                state = False #Bad boy...
        return state


    def is_me(self):
        logger.log("And arbiter is launched with the hostname:%s of addr :%s" % (self.host_name, socket.gethostname()), print_it=False)
        return self.host_name == socket.gethostname()


    def give_satellite_cfg(self):
        return {'port' : self.port, 'address' : self.address, 'name' : self.arbiter_name}


    def do_not_run(self):
        if self.con is None:
            self.create_connection()
        try:
            self.con.do_not_run()
            return True
        except Pyro.errors.URIError , exp:
            self.con = None
            return False
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return False

    def get_satellite_list(self, daemon_type):
        if self.con is None:
            self.create_connection()
        try:
            r = self.con.get_satellite_list(daemon_type)
            return r
        except Pyro.errors.URIError , exp:
            self.con = None
            return []
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return []

    def get_satellite_status(self, daemon_type, name):
        if self.con is None:
            self.create_connection()
        try:
            r = self.con.get_satellite_status(daemon_type, name)
            return r
        except Pyro.errors.URIError , exp:
            self.con = None
            return {}
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return {}


    def get_all_states(self):
        if self.con is None:
            self.create_connection()
        try:
            r = self.con.get_all_states()
            return r
        except Pyro.errors.URIError , exp:
            self.con = None
            return None
        except Pyro.errors.ProtocolError , exp:
            self.con = None
            return None




class ArbiterLinks(SatelliteLinks):
    name_property = "name"
    inner_class = ArbiterLink


    #We must have a realm property, so we find our realm
    def linkify(self, modules):
        self.linkify_s_by_plug(modules)


