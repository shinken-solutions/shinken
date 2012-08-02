#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


# Try to see if we are in an android device or not
is_android = True
try:
    import android
except ImportError:
    is_android = False

import sys
import os
import time
import traceback
import threading
import random
import smtplib
random.seed(time.time())
import uuid
from Queue import Empty
import socket
import hashlib
import zipfile
import tempfile
import shutil

from shinken.objects.config import Config
from shinken.objects.pack import Pack, Packs
from shinken.external_command import ExternalCommandManager
from shinken.dispatcher import Dispatcher
from shinken.daemon import Daemon, Interface
from shinken.log import logger
from shinken.brok import Brok
from shinken.external_command import ExternalCommand
from shinken.util import safe_print, strip_and_uniq
from shinken.skonfuiworker import SkonfUIWorker
from shinken.message import Message
from shinken.misc.datamanagerhostd import datamgr
from shinken.modulesmanager import ModulesManager

# DBG: code this!
from shinken.objects import Contact

# Now the bottle HTTP part :)
from shinken.webui.bottle import Bottle, run, static_file, view, route, request, response
# Debug
import shinken.webui.bottle as bottle
bottle.debug(True)

# Import bottle lib to make bottle happy
bottle_dir = os.path.abspath(os.path.dirname(bottle.__file__))
sys.path.insert(0, bottle_dir)

bottle.TEMPLATE_PATH.append(os.path.join(bottle_dir, 'views'))
bottle.TEMPLATE_PATH.append(bottle_dir)

try:
    from pymongo.connection import Connection
except ImportError:
    Connection = None


# Interface for the other Arbiter
# It connects, and together we decide who's the Master and who's the Slave, etc.
# Here is a also a function to get a new conf from the master
class IForArbiter(Interface):

    def have_conf(self, magic_hash):
        # I've got a conf and a good one
        if self.app.cur_conf and self.app.cur_conf.magic_hash == magic_hash:
            return True
        else:  # I've no conf or a bad one
            return False

    # The master Arbiter is sending us a new conf. Ok, we take it
    def put_conf(self, conf):
        super(IForArbiter, self).put_conf(conf)
        self.app.must_run = False

    def get_config(self):
        return self.app.conf

    # The master arbiter asks me not to run!
    def do_not_run(self):
        # If i'm the master, then F**K YOU!
        if self.app.is_master:
            print "Some f***ing idiot asks me not to run. I'm a proud master, so I decide to run anyway"
        # Else, I'm just a spare, so I listen to my master
        else:
            print "Someone asks me not to run"
            self.app.last_master_speack = time.time()
            self.app.must_run = False

    # Here a function called by check_shinken to get daemon status
    def get_satellite_status(self, daemon_type, daemon_name):
        daemon_name_attr = daemon_type + "_name"
        daemons = self.app.get_daemons(daemon_type)
        if daemons:
            for dae in daemons:
                if hasattr(dae, daemon_name_attr) and getattr(dae, daemon_name_attr) == daemon_name:
                    if hasattr(dae, 'alive') and hasattr(dae, 'spare'):
                        return {'alive': dae.alive, 'spare': dae.spare}
        return None

    # Here a function called by check_shinken to get daemons list
    def get_satellite_list(self, daemon_type):
        satellite_list = []
        daemon_name_attr = daemon_type + "_name"
        daemons = self.app.get_daemons(daemon_type)
        if daemons:
            for dae in daemons:
                if hasattr(dae, daemon_name_attr):
                    satellite_list.append(getattr(dae, daemon_name_attr))
                else:
                    # If one daemon has no name... ouch!
                    return None
            return satellite_list
        return None

    # Dummy call. We are a master, we managed what we want
    def what_i_managed(self):
        return []

    def get_all_states(self):
        res = {'arbiter': self.app.conf.arbiters,
               'scheduler': self.app.conf.schedulers,
               'poller': self.app.conf.pollers,
               'reactionner': self.app.conf.reactionners,
               'receiver': self.app.conf.receivers,
               'broker': self.app.conf.brokers}
        return res


# Main Skonf Class
class Hostd(Daemon):

    def __init__(self, config_files, is_daemon, do_replace, verify_only, debug, debug_file):

        super(Hostd, self).__init__('hostd', config_files[0], is_daemon, do_replace, debug, debug_file)

        self.config_files = config_files

        self.verify_only = verify_only

        self.broks = {}
        self.is_master = False

        self.nb_broks_send = 0

        # Now tab for external_commands
        self.external_commands = []

        self.fifo = None

        # Use to know if we must still be alive or not
        self.must_run = True

        self.interface = IForArbiter(self)
        self.conf = Config()

        self.workers = {}   # dict of active workers

        self.host_templates = None
        self.service_templates = None
        self.contact_templates = None
        self.timeperiod_templates = None

        self.datamgr = datamgr

    # Use for adding things like broks
    def add(self, b):
        if isinstance(b, Brok):
            self.broks[b.id] = b
        elif isinstance(b, ExternalCommand):
            self.external_commands.append(b)
        else:
            logger.warning('Cannot manage object type %s (%s)' % (type(b), b))

    def load_config_file(self):
        print "Loading configuration"
        # REF: doc/shinken-conf-dispatching.png (1)
        buf = self.conf.read_config(self.config_files)
        raw_objects = self.conf.read_config_buf(buf)

        print "Opening local log file"

        # First we need to get arbiters and modules first
        # so we can ask them some objects too
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')

        self.conf.early_arbiter_linking()

        self.modules = []
        print "Loading modules", getattr(self.conf, 'hostd_modules', '')
        modules_names = getattr(self.conf, 'hostd_modules', '').split(',')
        modules_names = strip_and_uniq(modules_names)
        for mod_name in modules_names:
            m = self.conf.modules.find_by_name(mod_name)
            if not m:
                logger.error('cannot find module %s' % mod_name)
                sys.exit(2)
            self.modules.append(m)

        logger.info("My own modules: " + ','.join([m.get_name() for m in self.modules]))

        self.override_modules_path = getattr(self.conf, 'override_modules_path', '')
        if self.override_modules_path:
            # We override the module manager
            print "Overring module manager"
            self.modules_manager = ModulesManager('hostd', self.override_modules_path, [])

        # we request the instances without them being *started*
        # (for these that are concerned ("external" modules):
        # we will *start* these instances after we have been daemonized (if requested)
        self.modules_manager.set_modules(self.modules)
        self.do_load_modules()

        for inst in self.modules_manager.instances:
            f = getattr(inst, 'load', None)
            if f and callable(f):
                f(self)

        ### Resume standard operations ###
        self.conf.create_objects(raw_objects)

        # Maybe conf is already invalid
        if not self.conf.conf_is_correct:
            sys.exit("***> One or more problems was encountered while processing the config files...")

        # Change Nagios2 names to Nagios3 ones
        self.conf.old_properties_names_to_new()

        # Manage all post-conf modules
        self.hook_point('early_configuration')

        # Load all file triggers
        #self.conf.load_packs()

        # Create Template links
        self.conf.linkify_templates()

        # All inheritances
        #self.conf.apply_inheritance()

        # Explode between types
        #self.conf.explode()

        # Create Name reversed list for searching list
        self.conf.create_reversed_list()

        # Cleaning Twins objects
        self.conf.remove_twins()

        # Implicit inheritance for services
        #self.conf.apply_implicit_inheritance()

        # Fill default values
        super(Config, self.conf).fill_default()

        # Remove templates from config
        # SAVE TEMPLATES
        #self.host_templates = self.conf.hosts.templates
        #self.service_templates = self.conf.services.templates
        #self.contact_templates = self.conf.contacts.templates
        #self.timeperiod_templates = self.conf.timeperiods.templates
        #self.packs = self.conf.packs
        # Then clean for other parts
        #self.conf.remove_templates()

        # We removed templates, and so we must recompute the
        # search lists
        self.conf.create_reversed_list()

        # Pythonize values
        #self.conf.pythonize()
        super(Config, self.conf).pythonize()

        # Linkify objects each others
        #self.conf.linkify()

        # applying dependencies
        #self.conf.apply_dependencies()

        # Hacking some global parameter inherited from Nagios to create
        # on the fly some Broker modules like for status.dat parameters
        # or nagios.log one if there are no already available
        #self.conf.hack_old_nagios_parameters()

        # Raise warning about curently unmanaged parameters
        #if self.verify_only:
        #    self.conf.warn_about_unmanaged_parameters()

        # Exlode global conf parameters into Classes
        #self.conf.explode_global_conf()

        # set ourown timezone and propagate it to other satellites
        #self.conf.propagate_timezone_option()

        # Look for business rules, and create the dep tree
        #self.conf.create_business_rules()
        # And link them
        #self.conf.create_business_rules_dependencies()

        # Warn about useless parameters in Shinken
        #if self.verify_only:
        #    self.conf.notice_about_useless_parameters()

        # Manage all post-conf modules
        self.hook_point('late_configuration')

        # Correct conf?
        #self.conf.is_correct()

        #If the conf is not correct, we must get out now
        #if not self.conf.conf_is_correct:
        #    sys.exit("Configuration is incorrect, sorry, I bail out")

        # REF: doc/shinken-conf-dispatching.png (2)
        #logger.info("Cutting the hosts and services into parts")
        #self.confs = self.conf.cut_into_parts()

        # The conf can be incorrect here if the cut into parts see errors like
        # a realm with hosts and not schedulers for it
        if not self.conf.conf_is_correct:
            self.conf.show_errors()
        #    sys.exit("Configuration is incorrect, sorry, I bail out")
        else:
            logger.info('Things look okay - No serious problems were detected during the pre-flight check')

        # Now clean objects of temporary/unecessary attributes for live work:
        self.conf.clean()

        # Exit if we are just here for config checking
        if self.verify_only:
            sys.exit(0)

        # Some properties need to be "flatten" (put in strings)
        # before being send, like realms for hosts for example
        # BEWARE: after the cutting part, because we stringify some properties
        #self.conf.prepare_for_sending()

        # Ok, here we must check if we go on or not.
        # TODO: check OK or not
        self.use_local_log = self.conf.use_local_log
        self.log_level = logger.get_level_id(self.conf.log_level)
        self.local_log = self.conf.local_log
        self.pidfile = os.path.abspath(self.conf.lock_file)
        self.idontcareaboutsecurity = self.conf.idontcareaboutsecurity
        self.user = self.conf.shinken_user
        self.group = self.conf.shinken_group
        self.override_plugins = getattr(self.conf, 'override_plugins', None)
        self.http_port = int(getattr(self.conf, 'http_port', '7765'))

        self.share_dir = self.conf.share_dir
        logger.info('Using share directory %s' % self.share_dir)

        self.packs_home = self.conf.packs_home
        logger.info('Using pack home %s' % self.packs_home)

        self.auth_secret = self.conf.auth_secret.encode('utf8', 'replace')

        # If the user set a workdir, let use it. If not, use the
        # pidfile directory
        if self.conf.workdir == '':
            self.workdir = os.path.abspath(os.path.dirname(self.pidfile))
        else:
            self.workdir = self.conf.workdir

        ##  We need to set self.host & self.port to be used by do_daemon_init_and_start
        self.host = '0.0.0.0'
        self.port = 0

        logger.info("Configuration Loaded")
        print ""

    def load_web_configuration(self):
        self.plugins = []

        #self.http_port = 7765 # int(getattr(modconf, 'port', '7767'))
        self.http_host = '0.0.0.0'  # getattr(modconf, 'host', '0.0.0.0')
        #self.auth_secret = 'YOUDONTKNOWIT'.encode('utf8', 'replace') # getattr(modconf, 'auth_secret').encode('utf8', 'replace')
        self.http_backend = 'auto'  # getattr(modconf, 'http_backend', 'auto')
        self.login_text = None  # getattr(modconf, 'login_text', None)
        self.allow_html_output = False  # to_bool(getattr(modconf, 'allow_html_output', '0'))
        self.remote_user_enable = '0'  # getattr(modconf, 'remote_user_enable', '0')
        self.remote_user_variable = 'X_REMOTE_USER'  # getattr(modconf, 'remote_user_variable', 'X_REMOTE_USER')

        # Load the photo dir and make it a absolute path
        self.photo_dir = 'photos'  # getattr(modconf, 'photo_dir', 'photos')
        self.photo_dir = os.path.abspath(self.photo_dir)
        print "Webui: using the backend", self.http_backend

    # We check if the photo directory exists. If not, try to create it
    def check_photo_dir(self):
        print "Checking photo path", self.photo_dir
        if not os.path.exists(self.photo_dir):
            print "Truing to create photo dir", self.photo_dir
            try:
                os.mkdir(self.photo_dir)
            except Exception, exp:
                print "Photo dir creation failed", exp

    # Main loop function
    def main(self):
        try:
            # Log will be broks
            for line in self.get_header():
                self.log.info(line)

            self.load_config_file()
            self.load_web_configuration()

            self.tmp_pack_path = '/tmp/tmp_packs'
            if not os.path.exists(self.tmp_pack_path):
                os.mkdir(self.tmp_pack_path)

            self.do_daemon_init_and_start()
            #self.uri_arb = self.pyro_daemon.register(self.interface, "ForArbiter")

            # Under Android, we do not have multiprocessing lib
            # so use standard Queue threads things
            # but in multiprocess, we are also using a Queue(). It's just
            # not the same
            if is_android:
                self.returns_queue = Queue()
            else:
                self.returns_queue = self.manager.Queue()

            # create the input queue of all workers
            try:
                if is_android:
                    self.workers_queue = Queue()
                else:
                    self.workers_queue = self.manager.Queue()
            # If we got no /dev/shm on linux, we can got problem here.
            # Must raise with a good message
            except OSError, exp:
                # We look for the "Function not implemented" under Linux
                if exp.errno == 38 and os.name == 'posix':
                    logger.error("Get an exception (%s). If you are under Linux, please check that your /dev/shm directory exists." % (str(exp)))
                    raise

            # For multiprocess things, we should not have
            # sockettimeouts. will be set explicitly in Pyro calls
            import socket
            socket.setdefaulttimeout(None)

            # ok we are now fully daemon (if requested)
            # now we can start our "external" modules (if any):
            self.modules_manager.start_external_instances()

            # Ok now we can load the retention data
            self.hook_point('load_retention')

            ## And go for the main loop
            self.do_mainloop()
        except SystemExit, exp:
            # With a 2.4 interpreter the sys.exit() in load_config_file
            # ends up here and must be handled.
            sys.exit(exp.code)
        except Exception, exp:
            logger.critical("I got an unrecoverable error. I have to exit")
            logger.critical("You can log a bug ticket at https://github.com/naparuba/shinken/issues/new to get help")
            logger.critical("Back trace of it: %s" % (traceback.format_exc()))
            raise

    def setup_new_conf(self):
        """ Setup a new conf received from a Master arbiter. """
        conf = self.new_conf
        self.new_conf = None
        self.cur_conf = conf
        self.conf = conf

    def do_loop_turn(self):
        if self.must_run:
            # Main loop
            self.run()

    # Get 'objects' from external modules
    # It can be used for get external commands for example
    def get_objects_from_from_queues(self):
        for f in self.modules_manager.get_external_from_queues():
            #print "Groking from module instance %s" % f
            while True:
                try:
                    o = f.get(block=False)
                    self.add(o)
                except Empty:
                    break
                # Maybe the queue got problem
                # log it and quit it
                except (IOError, EOFError), exp:
                    logger.warning("An external module queue got a problem '%s'" % str(exp))
                    break

    # We wait (block) for arbiter to send us something
    def wait_for_master_death(self):
        logger.info("Waiting for master death")
        timeout = 1.0
        self.last_master_speack = time.time()

        # Look for the master timeout
        master_timeout = 300
        for arb in self.conf.arbiters:
            if not arb.spare:
                master_timeout = arb.check_interval * arb.max_check_attempts
        logger.info("I'll wait master for %d seconds" % master_timeout)

        while not self.interrupted:
            elapsed, _, tcdiff = self.handleRequests(timeout)
            # if there was a system Time Change (tcdiff) then we have to adapt last_master_speak:
            if self.new_conf:
                self.setup_new_conf()
            if tcdiff:
                self.last_master_speack += tcdiff
            if elapsed:
                self.last_master_speack = time.time()
                timeout -= elapsed
                if timeout > 0:
                    continue

            timeout = 1.0
            sys.stdout.write(".")
            sys.stdout.flush()

            # Now check if master is dead or not
            now = time.time()
            if now - self.last_master_speack > master_timeout:
                logger.info("Master is dead!!!")
                self.must_run = True
                break

    # Take all external commands, make packs and send them to
    # the schedulers
    def push_external_commands_to_schedulers(self):
        # Now get all external commands and put them into the
        # good schedulers
        for ext_cmd in self.external_commands:
            self.external_command.resolve_command(ext_cmd)

        # Now for all alive schedulers, send the commands
        for sched in self.conf.schedulers:
            cmds = sched.external_commands
            if len(cmds) > 0 and sched.alive:
                safe_print("Sending %d commands" % len(cmds), 'to scheduler', sched.get_name())
                sched.run_external_commands(cmds)
            # clean them
            sched.external_commands = []

    # Main function
    def run(self):
        if self.conf.human_timestamp_log:
            logger.set_human_format()

        # Ok start to work :)
        self.check_photo_dir()

        self.request = request
        self.response = response

        self.load_plugins()

        # Declare the whole app static files AFTER the plugin ones
        self.declare_common_static()

        self.init_db()

        self.init_datamanager()
        # Launch the data thread"
        #self.workersmanager_thread = threading.Thread(None, self.workersmanager, 'httpthread')
        #self.workersmanager_thread.start()
        # TODO: look for alive and killing

        print "Starting HostdUI app"
        srv = run(host=self.http_host, port=self.http_port, server=self.http_backend)

#    def workersmanager(self):
#        while True:
#            print "Workers manager thread"
#            time.sleep(1)


    # Here we will load all plugins (pages) under the webui/plugins
    # directory. Each one can have a page, views and htdocs dir that we must
    # route correctly
    def load_plugins(self):
        from shinken.webui import plugins_hostd as plugins
        plugin_dir = os.path.abspath(os.path.dirname(plugins.__file__))
        if self.override_plugins:
            plugin_dir = self.override_plugins
        print "Loading plugin directory: %s" % plugin_dir

        # Load plugin directories
        plugin_dirs = [fname for fname in os.listdir(plugin_dir)
                        if os.path.isdir(os.path.join(plugin_dir, fname))]

        print "Plugin dirs", plugin_dirs
        sys.path.append(plugin_dir)
        # We try to import them, but we keep only the one of
        # our type
        for fdir in plugin_dirs:
            print "Try to load", fdir
            mod_path = 'shinken.webui.plugins_hostd.%s.%s' % (fdir, fdir)
            # Maybe we want to start a fully new set of pages? If so,
            # load only them
            if self.override_plugins:
                mod_path = '%s.%s' % (fdir, fdir)
            print "MOD PATH", mod_path
            try:
                m = __import__(mod_path, fromlist=[mod_path])
                m_dir = os.path.abspath(os.path.dirname(m.__file__))
                sys.path.append(m_dir)

                #print "Loaded module m", m
                print m.__file__
                pages = m.pages
                print "Try to load pages", pages
                for (f, entry) in pages.items():
                    routes = entry.get('routes', None)
                    v = entry.get('view', None)
                    static = entry.get('static', False)

                    # IMPORTANT: apply VIEW BEFORE route!
                    if v:
                        #print "Link function", f, "and view", v
                        f = view(v)(f)

                    # Maybe there is no route to link, so pass
                    if routes:
                        for r in routes:
                            method = entry.get('method', 'GET')
                            print "link function", f, "and route", r, "method", method

                            # Ok, we will just use the lock for all
                            # plugin page, but not for static objects
                            # so we set the lock at the function level.
                            lock_version = self.lockable_function(f)
                            f = route(r, callback=lock_version, method=method)

                    # If the plugin declare a static entry, register it
                    # and remeber: really static! because there is no lock
                    # for them!
                    if static:
                        self.add_static(fdir, m_dir)

                # And we add the views dir of this plugin in our TEMPLATE
                # PATH
                bottle.TEMPLATE_PATH.append(os.path.join(m_dir, 'views'))

                # And finally register me so the pages can get data and other
                # useful stuff
                m.app = self


            except Exception, exp:
                logger.log("Loading plugins: %s" % exp)

    def add_static(self, fdir, m_dir):
        static_route = '/static/' + fdir + '/:path#.+#'
        #print "Declaring static route", static_route
        def plugin_static(path):
            print "Ask %s and give %s" % (path, os.path.join(m_dir, 'htdocs'))
            return static_file(path, root=os.path.join(m_dir, 'htdocs'))
        route(static_route, callback=plugin_static)

    # We want a lock manager version of the plugin fucntions
    def lockable_function(self, f):
        #print "We create a lock verion of", f
        def lock_version(**args):
            #self.wait_for_no_writers()
            t = time.time()
            try:
                return f(**args)
            finally:
                print "rendered in", time.time() - t
                # We can remove us as a reader from now. It's NOT an atomic operation
                # so we REALLY not need a lock here (yes, I try without and I got
                # a not so accurate value there....)
                #self.global_lock.acquire()
                #self.nb_readers -= 1
                #self.global_lock.release()
        #print "The lock version is", lock_version
        return lock_version

    def declare_common_static(self):
        @route('/static/photos/:path#.+#')
        def give_photo(path):
            # If the file really exist, give it. If not, give a dummy image.
            if os.path.exists(os.path.join(self.photo_dir, path+'.jpg')):
                return static_file(path+'.jpg', root=self.photo_dir)
            else:
                return static_file('images/user.png', root=os.path.join(bottle_dir, 'htdocs'))

        # Route static files css files
        @route('/static/:path#.+#')
        def server_static(path):
            # By default give from the root in bottle_dir/htdocs. If the file is missing,
            # search in the share dir
            root = os.path.join(bottle_dir, 'htdocs')
            p = os.path.join(root, path)
            print "LOOK for FILE EXISTS", p
            if not os.path.exists(p):
                root = self.packs_home
                print "LOOK FOR PATH", path
                print "No such file, I look in", os.path.join(root, path)
            return static_file(path, root=root)

        # And add the favicon ico too
        @route('/favicon.ico')
        def give_favicon():
            return static_file('favicon.ico', root=os.path.join(bottle_dir, 'htdocs', 'images'))

    def old_run(self):
        suppl_socks = None

        # Now create the external commander. It's just here to dispatch
        # the commands to schedulers
        e = ExternalCommandManager(self.conf, 'dispatcher')
        e.load_arbiter(self)
        self.external_command = e

        print "Run baby, run..."
        timeout = 1.0

        while self.must_run and not self.interrupted:

            elapsed, ins, _ = self.handleRequests(timeout, suppl_socks)

            # If FIFO, read external command
            if ins:
                now = time.time()
                ext_cmds = self.external_command.get()
                if ext_cmds:
                    for ext_cmd in ext_cmds:
                        self.external_commands.append(ext_cmd)
                else:
                    self.fifo = self.external_command.open()
                    if self.fifo is not None:
                        suppl_socks = [self.fifo]
                    else:
                        suppl_socks = None
                elapsed += time.time() - now

            if elapsed or ins:
                timeout -= elapsed
                if timeout > 0:  # only continue if we are not over timeout
                    continue

            # Timeout
            timeout = 1.0  # reset the timeout value

            # Try to see if one of my module is dead, and
            # try to restart previously dead modules :)
            self.check_and_del_zombie_modules()

            # Call modules that manage a starting tick pass
            self.hook_point('tick')
            print "Tick"

            # If ask me to dump my memory, I do it
            if self.need_dump_memory:
                self.dump_memory()
                self.need_dump_memory = False

    def get_daemons(self, daemon_type):
        """ Returns the daemons list defined in our conf for the given type """
        # shouldn't the 'daemon_types' (whetever it is above) be always present?
        return getattr(self.conf, daemon_type + 's', None)

    # Helper functions for retention modules
    # So we give our broks and external commands
    def get_retention_data(self):
        r = {}
        r['broks'] = self.broks
        r['external_commands'] = self.external_commands
        return r

    # Get back our data from a retention module
    def restore_retention_data(self, data):
        broks = data['broks']
        external_commands = data['external_commands']
        self.broks.update(broks)
        self.external_commands.extend(external_commands)

    def get_user_auth(self):
        # First we look for the user sid
        # so we bail out if it's a false one
        user_name = self.request.get_cookie("user", secret=self.auth_secret)
        print "WE GOT COOKIE USER NAME", user_name

        # If we cannot check the cookie, bailout
        if not user_name:
            return None

        u = self.db.users.find_one({'_id': user_name})

        print "Find a user", user_name, u
        #c = Contact()
        #c.contact_name = user_name
        #c.is_admin = True
        return u

    # TODO: fix hard coded server/database
    def init_db(self):
        if not Connection:
            logger.error('You need the pymongo lib for running skonfui. Please install it')
            sys.exit(2)

        con = Connection('localhost')
        self.db = con.hostd  # shinken

    def init_datamanager(self):
        self.datamgr.load_conf(self.conf)
        self.datamgr.load_db(self.db)

    def check_auth(self, username, password):
        password_hash = hashlib.sha512(password).hexdigest()
        print "Looking for the user", username, "with password hash", password_hash
        r = self.db.users.find_one({'_id': username, 'pwd_hash': password_hash})
        print "Is user auth?", r
        return r is not None

    def get_user_by_name(self, username):
        r = self.db.users.find_one({'username': username})
        return r

    def get_user_by_key(self, api_key):
        r = self.db.users.find_one({'api_key': api_key})
        if not r:
            return None
        if not r['validated']:
            return None
        return r

    def get_email_by_name(self, username):
        r = self.db.users.find_one({'username': username})
        if not r:
            return ''
        return r['email']

    def is_actitaved(self, username):
        r = self.db.users.find_one({'_id': username})
        if not r:
            return False
        return r['validated']

    def get_api_key(self, username):
        r = self.db.users.find_one({'_id': username})
        if not r:
            return None
        return r['api_key']

    def get_last_packs(self, nb):
        return [p for p in self.db.packs.find().limit(nb).sort('upload_time', -1)]

    def save_user_stats(self, user, stats):
        stats['user'] = user['username']
        stats['_id'] = user['username']
        stats['upload_time'] = int(time.time())
        stats['state'] = 'pending'
        print "Saving cfg stats", stats
        self.db.cfg_stats.save(stats)

    def save_new_pack(self, user, filename, buf):
        filename = os.path.basename(filename)
        short_name = filename[:-4]
        print "Saving a new pack file from a user:", user, filename
        if not user:
            return None
        user_dir = os.path.join(self.tmp_pack_path, user)
        if not os.path.exists(user_dir):
            print "Creating the user directory", user_dir
            os.mkdir(user_dir)
        p = os.path.join(user_dir, filename)
        f = open(p, 'w')
        f.write(buf)
        f.close()
        print "File %s is saved" % p
        _id = uuid.uuid4().get_hex()
        d = {'_id': _id, 'upload_time': int(time.time()), 'filename': filename, 'filepath': p, 'path': '/unanalysed', 'user': user,
            'state': 'pending', 'pack_name': short_name, 'moderation_comment': '', 'link_id': _id}
        # Get all previously sent packs for the same user/filename, and put them as obsolete
        obs = self.db.packs.find({'filepath': p})
        for o in obs:
            print "The pack make obsolete the pack", o
            o['state'] = 'obsolete'
            o['obsoleted_by'] = _id
            self.db.packs.save(o)
        # Ok now we can save the pack :)
        print "Saving pending pack", d
        self.db.packs.save(d)
        # Now we will unzip and load all data from the pack
        self.load_pack_file(_id)

    def load_pack_file(self, pack):
        p = self.db.packs.find_one({'_id': pack})
        filepath = p['filepath']
        print "Analysing pack"
        if not zipfile.is_zipfile(filepath):
            print "ERROR: the pack %s is not a zip file!" % filepath
            p['state'] = 'refused'
            p['moderation_comment'] = 'The pack file is not a zip file'
            self.db.packs.save(p)
            return
        TMP_PATH = tempfile.mkdtemp()

        path = os.path.join(TMP_PATH, pack)
        print "UNFLATING PACK INTO", path
        f = zipfile.ZipFile(filepath)
        f.extractall(path)

        packs = Packs({})
        packs.load_file(path)
        packs = [i for i in packs]
        if len(packs) > 1:
            print "ERROR: the pack %s got too much .pack file in it!" % pack
            p['moderation_comment'] = "ERROR: no valid .pack in the pack"
            p['state'] = 'refused'
            self.db.packs.save(p)
            shutil.rmtree(TMP_PATH)
            return

        if len(packs) == 0:
            print "ERROR: no valid .pack in the pack %s" % pack
            p['state'] = 'refused'
            p['moderation_comment'] = "ERROR: no valid .pack in the pack"
            self.db.packs.save(p)
            shutil.rmtree(TMP_PATH)
            return

        # Now we move the pack to it's final directory
        dest_path = os.path.join(self.packs_home, pack)
        print "Will copy the tree in the pack tree", dest_path
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(path, dest_path)

        pck = packs.pop()
        print "We read pack", pck.__dict__
        # Now we can update the db pack entry
        p['pack_name'] = pck.pack_name
        p['description'] = pck.description
        p['macros'] = pck.macros
        p['path'] = pck.path
        p['templates'] = pck.templates
        p['services'] = pck.services
        p['commands'] = pck.commands

        if p['path'] == '/':
            p['path'] = '/uncategorized'
        p['doc_link'] = pck.doc_link
        if p['state'] == 'pending':
            p['state'] = 'ok'

        # Give a real link name to this pack
        p['link_id'] = '%s-%s' % (p['user'], p['pack_name'])
        print "We want to save the object", p
        self.db.packs.save(p)
        shutil.rmtree(TMP_PATH)

    def is_name_available(self, username):
        r = self.db.users.find_one({'_id': username})
        return r is None

    def register_user(self, username, pwdhash, email):
        ak = uuid.uuid4().get_hex()
        api_key = uuid.uuid4().get_hex()
        d = {'_id': username, 'username': username, 'pwd_hash': pwdhash, 'email': email, 'api_key': api_key, 'activating_key': ak, 'validated': False, 'is_admin': False, 'is_moderator': False}
        print "Saving new user", d
        self.db.users.save(d)

        # Now send the mail
        fromaddr = 'shinken@community.shinken-monitoring.org'
        toaddrs = [email]
        srvuri = 'http://community.shinken-monitoring.org'
        # Add the From: and To: headers at the start!
        msg = ("From: %s\r\nSubject: Registering to Shinken community website\r\nTo: %s\r\n\r\n"
              % (fromaddr, ", ".join(toaddrs)))
        msg += 'Thanks %s for registering in the Shinken community site and welcome! Please click on the link below to enable your account so you can start to get packs and submit new ones.\n' % username
        msg += ' %s/validate?activating_key=%s' % (srvuri, ak)
        print "Message length is " + repr(len(msg))
        print "MEssage is", msg
        print "Go to send mail"
        try:
            server = smtplib.SMTP('localhost')
            server.set_debuglevel(1)
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
        except Exception, exp:
            print "FUCK, there was a problem with the email sending!", exp

    def validate_user(self, activating_key):
        u = self.db.users.find_one({'activating_key': activating_key})
        print "Try to validate a user with the activated key", activating_key, 'and get', u
        if not u:
            return False
        print "User %s validated"
        u['validated'] = True
        self.db.users.save(u)

        return True

    def update_user(self, username, pwd_hash, email):
        r = self.db.users.find_one({'_id': username})
        if not r:
            return

        if pwd_hash:
            r['pwd_hash'] = pwd_hash

        old_email = r['email']
        r['email'] = email
        # If the user changed it's email, put it in validating
        if old_email != email:
            r['validated'] = False

        self.db.users.save(r)
