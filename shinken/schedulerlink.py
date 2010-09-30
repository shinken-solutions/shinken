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


#Scheduler is like a satellite for dispatcher
from satellitelink import SatelliteLink, SatelliteLinks
from util import to_int, to_bool, to_split
from item import Items

class SchedulerLink(SatelliteLink):
    id = 0
    
    #Ok we lie a little here because we are a mere link in fact
    my_type = 'scheduler'
    
    properties={'scheduler_name' : {'required' : True , 'fill_brok' : ['full_status']},#, 'pythonize': None},
                'address' : {'required' : True, 'fill_brok' : ['full_status']},#, 'pythonize': to_bool},
                'port' : {'required':  False, 'default' : '7768', 'pythonize': to_int, 'fill_brok' : ['full_status']},
                'spare' : {'required':  False, 'default' : '0', 'pythonize': to_bool, 'fill_brok' : ['full_status']},
                'modules' : {'required' : False, 'default' : '', 'pythonize' : to_split},
                'weight': {'required':  False, 'default' : '1', 'pythonize': to_int, 'fill_brok' : ['full_status']},
                'manage_arbiters' : {'required' : False, 'default' : '0', 'pythonize' : to_int},
                'use_timezone' : {'required' : False, 'default' : 'NOTSET'},
                }
 
    running_properties = {'con' : {'default' : None},
                          'alive' : {'default' : False, 'fill_brok' : ['full_status']},
                          'conf' : {'default' : None},
                          'need_conf' : {'default' : True},
                          'broks' : {'default' : []},
                          }
    macros = {}


    def get_name(self):
        return self.scheduler_name


    def run_external_command(self, command):
        if self.con == None:
            self.create_connexion()
        if not self.alive:
            return None
        print "Send command", command
        self.con.run_external_command(command)


    def register_to_my_realm(self):
        self.realm.schedulers.append(self)


    def give_satellite_cfg(self):
        return {'port' : self.port, 'address' : self.address, 'name' : self.scheduler_name, 'instance_id' : self.id, 'active' : self.conf!=None}

class SchedulerLinks(SatelliteLinks):
    name_property = "name"
    inner_class = SchedulerLink

