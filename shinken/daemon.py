#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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
import threading
import traceback
import cStringIO
import logging
import inspect
from Queue import Empty

# Try to see if we are in an android device or not
try:
    import android
    is_android = True
except ImportError:
    is_android = False
    from multiprocessing.managers import SyncManager


import shinken.http_daemon
from shinken.http_daemon import HTTPDaemon, InvalidWorkDir
from shinken.log import logger
from shinken.stats import statsmgr
from shinken.modulesctx import modulesctx
from shinken.modulesmanager import ModulesManager
from shinken.property import StringProp, BoolProp, PathProp, ConfigPathProp, IntegerProp,\
    LogLevelProp
from shinken.misc.common import setproctitle


try:
    import pwd
    import grp
    from pwd import getpwnam
    from grp import getgrnam, getgrall

    def get_cur_user():
        return pwd.getpwuid(os.getuid()).pw_name

    def get_cur_group():
        return grp.getgrgid(os.getgid()).gr_name

    def get_all_groups():
        return getgrall()
except ImportError, exp:  # Like in nt system or Android
    # temporary workaround:
    def get_cur_user():
        return "shinken"

    def get_cur_group():
        return "shinken"

    def get_all_groups():
        return []


# #########################   DAEMON PART    ###############################
# The standard I/O file descriptors are redirected to /dev/null by default.
REDIRECT_TO = getattr(os, "devnull", "/dev/null")

UMASK = 027
from shinken.bin import VERSION

""" TODO: Add some comment about this class for the doc"""
class InvalidPidFile(Exception):
    pass


""" Interface for Inter satellites communications """
class Interface(object):

    #  'app' is to be set to the owner of this interface.
    def __init__(self, app):
        self.app = app
        self.start_time = int(time.time())

        self.running_id = "%d.%d" % (
            self.start_time, random.randint(0, 100000000)
        )


    doc = 'Test the connection to the daemon. Returns: pong'
    def ping(self):
        return "pong"
    ping.need_lock = False
    ping.doc = doc

    doc = 'Get the start time of the daemon'
    def get_start_time(self):
        return self.start_time

    doc = 'Get the current running id of the daemon (scheduler)'
    def get_running_id(self):
        return self.running_id
    get_running_id.need_lock = False
    get_running_id.doc = doc


    doc = 'Send a new configuration to the daemon (internal)'
    def put_conf(self, conf):
        self.app.new_conf = conf
    put_conf.method = 'post'
    put_conf.doc = doc


    doc = 'Ask the daemon to wait a new conf'
    def wait_new_conf(self):
        self.app.cur_conf = None
    wait_new_conf.need_lock = False
    wait_new_conf.doc = doc


    doc = 'Does the daemon got an active configuration'
    def have_conf(self):
        return self.app.cur_conf is not None
    have_conf.need_lock = False
    have_conf.doc = doc


    doc = 'Set the current log level in [NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL, UNKNOWN]'
    def set_log_level(self, loglevel):
        return logger.setLevel(loglevel)
    set_log_level.doc = doc


    doc = 'Get the current log level in [NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL, UNKNOWN]'
    def get_log_level(self):
        return {logging.NOTSET: 'NOTSET',
                logging.DEBUG: 'DEBUG',
                logging.INFO: 'INFO',
                logging.WARNING: 'WARNING',
                logging.ERROR: 'ERROR',
                logging.CRITICAL: 'CRITICAL'}.get(logger._level, 'UNKNOWN')
    get_log_level.doc = doc

    doc = 'List the methods available on the daemon'
    def api(self):
        return self.app.http_daemon.registered_fun_names
    api.doc = doc


    doc = 'List the api methods and their parameters'
    def api_full(self):
        res = {}
        for (fname, f) in self.app.http_daemon.registered_fun.iteritems():
            fclean = fname.replace('_', '-')
            argspec = inspect.getargspec(f)
            args = [a for a in argspec.args if a != 'self']
            defaults = self.app.http_daemon.registered_fun_defaults.get(fname, {})
            e = {}
            # Get a string about the args and co
            _s_nondef_args = ', '.join([a for a in args if a not in defaults])
            _s_def_args = ', '.join(['%s=%s' % (k, v) for (k, v) in defaults.iteritems()])
            _s_args = ''
            if _s_nondef_args:
                _s_args += _s_nondef_args
            if _s_def_args:
                _s_args += ', ' + _s_def_args
            e['proto'] = '%s(%s)' % (fclean, _s_args)
            e['need_lock'] = getattr(f, 'need_lock', True)
            e['method'] = getattr(f, 'method', 'GET').upper()
            e['encode'] = getattr(f, 'encode', 'json')
            doc = getattr(f, 'doc', '')
            if doc:
                e['doc'] = doc
            res[fclean] = e
        return res
    api.doc = doc


# If we are under android, we can't give parameters
if is_android:
    DEFAULT_WORK_DIR = '/sdcard/sl4a/scripts/'
    DEFAULT_LIB_DIR = DEFAULT_WORK_DIR
else:
    DEFAULT_WORK_DIR = '/var/run/shinken/'
    DEFAULT_LIB_DIR = '/var/lib/shinken/'


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
        'modules_dir':    PathProp(default=os.path.join(DEFAULT_LIB_DIR, 'modules')),
        'host':          StringProp(default='0.0.0.0'),
        'user':          StringProp(default=get_cur_user()),
        'group':         StringProp(default=get_cur_group()),
        'use_ssl':       BoolProp(default=False),
        'server_key':     StringProp(default='etc/certs/server.key'),
        'ca_cert':       StringProp(default='etc/certs/ca.pem'),
        'server_cert':   StringProp(default='etc/certs/server.cert'),
        'use_local_log': BoolProp(default=True),
        'log_level':     LogLevelProp(default='WARNING'),
        'hard_ssl_name_check':    BoolProp(default=False),
        'idontcareaboutsecurity': BoolProp(default=False),
        'daemon_enabled': BoolProp(default=True),
        'spare':         BoolProp(default=False),
        'max_queue_size': IntegerProp(default=0),
        'daemon_thread_pool_size': IntegerProp(default=8),
        'http_backend':  StringProp(default='auto'),
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

        self.http_daemon = None

        # Log init
        # self.log = logger
        # self.log.load_obj(self)
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

        # We will initialize the Manager() when we load modules
        # and be really forked()
        self.manager = None

        os.umask(UMASK)
        self.set_exit_handler()


    # At least, lose the local log file if needed
    def do_stop(self):
        # Maybe the modules manager is not even created!
        if getattr(self, 'modules_manager', None):
            # We save what we can but NOT for the scheduler
            # because the current sched object is a dummy one
            # and the old one has already done it!
            if not hasattr(self, 'sched'):
                self.hook_point('save_retention')
            # And we quit
            print('Stopping all modules')
            self.modules_manager.stop_all()
            print('Stopping inter-process message')
        if self.http_daemon:
            # Release the lock so the daemon can shutdown without problem
            try:
                self.http_daemon.lock.release()
            except Exception:
                pass
            self.http_daemon.shutdown()


    def request_stop(self):
        self.unlink()
        self.do_stop()
        # Brok facilities are no longer available simply print the message to STDOUT
        print("Stopping daemon. Exiting")
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
        logger.info("I correctly loaded the modules: [%s]",
                    ','.join([inst.get_name() for inst in self.modules_manager.instances]))


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


    def load_modules_manager(self):
        if not modulesctx.get_modulesdir():
            modulesctx.set_modulesdir(self.find_modules_path())
        self.modules_manager = ModulesManager(self.name, self.find_modules_path(), [])
        # Set the modules watchdogs
        # TOFIX: Beware, the arbiter do not have the max_queue_size property
        self.modules_manager.set_max_queue_size(getattr(self, 'max_queue_size', 0))
        # And make the module manager load the sub-process Queue() manager
        self.modules_manager.load_manager(self.manager)


    # create a dir and set to my user
    def __create_directory(self, d):
        if not os.path.exists(d):
            os.mkdir(d)
            # And set the user as shinken so the sub-fork can
            # reopen the pid when no more root
            if os.name != 'nt':
                uid = self.find_uid_from_name()
                gid = self.find_gid_from_name()
                os.chown(d, uid, gid)


    def change_to_workdir(self):
        self.workdir = os.path.abspath(self.workdir)
        try:
            # If the directory is missing, try to create it for me
            if not os.path.exists(self.workdir):
                self.__create_directory(self.workdir)
            os.chdir(self.workdir)
        except Exception, e:
            raise InvalidWorkDir(e)
        self.debug_output.append("Successfully changed to workdir: %s" % (self.workdir))


    def unlink(self):
        logger.debug("Unlinking %s", self.pidfile)
        try:
            os.unlink(self.pidfile)
        except Exception, e:
            logger.error("Got an error unlinking our pidfile: %s", e)


    # Look if we need a local log or not
    def register_local_log(self):
        # The arbiter doesn't have such attribute
        if hasattr(self, 'use_local_log') and self.use_local_log:
            try:
                # self.local_log_fd = self.log.register_local_log(self.local_log)
                self.local_log_fd = logger.register_local_log(self.local_log)
            except IOError, exp:
                logger.error("Opening the log file '%s' failed with '%s'", self.local_log, exp)
                sys.exit(2)
            logger.info("Using the local log file '%s'", self.local_log)


    # Only on linux: Check for /dev/shm write access
    def check_shm(self):
        import stat
        shm_path = '/dev/shm'
        if os.name == 'posix' and os.path.exists(shm_path):
            # We get the access rights, and we check them
            mode = stat.S_IMODE(os.lstat(shm_path)[stat.ST_MODE])
            if not mode & stat.S_IWUSR or not mode & stat.S_IRUSR:
                logger.critical("The directory %s is not writable or readable."
                                "Please make it read writable: %s", shm_path, shm_path)
                sys.exit(2)


    def __open_pidfile(self, write=False):
        # if problem on opening or creating file it'll be raised to the caller:
        try:
            p = os.path.abspath(self.pidfile)
            # Look if the pid directory is existing or not
            # (some systems are cleaning /var/run directories, yes I look
            # at you debian 8)
            p_dir = os.path.dirname(p)
            if not os.path.exists(p_dir):
                self.__create_directory(p_dir)
            self.debug_output.append("Opening pid file: %s" % p)
            # Windows do not manage the rw+ mode,
            # so we must open in read mode first, then reopen it write mode...
            if not write and os.path.exists(p):
                self.fpid = open(p, 'r+')
            else:  # If it doesn't exist too, we create it as void
                self.fpid = open(p, 'w+')
        except Exception as err:
            raise InvalidPidFile(err)


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
            pid = int(self.fpid.readline().strip(' \r\n'))
        except Exception as err:
            logger.info("Stale pidfile exists at %s (%s). Reusing it.", err, self.pidfile)
            return

        try:
            os.kill(pid, 0)
        except Exception as err:  # consider any exception as a stale pidfile.
            # this includes :
            #  * PermissionError when a process with same pid exists but is executed by another user
            #  * ProcessLookupError: [Errno 3] No such process
            logger.info("Stale pidfile exists (%s), Reusing it.", err)
            return

        if not self.do_replace:
            raise SystemExit("valid pidfile exists (pid=%s) and not forced to replace. Exiting."
                             % pid)

        self.debug_output.append("Replacing previous instance %d" % pid)
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGQUIT)
        except os.error as err:
            if err.errno != errno.ESRCH:
                raise

        self.fpid.close()
        # TODO: give some time to wait that previous instance finishes?
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
        del self.fpid  # no longer needed


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

        # We close all fd but what we need:
        self.close_fds(skip_close_fds + (self.fpid.fileno(), fdtemp))

        os.dup2(fdtemp, 1)  # standard output (1)
        os.dup2(fdtemp, 2)  # standard error (2)

        # Now the fork/setsid/fork..
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        if pid != 0:
            # In the father: we check if our child exit correctly
            # it has to write the pid of our future little child..
            def do_exit(sig, frame):
                logger.error("Timeout waiting child while it should have quickly returned ;"
                             "something weird happened")
                os.kill(pid, 9)
                sys.exit(1)
            # wait the child process to check its return status:
            signal.signal(signal.SIGALRM, do_exit)
            signal.alarm(3)  # forking & writing a pid in a file should be rather quick..
            # if it's not then something wrong can already be on the way so let's wait max
            # 3 secs here.
            pid, status = os.waitpid(pid, 0)
            if status != 0:
                logger.error("Something weird happened with/during second fork: status= %s", status)
            os._exit(status != 0)

        # halfway to daemonize..
        os.setsid()
        try:
            pid = os.fork()
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))
        if pid != 0:
            # we are the last step and the real daemon is actually correctly created at least.
            # we have still the last responsibility to write the pid of the daemon itself.
            self.write_pid(pid)
            os._exit(0)

        self.fpid.close()
        del self.fpid
        self.pid = os.getpid()
        self.debug_output.append("We are now fully daemonized :) pid=%d" % self.pid)
        # We can now output some previously silenced debug output
        logger.info("Printing stored debug messages prior to our daemonization")
        for s in self.debug_output:
            logger.info(s)
        del self.debug_output
        self.set_proctitle()


    if is_android:
        def _create_manager(self):
            pass
    else:
        # The Manager is a sub-process, so we must be sure it won't have
        # a socket of your http server alive
        def _create_manager(self):
            manager = SyncManager(('127.0.0.1', 0))
            def close_http_daemon(daemon):
                try:
                    # Be sure to release the lock so there won't be lock in shutdown phase
                    daemon.lock.release()
                except Exception, exp:
                    pass
                daemon.shutdown()
            # Some multiprocessing lib got problems with start() that cannot take args
            # so we must look at it before
            startargs = inspect.getargspec(manager.start)
            # startargs[0] will be ['self'] if old multiprocessing lib
            # and ['self', 'initializer', 'initargs'] in newer ones
            # note: windows do not like pickle http_daemon...
            if os.name != 'nt' and len(startargs[0]) > 1:
                manager.start(close_http_daemon, initargs=(self.http_daemon,))
            else:
                manager.start()
            return manager


    # Main "go daemon" mode. Will launch the double fork(), close old file descriptor
    # and such things to have a true DAEMON :D
    # use_pyro= open the TCP port for communication
    # fake= use for test to do not launch runonly feature, like the stats reaper thread
    def do_daemon_init_and_start(self, use_pyro=True, fake=False):
        self.change_to_workdir()        
        self.change_to_user_group()
        self.check_parallel_run()
        if use_pyro:
            self.setup_pyro_daemon()

        # Setting log level
        logger.setLevel(self.log_level)
        # Force the debug level if the daemon is said to start with such level
        if self.debug:
            logger.setLevel('DEBUG')

        # Then start to log all in the local file if asked so
        self.register_local_log()
        if self.is_daemon:
            socket_fds = [sock.fileno() for sock in self.http_daemon.get_sockets()]
            # Do not close the local_log file too if it's open
            if self.local_log_fd:
                socket_fds.append(self.local_log_fd)

            socket_fds = tuple(socket_fds)
            self.daemonize(skip_close_fds=socket_fds)
        else:
            self.write_pid()

        # Now we can start our Manager
        # interprocess things. It's important!
        self.manager = self._create_manager()

        # We can start our stats thread but after the double fork() call and if we are not in
        # a test launch (time.time() is hooked and will do BIG problems there)
        if not fake:
            statsmgr.launch_reaper_thread()

        # Now start the http_daemon thread
        self.http_thread = None
        if use_pyro:
            # Directly acquire it, so the http_thread will wait for us
            self.http_daemon.lock.acquire()
            self.http_thread = threading.Thread(None, self.http_daemon_thread, 'http_thread')
            # Don't lock the main thread just because of the http thread
            self.http_thread.daemon = True
            self.http_thread.start()


    # TODO: we do not use pyro anymore, change the function name....
    def setup_pyro_daemon(self):
        if hasattr(self, 'use_ssl'):  # "common" daemon
            ssl_conf = self
        else:
            ssl_conf = self.conf     # arbiter daemon..

        use_ssl = ssl_conf.use_ssl
        ca_cert = ssl_cert = ssl_key = ''
        http_backend = self.http_backend

        # The SSL part
        if use_ssl:
            ssl_cert = os.path.abspath(str(ssl_conf.server_cert))
            if not os.path.exists(ssl_cert):
                logger.error('Error : the SSL certificate %s is missing (server_cert).'
                             'Please fix it in your configuration', ssl_cert)
                sys.exit(2)
            ca_cert = os.path.abspath(str(ssl_conf.ca_cert))
            logger.info("Using ssl ca cert file: %s", ca_cert)
            ssl_key = os.path.abspath(str(ssl_conf.server_key))
            if not os.path.exists(ssl_key):
                logger.error('Error : the SSL key %s is missing (server_key).'
                             'Please fix it in your configuration', ssl_key)
                sys.exit(2)
            logger.info("Using ssl server cert/key files: %s/%s", ssl_cert, ssl_key)

            if ssl_conf.hard_ssl_name_check:
                logger.info("Enabling hard SSL server name verification")

        # Let's create the HTTPDaemon, it will be exec after
        self.http_daemon = HTTPDaemon(self.host, self.port, http_backend,
                                      use_ssl, ca_cert, ssl_key,
                                      ssl_cert, ssl_conf.hard_ssl_name_check,
                                      self.daemon_thread_pool_size)
        # TODO: fix this "hack" :
        shinken.http_daemon.daemon_inst = self.http_daemon

    # Global loop part
    def get_socks_activity(self, socks, timeout):
        # some os are not managing void socks list, so catch this
        # and just so a simple sleep instead
        if socks == []:
            time.sleep(timeout)
            return []
        try:
            ins, _, _ = select.select(socks, [], [], timeout)
        except select.error, e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins

    # Find the absolute path of the shinken module directory and returns it.
    # If the directory do not exist, we must exit!
    def find_modules_path(self):
        modules_dir = getattr(self, 'modules_dir', None)
        if not modules_dir:
            modules_dir = modulesctx.get_modulesdir()
            if not modules_dir:
                logger.error("Your configuration is missing the path to the modules (modules_dir). "
                             "I set it by default to /var/lib/shinken/modules. Please configure it")
                modules_dir = '/var/lib/shinken/modules'
                modulesctx.set_modulesdir(modules_dir)
            self.modules_dir = modules_dir
        logger.info("Modules directory: %s", modules_dir)
        if not os.path.exists(modules_dir):
            raise RuntimeError("The modules directory '%s' is missing! Bailing out."
                               "Please fix your configuration" % (modules_dir,))
        return modules_dir


    # modules can have process, and they can die
    def check_and_del_zombie_modules(self):
        # Active children make a join with every one, useful :)
        self.modules_manager.check_alive_instances()
        # and try to restart previous dead :)
        self.modules_manager.try_to_restart_deads()


    # Just give the uid of a user by looking at it's name
    def find_uid_from_name(self):
        try:
            return getpwnam(self.user)[2]
        except KeyError, exp:
            logger.error("The user %s is unknown", self.user)
            return None

    # Just give the gid of a group by looking at its name
    def find_gid_from_name(self):
        try:
            return getgrnam(self.group)[2]
        except KeyError, exp:
            logger.error("The group %s is unknown", self.group)
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
            logger.error("I do not agree with it. If you really want it, put:")
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
            logger.info('Trying to initialize additional groups for the daemon')
            try:
                os.initgroups(self.user, gid)
            except OSError, e:
                logger.warning('Cannot call the additional groups setting with initgroups (%s)',
                               e.strerror)
        elif hasattr(os, 'setgroups'):
            groups = [gid] + \
                     [group.gr_gid for group in get_all_groups() if self.user in group.gr_mem]
            try:
                os.setgroups(groups)
            except OSError, e:
                logger.warning('Cannot call the additional groups setting with setgroups (%s)',
                               e.strerror)
        try:
            # First group, then user :)
            os.setregid(gid, gid)
            os.setreuid(uid, uid)
        except OSError, e:
            logger.error("cannot change user/group to %s/%s (%s [%d]). Exiting",
                         self.user, self.group, e.strerror, e.errno)
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
                logger.error("Bad or missing config file: %s ", self.config_file)
                sys.exit(2)
            try:
                for (key, value) in config.items('daemon'):
                    if key in properties:
                        value = properties[key].pythonize(value)
                    setattr(self, key, value)
            except ConfigParser.InterpolationMissingOptionError, e:
                e = str(e)
                wrong_variable = e.split('\n')[3].split(':')[1].strip()
                logger.error("Incorrect or missing variable '%s' in config file : %s",
                             wrong_variable, self.config_file)
                sys.exit(2)
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
        # print "Create relative paths with", reference_path
        properties = self.__class__.properties
        for prop, entry in properties.items():
            if isinstance(entry, ConfigPathProp):
                path = getattr(self, prop)
                if not os.path.isabs(path):
                    new_path = os.path.join(reference_path, path)
                    # print "DBG: changing", entry, "from", path, "to", new_path
                    path = new_path
                setattr(self, prop, path)
                # print "Setting %s for %s" % (path, prop)


    def manage_signal(self, sig, frame):
        logger.debug("I'm process %d and I received signal %s", os.getpid(), str(sig))
        if sig == signal.SIGUSR1:  # if USR1, ask a memory dump
            self.need_dump_memory = True
        elif sig == signal.SIGUSR2:  # if USR2, ask objects dump
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

    def set_proctitle(self):
        setproctitle("shinken-%s" % self.name)

    def get_header(self):
        return ["Shinken %s" % VERSION,
                "Copyright (c) 2009-2014:",
                "Gabes Jean (naparuba@gmail.com)",
                "Gerhard Lausser, Gerhard.Lausser@consol.de",
                "Gregory Starck, g.starck@gmail.com",
                "Hartmut Goebel, h.goebel@goebel-consult.de",
                "License: AGPL"]


    def print_header(self):
        for line in self.get_header():
            logger.info(line)


    # Main fonction of the http daemon thread will loop forever unless we stop the root daemon
    def http_daemon_thread(self):
        logger.info("Starting HTTP daemon")

        # The main thing is to have a pool of X concurrent requests for the http_daemon,
        # so "no_lock" calls can always be directly answer without having a "locked" version to
        # finish
        try:
            self.http_daemon.run()
        except Exception, exp:
            logger.error('The HTTP daemon failed with the error %s, exiting', str(exp))
            output = cStringIO.StringIO()
            traceback.print_exc(file=output)
            logger.error("Back trace of this error: %s", output.getvalue())
            output.close()
            self.do_stop()
            # Hard mode exit from a thread
            os._exit(2)


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
        socks = []
        if suppl_socks:
            socks.extend(suppl_socks)
        # Release the lock so the http_thread can manage request during we are waiting
        if self.http_daemon:
            self.http_daemon.lock.release()
        # Ok give me the socks taht moved during the timeout max
        ins = self.get_socks_activity(socks, timeout)
        # Ok now get back the global lock!
        if self.http_daemon:
            self.http_daemon.lock.acquire()
        tcdiff = self.check_for_system_time_change()
        before += tcdiff
        # Increase our sleep time for the time go in select
        self.sleep_time += time.time() - before
        if len(ins) == 0:  # trivial case: no fd activity:
            return 0, [], tcdiff
        # HERE WAS THE HTTP, but now it's managed in an other thread
        # for sock in socks:
        #    if sock in ins and sock not in suppl_socks:
        #        ins.remove(sock)
        # Track in elapsed the WHOLE time, even with handling requests
        elapsed = time.time() - before
        if elapsed == 0:  # we have done a few instructions in 0 second exactly!? quantum computer?
            elapsed = 0.01  # but we absolutely need to return!= 0 to indicate that we got activity
        return elapsed, ins, tcdiff


    # Check for a possible system time change and act correspondingly.
    # If such a change is detected then we return the number of seconds that changed.
    # 0 if no time change was detected.
    # Time change can be positive or negative:
    # positive when we have been sent in the future and negative if we have been sent in the past.
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
        logger.warning('A system time change of %s has been detected.  Compensating...', difference)


    # Use to wait conf from arbiter.
    # It send us conf in our http_daemon. It put the have_conf prop
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
        _t = time.time()
        for inst in self.modules_manager.instances:
            full_hook_name = 'hook_' + hook_name
            if hasattr(inst, full_hook_name):
                f = getattr(inst, full_hook_name)
                try:
                    f(self)
                except Exception as exp:
                    logger.warning('The instance %s raised an exception %s. I disabled it,'
                                   'and set it to restart later', inst.get_name(), str(exp))
                    self.modules_manager.set_to_restart(inst)
        statsmgr.incr('core.hook.%s' % hook_name, time.time() - _t)


    # Dummy function for daemons. Get all retention data
    # So a module can save them
    def get_retention_data(self):
        return []


    # Save, to get back all data
    def restore_retention_data(self, data):
        pass


    # Dummy function for having the stats main structure before sending somewhere
    def get_stats_struct(self):
        r = {'metrics': [], 'version': VERSION, 'name': '', 'type': '', 'modules':
             {'internal': {}, 'external': {}}}
        modules = r['modules']

        # first get data for all internal modules
        for mod in self.modules_manager.get_internal_instances():
            mname = mod.get_name()
            state = {True: 'ok', False: 'stopped'}[(mod not in self.modules_manager.to_restart)]
            e = {'name': mname, 'state': state}
            modules['internal'][mname] = e
        # Same but for external ones
        for mod in self.modules_manager.get_external_instances():
            mname = mod.get_name()
            state = {True: 'ok', False: 'stopped'}[(mod not in self.modules_manager.to_restart)]
            e = {'name': mname, 'state': state}
            modules['external'][mname] = e

        return r

    @staticmethod
    def print_unrecoverable(trace):
        logger.critical("I got an unrecoverable error. I have to exit.")
        logger.critical("You can get help at https://github.com/naparuba/shinken")
        logger.critical("If you think this is a bug, create a new ticket including"
                        "details mentioned in the README")
        logger.critical("Back trace of the error: %s", trace)

    def get_objects_from_from_queues(self):
        ''' Get objects from "from" queues and add them.
        :return: True if we got some objects, False otherwise.
        '''
        had_some_objects = False
        for queue in self.modules_manager.get_external_from_queues():
            while True:
                try:
                    o = queue.get(block=False)
                except (Empty, IOError, EOFError) as err:
                    if not isinstance(err, Empty):
                        logger.error("An external module queue got a problem '%s'", str(exp))
                    break
                else:
                    had_some_objects = True
                    self.add(o)
        return had_some_objects
