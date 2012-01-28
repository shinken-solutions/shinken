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


from item import Item, Items

from shinken.property import BoolProp, IntegerProp, StringProp, ListProp


_special_properties = ( 'service_notification_commands', 'host_notification_commands',
                        'service_notification_period', 'host_notification_period' )


class NotificationWay(Item):
    id = 1#0 is always special in database, so we do not take risk here
    my_type = 'notificationway'

    properties = Item.properties.copy()
    properties.update({
        'notificationway_name':         StringProp (fill_brok=['full_status']),
        'host_notifications_enabled':   BoolProp   (default='1', fill_brok=['full_status']),
        'service_notifications_enabled':BoolProp   (default='1', fill_brok=['full_status']),
        'host_notification_period':     StringProp (fill_brok=['full_status']),
        'service_notification_period':  StringProp (fill_brok=['full_status']),
        'host_notification_options':    ListProp   (fill_brok=['full_status']),
        'service_notification_options': ListProp   (fill_brok=['full_status']),
        'host_notification_commands':   StringProp (fill_brok=['full_status']),
        'service_notification_commands':StringProp (fill_brok=['full_status']),
        'min_business_impact':                IntegerProp(default = '0', fill_brok=['full_status']),
    })
    
    running_properties = Item.running_properties.copy()

    # This tab is used to transform old parameters name into new ones
    # so from Nagios2 format, to Nagios3 ones.
    # Or Shinken deprecated names like criticity
    old_properties = {
        'min_criticity'            :    'min_business_impact',
    }


    macros = {}

    #For debugging purpose only (nice name)
    def get_name(self):
        return self.notificationway_name


    #Search for notification_options with state and if t is
    #in service_notification_period
    def want_service_notification(self, t, state, type, business_impact, cmd=None):
        if not self.service_notifications_enabled:
            return False

        # Maybe the command we ask for are not for us, but for another notification ways
        # on the same contact. If so, bail out
        if cmd and not cmd in self.service_notification_commands:
            return False

        # If the business_impact is not high enough, we bail out
        if business_impact < self.min_business_impact:
            return False

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
            return b
        elif type in ('FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            return b and 'f' in self.service_notification_options
        elif type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED'):
            #No notification when a downtime was cancelled. Is that true??
            # According to the documentation we need to look at _host_ options
            return b and 's' in self.host_notification_options

        return False


    #Search for notification_options with state and if t is in
    #host_notification_period
    def want_host_notification(self, t, state, type, business_impact, cmd=None):
        if not self.host_notifications_enabled:
            return False

        # If the business_impact is not high enough, we bail out
        if business_impact < self.min_business_impact:
            return False

        # Maybe the command we ask for are not for us, but for another notification ways
        # on the same contact. If so, bail out
        if cmd and not cmd in self.host_notification_commands:
            return False

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
            return b
        elif type in ('FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            return b and 'f' in self.host_notification_options
        elif type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED'):
            return b and 's' in self.host_notification_options

        return False


    #Call to get our commands to launch a Notification
    def get_notification_commands(self, type):
        #service_notification_commands for service
        notif_commands_prop = type+'_notification_commands'
        notif_commands = getattr(self, notif_commands_prop)
        return notif_commands



    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        #A null notif way is a notif way that will do nothing (service = n, hot =n)
        is_null_notifway = False
        if hasattr(self, 'service_notification_options') and self.service_notification_options==['n']:
            if hasattr(self, 'host_notification_options') and self.host_notification_options==['n']:
                is_null_notifway = True
                return True

        for prop, entry in cls.properties.items():
            if prop not in _special_properties:
                if not hasattr(self, prop) and entry.required:
                    print self.get_name(), " : I do not have", prop
                    state = False #Bad boy...

        #Ok now we manage special cases...
        #Service part
        if not hasattr(self, 'service_notification_commands') :
            print self.get_name()," : do not have any service_notification_commands defined"
            state = False
        else:
            for cmd in self.service_notification_commands:
                if cmd is None:
                    print self.get_name()," : a service_notification_command is missing"
                    state = False
                if not cmd.is_valid():
                    print self.get_name()," : a service_notification_command is invalid", cmd.get_name()
                    state = False
        
        if getattr(self, 'service_notification_period', None) is None:
            print self.get_name()," : the service_notification_period is invalid"
            state = False

        #Now host part
        if not hasattr(self, 'host_notification_commands') :
            print self.get_name()," : do not have any host_notification_commands defined"
            state = False
        else:
            for cmd in self.host_notification_commands:
                if cmd is None :
                    print self.get_name()," : a host_notification_command is missing"
                    state = False
                if not cmd.is_valid():
                    print self.get_name()," : a host_notification_command is invalid", cmd.get_name(), cmd.__dict__
                    state = False

        if getattr(self, 'host_notification_period', None) is None:
            print self.get_name()," : the host_notification_period is invalid"
            state = False

        return state




class NotificationWays(Items):
    name_property = "notificationway_name"
    inner_class = NotificationWay

    def linkify(self, timeperiods, commands):
        self.linkify_with_timeperiods(timeperiods, 'service_notification_period')
        self.linkify_with_timeperiods(timeperiods, 'host_notification_period')
        self.linkify_command_list_with_commands(commands, 'service_notification_commands')
        self.linkify_command_list_with_commands(commands, 'host_notification_commands')


    def new_inner_member(self, name=None, params={}):
        if name is None:
            name = NotificationWay.id
        params['notificationway_name'] = name
        #print "Asking a new inner notificationway from name %s with params %s" % (name, params)
        nw = NotificationWay(params)
        self.items[nw.id] = nw
