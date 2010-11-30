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

import os, time, copy
import shlex
import sys

#Unix and windows do not have the same import
if os.name == 'nt':
    import subprocess
    import ctypes
    TerminateProcess = ctypes.windll.kernel32.TerminateProcess
else:
    import subprocess

# This class is use just for having a common id between actions and checks

class Action:
    id = 0
    def __init__(self):
        pass


    # If the command line got shell caracters, we should go in a shell
    # mode. So look at theses parameters
    # Note : it's "hard", but in fact you can launch it 100000times
    # a second so... I don't care :) (and at least it's easy to understand)
    def got_shell_caracters(self):
        for c in self.command:
            if c in ['!','$','^','&','*','(',')','~','[',']','|','{','}',';','<','>','?','`']:
                return True
        return False


    def get_outputs(self, out, max_plugins_output_length):
        #print "Get only," , max_plugins_output_length, "bytes"
        # Squize all output after max_plugins_output_length
        out = out[:max_plugins_output_length]
        # Then cuts by lines
        elts = out.split('\n')
        # For perf data
        elts_line1 = elts[0].split('|')
        # First line before | is output
        self.output = elts_line1[0]
        # After | is perfdata
        if len(elts_line1) > 1:
            self.perf_data = elts_line1[1]
        # The others lines are long_output
        if len(elts) > 1:
            self.long_output = '\n'.join(elts[1:])


    # Mix the env into the environnment variables
    # into a new local env dict
    # rmq : we cannot just update os.environ because
    # it will be modified for all other checks too
    def get_local_environnement(self):
        local_env = copy.copy(os.environ)
        for p in self.env:
            local_env[p] = self.env[p]
        return local_env


    def execute(self):
        if os.name == 'nt':
            self.execute_windows()
        else:
            self.execute_unix()


    def execute_windows(self):
        #self.timeout = 20
        self.status = 'launched'
        self.check_time = time.time()
        self.wait_time = 0.0001
        self.last_poll = self.check_time
        local_env = self.get_local_environnement()
        try:
            self.process = subprocess.Popen(shlex.split(self.command),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=local_env, shell=True)
        except WindowsError, exp:
            print "We kill the process : ", exp, self.command
            self.status = 'timeout'
            self.execution_time = time.time() - self.check_time
            return


    def execute_unix(self):
        self.status = 'launched'
        self.check_time = time.time()
        self.last_poll = self.check_time
        self.wait_time = 0.0001
        #cmd = ['/bin/sh', '-c', self.command]
        # Nagios do not use the /bin/sh -c command, so I don't do it too

        # Get a local env variables with our additionnal values
        local_env = self.get_local_environnement()

        # We allow direct launch only for 2.7 and higher version
        # because if a direct launch crash, under this the file hanldes
        # are not releases, it's not good.
        if sys.version_info >= (2,7):
            shell_launch = self.got_shell_caracters()
        else:
            shell_launch = True
        # Maybe we will failed in our first attempt, we can retry
        still_loop = True

        while still_loop:
            if shell_launch:
                try:
                    self.process = subprocess.Popen(self.command,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        close_fds=True, shell=True, env=local_env)
                    return
                except OSError , exp:
                    print "Debug : Error in launching shell command:", self.command, exp
                    print "Way: launch command?", self.got_shell_caracters()
                    self.output = exp.__str__()
                    self.exit_status = 2
                    self.status = 'done'
                    self.execution_time = time.time() - self.check_time
                    return
            else:
                # Direct exec, quicker but only for 2.7 and higher, sorry.
                try:
                    p = subprocess.Popen(shlex.split(self.command),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        close_fds=True, env=local_env)
                    self.process = p
                    return
                except OSError , exp:
                    # Maybe it's just a shell we try to exec. So we must retry
                    if exp.errno == 8 and exp.strerror == 'Exec format error':
                        shell_launch = True
                        continue # loop and go in the shell launch this time
                    # Here, we are with a real error
                    print "Debug : Error in launching direct exec command:", self.command, exp
                    self.output = exp.__str__()
                    self.exit_status = 2
                    self.status = 'done'
                    self.execution_time = time.time() - self.check_time
                    return


    def check_finished(self, max_plugins_output_length):
        if os.name == 'nt':
            self.check_finished_windows(max_plugins_output_length)
        else:
            self.check_finished_unix(max_plugins_output_length)


    def check_finished_unix(self, max_plugins_output_length):
        # We must wait, but checks are variable in time
        # so we do not wait the same for an little check
        # than a long ping. So we do like TCP : slow start with *2
        # but do not wait more than 0.1s.
        self.last_poll = time.time()
        if self.process.poll() is None:
            self.wait_time = min(self.wait_time*2, 0.1)
            #time.sleep(wait_time)
            now = time.time()
            if (now - self.check_time) > self.timeout:
                #process.kill()
                # HEAD SHOT
                os.kill(self.process.pid, 9)
                #print "Kill", self.process.pid, self.command, now - self.check_time
                self.status = 'timeout'
                self.execution_time = now - self.check_time
                self.exit_status = 3
                return
            return
        # Get standards outputs
        self.exit_status = self.process.returncode
        (stdoutdata, stderrdata) = self.process.communicate()

        # if the exit status is anormal, we add stderr to the output
        if self.exit_status not in [0, 1, 2, 3]:
            stdoutdata = stdoutdata + stderrdata
        # Now grep what we want in the output
        self.get_outputs(stdoutdata, max_plugins_output_length)

        self.status = 'done'
        self.execution_time = time.time() - self.check_time


    def check_finished_windows(self, max_plugins_output_length):
        # We must wait, but checks are variable in time
        # so we do not wait the same for an little check
        # than a long ping. So we do like TCP : slow start with *2
        # but do not wait more than 0.1s.
        self.last_poll = time.time()
        if self.process.poll() is None:
            self.wait_time = min(self.wait_time*2, 0.1)
            #time.sleep(wait_time)
            now = time.time()
            if (now - self.check_time) > self.timeout:
                #process.kill()
                # HEAD SHOT
                TerminateProcess(int(self.process._handle), -1)
                #print "Kill", self.process.pid, self.command
                self.status = 'timeout'
                self.execution_time = now - self.check_time
                self.exit_status = 3
                return
            return
        # Get standards outputs
        self.exit_status = self.process.returncode
        (stdoutdata, stderrdata) = self.process.communicate()

        #we should not keep the process now
        del self.process
        
        # if the exit status is anormal, we add stderr to the output
        if self.exit_status not in [0, 1, 2, 3]:
            stdoutdata = stdoutdata + stderrdata
        #self.get_outputs(self.process.stdout.read(),max_plugins_output_length)
        # Now grep what we want in the output
        self.get_outputs(stdoutdata, max_plugins_output_length)

        # if self.exit_status != 0:
        #    print "DBG:", self.command, self.exit_status, self.output
        self.status = 'done'
        self.execution_time = time.time() - self.check_time
