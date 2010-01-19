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


from command import CommandCall
from item import Item, Items
from util import to_split, to_bool

class Contact(Item):
    id = 1#0 is always special in database, so we do not take risk here
    my_type = 'contact'

    properties={'contact_name' : {'required':True, 'status_broker_name' : None},
                'alias' : {'required':False, 'default':'none', 'status_broker_name' : None},
                'contactgroups' : {'required':False, 'default':''},
                'host_notifications_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'service_notifications_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'host_notification_period' : {'required':True},
                'service_notification_period' : {'required':True},
                'host_notification_options' : {'required':True, 'pythonize': to_split},
                'service_notification_options' : {'required':True, 'pythonize': to_split},
                'host_notification_commands' : {'required':True},
                'service_notification_commands' : {'required':True},
                'email' : {'required' : False, 'default':'none', 'status_broker_name' : None},
                'pager' : {'required' : False, 'default':'none', 'status_broker_name' : None},
                'address1' : {'required' : False, 'default':'none'},
                'address2' : {'required' : False, 'default':'none'},
                'address3' : {'required' : False, 'default':'none'},
                'address4' : {'required' : False, 'default':'none'},
                'address5' : {'required' : False, 'default':'none'},
                'address6' : {'required' : False, 'default':'none'},
                'can_submit_commands' : {'required' : False, 'default':'0', 'pythonize': to_bool, 'status_broker_name' : None},
                'retain_status_information' : {'required' : False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'retain_nonstatus_information' : {'required' : False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None}
                }

    running_properties = {}

    
    macros = {
        'CONTACTNAME' : 'contact_name',
        'CONTACTALIAS' : 'alias',
        'CONTACTEMAIL' : 'email',
        'CONTACTPAGER' : 'pager',
        'CONTACTADDRESS1' : 'address1',
        'CONTACTADDRESS2' : 'address2',
        'CONTACTADDRESS3' : 'address3',
        'CONTACTADDRESS4' : 'address4',
        'CONTACTADDRESS5' : 'address5',
        'CONTACTADDRESS6' : 'address6',
        'CONTACTGROUPNAME' : 'get_groupname',
        'CONTACTGROUPNAMES' : 'get_groupnames'
        }


    #For debugging purpose only (nice name)
    def get_name(self):
        return self.contact_name


    #Search for notification_options with state and if t is
    #in service_notification_period
    def want_service_notification(self, t, state, type):
        b = self.service_notification_period.is_time_valid(t)
        if 'n' in self.service_notification_options:
            return False
        t = {'WARNING' : 'w', 'UNKNOWN' : 'u', 'CRITICAL' : 'c',
             'RECOVERY' : 'r', 'FLAPPING' : 'f', 'DOWNTIME' : 's'}
        if type == 'PROBLEM':
            if state in t:
                return b and t[state] in self.service_notification_options
        elif type == 'RECOVERY':
            if type in t:
                return b and t[type] in self.service_notification_options
        elif type == 'ACKNOWLEDGEMENT':
            pass
        elif type == 'FLAPPINGSTART' or type == 'FLAPPINGSTOP' or type == 'FLAPPINGDISABLED':
            pass 
        elif type == 'DOWNTIMESTART' or type == 'DOWNTIMEEND' or 'DOWNTIMECANCELLED':
            pass # later...

        return False


    #Search for notification_options with state and if t is in
    #host_notification_period
    def want_host_notification(self, t, state, type):
        b = self.host_notification_period.is_time_valid(t)
        if 'n' in self.host_notification_options:
            return False
        t = {'DOWN' : 'd', 'UNREACHABLE' : 'u', 'RECOVERY' : 'r',
             'FLAPPING' : 'f', 'DOWNTIME' : 's'}
        if type == 'PROBLEM':
            if state in t:
                return b and t[state] in self.host_notification_options
        elif type == 'RECOVERY':
            if type in t:
                return b and t[type] in self.host_notification_options
        elif type == 'ACKNOWLEDGEMENT':
            pass
        elif type == 'FLAPPINGSTART' or type == 'FLAPPINGSTOP' or type == 'FLAPPINGDISABLED':
            pass 
        elif type == 'DOWNTIMESTART' or type == 'DOWNTIMEEND' or 'DOWNTIMECANCELLED':
            pass # later...

        return False


    def clean(self):
        pass


    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['service_notification_commands', 'service_notification_commands', \
                                  'service_notification_period', 'host_notification_period']
        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    print self.get_name(), " : I do not have", prop
                    state = False #Bad boy...
        #Ok now we manage special cases...
        #Service part
        if not hasattr(self, 'service_notification_commands') :
            print self.get_name()," : do not have any service_notification_commands defined"
            state = False
        else:
            for cmd in self.service_notification_commands:
                if cmd == None:
                    print self.get_name()," : a service_notification_command is missing"
                    state = False
                if not cmd.is_valid():
                    print self.get_name()," : a service_notification_command is invalid", cmd.get_name()
                    state = False
        if not hasattr(self, 'service_notification_period') or self.service_notification_period==None:
            print self.get_name()," : the service_notification_period is invalid"
            state = False

        #Now host part
        if not hasattr(self, 'host_notification_commands') :
            print self.get_name()," : do not have any host_notification_commands defined"
            state = False
        else:
            for cmd in self.host_notification_commands:
                if cmd == None :
                    print self.get_name()," : a host_notification_command is missing"
                    state = False
                if not cmd.is_valid():
                    print self.get_name()," : a host_notification_command is invalid", cmd.get_name(), cmd.__dict__
                    state = False
        if not hasattr(self, 'host_notification_period') or self.host_notification_period==None:
            print self.get_name()," : the host_notification_period is invalid"
            state = False
            
        return state




class Contacts(Items):
    name_property = "contact_name"
    inner_class = Contact

    def linkify(self, timeperiods, commands):
        self.linkify_c_by_tp(timeperiods)
        self.linkify_c_by_cmd(commands)

    
    #We just search for each timeperiod the id of the tp
    #and replace the name by the id
    def linkify_c_by_tp(self, timeperiods):
        for c in self:
            sntp_name = c.service_notification_period
            hntp_name = c.host_notification_period

            #The new member list, in id
            sntp = timeperiods.find_by_name(sntp_name)
            hntp = timeperiods.find_by_name(hntp_name)
            
            c.service_notification_period = sntp
            c.host_notification_period = hntp


    #Simplify hosts commands by commands id
    def linkify_c_by_cmd(self, commands):
        for c in self:
            tmp = []
            for cmd in c.service_notification_commands.split(','):
                tmp.append(CommandCall(commands, cmd))
            c.service_notification_commands = tmp

            tmp = []
            for cmd in c.host_notification_commands.split(','):
                tmp.append(CommandCall(commands, cmd))
            c.host_notification_commands = tmp


    #We look for contacts property in contacts and
    def explode(self, contactgroups):
        #Contactgroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('contactgroups')
        for c in self:
            if not c.is_tpl():
                cname = c.contact_name
                if hasattr(c, 'contactgroups'):
                    cgs = c.contactgroups.split(',')
                    for cg in cgs:
                        contactgroups.add_member(cname, cg.strip())

