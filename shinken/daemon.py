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

import os, errno, sys, ConfigParser
import time
import signal
import select


if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam


##########################   DAEMON PART    ###############################
# The standard I/O file descriptors are redirected to /dev/null by default.
REDIRECT_TO = getattr(os, "devnull", "/dev/null")

UMASK = 0
VERSION = "0.5"

class Daemon:

    def __init__(self):
        self.interrupted = False
        os.umask(UMASK)
        self.set_exit_handler()
 

    def change_to_workdir(self):
        os.chdir(self.workdir)
        print("Successfully changed to workdir: %s" % (self.workdir))

    def unlink(self):
        print "Unlinking", self.pidfile
        os.unlink(self.pidfile)

    def check_shm(self):
        """ Only on linux: Check for /dev/shm write access """
        import stat
        shm_path = '/dev/shm'
        if os.name == 'posix' and os.path.exists(shm_path):
            # We get the access rights, and we check them
            mode = stat.S_IMODE(os.lstat(shm_path)[stat.ST_MODE])
            if not mode & stat.S_IWUSR or not mode & stat.S_IRUSR:
                print("The directory %s is not writable or readable. Please launch as root chmod 777 %s" % (shm_path, shm_path))
                sys.exit(2)   


    def check_parallel_run(self, do_replace):
        """ Check (in pidfile) if there isn't already a daemon running. If yes and do_replace: kill it.
Keep in self.fpid the File object to the pidfile. Will be used by writepid.
"""
        ## if problem on open or creating file it'll be raised to the caller:
        self.fpid = open(self.pidfile, 'arw+')
        try:
            pid = int(self.fpid.read())
        except:
            print "stale pidfile exists (no or invalid or unreadable content).  reusing it."
            return
        
        try:
            os.kill(pid, 0)
        except OverflowError as e:
            ## pid is too long for "kill" : so bad content:
            print("stale pidfile exists: pid=%d is too long" % (pid))
            return
        except os.error as e:
            if e.errno == errno.ESRCH:
                print("stale pidfile exists (pid=%d not exists).  reusing it." % (pid))
                return
            raise
            
        if not do_replace:
            raise SystemExit, "valid pidfile exists and not forced to replace.  Exiting."
        
        print "Replacing previous instance ", pid
        try:
            os.kill(pid, 3)
        except os.error as e:
            if e.errno != errno.ESRCH:
                raise
        
        self.fpid.close()
        ## TODO: give some time to wait that previous instance finishes ?
        time.sleep(1)
        ## we must also reopen the pid file cause the previous instance will normally have deleted it !!
        self.fpid = open(self.pidfile, 'arw+')


    def write_pid(self, pid=None):
        if pid is None: 
            pid = os.getpid()
        self.fpid.seek(0)
        self.fpid.truncate()
        self.fpid.write("%d" % (pid))
        self.fpid.close()
        del self.fpid ## no longer needed

    def close_fds(self, skip_close_fds=None):
        if skip_close_fds is None:
            skip_close_fds = tuple()
        
        #First we manage the file descriptor, because debug file can be
        #relative to pwd
        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024

        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            if fd in skip_close_fds: continue
            try:
                os.close(fd)
            except OSError:# ERROR, fd wasn't open to begin with (ignored)
                pass


    def daemonize(self, do_debug=False, debug_file='', skip_close_fds=None):
        """ Go in "daemon" mode: close unused fds, redirect stdout/err, chdir, umask, fork-setsid-fork-writepid """
        
        if skip_close_fds is None:
            skip_close_fds = tuple()

        self.close_fds(skip_close_fds + ( self.fpid.fileno() ,))
        
        if do_debug:
            fdtemp = os.open(debug_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        else:
            fdtemp = os.open(REDIRECT_TO, os.O_RDWR)
        os.dup2(fdtemp, 1) # standard output (1)
        os.dup2(fdtemp, 2) # standard error (2)

        # Now the Fork/Fork
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if pid != 0:
            ## in the father
            def do_exit(sig, frame):
                print("timeout waiting child while it should have quickly returned ; something weird happened")
                os.kill(pid, 9)
                sys.exit(1)
            ## wait the child process to check its return status:
            signal.signal(signal.SIGALRM, do_exit)
            signal.alarm(3)  ## TODO: define alarm value somewhere else and/or use config variable
            pid, status = os.waitpid(pid, 0)
            if status != 0:
                print("something weird happened with/during second fork : status=", status)
            self.close_fds()
            os._exit(status)
        
        os.setsid()
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if pid != 0:
            self.write_pid(pid)
            self.close_fds()
            os._exit(0)

        self.fpid.close()
        del self.fpid
        print("We are now fully daemonized :) pid=", os.getpid())
 

    def get_socks_activity(self, socks, timeout):
        try:
            ins, _, _ = select.select(socks, [], [], timeout)
        except select.error as e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins

    #Just give the uid of a user by looking at it's name
    def find_uid_from_name(self):
        try:
            return getpwnam(self.user)[2]
        except KeyError , exp:
            print "Error: the user", self.user, "is unknown"
            return None

    #Just give the gid of a group by looking at it's name
    def find_gid_from_name(self):
        try:
            return getgrnam(self.group)[2]
        except KeyError , exp:
            print "Error: the group", self.group, "is unknown"
            return None


    def change_to_user_group(self, insane=None):
        """ Change user of the running program. Just insult the admin if he wants root run (it can override).
If change failed we sys.exit(2) """
        if insane is None:
            insane = not self.idontcareaboutsecurity

        # TODO: change user on nt
        if os.name == 'nt':
            print("Sorry, you can't change user on this system")
            return

        if (self.user == 'root' or self.group == 'root') and not insane:
            print "What's ??? You want the application run under the root account?"
            print "I am not agree with it. If you really want it, put :"
            print "idontcareaboutsecurity=yes"
            print "in the config file"
            print "Exiting"
            sys.exit(2)

        uid = self.find_uid_from_name()
        gid = self.find_gid_from_name()
        if uid == None or gid == None:
            print "Exiting"
            sys.exit(2)
        try:
            # First group, then user :)
            os.setregid(gid, gid)
            os.setreuid(uid, uid)
        except OSError, e:
            print "Error : cannot change user/group to %s/%s (%s [%d])" % (self.user, self.group, e.strerror, e.errno)
            print "Exiting"
            sys.exit(2)


    def parse_config_file(self):
        """ Parse self.config_file and get all properties in it.
If some properties need a pythonization, we do it.
Also put default value in the properties if some are missing in the config_file """
        properties = self.__class__.properties
        if self.config_file != None:
            config = ConfigParser.ConfigParser()
            config.read(self.config_file)
            if config._sections == {}:
                print "Bad or missing config file : %s " % self.config_file
                sys.exit(2)
            for (key, value) in config.items('daemon'):
                if key in properties and properties[key]['pythonize'] != None:
                    value = properties[key]['pythonize'](value)
                setattr(self, key, value)
        else:
            print "No config file specified, use defaults parameters"
        #Now fill all defaults where missing parameters
        for prop in properties:
            if not hasattr(self, prop):
                value = properties[prop]['default']
                if prop in properties and properties[prop]['pythonize'] != None:
                    value = properties[prop]['pythonize'](value)
                setattr(self, prop, value)
                print "Using default value :", prop, value


    #Some paths can be relatives. We must have a full path by taking
    #the config file by reference
    def relative_paths_to_full(self, reference_path):
        #print "Create relative paths with", reference_path
        properties = self.__class__.properties
        for prop in properties:
            if 'path' in properties[prop] and properties[prop]['path']:
                path = getattr(self, prop)
                new_path = path
                #Windows full paths are like c:/blabla
                #Unixes are like /blabla
                #So we look for : on windows, / for Unixes
                if os.name != 'nt':
                    #os.sep = / on Unix
                    #so here if not
                    if path != '' and path[0] != os.sep :
                        new_path = reference_path + os.sep + path
                else:
                    #os.sep = \ on windows, and we must look at c: like format
                    if len(path) > 2 and path[1] != ':':
                        new_path = reference_path + os.sep + path
                setattr(self, prop, new_path)
                #print "Setting %s for %s" % (new_path, prop)


    def manage_signal(self, sig, frame):
        print("I'm process %d and I received signal %s" % (os.getpid(), str(sig)))
        self.interrupted = True

    def set_exit_handler(self):
        func = self.manage_signal
        if os.name == "nt":
            try:
                import win32api
                win32api.SetConsoleCtrlHandler(func, True)
            except ImportError:
                version = ".".join(map(str, sys.version_info[:2]))
                raise Exception("pywin32 not installed for Python " + version)
        else:
            signal.signal(signal.SIGTERM, func)


    def get_header(self):
        return ["Shinken %s" % VERSION,
                "Copyright (c) 2009-2010 :",
                "Gabes Jean (naparuba@gmail.com)",
                "Gerhard Lausser, Gerhard.Lausser@consol.de",
                "License: AGPL"]

    def print_header(self):
        for line in self.get_header():
            print line

    def do_loop_turn(self):
        raise NotImplementedError()

    def do_stop(self):
        pass

    def request_stop(self):
        self.unlink()  ## unlink first
        self.do_stop()
        print("Exiting")
        sys.exit(0)

    def do_mainloop(self):
        while True:
            self.do_loop_turn()
            if self.interrupted:
                break
        self.request_stop()
