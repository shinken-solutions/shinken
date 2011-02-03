#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
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

import shinken.pyro_wrapper as pyro
from shinken.pyro_wrapper import InvalidWorkDir
Pyro = pyro.Pyro

from shinken.log import logger


if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam


##########################   DAEMON PART    ###############################
# The standard I/O file descriptors are redirected to /dev/null by default.
REDIRECT_TO = getattr(os, "devnull", "/dev/null")

UMASK = 0
VERSION = "0.5"


class InvalidPidDir(Exception): pass


class Daemon:

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        self.config_file = config_file
        self.is_daemon = is_daemon
        self.do_replace = do_replace
        self.debug = debug
        self.debug_file = debug_file
        self.interrupted = False
                
        # Log init
        self.log = logger
        self.log.load_obj(self)
        
        os.umask(UMASK)
        self.set_exit_handler()

 
 
    def add(self, elt):
        """ Dummy method for adding broker to this daemon """
        pass

 
    def do_load_config(self):
        self.parse_config_file()
        if self.config_file != None:
            #Some paths can be relatives. We must have a full path by taking
            #the config file by reference
            self.relative_paths_to_full(os.path.dirname(self.config_file))

    def change_to_workdir(self):
        try:
            os.chdir(self.workdir)
        except Exception, e:
            raise InvalidWorkDir(e)
        print("Successfully changed to workdir: %s" % (self.workdir))

    def unlink(self):
        print "Unlinking", self.pidfile
        try:
            os.unlink(self.pidfile)
        except Exception, e:
            print("Got an error unlinking our pidfile: %s" % (e))

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

    def __open_pidfile(self):
        ## if problem on open or creating file it'll be raised to the caller:
        try:
            self.fpid = open(self.pidfile, 'arw+')
        except Exception, e:
            raise InvalidPidDir(e)     

    def check_parallel_run(self):
        """ Check (in pidfile) if there isn't already a daemon running. If yes and do_replace: kill it.
Keep in self.fpid the File object to the pidfile. Will be used by writepid.
"""
        self.__open_pidfile()
        try:
            pid = int(self.fpid.read())
        except:
            print "stale pidfile exists (no or invalid or unreadable content).  reusing it."
            return
        
        try:
            os.kill(pid, 0)
        except OverflowError, e:
            ## pid is too long for "kill" : so bad content:
            print("stale pidfile exists: pid=%d is too long" % (pid))
            return
        except os.error, e:
            if e.errno == errno.ESRCH:
                print("stale pidfile exists (pid=%d not exists).  reusing it." % (pid))
                return
            raise
            
        if not self.do_replace:
            raise SystemExit, "valid pidfile exists and not forced to replace.  Exiting."
        
        print "Replacing previous instance ", pid
        try:
            os.kill(pid, 3)
        except os.error, e:
            if e.errno != errno.ESRCH:
                raise
        
        self.fpid.close()
        ## TODO: give some time to wait that previous instance finishes ?
        time.sleep(1)
        ## we must also reopen the pid file cause the previous instance will normally have deleted it !!
        self.__open_pidfile()


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

    def daemonize(self, skip_close_fds=None):
        """ Go in "daemon" mode: close unused fds, redirect stdout/err, chdir, umask, fork-setsid-fork-writepid """
        
        if skip_close_fds is None:
            skip_close_fds = tuple()

        print("Redirecting stdout and stderr as necessary..")
        if self.debug:
            fdtemp = os.open(self.debug_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        else:
            fdtemp = os.open(REDIRECT_TO, os.O_RDWR)
        
        ## We close all fd but what we need:
        self.close_fds(skip_close_fds + ( self.fpid.fileno() , fdtemp ))

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
        print("We are now fully daemonized :) pid=%d" % (os.getpid()))


    def do_daemon_init_and_start(self, ssl_conf=None):
        self.check_parallel_run()
        self.setup_pyro_daemon(ssl_conf)
        self.change_to_user_group()
        self.change_to_workdir()  ## must be done AFTER pyro daemon init
        if self.is_daemon:
            daemon_socket_fds = tuple( sock.fileno() for sock in pyro.get_sockets(self.daemon) )
            self.daemonize(skip_close_fds=daemon_socket_fds)
        else:
            self.write_pid()


    def setup_pyro_daemon(self, ssl_conf=None):
        if ssl_conf is None: 
            ssl_conf = self
        
        # The SSL part
        if ssl_conf.use_ssl:
            Pyro.config.PYROSSL_CERTDIR = os.path.abspath(ssl_conf.certs_dir)
            print "Using ssl certificate directory : %s" % Pyro.config.PYROSSL_CERTDIR
            Pyro.config.PYROSSL_CA_CERT = os.path.abspath(ssl_conf.ca_cert)
            print "Using ssl ca cert file : %s" % Pyro.config.PYROSSL_CA_CERT
            Pyro.config.PYROSSL_CERT = os.path.abspath(ssl_conf.server_cert)
            print"Using ssl server cert file : %s" % Pyro.config.PYROSSL_CERT
            if self.hard_ssl_name_check:
                Pyro.config.PYROSSL_POSTCONNCHECK=1
            else:
                Pyro.config.PYROSSL_POSTCONNCHECK=0

        #create the server
        Pyro.config.PYRO_STORAGE = self.workdir
        Pyro.config.PYRO_COMPRESSION = 1
        Pyro.config.PYRO_MULTITHREADED = 0        

        self.daemon = pyro.init_daemon(self.host, self.port, ssl_conf.use_ssl)


    def get_socks_activity(self, socks, timeout):
        try:
            ins, _, _ = select.select(socks, [], [], timeout)
        except select.error, e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins


    def find_modules_path(self):
        """ Find the absolute path of the shinken module directory and set it in self.modulespath  """
        import shinken
        
        # BEWARE: this way of finding path is good if we still
        # DO NOT HAVE CHANGE PWD!!!
        # Now get the module path. It's in fact the directory modules
        # inside the shinken directory. So let's find it.

        print "modulemanager file", shinken.modulesmanager.__file__
        modulespath = os.path.abspath(shinken.modulesmanager.__file__)
        print "modulemanager absolute file", modulespath
        # We got one of the files of
        elts = os.path.dirname(modulespath).split(os.sep)[:-1]
        elts.append('shinken')
        elts.append('modules')
        self.modulespath = os.sep.join(elts)
        logger.log("Using modules path : %s" % os.sep.join(elts))


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
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, func)


    def get_header(self):
        return ["Shinken %s" % VERSION,
                "Copyright (c) 2009-2010 :",
                "Gabes Jean (naparuba@gmail.com)",
                "Gerhard Lausser, Gerhard.Lausser@consol.de",
	        "Gregory Starck, g.starck@gmail.com",
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
