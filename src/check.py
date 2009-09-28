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

import time

from pexpect import *
from action import Action


class Check(Action):
    __slots__ = ('id', 'is_a', 'type', '_in_timeout', 'status', 'exit_status',\
                  '_command', 'output', 'long_output', 'ref', 'ref_type', \
                     't_to_go', 'depend_on', 'depend_on_me', 'check_time', \
                     'execution_time')
    #id = 0 #Is common to Actions
    def __init__(self, status, command, ref, ref_type, t_to_go, dep_check=None):
        self.is_a = 'check'
        self.type = ''
        self.id = Action.id
        Action.id += 1
        self._in_timeout = False
        self.status = status
        self.exit_status = 3
        self._command = command
        self.output = ''
        self.long_output = ''
        self.ref = ref
        self.ref_type = ref_type
        self.t_to_go = t_to_go
        self.depend_on = []
        if dep_check is None:
            self.depend_on_me = []
        else:
            self.depend_on_me = [dep_check]
        self.check_time = 0
        self.execution_time = 0
        self.perf_data = ''

    
    def get_return_from(self, c):
        self.exit_status  = c.exit_status
        self.output = c.output
        self.long_output = c.long_output
        self.check_time = c.check_time
        self.execution_time = c.execution_time
        self.perf_data = c.perf_data
        

    def get_outputs(self, out):
        elts = out.split('\n')
        #For perf data
        elts_line1 = elts[0].split('|')
        #First line before | is output
        self.output = elts_line1[0]
        #After | is perfdata
        if len(elts_line1) > 1:
            self.perf_data = elts_line1[1]
        #The others lines are long_output
        if len(elts) > 1:
            self.long_output = '\n'.join(elts[1:])

    
    def execute(self):
        child = spawn ('/bin/sh -c "%s"' % self._command)
        self.status = 'lanched'
        self.check_time = time.time()

        try:
            child.expect_exact(EOF, timeout=5)
            self.get_outputs(child.before)
            child.terminate(force=True)
            self.exit_status = child.exitstatus
            self.status = 'done'
        except TIMEOUT:
            print "On le kill"
            self.status = 'timeout'
            child.terminate(force=True)
        self.execution_time = time.time() - self.check_time


    def is_launchable(self, t):
        return t > self.t_to_go
    
    
    def set_status(self, status):
        self.status = status


    def get_status(self):
        return self.status

    
    def get_output(self):
        return self.output

    
    def __str__(self):
        return "Check %d status:%s command:%s ref:%s" % (self.id, self.status, self._command, self.ref)


    def get_id(self):
        return self.id
