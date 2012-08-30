#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

import os
import errno
import sys
import time
import signal
import select
import random
import ConfigParser

# Try to see if we are in an android device or not
is_android = True
try:
    import android
except ImportError:
    is_android = False


if not is_android:
    from multiprocessing import Queue, Manager, active_children, cpu_count
else:
    from multiprocessing import active_children

import shinken.pyro_wrapper as pyro
from shinken.pyro_wrapper import InvalidWorkDir, Pyro

from shinken.log import logger
from shinken.modulesmanager import ModulesManager
from shinken.property import StringProp, BoolProp, PathProp, ConfigPathProp, IntegerProp, LogLevelProp


try:
    import pwd, grp
    from pwd import getpwnam
    from grp import getgrnam


    def get_cur_user():
        return pwd.getpwuid(os.getuid()).pw_name


    def get_cur_group():
        return grp.getgrgid(os.getgid()).gr_name
except ImportError, exp:  # Like in nt system or Android


    # temporary workarround:
    def get_cur_user():
        return "shinken"


    def get_cur_group():
        return "shinken"

##########################   DAEMON PART    ###############################
# The standard I/O file descriptors are redirected to /dev/null by default.
REDIRECT_TO = getattr(os, "devnull", "/dev/null")

UMASK = 027
from shinken.bin import VERSION

""" TODO: Add some comment about this class for the doc"""
class InvalidPidFile(Exception): pass


""" Interface for pyro communications """
class Interface(Pyro.core.ObjBase, object):

    #  'app' is to be set to the owner of this interface.
    def __init__(self, app):

        Pyro.core.ObjBase.__init__(self)

        self.app = app
        self.running_id = "%d.%d" % (time.time(), random.random())

    def ping(self):
        return "pong"

    def get_running_id(self):
        return self.running_id

    def put_conf(self, conf):
        self.app.new_conf = conf

    def wait_new_conf(self):
        self.app.cur_conf = None

    def have_conf(self):
        return self.app.cur_conf is not None

    def set_log_level(self, loglevel):
        return logger.set_level(loglevel)

# If we are under android, we can't give parameters
if is_android:
    DEFAULT_WORK_DIR = '/sdcard/sl4a/scripts/'
else:
    DEFAULT_WORK_DIR = 'var'


class Daemon(object):

    properties = {
        # workdir is relative to $(dirname "$0"/..)
        # where "$0" is the path of the file being executed,
        # in python normally known as:
        #
        #  os.path.join( os.getcwd(), sys.argv[0] )
        #
        # as returned once the daemon is started.
        'workdir':       PathProp(default=DEFAULT_WORK_DIR),
        'host':          StringProp(default='0.0.0.0'),
        'user':          StringProp(default=get_cur_user()),
        'group':         StringProp(default=get_cur_group()),
        'use_ssl':       BoolProp(default='0'),
        'certs_dir':     StringProp(default='etc/certs'),
        'ca_cert':       StringProp(default='etc/certs/ca.pem'),
        'server_cert':   StringProp(default='etc/certs/server.pem'),
        'use_local_log': BoolProp(default='1'),
        'log_level':     LogLevelProp(default='WARNING'),
        'hard_ssl_name_check':    BoolProp(default='0'),
        'idontcareaboutsecurity': BoolProp(default='0'),
        'daemon_enabled':BoolProp(default='1'),
        'spare':         BoolProp(default='0'),
        'max_queue_size': IntegerProp(default='0'),
    }

    def __init__(self, name, config_file, is_daemon, do_replace, debug, debug_file):

        self.check_shm()

        self.name = name
        self.config_file = config_file
        self.is_daemon = is_daemon
        self.do_replace = do_replace
        self.debug = debug
        self.debug_file = debug_file
        self.interrupted = False

        # Track time
        now = time.time()
        self.program_start = now
        self.t_each_loop = now  # used to track system time change
        self.sleep_time = 0.0  # used to track the time we wait

        self.pyro_daemon = None

        # Log init
        #self.log = logger
        #self.log.load_obj(self)
        logger.load_obj(self)

        self.new_conf = None  # used by controller to push conf
        self.cur_conf = None

        # Flag to know if we need to dump memory or not
        self.need_dump_memory = False

        # Flag to dump objects or not
        self.need_objects_dump = False

        # Keep a trace of the local_log file desc if needed
        self.local_log_fd = None

        # Put in queue some debug output we will raise
        # when we will be in daemon
        self.debug_output = []

        # We will inialize the Manager() when we load modules
        # and be really forked()
        self.manager = None

        self.modules_manager = ModulesManager(name, self.find_modules_path(), [])

        os.umask(UMASK)
        self.set_exit_handler()


    # At least, lose the local log file if needed
    def do_stop(self):
        if self.modules_manager:
            # We save what we can but NOT for the scheduler
            # because the current sched object is a dummy one
            # and the old one has already done it!
            if not hasattr(self, 'sched'):
                self.hook_point('save_retention')
            # And we quit
            print('Stopping all modules')
            self.modules_manager.stop_all()
            print('Stopping inter-process message (PYRO)')
        if self.pyro_daemon:
            pyro.shutdown(self.pyro_daemon)
        logger.quit()


    def request_stop(self):
        self.unlink()
        self.do_stop()
        # Brok facilities are no longer available simply print the message to STDOUT
        print ("Stopping daemon. Exiting", )
        sys.exit(0)


    # Maybe this daemon is configured to NOT run, if so, bailout
    def look_for_early_exit(self):
        if not self.daemon_enabled:
            logger.info('This daemon is disabled in configuration. Bailing out')
            self.request_stop()


    def do_loop_turn(self):
        raise NotImplementedError()


    # Main loop for nearly all daemon
    # the scheduler is not managed by it :'(
    def do_mainloop(self):
        while True:
            self.do_loop_turn()
            # If ask us to dump memory, do it
            if self.need_dump_memory:
                self.dump_memory()
                self.need_dump_memory = False
            if self.need_objects_dump:
                logger.debug('Dumping objects')
                self.need_objects_dump = False
            # Maybe we ask us to die, if so, do it :)
            if self.interrupted:
                break
        self.request_stop()

    def do_load_modules(self):
        self.modules_manager.load_and_init()
        logger.info("I correctly loaded the modules: [%s]" % (','.join([inst.get_name() for inst in self.modules_manager.instances])))

    # Dummy method for adding broker to this daemon
    def add(self, elt):
        pass

    def dump_memory(self):
        logger.info("I dump my memory, it can take a minute")


        try:
            from guppy import hpy
            hp = hpy()
            logger.info(hp.heap())
        except ImportError:
            logger.warning('I do not have the module guppy for memory dump, please install it')

    def load_config_file(self):
        self.parse_config_file()
        if self.config_file is not None:
            # Some paths can be relatives. We must have a full path by taking
            # the config file by reference
            self.relative_paths_to_full(os.path.dirname(self.config_file))
            pass
        # Set the modules watchdogs
        self.modules_manager.set_max_queue_size(self.max_queue_size)

    def change_to_workdir(self):
        try:
            os.chdir(self.workdir)
        except Exception, e:
            raise InvalidWorkDir(e)
        self.debug_output.append("Successfully changed to workdir: %s" % (self.workdir))

    def unlink(self):
        logger.debug("Unlinking %s" % self.pidfile)
        try:
            os.unlink(self.pidfile)
        except Exception, e:
            logger.error("Got an error unlinking our pidfile: %s" % (e))

    # Look if we need a local log or not
    def register_local_log(self):
        # The arbiter doesn't have such attribute
        if hasattr(self, 'use_local_log') and self.use_local_log:
            try:
                #self.local_log_fd = self.log.register_local_log(self.local_log)
                self.local_log_fd = logger.register_local_log(self.local_log)
            except IOError, exp:
                logger.error("Opening the log file '%s' failed with '%s'" % (self.local_log, exp))
                sys.exit(2)
            logger.info("Using the local log file '%s'" % self.local_log)

    # Only on linux: Check for /dev/shm write access
    def check_shm(self):
        import stat
        shm_path = '/dev/shm'
        if os.name == 'posix' and os.path.exists(shm_path):
            # We get the access rights, and we check them
            mode = stat.S_IMODE(os.lstat(shm_path)[stat.ST_MODE])
            if not mode & stat.S_IWUSR or not mode & stat.S_IRUSR:
                logger.critical("The directory %s is not writable or readable. Please make it read writable: %s" % (shm_path, shm_path))
                sys.exit(2)

    def __open_pidfile(self, write=False):
        ## if problem on opening or creating file it'll be raised to the caller:
        try:
            p = os.path.abspath(self.pidfile)
            self.debug_output.append("Opening pid file: %s" % self.pidfile)
            # Windows do not manage the rw+ mode, so we must open in read mode first, then reopen it write mode...
            if not write and os.path.exists(p):
                self.fpid = open(p, 'r+')
            else:  # If it doesnt exist too, we create it as void
                self.fpid = open(p, 'w+')
        except Exception, e:
            raise InvalidPidFile(e)

    # Check (in pidfile) if there isn't already a daemon running. If yes and do_replace: kill it.
    # Keep in self.fpid the File object to the pidfile. Will be used by writepid.
    def check_parallel_run(self):


        # TODO: other daemon run on nt
        if os.name == 'nt':
            logger.warning("The parallel daemon check is not available on nt")
            self.__open_pidfile(write=True)
            return

        # First open the pid file in open mode
        self.__open_pidfile()
        try:
            pid = int(self.fpid.read())
        except:
            logger.warning("Stale pidfile exists (no or invalid or unreadable content). Reusing it.")
            return

        try:
            os.kill(pid, 0)
        except OverflowError, e:
            ## pid is too long for "kill": so bad content:
            logger.error("Stale pidfile exists: pid=%d is too long" % (pid))
            return
        except os.error, e:
            if e.errno == errno.ESRCH:
                logger.warning("Stale pidfile exists (pid=%d not exists). Reusing it." % (pid))
                return
            raise

        if not self.do_replace:
            raise SystemExit, "valid pidfile exists and not forced to replace.  Exiting."

        self.debug_output.append("Replacing previous instance %d" % pid)
        try:
            os.kill(pid, 3)
        except os.error, e:
            if e.errno != errno.ESRCH:
                raise

        self.fpid.close()
        ## TODO: give some time to wait that previous instance finishes?
        time.sleep(1)
        # we must also reopen the pid file in write mode
        # because the previous instance should have deleted it!!
        self.__open_pidfile(write=True)

    def write_pid(self, pid=None):
        if pid is None:
            pid = os.getpid()
        self.fpid.seek(0)
        self.fpid.truncate()
        self.fpid.write("%d" % (pid))
        self.fpid.close()
        del self.fpid  ## no longer needed

    # Close all the process file descriptors. Skip the descriptors
    # present in the skip_close_fds list
    def close_fds(self, skip_close_fds):
        # First we manage the file descriptor, because debug file can be
        # relative to pwd
        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024

        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            if fd in skip_close_fds:
                continue
            try:
                os.close(fd)
            except OSError:  # ERROR, fd wasn't open to begin with (ignored)
                pass

    # Go in "daemon" mode: close unused fds, redirect stdout/err,
    # chdir, umask, fork-setsid-fork-writepid
    def daemonize(self, skip_close_fds=None):

        if skip_close_fds is None:
            skip_close_fds = tuple()

        self.debug_output.append("Redirecting stdout and stderr as necessary..")
        if self.debug:
            fdtemp = os.open(self.debug_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        else:
            fdtemp = os.open(REDIRECT_TO, os.O_RDWR)

        ## We close all fd but what we need:
        self.close_fds(skip_close_fds + (self.fpid.fileno(), fdtemp))

        os.dup2(fdtemp, 1)  # standard output (1)
        os.dup2(fdtemp, 2)  # standard error (2)

        # Now the fork/setsid/fork..
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if pid != 0:
            # In the father: we check if our child exit correctly
            # it has to write the pid of our futur little child..
            def do_exit(sig, frame):
                logger.error("Timeout waiting child while it should have quickly returned ; something weird happened")
                os.kill(pid, 9)
                sys.exit(1)
            # wait the child process to check its return status:
            signal.signal(signal.SIGALRM, do_exit)
            signal.alarm(3)  # forking & writing a pid in a file should be rather quick..
            # if it's not then something wrong can already be on the way so let's wait max 3 secs here.
            pid, status = os.waitpid(pid, 0)
            if status != 0:
                logger.error("Something weird happened with/during second fork: status=", status)
            os._exit(status != 0)

        # halfway to daemonize..
        os.setsid()
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if pid != 0:
            # we are the last step and the real daemon is actually correctly created at least.
            # we have still the last responsibility to write the pid of the daemon itself.
            self.write_pid(pid)
            os._exit(0)

        self.fpid.close()
        del self.fpid
        self.pid = os.getpid()
        self.debug_output.append("We are now fully daemonized :) pid=%d" % self.pid)
        # We can now output some previously silenced debug ouput
        logger.warning("Printing stored debug messages prior to our daemonization")
        for s in self.debug_output:
            logger.debug(s)
        del self.debug_output

    def do_daemon_init_and_start(self, use_pyro=True):
        self.change_to_user_group()
        self.change_to_workdir()
        self.check_parallel_run()
        if use_pyro:
            self.setup_pyro_daemon()

        # Setting log level
        logger.set_level(self.log_level)
        # Force the debug level if the daemon is said to start with such level
        if self.debug:
            logger.set_level('DEBUG')
        
        # Then start to log all in the local file if asked so
        self.register_local_log()
        if self.is_daemon:
            socket_fds = [sock.fileno() for sock in self.pyro_daemon.get_sockets()]
            # Do not close the local_log file too if it's open
            if self.local_log_fd:
                socket_fds.append(self.local_log_fd)

            socket_fds = tuple(socket_fds)
            self.daemonize(skip_close_fds=socket_fds)
        else:
            self.write_pid()

        # Now we can start our Manager
        # interprocess things. It's important!
        if is_android:
            self.manager = None
        else:
            self.manager = Manager()
        # And make the module manager know it
        self.modules_manager.load_manager(self.manager)

    def setup_pyro_daemon(self):

        if hasattr(self, 'use_ssl'):  # "common" daemon
            ssl_conf = self
        else:
            ssl_conf = self.conf     # arbiter daemon..

        # The SSL part
        if ssl_conf.use_ssl:
            # Maybe this Pyro version do not manage SSL, if so, bailout
            if not hasattr(Pyro.config, 'PYROSSL_CERTDIR'):
                logger.error('Sorry, this Pyro version do not manage SSL.')
                sys.exit(2)
            Pyro.config.PYROSSL_CERTDIR = os.path.abspath(ssl_conf.certs_dir)
            logger.debug("Using ssl certificate directory: %s" % Pyro.config.PYROSSL_CERTDIR)
            Pyro.config.PYROSSL_CA_CERT = os.path.abspath(ssl_conf.ca_cert)
            logger.debug("Using ssl ca cert file: %s" % Pyro.config.PYROSSL_CA_CERT)
            Pyro.config.PYROSSL_CERT = os.path.abspath(ssl_conf.server_cert)
            logger.debug("Using ssl server cert file: %s" % Pyro.config.PYROSSL_CERT)

            if self.hard_ssl_name_check:
                Pyro.config.PYROSSL_POSTCONNCHECK = 1
            else:
                Pyro.config.PYROSSL_POSTCONNCHECK = 0

        # create the server, but Pyro > 4.8 veersion
        # do not have such objets...
        try:
            Pyro.config.PYRO_STORAGE = "."
            Pyro.config.PYRO_COMPRESSION = 1
            Pyro.config.PYRO_MULTITHREADED = 0
        except:
            pass

        self.pyro_daemon = pyro.ShinkenPyroDaemon(self.host, self.port, ssl_conf.use_ssl)

    def get_socks_activity(self, socks, timeout):
        try:
            ins, _, _ = select.select(socks, [], [], timeout)
        except select.error, e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins

    # Find the absolute path of the shinken module directory and returns it.
    def find_modules_path(self):
        import shinken
        # BEWARE: this way of finding path is good if we still
        # DO NOT HAVE CHANGED PWD!!!
        # Now get the module path. It's in fact the directory modules
        # inside the shinken directory. So let's find it.

        self.debug_output.append("modulemanager file %s" % shinken.modulesmanager.__file__)
        modulespath = os.path.abspath(shinken.modulesmanager.__file__)
        self.debug_output.append("modulemanager absolute file %s" % modulespath)
        # We got one of the files
        parent_path = os.path.dirname(os.path.dirname(modulespath))
        modulespath = os.path.join(parent_path, 'shinken', 'modules')
        self.debug_output.append("Using modules path: %s" % (modulespath))

        return modulespath

    # modules can have process, and they can die
    def check_and_del_zombie_modules(self):
        # Active children make a join with every one, useful :)
        act = active_children()
        self.modules_manager.check_alive_instances()
        # and try to restart previous dead :)
        self.modules_manager.try_to_restart_deads()

    # Just give the uid of a user by looking at it's name
    def find_uid_from_name(self):
        try:
            return getpwnam(self.user)[2]
        except KeyError, exp:
            logger.error("The user %s is unknown" % self.user)
            return None

    # Just give the gid of a group by looking at its name
    def find_gid_from_name(self):
        try:
            return getgrnam(self.group)[2]
        except KeyError, exp:
            logger.error("The group %s is unknown" % self.group)
            return None

    # Change user of the running program. Just insult the admin
    # if he wants root run (it can override). If change failed we sys.exit(2)
    def change_to_user_group(self, insane=None):
        if insane is None:
            insane = not self.idontcareaboutsecurity

        if is_android:
            logger.warning("You can't change user on this system")
            return

        # TODO: change user on nt
        if os.name == 'nt':
            logger.warning("You can't change user on this system")
            return

        if (self.user == 'root' or self.group == 'root') and not insane:
            logger.error("You want the application run under the root account?")
            logger.error("I am not agree with it. If you really want it, put:")
            logger.error("idontcareaboutsecurity=yes")
            logger.error("in the config file")
            logger.error("Exiting")
            sys.exit(2)

        uid = self.find_uid_from_name()
        gid = self.find_gid_from_name()

        if uid is None or gid is None:
            logger.error("uid or gid is none. Exiting")
            sys.exit(2)
            
        # Maybe the os module got the initgroups function. If so, try to call it.
        # Do this when we are still root
        if hasattr(os, 'initgroups'):
            logger.info('Trying to initialize additonnal groups for the daemon')
            try:
                os.initgroups(self.user, gid)
            except OSError, e:
                logger.warning('Cannot call the additonnal groups setting with initgroups (%s)' % e.strerror)
        try:
            # First group, then user :)
            os.setregid(gid, gid)
            os.setreuid(uid, uid)
        except OSError, e:
            logger.error("cannot change user/group to %s/%s (%s [%d]). Exiting" % (self.user, self.group, e.strerror, e.errno))
            sys.exit(2)

    # Parse self.config_file and get all properties in it.
    # If some properties need a pythonization, we do it.
    # Also put default value in the properties if some are missing in the config_file
    def parse_config_file(self):
        properties = self.__class__.properties
        if self.config_file is not None:
            config = ConfigParser.ConfigParser()
            config.read(self.config_file)
            if config._sections == {}:
                logger.error("Bad or missing config file: %s " % self.config_file)
                sys.exit(2)
            for (key, value) in config.items('daemon'):
                if key in properties:
                    value = properties[key].pythonize(value)
                setattr(self, key, value)
        else:
            logger.warning("No config file specified, use defaults parameters")
        # Now fill all defaults where missing parameters
        for prop, entry in properties.items():
            if not hasattr(self, prop):
                value = entry.pythonize(entry.default)
                setattr(self, prop, value)

    # Some paths can be relatives. We must have a full path by taking
    # the config file by reference
    def relative_paths_to_full(self, reference_path):
        #print "Create relative paths with", reference_path
        properties = self.__class__.properties
        for prop, entry in properties.items():
            if isinstance(entry, ConfigPathProp):
                path = getattr(self, prop)
                if not os.path.isabs(path):
                    new_path = os.path.join(reference_path, path)
                    #print "DBG: changing", entry, "from", path, "to", new_path
                    path = new_path
                setattr(self, prop, path)
                #print "Setting %s for %s" % (path, prop)

    def manage_signal(self, sig, frame):
        logger.debug("I'm process %d and I received signal %s" % (os.getpid(), str(sig)))
        if sig == 10:  # if USR1, ask a memory dump
            self.need_dump_memory = True
        elif sig == 12: # if USR2, ask objects dump
            self.need_objects_dump = True
        else:  # Ok, really ask us to die :)
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
            for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1, signal.SIGUSR2):
                signal.signal(sig, func)

    def get_header(self):
        return ["Shinken %s" % VERSION,
                "Copyright (c) 2009-2011:",
                "Gabes Jean (naparuba@gmail.com)",
                "Gerhard Lausser, Gerhard.Lausser@consol.de",
                "Gregory Starck, g.starck@gmail.com",
                "Hartmut Goebel, h.goebel@goebel-consult.de",
                "License: AGPL"]

    def print_header(self):
        for line in self.get_header():
            logger.info(line)

# Wait up to timeout to handle the pyro daemon requests.
# If suppl_socks is given it also looks for activity on that list of fd.
# Returns a 3-tuple:
# If timeout: first arg is 0, second is [], third is possible system time change value
# If not timeout (== some fd got activity):
#  - first arg is elapsed time since wait,
#  - second arg is sublist of suppl_socks that got activity.
#  - third arg is possible system time change value, or 0 if no change.
    def handleRequests(self, timeout, suppl_socks=None):

        if suppl_socks is None:
            suppl_socks = []
        before = time.time()
        socks = self.pyro_daemon.get_sockets()
        if suppl_socks:
            socks.extend(suppl_socks)
        ins = self.get_socks_activity(socks, timeout)
        tcdiff = self.check_for_system_time_change()
        before += tcdiff
        # Increase our sleep time for the time go in select
        self.sleep_time += time.time() - before
        if len(ins) == 0:  # trivial case: no fd activity:
            return 0, [], tcdiff
        for sock in socks:
            if sock in ins and sock not in suppl_socks:
                self.pyro_daemon.handleRequests(sock)
                ins.remove(sock)
        # Tack in elapsed the WHOLE time, even with handling requests
        elapsed = time.time() - before
        if elapsed == 0:  # we have done a few instructions in 0 second exactly!? quantum computer?
            elapsed = 0.01  # but we absolutely need to return!= 0 to indicate that we got activity
        return elapsed, ins, tcdiff

    # Check for a possible system time change and act correspondingly.
    # If such a change is detected then we return the number of seconds that changed. 0 if no time change was detected.
    # Time change can be positive or negative:
    # positive when we have been sent in the futur and negative if we have been sent in the past.
    def check_for_system_time_change(self):

        now = time.time()
        difference = now - self.t_each_loop

        # If we have more than 15 min time change, we need to compensate it
        if abs(difference) > 900:
            self.compensate_system_time_change(difference)
        else:
            difference = 0

        self.t_each_loop = now

        return difference

    # Default action for system time change. Actually a log is done
    def compensate_system_time_change(self, difference):
        logger.warning('A system time change of %s has been detected.  Compensating...' % difference)

    # Use to wait conf from arbiter.
    # It send us conf in our pyro_daemon. It put the have_conf prop
    # if he send us something
    # (it can just do a ping)
    def wait_for_initial_conf(self, timeout=1.0):
        logger.info("Waiting for initial configuration")
        cur_timeout = timeout
        # Arbiter do not already set our have_conf param
        while not self.new_conf and not self.interrupted:
            elapsed, _, _ = self.handleRequests(cur_timeout)
            if elapsed:
                cur_timeout -= elapsed
                if cur_timeout > 0:
                    continue
                cur_timeout = timeout
            sys.stdout.write(".")
            sys.stdout.flush()

    # We call the function of modules that got the this
    # hook function
    def hook_point(self, hook_name):
        for inst in self.modules_manager.instances:
            full_hook_name = 'hook_' + hook_name
            if hasattr(inst, full_hook_name):
                f = getattr(inst, full_hook_name)
                try:
                    f(self)
                except Exception, exp:
                    logger.warning('The instance %s raised an exception %s. I disabled it, and set it to restart later' % (inst.get_name(), str(exp)))
                    self.modules_manager.set_to_restart(inst)

    # Dummy function for daemons. Get all retention data
    # So a module can save them
    def get_retention_data(self):
        return []

    # Save, to get back all data
    def restore_retention_data(self, data):
        pass
