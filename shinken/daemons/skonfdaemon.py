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
from Queue import Empty
import socket

from shinken.objects import Config
from shinken.external_command import ExternalCommandManager
from shinken.dispatcher import Dispatcher
from shinken.daemon import Daemon, Interface
from shinken.log import logger
from shinken.brok import Brok
from shinken.external_command import ExternalCommand
from shinken.util import safe_print
from shinken.skonfuiworker import SkonfUIWorker
from shinken.message import Message

# DBG : code this!
from shinken.objects import Contact

# Now the bottle HTTP part :)
from shinken.webui.bottle import Bottle, run, static_file, view, route, request, response
# Debug
import shinken.webui.bottle as bottle
bottle.debug(True)

#Import bottle lib to make bottle happy
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
        else: #I've no conf or a bad one
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
        daemon_name_attr = daemon_type+"_name"
        daemons = self.app.get_daemons(daemon_type)
        if daemons:
            for dae in daemons:
                if hasattr(dae, daemon_name_attr) and getattr(dae, daemon_name_attr) == daemon_name:
                    if hasattr(dae, 'alive') and hasattr(dae, 'spare'):
                        return {'alive' : dae.alive, 'spare' : dae.spare}
        return None

    # Here a function called by check_shinken to get daemons list
    def get_satellite_list(self, daemon_type):
        satellite_list = []
        daemon_name_attr = daemon_type+"_name"
        daemons = self.app.get_daemons(daemon_type)
        if daemons:
            for dae in daemons:
                if hasattr(dae, daemon_name_attr):
                    satellite_list.append(getattr(dae, daemon_name_attr))
                else:
                    #If one daemon has no name... ouch!
                    return None
            return satellite_list
        return None


    # Dummy call. We are a master, we managed what we want
    def what_i_managed(self):
        return []


    def get_all_states(self):
        res = {'arbiter' : self.app.conf.arbiters,
               'scheduler' : self.app.conf.schedulers,
               'poller' : self.app.conf.pollers,
               'reactionner' : self.app.conf.reactionners,
               'receiver' : self.app.conf.receivers,
               'broker' : self.app.conf.brokers}
        return res


# Main Skonf Class
class Skonf(Daemon):

    def __init__(self, config_files, is_daemon, do_replace, verify_only, debug, debug_file):
        
        super(Skonf, self).__init__('skonf', config_files[0], is_daemon, do_replace, debug, debug_file)
        
        self.config_files = config_files

        self.verify_only = verify_only

        self.broks = {}
        self.is_master = False
        self.me = None

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

        # Search wich Arbiterlink I am
        for arb in self.conf.arbiters:
            if arb.is_me():
                arb.need_conf = False
                self.me = arb
                self.is_master = not self.me.spare
                logger.info("I am the %s Arbiter : %s" % ('master' if self.is_master else 'spare', arb.get_name()))

                # Set myself as alive ;)
                self.me.alive = True
            else: #not me
                arb.need_conf = True

        if not self.me:
            sys.exit("Error: I cannot find my own Arbiter object, I bail out. \
                     To solve it, please change the host_name parameter in \
                     the object Arbiter in the file shinken-specific.cfg. \
                     With the value %s \
                     Thanks." % socket.gethostname())

        logger.info("My own modules : " + ','.join([m.get_name() for m in self.me.modules]))

        # we request the instances without them being *started* 
        # (for these that are concerned ("external" modules):
        # we will *start* these instances after we have been daemonized (if requested)
        self.modules_manager.set_modules(self.me.modules)
        self.do_load_modules()

        # Call modules that manage this read configuration pass
        self.hook_point('read_configuration')

        # Now we ask for configuration modules if they
        # got items for us
        for inst in self.modules_manager.instances:
            if 'configuration' in inst.phases:
                try :
                    r = inst.get_objects()
                except Exception, exp:
                    print "The instance %s raise an exception %s. I bypass it" % (inst.get_name(), str(exp))
                    continue
                
                types_creations = self.conf.types_creations
                for k in types_creations:
                    (cls, clss, prop) = types_creations[k]
                    if prop in r:
                        for x in r[prop]:
                            # test if raw_objects[k] is already set - if not, add empty array
                            if not k in raw_objects:
                                raw_objects[k] = []
                            # now append the object
                            raw_objects[k].append(x)
                        print "Added %i objects to %s from module %s" % (len(r[prop]), k, inst.get_name())


        ### Resume standard operations ###
        self.conf.create_objects(raw_objects)

        # Maybe conf is already invalid
        if not self.conf.conf_is_correct:
            sys.exit("***> One or more problems was encountered while processing the config files...")

        # Change Nagios2 names to Nagios3 ones
        self.conf.old_properties_names_to_new()

        # Manage all post-conf modules
        self.hook_point('early_configuration')

        # Create Template links
        self.conf.linkify_templates()

        # All inheritances
        self.conf.apply_inheritance()

        # Explode between types
        self.conf.explode()

        # Create Name reversed list for searching list
        self.conf.create_reversed_list()

        # Cleaning Twins objects
        self.conf.remove_twins()

        # Implicit inheritance for services
        self.conf.apply_implicit_inheritance()

        # Fill default values
        self.conf.fill_default()
        
        # Remove templates from config
        # SAVE TEMPLATES
        self.host_templates = self.conf.hosts.templates
        # Then clean for other parts
        self.conf.remove_templates()

        # We removed templates, and so we must recompute the
        # search lists
        self.conf.create_reversed_list()
        
        # Pythonize values
        self.conf.pythonize()

        # Linkify objects each others
        self.conf.linkify()

        # applying dependencies
        self.conf.apply_dependencies()

        # Hacking some global parameter inherited from Nagios to create
        # on the fly some Broker modules like for status.dat parameters
        # or nagios.log one if there are no already available
        self.conf.hack_old_nagios_parameters()

        # Raise warning about curently unmanaged parameters
        if self.verify_only:
            self.conf.warn_about_unmanaged_parameters()

        # Exlode global conf parameters into Classes
        self.conf.explode_global_conf()

        # set ourown timezone and propagate it to other satellites
        self.conf.propagate_timezone_option()

        # Look for business rules, and create the dep tree
        self.conf.create_business_rules()
        # And link them
        self.conf.create_business_rules_dependencies()

        # Warn about useless parameters in Shinken
        if self.verify_only:
            self.conf.notice_about_useless_parameters()

        # Manage all post-conf modules
        self.hook_point('late_configuration')
        
        # Correct conf?
        self.conf.is_correct()

        #If the conf is not correct, we must get out now
        #if not self.conf.conf_is_correct:
        #    sys.exit("Configuration is incorrect, sorry, I bail out")

        # REF: doc/shinken-conf-dispatching.png (2)
        logger.info("Cutting the hosts and services into parts")
        self.confs = self.conf.cut_into_parts()

        # The conf can be incorrect here if the cut into parts see errors like
        # a realm with hosts and not schedulers for it
        if not self.conf.conf_is_correct:
            self.conf.show_errors()
            sys.exit("Configuration is incorrect, sorry, I bail out")

        logger.info('Things look okay - No serious problems were detected during the pre-flight check')

        # Now clean objects of temporary/unecessary attributes for live work:
        self.conf.clean()

        # Exit if we are just here for config checking
        if self.verify_only:
            sys.exit(0)

        # Some properties need to be "flatten" (put in strings)
        # before being send, like realms for hosts for example
        # BEWARE: after the cutting part, because we stringify some properties
        self.conf.prepare_for_sending()

        # Ok, here we must check if we go on or not.
        # TODO : check OK or not
        self.use_local_log = self.conf.use_local_log
        self.log_level = logger.get_level_id(self.conf.log_level)
        self.local_log = self.conf.local_log
        self.pidfile = os.path.abspath(self.conf.lock_file)
        self.idontcareaboutsecurity = self.conf.idontcareaboutsecurity
        self.user = self.conf.shinken_user
        self.group = self.conf.shinken_group
        
        # If the user set a workdir, let use it. If not, use the
        # pidfile directory
        if self.conf.workdir == '':
            self.workdir = os.path.abspath(os.path.dirname(self.pidfile))
        else:
            self.workdir = self.conf.workdir
        #print "DBG curpath=", os.getcwd()
        #print "DBG pidfile=", self.pidfile
        #print "DBG workdir=", self.workdir

        ##  We need to set self.host & self.port to be used by do_daemon_init_and_start
        self.host = self.me.address
        self.port = 8766#self.me.port
        
        logger.info("Configuration Loaded")
        print ""


    def load_web_configuration(self):
        self.plugins = []

        self.http_port = 7766#int(getattr(modconf, 'port', '7767'))
        self.http_host = '0.0.0.0'#getattr(modconf, 'host', '0.0.0.0')
        self.auth_secret = 'CHANGE_ME'.encode('utf8', 'replace')#getattr(modconf, 'auth_secret').encode('utf8', 'replace')
        self.http_backend = 'auto'#getattr(modconf, 'http_backend', 'auto')
        self.login_text = None#getattr(modconf, 'login_text', None)
        self.allow_html_output = False#to_bool(getattr(modconf, 'allow_html_output', '0'))
        self.remote_user_enable = '0'#getattr(modconf, 'remote_user_enable', '0')
        self.remote_user_variable = 'X_REMOTE_USER'#getattr(modconf, 'remote_user_variable', 'X_REMOTE_USER')

        # Load the photo dir and make it a absolute path
        self.photo_dir = 'photos'#getattr(modconf, 'photo_dir', 'photos')
        self.photo_dir = os.path.abspath(self.photo_dir)
        print "Webui : using the backend", self.http_backend




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

            self.do_daemon_init_and_start()
            self.uri_arb = self.pyro_daemon.register(self.interface, "ForArbiter")

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
            # now we can start our "external" modules (if any) :
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
        for arb in self.conf.arbiters:
            if (arb.address, arb.port) == (self.host, self.port):
                self.me = arb
                arb.is_me = lambda: True  # we now definitively know who we are, just keep it.
            else:
                arb.is_me = lambda: False # and we know who we are not, just keep it.


    def do_loop_turn(self):
        # If I am a spare, I wait for the master arbiter to send me
        # true conf. When
        if self.me.spare:
            self.wait_for_initial_conf()
            if not self.new_conf:
                return
            self.setup_new_conf()
            print "I must wait now"
            self.wait_for_master_death()

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
        # Before running, I must be sure who am I
        # The arbiters change, so we must refound the new self.me
        for arb in self.conf.arbiters:
            if arb.is_me():
                self.me = arb

        if self.conf.human_timestamp_log:
            logger.set_human_format()
        
        # Ok start to work :)
        self.check_photo_dir()

        self.request = request
        self.response = response

        self.load_plugins()

        # Declare the whole app static files AFTER the plugin ones
        self.declare_common_static()
        
        # Start sub workers
        for i in xrange(1, 3):
            self.create_and_launch_worker()

        self.init_db()

        # Launch the data thread"
        self.workersmanager_thread = threading.Thread(None, self.workersmanager, 'httpthread')
        self.workersmanager_thread.start()
        # TODO : look for alive and killing

        print "Starting SkonfUI app"
        srv = run(host=self.http_host, port=self.http_port, server=self.http_backend)


    def workersmanager(self):
        while True:
            print "Workers manager thread"
            time.sleep(1)


    # Here we will load all plugins (pages) under the webui/plugins
    # directory. Each one can have a page, views and htdocs dir that we must
    # route correctly
    def load_plugins(self):
        from shinken.webui import plugins_skonf as plugins
        plugin_dir = os.path.abspath(os.path.dirname(plugins.__file__))
        print "Loading plugin directory : %s" % plugin_dir
        
        # Load plugin directories
        plugin_dirs = [ fname for fname in os.listdir(plugin_dir)
                        if os.path.isdir(os.path.join(plugin_dir, fname)) ]

        print "Plugin dirs", plugin_dirs
        sys.path.append(plugin_dir)
        # We try to import them, but we keep only the one of
        # our type
        for fdir in plugin_dirs:
            print "Try to load", fdir
            mod_path = 'shinken.webui.plugins_skonf.%s.%s' % (fdir, fdir)
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

                    # IMPORTANT : apply VIEW BEFORE route!
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
                    # and remeber : really static! because there is no lock
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
               logger.log("Loading plugins : %s" % exp)





    def add_static(self, fdir, m_dir):
        static_route = '/static/'+fdir+'/:path#.+#'
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
            return static_file(path, root=os.path.join(bottle_dir, 'htdocs'))

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
                        suppl_socks = [ self.fifo ]
                    else:
                        suppl_socks = None
                elapsed += time.time() - now

            if elapsed or ins:
                timeout -= elapsed
                if timeout > 0: # only continue if we are not over timeout
                    continue  
            
            # Timeout
            timeout = 1.0 # reset the timeout value

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
        # shouldn't the 'daemon_types' (whetever it is above) be always present ?
        return getattr(self.conf, daemon_type+'s', None)

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

        # If we cannot check the cookie, bailout
        if not user_name:
            return None

        #c = self.datamgr.get_contact(user_name)
        c = Contact()
        c.contact_name = user_name
        c.is_admin = True
        return c





    # Create and launch a new worker, and put it into self.workers
    def create_and_launch_worker(self):
        w = SkonfUIWorker(1, self.workers_queue, self.returns_queue, 1, mortal=False, max_plugins_output_length = 1, target=None)
        w.module_name = 'skonfuiworker'
        w.add_database_data('localhost')

        # save this worker
        self.workers[w.id] = w
        
        logger.info("[%s] Allocating new %s Worker : %s" % (self.name, w.module_name, w.id))
        
        # Ok, all is good. Start it!
        w.start()


    # TODO : fix hard coded server/database
    def init_db(self):
       if not Connection:
          logger.error('You need the pymongo lib for running skonfui. Please install it')
          sys.exit(2)

       con = Connection('localhost')
       self.db = con.shinken


    # TODO : code this!
    def check_auth(self, login, password):
       return True

    # We are asking to a worker .. to work :)
    def ask_new_scan(self, id):
       msg = Message(id=0, type='ScanAsk', data={'scan_id' : id})
       print "Creating a Message for ScanAsk", msg
       self.workers_queue.put(msg)


        # Will get all label/uri for external UI like PNP or NagVis
    def get_external_ui_link(self):
        lst = []
        for mod in self.modules_manager.get_internal_instances():
            try:
                f = getattr(mod, 'get_external_ui_link', None)
                if f and callable(f):
                    r = f()
                    lst.append(r)
            except Exception , exp:
                print exp.__dict__
                logger.log("[%s] Warning : The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(),str(exp)))
                logger.log("[%s] Exception type : %s" % (self.name, type(exp)))
                logger.log("Back trace of this kill: %s" % (traceback.format_exc()))
                self.modules_manager.set_to_restart(mod)        

        safe_print("Will return external_ui_link::", lst)
        return lst

