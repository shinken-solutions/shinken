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

from item import Item, Items
from util import to_int, to_char, to_split, to_bool, strip_and_uniq
from escalation import Escalation

class Hostescalation(Item):
    id = 1 #0 is always special in database, so we do not take risk here
    my_type = 'serviceescalation'

    properties={'host_name' : {'required' : True},
                'hostgroup_name' : {'required' : True},
                'first_notification' : {'required' : True, 'pythonize' : to_int},
                'last_notification' : {'required': True, 'pythonize' : to_int},
                'notification_interval' : {'required' : True, 'pythonize' : to_int},
                'escalation_period' : {'required': False},
                'escalation_options' : {'required': False, 'default': 'd,u,r,w,c', 'pythonize' : to_split},
                'contacts' : {'required':True},
                'contact_groups' : {'required':True},
                }
    
    running_properties = {}
    
    
    macros = {}
    
    
    #For debugging purpose only (nice name)
    def get_name(self):
        return ''


class Hostescalations(Items):
    name_property = ""
    inner_class = Hostescalation

            
    #We look for contacts property in contacts and
    def explode(self, escalations):
        #Now we explode all escalations (host_name, service_description) to escalations
        for es in self:
            properties = es.__class__.properties            
            creation_dict = {'escalation_name' : 'Generated-Hostescalation-%d' % es.id}
            for prop in properties:
                if hasattr(es, prop):
                    creation_dict[prop] = getattr(es, prop)
            s = Escalation(creation_dict)
            escalations.add_escalation(s)

        print "All escalations"
        for es in escalations:
            print es
