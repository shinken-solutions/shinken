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

class Escalation(Item):
    id = 1 #0 is always special in database, so we do not take risk here
    my_type = 'escalation'

    properties={'escalation_name' : {'required' : True},
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
        return self.escalation_name


class Escalations(Items):
    name_property = "escalation_name"
    inner_class = Escalation

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
    def explode(self, contactgroups):
        #We adding all contacts of the contactgroups into the contacts property
        for es in self:
            if hasattr(es, 'contact_groups'):
                cgnames = es.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if hasattr(s, 'contacts'):
                            es.contacts += ','+cnames
                        else:
                            es.contacts = cnames

