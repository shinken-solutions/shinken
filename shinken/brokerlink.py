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


from satellitelink import SatelliteLink, SatelliteLinks
from util import to_int, to_bool, to_split
from item import Items

class BrokerLink(SatelliteLink):
    id = 0
    my_type = 'broker'
    properties={'broker_name' : {'required' : True },
                'address' : {'required' : True},
                'port' : {'required':  False, 'default': '7772', 'pythonize': to_int},
                'spare' : {'required':  False, 'default' : '0', 'pythonize': to_bool},
                'manage_sub_realms' : {'required':  False, 'default' : '1', 'pythonize': to_bool},
                'manage_arbiters' : {'required':  False, 'default' : '0', 'pythonize': to_bool, 'to_send' : True},
                'modules' : {'required':  False, 'default' : '', 'pythonize' : to_split, 'to_send' : True},
                'polling_interval': {'required':  False, 'default' : '1', 'pythonize': to_int, 'to_send' : True},
                }
 
    running_properties = {'con' : {'default' : None},
                          'alive' : {'default' : False, 'fill_brok' : ['full_status']}
                          }
    macros = {}

    def get_name(self):
        return self.broker_name


    def register_to_my_realm(self):
        self.realm.brokers.append(self)




class BrokerLinks(SatelliteLinks):
    name_property = "name"
    inner_class = BrokerLink

    
