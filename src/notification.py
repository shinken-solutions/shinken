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


from pexpect import *
from action import Action
from brok import Brok

class Notification(Action):
    #id = 0
    
    properties={'notification_type' : {'required': False, 'default':0, 'status_broker_name' : None},
                'start_time' : {'required': False, 'default':0, 'status_broker_name' : None},
                'end_time' : {'required': False, 'default':0, 'status_broker_name' : None},
                'contact_name' : {'required': False, 'default':'', 'status_broker_name' : None},
                'host_name' : {'required': False, 'default':'', 'status_broker_name' : None},
                'service_description' : {'required': False, 'default':'', 'status_broker_name' : None},
                'reason_type' : {'required': False, 'default':0, 'status_broker_name' : None},
                'state' : {'required': False, 'default':0, 'status_broker_name' : None},
                'output' : {'required': False, 'default':'', 'status_broker_name' : None},
                'ack_author' : {'required': False, 'default':'', 'status_broker_name' : None},
                'ack_data' : {'required': False, 'default':'', 'status_broker_name' : None},
                'escalated' : {'required': False, 'default':0, 'status_broker_name' : None},
                'contacts_notified' : {'required': False, 'default':0, 'status_broker_name' : None}
                }

    macros = {
        'NOTIFICATIONTYPE' : 'type',
        'NOTIFICATIONRECIPIENTS' : 'recipients',
        'NOTIFICATIONISESCALATED' : 'is_escaladed',
        'NOTIFICATIONAUTHOR' : 'author',
        'NOTIFICATIONAUTHORNAME' : 'author_name',
        'NOTIFICATIONAUTHORALIAS' : 'author_alias',
        'NOTIFICATIONCOMMENT' : 'comment',
        'HOSTNOTIFICATIONNUMBER' : 'number',
        'HOSTNOTIFICATIONID' : 'get_id',
        'SERVICENOTIFICATIONNUMBER' : 'number',
        'SERVICENOTIFICATIONID' : 'get_id'
        }
    
    
    def __init__(self, type , status, command, ref, ref_type, t_to_go, \
                 contact_name='', host_name='', service_description='',
                 reason_type=1, state=0, ack_author='', ack_data='', escalated=0, contacts_notified=0,
                 start_time=0, end_time=0, notification_type=0):
        self.is_a = 'notification'
        self.type = type

        self.id = Action.id
        Action.id += 1

        self._in_timeout = False
        self.status = status
        self.exit_status = 3
        self._command = command
        self.output = None
        self.ref = ref
        self.ref_type = ref_type
        self.t_to_go = t_to_go
        
        #For brok
        self.contact_name = contact_name
        self.host_name = host_name
        self.service_description = service_description
        self.reason_type = reason_type
        self.state = state
        self.ack_author = ack_author
        self.ack_data = ack_data
        self.escalated = escalated
        self.contacts_notified = contacts_notified
        self.start_time = start_time
        self.end_time = end_time
        self.notification_type = notification_type
    
    def execute(self):
        print "Notification %s" % self._command
        child = spawn ('/bin/sh -c "%s"' % self._command)
        self.status = 'lanched'
        
        try:
            child.expect_exact(EOF, timeout=5)
            self.output = child.before
            child.terminate(force=True)
            self.exit_status = child.exitstatus
            #if self.exit_status != 0:
            #    print " ********************** DANGER DANGER DANGER !!!!!!!!! *********** %d" % self.exit_status
            #print "Exit status:", child.exitstatus
            self.status = 'done'
        except TIMEOUT:
            print "On le kill"
            self.status = 'timeout'
            child.terminate(force=True)


    def is_launchable(self, t):
        #print "Is_launchable?",t, self.t_to_go
        return t > self.t_to_go

    
    def set_status(self, status):
        self.status = status


    def get_status(self):
        return self.status

    
    def get_output(self):
        return self.output

    
    def __str__(self):
        return ''#str(self.__dict__)


    def get_id(self):
        return self.id

    
    #Fill data with info of item by looking at brok_type
    #in props of properties or running_propterties
    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        #Now config properties
        for prop in cls.properties:
            if brok_type in cls.properties[prop]:
                broker_name = cls.properties[prop][brok_type]
                if broker_name is None:
                    data[prop] = getattr(self, prop)
                else:
                    data[broker_name] = getattr(self, prop)


    #Get a brok with initial status
    def get_initial_status_brok(self):
        data = {'id' : self.id}
        
        self.fill_data_brok_from(data, 'status_broker_name')
        b = Brok('notification_raise', data)
        return b


