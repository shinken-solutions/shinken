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
                'escalation_period' : {'required': False, 'default' : None},
                'escalation_options' : {'required': False, 'default': 'd,u,r,w,c', 'pythonize' : to_split},
                'contacts' : {'required':True},
                'contact_groups' : {'required':True},
                }
    
    running_properties = {}
    
    
    macros = {}
    
    
    #For debugging purpose only (nice name)
    def get_name(self):
        return self.escalation_name


    #Return True if :
    #*time in in escalation_period or we do not have escalation_period
    #*status is in escalation_options
    #*the notification number is in our interval [[first_notification .. last_notification]]
    def is_eligible(self, t, status, notif_number):
        small_states = {'WARNING' : 'w', 'UNKNOWN' : 'u', 'CRITICAL' : 'c',
             'RECOVERY' : 'r', 'FLAPPING' : 'f', 'DOWNTIME' : 's',
             'DOWN' : 'd', 'UNREACHABLE' : 'u', 'OK' : 'o', 'UP' : 'o'}

        print self.get_name(), 'ask for eligible with', status, small_states[status], self.escalation_period.is_time_valid(t), 'level:%d' % notif_number

        #Begin with the easy cases
        if notif_number < self.first_notification:
            print "Bad notif number, too early", self.first_notification
            return False
        
        #self.last_notification = 0 mean no end
        if self.last_notification != 0 and notif_number > self.last_notification:
            print 'notif number too late', self.last_notification
            return False

        if status in small_states and small_states[status] not in self.escalation_options:
            print "Bad status", small_states[status], 'not in', self.escalation_options
            return False
        
        #Maybe the time is not in our escalation_period
        if self.escalation_period != None and not self.escalation_period.is_time_valid(t):
            print "Bad time, no luck"
            return False

        #Ok, I do not see why not escalade. So it's True :)
        return True




class Escalations(Items):
    name_property = "escalation_name"
    inner_class = Escalation

    def linkify(self, timeperiods, contacts, services, hosts):
        self.linkify_es_by_tp(timeperiods)
        self.linkify_es_by_c(contacts)
        self.linkify_es_by_s(services)
        self.linkify_es_by_h(hosts)


    def add_escalation(self, es):
        self.items[es.id] = es

    
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
                contacts_tab = strip_and_uniq(contacts_tab)
                new_contacts = []
                for c_name in contacts_tab:
                    c = contacts.find_by_name(c_name)
                    if c != None:
                        #print "Link with contact", c.get_name()
                        new_contacts.append(c)
                es.contacts = new_contacts
    

    #Will register esclations into service.escalations
    def linkify_es_by_s(self, services):
        for es in self:
            #If no host, no hope of having a service
            if hasattr(es, 'host_name') and es.host_name.strip() != '':
                #Is is an escalation for services?
                if hasattr(es, 'service_description') and es.service_description.strip() != '':
                    snames = es.service_description.split(',')
                    snames = strip_and_uniq(snames)
                    hnames = es.host_name.split(',')
                    hnames = strip_and_uniq(hnames)
                    for hname in hnames:
                        for sname in snames:
                            s = services.find_srv_by_name_and_hostname(hname, sname)
                            if s != None:
                                #print "Linking service", s.get_name(), 'with me', es.get_name()
                                s.escalations.append(es)
                                #print "Now service", s.get_name(), 'have', s.escalations


    #Will rgister escalations into host.escalations
    def linkify_es_by_h(self, hosts):
        for es in self:
            #If no host, no hope of having a service
            if hasattr(es, 'host_name') and es.host_name.strip() != '':
                #I must be NOT a escalati on for service
                if not hasattr(es, 'service_description') or es.service_description.strip() == '':
                    hnames = es.host_name.split(',')
                    hnames = strip_and_uniq(hnames)
                    for hname in hnames:
                        h = hosts.find_by_name(hname)
                        if h != None:
                            #print "Linking host", h.get_name(), 'with me', es.get_name()
                            h.escalations.append(es)
                            #print "Now host", h.get_name(), 'have', h.escalations

    
    #We look for contacts property in contacts and
    def explode(self, hostgroups, contactgroups):
        #We adding all hosts of the hostgroups into the host_name property
        for se in self:
            if hasattr(se, 'hostgroup_name'):
                #print "Exploding hostgroups", se.hostgroup_name
                hgnames = se.hostgroup_name.split(',')
                for hgname in hgnames:
                    hgname = hgname.strip()
                    hnames = hostgroups.get_members_by_name(hgname)
                    #We add hosts in the service host_name
                    if hasattr(se, 'host_name') and hnames != []:
                        se.host_name += ',' + str(hnames)
                    else:
                        se.host_name = str(hnames)
                #print "Finally got: host_name", se.host_name

        #We adding all hosts of the hostgroups into the host_name property
        #because we add the hostgroup one AFTER the host, they are before and 
        #hostgroup one will NOT be created
        for s in self:
            if hasattr(s, 'contact_groups'):
                #print "Exploding Contact groups", s.contact_groups
                cgnames = s.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if hasattr(s, 'contacts'):
                            s.contacts += ','+cnames
                        else:
                            s.contacts = cnames
                #print "Finally got: contacts", se.contacts
        
