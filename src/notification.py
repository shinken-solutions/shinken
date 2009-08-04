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

class Notification(Action):
    #id = 0
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
    
    
    def __init__(self, type , status, command, ref, ref_type, t_to_go):
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
