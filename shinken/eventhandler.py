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

import time

#Unix and windows do not have the same import
#if os.name == 'nt':
#    import subprocess, datetime, os, time, signal
#    import ctypes
#    TerminateProcess = ctypes.windll.kernel32.TerminateProcess
#else:
#    from pexpect import *

from action import Action
from shinken.property import UnusedProp, BoolProp, IntegerProp, FloatProp, CharProp, StringProp, ListProp

class EventHandler(Action):
    properties={'is_a': StringProp(
            default='eventhandler'),
                'type': StringProp(
            default=''),
                '_in_timeout': StringProp(
            default=False),
                'status': StringProp(
            default=''),
                'exit_status': StringProp(
            default=3),
                'state': StringProp(
            default=0),
                'output': StringProp(
            default=''),
                'long_output': StringProp(
            default=''),
#                'ref': StringProp(
#            default=-1),
                #'ref_type' : {'required': False, 'default':''},
                't_to_go': StringProp(
            default=0),
                'check_time': StringProp(
            default=0),
                'execution_time': StringProp(
            default=0),
                'env': StringProp(
            default={}),
                }
    #id = 0 #Is common to Actions
    def __init__(self, command, id=None, timeout=10, env={}):
        self.is_a = 'eventhandler'
        self.type = ''
        self.status = 'scheduled'
        if id == None: #id != None is for copy call only
            self.id = Action.id
            Action.id += 1
        self._in_timeout = False
        self.timeout = timeout
        self.exit_status = 3
        self.command = command
        self.output = ''
        self.long_output = ''
        self.t_to_go = time.time()
        self.check_time = 0
        self.execution_time = 0
        self.perf_data = ''
        self.env = {}



    #return a copy of the check but just what is important for execution
    #So we remove the ref and all
    def copy_shell(self):
        #We create a dummy check with nothing in it, jsut defaults values
        new_n = EventHandler('', id=self.id)
        only_copy_prop = ['id', 'status', 'command', 't_to_go', 'timeout', 'env']
        for prop in only_copy_prop:
            val = getattr(self, prop)
            setattr(new_n, prop, val)
        return new_n


    def get_return_from(self, e):
        self.exit_status  = e.exit_status
        self.output = e.output
        self.long_output = e.long_output
        self.check_time = e.check_time
        self.execution_time = e.execution_time
        self.perf_data = e.perf_data


    def get_outputs(self, out, max_plugins_output_length):
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


#    def execute(self):
#        print "Launching EVENT HANDLER command", self.command
#        child = spawn ('/bin/sh -c "%s"' % self.command)
#        self.status = 'launched'
#        self.check_time = time.time()
#
#        try:
#            child.expect_exact(EOF, timeout=5)
#            self.get_outputs(child.before)
#            child.terminate(force=True)
#            self.exit_status = child.exitstatus
#            self.status = 'done'
#        except TIMEOUT:
#            print "On le kill"
#            self.status = 'timeout'
#            child.terminate(force=True)
#        self.execution_time = time.time() - self.check_time


    def is_launchable(self, t):
        return t > self.t_to_go


    def set_status(self, status):
        self.status = status


    def get_status(self):
        return self.status


    def get_output(self):
        return self.output


    def __str__(self):
        return "Check %d status:%s command:%s" % (self.id, self.status, self.command)


    def get_id(self):
        return self.id


    #Call by picle for dataify the coment
    #because we DO NOT WANT REF in this pickleisation!
    def __getstate__(self):
#        print "Asking a getstate for a downtime on", self.ref.get_dbg_name()
        cls = self.__class__
        #id is not in *_properties
        res = [self.id]
        for prop in cls.properties:
            res.append(getattr(self, prop))
        #We reverse because we want to recreate
        #By check at properties in the same order
        res.reverse()
        return res


    #Inversed funtion of getstate
    def __setstate__(self, state):
        cls = self.__class__
        self.id = state.pop()
        for prop in cls.properties:
	    val = state.pop()
            setattr(self, prop, val)
