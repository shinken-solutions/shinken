#!/usr/bin/env python
# Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


from shinken.action import Action


class Check(Action):
    __slots__ = ('id', 'is_a', 'type', '_in_timeout', 'status', 'exit_status',\
                  '_command', 'output', 'long_output', 'ref', 'ref_type', \
                     't_to_go', 'depend_on', 'depend_on_me', 'check_time', \
                     'execution_time', 'env')

    properties={'is_a' : {'required': False, 'default':'check'},
                'type' : {'required': False, 'default': ''},
                '_in_timeout' : {'required': False, 'default': False},
                'status' : {'required': False, 'default':''},
                'exit_status' : {'required': False, 'default':3},
                'state' : {'required': False, 'default':0},
                'output' : {'required': False, 'default':''},
                'long_output' : {'required': False, 'default':''},
                'ref' : {'required': False, 'default': -1},
                #'ref_type' : {'required': False, 'default':''},
                't_to_go' : {'required': False, 'default': 0},
                'depend_on' : {'required': False, 'default': []},
                'dep_check' : {'required': False, 'default': []},
                'check_time' : {'required': False, 'default': 0},
                'execution_time' : {'required': False, 'default': 0},
                'perf_data' : {'required': False, 'default':''},
                'poller_tag' : {'required': False, 'default': None},
                'env' : {'required' : False, 'default' : {}},
                'internal' : {'required': False, 'default':False},
                }

    #id = 0 #Is common to Actions
    def __init__(self, status, command, ref, t_to_go, dep_check=None, id=None, timeout=10, poller_tag=None, env={}):
        self.is_a = 'check'
        self.type = ''
        if id == None: #id != None is for copy call only
            self.id = Action.id
            Action.id += 1
        self._in_timeout = False
        self.timeout = timeout
        self.status = status
        self.exit_status = 3
        self.command = command
        self.output = ''
        self.long_output = ''
        self.ref = ref
        #self.ref_type = ref_type
        self.t_to_go = t_to_go
        self.depend_on = []
        if dep_check is None:
            self.depend_on_me = []
        else:
            self.depend_on_me = [dep_check]
        self.check_time = 0
        self.execution_time = 0
        self.perf_data = ''
        self.poller_tag = poller_tag
        self.env = env
        self.internal = False


    #return a copy of the check but just what is important for execution
    #So we remove the ref and all
    def copy_shell(self):
        #We create a dummy check with nothing in it, jsut defaults values
        new_c = Check('', '', '', '', '', id=self.id)
        only_copy_prop = ['id', 'status', 'command', 't_to_go', 'timeout', 'env']
        for prop in only_copy_prop:
            val = getattr(self, prop)
            setattr(new_c, prop, val)
        return new_c


    def get_return_from(self, c):
        self.exit_status  = c.exit_status
        self.output = c.output
        self.long_output = c.long_output
        self.check_time = c.check_time
        self.execution_time = c.execution_time
        self.perf_data = c.perf_data


#    def get_outputs(self, out):
#        elts = out.split('\n')
#        #For perf data
#        elts_line1 = elts[0].split('|')
#        #First line before | is output
#        self.output = elts_line1[0]
#        #After | is perfdata
#        if len(elts_line1) > 1:
#            self.perf_data = elts_line1[1]
#        #The others lines are long_output
#        if len(elts) > 1:
#            self.long_output = '\n'.join(elts[1:])


#    def execute(self):
#        if os.name == 'nt':
#            self.execute_windows()
#        else:
#            self.execute_unix()


#    def execute_windows(self):
#        """call shell-command and either return its output or kill it
#        if it doesn't normally exit within timeout seconds and return None"""
#        timeout = 5
#        self.status = 'launched'
#        self.check_time = time.time()
#        start = datetime.datetime.now()
#        try:
#            process = subprocess.Popen(self.command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        except WindowsError:
#            print "On le kill"
#            self.status = 'timeout'
#            self.execution_time = time.time() - self.check_time
#            return
#        while process.poll() is None:
#            time.sleep(0.01)
#            now = datetime.datetime.now()
#            if (now - start).seconds> timeout:
#                TerminateProcess(int(process._handle), -1)
#                print "On le kill"
#                self.status = 'timeout'
#                self.execution_time = time.time() - self.check_time
#                return
#        self.get_outputs(process.stdout.read())
#        self.exit_status = process.returncode
#        print "Output:", self.output, self.long_output, "exit status", self.exit_status
#        self.status = 'done'
#        self.execution_time = time.time() - self.check_time


#    def execute_unix(self):
#        #print "Launching command", self.command
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
        return "Check %d status:%s command:%s ref:%s" % (self.id, self.status, self.command, self.ref)


    def get_id(self):
        return self.id
