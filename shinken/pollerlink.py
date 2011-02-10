#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
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


#This class is the link between Arbiter and Poller. With It, arbiter
#can see if a poller is alive, and can send it new configuration

from shinken.satellitelink import SatelliteLink, SatelliteLinks
from shinken.util import to_int, to_bool, to_split
from shinken.property import UnusedProp, BoolProp, IntegerProp, FloatProp, CharProp, StringProp, ListProp

class PollerLink(SatelliteLink):
    id = 0
    my_type = 'poller'
    #To_send : send or not to satellite conf
    properties = {
        'poller_name':  StringProp(fill_brok=['full_status'], to_send=True),
        'address':      StringProp(fill_brok=['full_status']),
        'port':         IntegerProp(default=7771, fill_brok=['full_status']),
        'spare':        BoolProp(default='0', fill_brok=['full_status']),
        'passive' :     BoolProp(default='0', fill_brok=['full_status']),
        'manage_sub_realms': BoolProp(default='0', fill_brok=['full_status']),
        'modules':      ListProp(default='', to_send=True),
        'min_workers':  IntegerProp(default='1', fill_brok=['full_status'], to_send=True),
        'max_workers':  IntegerProp(default='30', fill_brok=['full_status'], to_send=True),
        'processes_by_worker': IntegerProp(default='256', fill_brok=['full_status'], to_send=True),
        'polling_interval': IntegerProp(default='1', fill_brok=['full_status'], to_send=True),
        'manage_arbiters': IntegerProp(default='0'),
        'poller_tags':  ListProp(default='', to_send=True),
        'use_timezone': StringProp(default='NOTSET', to_send=True),
        'timeout':      IntegerProp(default='3', fill_brok=['full_status']),
        'data_timeout': IntegerProp(default='120', fill_brok=['full_status']),
        'max_check_attempts': IntegerProp(default='3', fill_brok=['full_status']),
        'realm' :       StringProp(default=''),
    }

    running_properties = {
        'con':       StringProp(default=None),
        'alive':     StringProp(default=True, fill_brok=['full_status'], to_send=True),
        'broks':     StringProp(default=[]),
        'attempt':   StringProp(default=0, fill_brok=['full_status']), # the number of failed attempt
        'reachable': StringProp(default=False, fill_brok=['full_status']), # can be network ask or not (dead or check in timeout or error)
        'configuration_errors': StringProp(default=[]),
    }
    macros = {}

    def get_name(self):
        return self.poller_name


    def register_to_my_realm(self):
        self.realm.pollers.append(self)
        if self.poller_tags != []:
            print "I %s manage tags : %s " % (self.get_name(), self.poller_tags)

class PollerLinks(SatelliteLinks):
    name_property = "poller_name"
    inner_class = PollerLink
