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

if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam


##########################   DAEMON PART    ###############################
# The standard I/O file descriptors are redirected to /dev/null by default.
if (hasattr(os, "devnull")):
    REDIRECT_TO = os.devnull
else:
    REDIRECT_TO = "/dev/null"

UMASK = 0
VERSION = "0.1"

class Daemon:
    #the instances will have their own init
    def __init__(self):
        pass


    def unlink(self):
        print "Unlinking", self.pidfile
        os.unlink(self.pidfile)


    def findpid(self):
        f = open(self.pidfile)
        p = f.read()
        f.close()
        return int(p)


    #Check if previous run are still launched by reading the pidfile
    #if the pid exist by not the pid, we remove the pidfile
    #if still exit, we can replace (kill) the other run
    #or just bail out
    def check_parallel_run(self, do_replace):
        if os.path.exists(self.pidfile):
            p = self.findpid()
            try:
                os.kill(p, 0)
            except os.error, detail:
                if detail.errno == errno.ESRCH:
                    print "stale pidfile exists.  removing it."
                    os.unlink(self.pidfile)
            else:
                #if replace, kill the old process
                if do_replace:
                    print "Replacing",p
                    os.kill(p, 3)
                else:
                    raise SystemExit, "valid pidfile exists.  Exiting."


    #Make the program a daemon. It can redirect all outputs (stdout, stderr) to debug file if need
    #or to devnull if no debug
    def create_daemon(self, do_debug=False, debug_file=''):
        #First we manage the file descriptor, because debug file can be
        #relative to pwd
        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024

        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:# ERROR, fd wasn't open to begin with (ignored)
                pass
        #If debug, all will be writen to if
        if do_debug:
            os.open(debug_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        else:#else, nowhere...
            os.open(REDIRECT_TO, os.O_RDWR)
        os.dup2(0, 1)# standard output (1)
        os.dup2(0, 2)# standard error (2)

        #Now the Fork/Fork
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if (pid == 0):
            os.setsid()
            try:
                pid = os.fork()
            except OSError, e:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)
            if (pid == 0):
                os.chdir(self.workdir)
                os.umask(UMASK)
            else:
                os._exit(0)
        else:
            os._exit(0)

        #Ok, we daemonize :)
        #We writ the pid file now
        f = open(self.pidfile, "w")
        f.write("%d" % os.getpid())
        f.close()


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


    #Change user of the running program. Just insult the admin
    #if he wants root run (it can override). If change failed,
    #it exit 2
    def change_user(self, insane=False):
        if (self.user == 'root' or self.group == 'root') and not insane:
            print "What's ??? You want the application run under the root account?"
            print "I am not agree with it. If you really whant it, put :"
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
            #First group, then user :)
            os.setregid(gid, gid)
            os.setreuid(uid, uid)
        except OSError, e:
            print "Error : cannot change user/group to %s/%s (%s [%d])" % (self.user, self.group, e.strerror, e.errno)
            print "Exiting"
            sys.exit(2)


    #Parse self.config_file and get all properties in it
    #If properties need a pythonization, we do it. It
    #also put default value id the propertie is missing in
    #the config_file
    def parse_config_file(self):
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
        print "Dummy signal function Do not use this function dumbass dev ! "
        sys.exit(0)


    #Set an exit function that is call when we quit
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
            import signal
            signal.signal(signal.SIGTERM, func)


    def get_header(self):
        return ["Shinken %s" % VERSION,
                "Copyright (c) 2009-2010 Gabes Jean (naparuba@gmail.com)",
                "Gerhard Lausser, Gerhard.Lausser@consol.de",
                "License: AGPL"]

    def print_header(self):
        for line in self.get_header():
            print line
