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


#Scheduler is like a satellite for dispatcher
from shinken.satellitelink import SatelliteLink, SatelliteLinks
from shinken.property import BoolProp, IntegerProp, StringProp, ListProp

from shinken.pyro_wrapper import Pyro


class SchedulerLink(SatelliteLink):
    id = 0

    #Ok we lie a little here because we are a mere link in fact
    my_type = 'scheduler'

    properties = {
        'scheduler_name':   StringProp(fill_brok=['full_status']),
        'address':          StringProp(fill_brok=['full_status']),
        'port':             IntegerProp(default='7768', fill_brok=['full_status']),
        'spare':            BoolProp(default='0', fill_brok=['full_status']),
        'modules':          ListProp(default=''),
        'weight':           IntegerProp(default='1', fill_brok=['full_status']),
        'manage_arbiters':  IntegerProp(default='0'),
        'use_timezone':     StringProp(default='NOTSET', override=True),
        'timeout':          IntegerProp(default='3', fill_brok=['full_status']),
        'data_timeout':     IntegerProp(default='120', fill_brok=['full_status']),
        'max_check_attempts': IntegerProp(default='3', fill_brok=['full_status']),
        'realm' :           StringProp(default=''),
    }
    
    running_properties = {
        'con':       StringProp(default=None),
        'alive':     StringProp(default=True, fill_brok=['full_status']), # DEAD or not
        'attempt':   StringProp(default=0, fill_brok=['full_status']), # the number of failed attempt
        'reachable': StringProp(default=False, fill_brok=['full_status']), # can be network ask or not (dead or check in timeout or error)
        'conf':      StringProp(default=None),
        'need_conf': StringProp(default=True),
        'broks':     StringProp(default=[]),
        'configuration_errors' : StringProp(default=[]),
    }
    
    macros = {}


    def get_name(self):
        return self.scheduler_name


    def run_external_command(self, command):
        if self.con is None:
            self.create_connexion()
        if not self.alive:
            return None
        print "Send command", command
        try:
            self.con.run_external_command(command)
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



    def register_to_my_realm(self):
        self.realm.schedulers.append(self)


    def give_satellite_cfg(self):
        return {'port' : self.port, 'address' : self.address, 'name' : self.scheduler_name, 'instance_id' : self.id, 'active' : self.confis notNone}


    #Some parameters can give as 'overriden parameters' like use_timezone
    #so they will be mixed (in the scheduler) with the standard conf send by the arbiter
    def get_override_configuration(self):
        r = {}
        properties = self.__class__.properties
        for prop in properties:
            entry = properties[prop]
            if entry.override:
                r[prop] = getattr(self, prop)
        return r

class SchedulerLinks(SatelliteLinks):
    name_property = "scheduler_name"
    inner_class = SchedulerLink
