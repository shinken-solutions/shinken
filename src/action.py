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

import os, time
import shlex

#Unix and windows do not have the same import
if os.name == 'nt':
    import subprocess, datetime, signal
    import ctypes
    TerminateProcess = ctypes.windll.kernel32.TerminateProcess
else:
    import subprocess, datetime, signal

#This class is use just for having a common id between actions and checks

class Action:
    id = 0
    def __init__(self):
        pass


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
        if os.name == 'nt':
            self.execute_windows()
        else:
            self.execute_unix()

 
    def execute_windows(self):
        #self.timeout = 20
        self.status = 'lanched'
        self.check_time = time.time()
        self.wait_time = 0.0001
        self.last_poll = self.check_time
        try:
            process = subprocess.Popen(shlex.split(self.command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except WindowsError:
            print "On le kill"
            self.status = 'timeout'
            self.execution_time = time.time() - self.check_time
            return


    def execute_unix(self):
        self.status = 'lanched'
        self.check_time = time.time()
        self.last_poll = self.check_time
        self.wait_time = 0.0001
        #cmd = ['/bin/sh', '-c', self.command]
        #Nagios do not use the /bin/sh -c command, so I don't do it too
        try:
            self.process = subprocess.Popen(shlex.split(self.command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        except OSError as exp:
            print "FUCK:", exp
            self.output = exp
            self.exit_status = 2
            self.status = 'done'
            self.execution_time = time.time() - self.check_time
            return


    def check_finished(self):
        if os.name == 'nt':
            self.check_finished_windows()
        else:
            self.check_finished_unix()
    

    def check_finished_unix(self):
        #We must wait, but checks are variable in time
        #so we do not wait the same for an little check
        #than a long ping. So we do like TCP : slow start with *2
        #but do not wait more than 0.1s.
        self.last_poll = time.time()
        if self.process.poll() is None:
            self.wait_time = min(self.wait_time*2, 0.1)
            #time.sleep(wait_time)
            now = time.time()
            if (now - self.check_time) > self.timeout:
                #process.kill()
                #HEAD SHOT
                os.kill(self.process.pid, 9) 
                #print "Kill", self.process.pid, self.command, now - self.check_time
                self.status = 'timeout'
                self.execution_time = now - self.check_time
                self.exit_status = 3
                return
            return
        (stdoutdata, stderrdata) = self.process.communicate()
        self.get_outputs(stdoutdata)
        self.exit_status = self.process.returncode
        #if self.exit_status != 0:
        #    print "DBG:", self.command, self.exit_status, self.output
        self.status = 'done'
        self.execution_time = time.time() - self.check_time


    def check_finished_windows(self):
        #We must wait, but checks are variable in time
        #so we do not wait the same for an little check
        #than a long ping. So we do like TCP : slow start with *2
        #but do not wait more than 0.1s.
        self.last_poll = time.time()
        if self.process.poll() is None:
            self.wait_time = min(self.wait_time*2, 0.1)
            #time.sleep(wait_time)
            now = time.time()
            if (now - self.check_time) > self.timeout:
                #process.kill()
                #HEAD SHOT
                TerminateProcess(int(self.process._handle), -1)
                #print "Kill", self.process.pid, self.command
                self.status = 'timeout'
                self.execution_time = now - self.check_time
                self.exit_status = 3
                return
            return
        self.get_outputs(self.process.stdout.read())
        self.exit_status = self.process.returncode
        #if self.exit_status != 0:
        #    print "DBG:", self.command, self.exit_status, self.output
        self.status = 'done'
        self.execution_time = time.time() - self.check_time
