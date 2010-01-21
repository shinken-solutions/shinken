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

    def linkify(self, timeperiods, contacts):
        self.linkify_es_by_tp(timeperiods)
        self.linkify_es_by_c(contacts)
    
    #We just search for each timeperiod the tp
    #and replace the name by the tp
    def linkify_es_by_tp(self, timeperiods):
        for es in self:
            tp_name = es.escalation_period

            #The new member list, in id
            tp = timeperiods.find_by_name(tp_name)
            
            es.escalation_period = tp

    #Make link between escalation and it's contacts
    def linkify_es_by_c(self, contacts):
        for es in self:
            if hasattr(es, 'contacts'):
                contacts_tab = es.contacts.split(',')
                new_contacts = []
                for c_name in contacts_tab:
                    c_name = c_name.strip()
                    c = contacts.find_by_name(c_name)
                    new_contacts.append(c)
                es.contacts = new_contacts

            
    #We look for contacts property in contacts and
    def explode(self, escalations):
        #Now we explode all escalations (host_name, service_description) to escalations
        for es in self:
            properties = es.__class__.properties            
            creation_dict = {'escalation_name' : 'Generated-Hostescalation-%d' % es.id}
            for prop in properties:
                if hasattr(es, prop):
                    creation_dict[prop] = getattr(es, prop)
            #print "Creation an escalation with :", creation_dict
            s = Escalation(creation_dict)
            escalations.add_escalation(s)

