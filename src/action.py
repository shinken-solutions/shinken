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

#Unix and windows do not have the same import
if os.name == 'nt':
    import subprocess, datetime, signal
    import ctypes
    TerminateProcess = ctypes.windll.kernel32.TerminateProcess
else:
    from pexpect import *
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
        timeout = 5
        self.status = 'lanched'
        self.check_time = time.time()
        start = datetime.datetime.now()
        try:
            process = subprocess.Popen(self.command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except WindowsError:
            print "On le kill"
            self.status = 'timeout'
            self.execution_time = time.time() - self.check_time
            return
        while process.poll() is None:
            time.sleep(0.01)
            now = datetime.datetime.now()
            if (now - start).seconds> timeout:
                TerminateProcess(int(process._handle), -1)
                print "On le kill"
                self.status = 'timeout'
                self.execution_time = time.time() - self.check_time
                return
        self.get_outputs(process.stdout.read())
        self.exit_status = process.returncode
        print "Output:", self.output, self.long_output, "exit status", self.exit_status
        self.status = 'done'
        self.execution_time = time.time() - self.check_time


    #def execute_unix(self):
    #    child = spawn ('/bin/sh -c "%s"' % self.command)
    #    self.status = 'lanched'
    #    self.check_time = time.time()

    #    try:
    #        child.expect_exact(EOF, timeout=5)
    #        self.get_outputs(child.before)
    #        child.terminate(force=True)
    #        self.exit_status = child.exitstatus
    #        self.status = 'done'
    #    except TIMEOUT:
    #        print "On le kill"
    #        self.status = 'timeout'
    #        child.terminate(force=True)
    #    self.execution_time = time.time() - self.check_time


    def execute_unix(self):
        timeout = 5
        self.status = 'lanched'
        self.check_time = time.time()
        #self.command = '/bin/sh -c "%s"' % self.command
        cmd = ['/bin/sh', '-c', self.command]
        #print cmd
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #We must wait, but checks are variable in time
        #so we do not wait the same for an little check
        #than a long ping. So we do like TCP : slow start with *2
        #but do not wait more than 0.1s.
        wait_time = 0.0001
        while process.poll() is None:
            wait_time = min(wait_time*2, 0.1)
            time.sleep(wait_time)
            now = time.time()
            if (now - self.check_time) > timeout:
                process.kill()
                print "On le kill"
                self.status = 'timeout'
                self.execution_time = now - self.check_time
                self.exit_status = 3
                return
        self.get_outputs(process.stdout.read())
        self.exit_status = process.returncode
        self.status = 'done'
        self.execution_time = time.time() - self.check_time
