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

import sys
import os
import time
import traceback
from Queue import Empty
import socket
import traceback
import cStringIO
import cPickle
import copy
import json

from shinken.objects.config import Config
from shinken.external_command import ExternalCommandManager
from shinken.dispatcher import Dispatcher
from shinken.daemon import Daemon, Interface
from shinken.log import logger
from shinken.brok import Brok
from shinken.external_command import ExternalCommand


# Interface for the other Arbiter
# It connects, and together we decide who's the Master and who's the Slave, etc.
# Here is a also a function to get a new conf from the master
class IForArbiter(Interface):
    def have_conf(self, magic_hash):
        # Beware, we got an str in entry, not an int
        magic_hash = int(magic_hash)
        # I've got a conf and a good one
        if self.app.cur_conf and self.app.cur_conf.magic_hash == magic_hash:
            return True
        else:  # I've no conf or a bad one
            return False


    # The master Arbiter is sending us a new conf in a pickle way. Ok, we take it
    def put_conf(self, conf):
        conf = cPickle.loads(conf)
        super(IForArbiter, self).put_conf(conf)
        self.app.must_run = False
    put_conf.method = 'POST'


    def get_config(self):
        return self.app.conf


    # The master arbiter asks me not to run!
    def do_not_run(self):
        # If I'm the master, ignore the command
        if self.app.is_master:
            logger.debug("Received message to not run. I am the Master, ignore and continue to run.")
        # Else, I'm just a spare, so I listen to my master
        else:
            logger.debug("Received message to not run. I am the spare, stopping.")
            self.app.last_master_speack = time.time()
            self.app.must_run = False
    do_not_run.need_lock = False


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


    # Dummy call. We are the master, we manage what we want
    def what_i_managed(self):
        return {}
    what_i_managed.need_lock = False


    def get_all_states(self):
        res = {'arbiter': self.app.conf.arbiters,
               'scheduler': self.app.conf.schedulers,
               'poller': self.app.conf.pollers,
               'reactionner': self.app.conf.reactionners,
               'receiver': self.app.conf.receivers,
               'broker': self.app.conf.brokers}
        return res


    # Try to give some properties of our objects
    def get_objects_properties(self, table, properties=[]):
        logger.debug('ASK:: table= %s, properties= %s' % (str(table), str(properties)))
        objs = getattr(self.conf, table, None)
        logger.debug("OBJS:: %s" % str(objs))
        if not objs:
            return ''
        res = []
        for obj in objs:
            l = []
            for prop in properties:
                v = getattr(obj, prop, '')
                l.append(v)
            res.append(l)
        return "OKIIIII"


# Main Arbiter Class
class Arbiter(Daemon):

    def __init__(self, config_files, is_daemon, do_replace, verify_only, debug, debug_file, profile=None, analyse=None, migrate=None, arb_name=''):

        super(Arbiter, self).__init__('arbiter', config_files[0], is_daemon, do_replace, debug, debug_file)

        self.config_files = config_files
        self.verify_only = verify_only
        self.analyse = analyse
        self.migrate = migrate
        self.arb_name = arb_name

        self.broks = {}
        self.is_master = False
        self.me = None

        self.nb_broks_send = 0

        # Now tab for external_commands
        self.external_commands = []

        self.fifo = None

        # Used to work out if we must still be alive or not
        self.must_run = True

        self.interface = IForArbiter(self)
        self.conf = Config()



    # Use for adding things like broks
    def add(self, b):
        if isinstance(b, Brok):
            self.broks[b.id] = b
        elif isinstance(b, ExternalCommand):
            self.external_commands.append(b)
        else:
            logger.warning('Cannot manage object type %s (%s)' % (type(b), b))

    # We must push our broks to the broker
    # because it's stupid to make a crossing connection
    # so we find the broker responsible for our broks,
    # and we send it to him
    # TODO: better find the broker, here it can be dead?
    # or not the good one?
    def push_broks_to_broker(self):
        for brk in self.conf.brokers:
            # Send only if alive of course
            if brk.manage_arbiters and brk.alive:
                is_send = brk.push_broks(self.broks)
                if is_send:
                    # They are gone, we keep none!
                    self.broks.clear()

    # We must take external_commands from all satellites
    # like brokers, pollers, reactionners or receivers
    def get_external_commands_from_satellites(self):
        sat_lists = [self.conf.brokers, self.conf.receivers,
                     self.conf.pollers, self.conf.reactionners]
        for lst in sat_lists:
            for sat in lst:
                # Get only if alive of course
                if sat.alive:
                    new_cmds = sat.get_external_commands()
                    for new_cmd in new_cmds:
                        self.external_commands.append(new_cmd)

    # Our links to satellites can raise broks. We must send them
    def get_broks_from_satellitelinks(self):
        tabs = [self.conf.brokers, self.conf.schedulers,
                    self.conf.pollers, self.conf.reactionners,
                self.conf.receivers]
        for tab in tabs:
            for s in tab:
                new_broks = s.get_all_broks()
                for b in new_broks:
                    self.add(b)

    # Our links to satellites can raise broks. We must send them
    def get_initial_broks_from_satellitelinks(self):
        tabs = [self.conf.brokers, self.conf.schedulers,
                self.conf.pollers, self.conf.reactionners,
                self.conf.receivers]
        for tab in tabs:
            for s in tab:
                b = s.get_initial_status_brok()
                self.add(b)


    # Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        self.fifo = e.open()


    def get_daemon_links(self, daemon_type):
        # the attribute name to get these differs for schedulers and arbiters
        return daemon_type + 's'


    def load_config_file(self):
        logger.info("Loading configuration")
        # REF: doc/shinken-conf-dispatching.png (1)
        buf = self.conf.read_config(self.config_files)
        raw_objects = self.conf.read_config_buf(buf)

        logger.debug("Opening local log file")

        # First we need to get arbiters and modules
        # so we can ask them for objects
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')

        self.conf.early_arbiter_linking()

        # Search which Arbiterlink I am
        for arb in self.conf.arbiters:
            if arb.is_me(self.arb_name):
                arb.need_conf = False
                self.me = arb
                self.is_master = not self.me.spare
                if self.is_master:
                    logger.info("I am the master Arbiter: %s" % arb.get_name())
                else:
                    logger.info("I am a spare Arbiter: %s" % arb.get_name())

                # Set myself as alive ;)
                self.me.alive = True
            else:  # not me
                arb.need_conf = True

        if not self.me:
            sys.exit("Error: I cannot find my own Arbiter object, I bail out. \
                     To solve it, please change the host_name parameter in \
                     the object Arbiter in the file shinken-specific.cfg. \
                     With the value %s \
                     Thanks." % socket.gethostname())

        logger.info("My own modules: " + ','.join([m.get_name() for m in self.me.modules]))

        self.modules_dir = getattr(self.conf, 'modules_dir', '')

        # Ok it's time to load the module manager now!
        self.load_modules_manager()
        # we request the instances without them being *started*
        # (for those that are concerned ("external" modules):
        # we will *start* these instances after we have been daemonized (if requested)
        self.modules_manager.set_modules(self.me.modules)
        self.do_load_modules()

        # Call modules that manage this read configuration pass
        self.hook_point('read_configuration')

        # Now we ask for configuration modules if they
        # got items for us
        for inst in self.modules_manager.instances:
            if 'configuration' in inst.phases:
                try:
                    r = inst.get_objects()
                except Exception, exp:
                    logger.error("Instance %s raised an exception %s. Log and continue to run" % (inst.get_name(), str(exp)))
                    output = cStringIO.StringIO()
                    traceback.print_exc(file=output)
                    logger.error("Back trace of this remove: %s" % (output.getvalue()))
                    output.close()
                    continue

                types_creations = self.conf.types_creations
                for k in types_creations:
                    (cls, clss, prop) = types_creations[k]
                    if prop in r:
                        for x in r[prop]:
                            # test if raw_objects[k] are already set - if not, add empty array
                            if not k in raw_objects:
                                raw_objects[k] = []
                            # now append the object
                            raw_objects[k].append(x)
                        logger.debug("Added %i objects to %s from module %s" % (len(r[prop]), k, inst.get_name()))

        ### Resume standard operations ###
        self.conf.create_objects(raw_objects)

        # Maybe conf is already invalid
        if not self.conf.conf_is_correct:
            sys.exit("***> One or more problems was encountered while processing the config files...")

        # Change Nagios2 names to Nagios3 ones
        self.conf.old_properties_names_to_new()

        # Manage all post-conf modules
        self.hook_point('early_configuration')

        # Ok here maybe we should stop because we are in a pure migration run
        if self.migrate:
            print "Migration MODE. Early exiting from configuration relinking phase"
            return

        # Load all file triggers
        self.conf.load_triggers()

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
        self.conf.remove_templates()

        # We compute simple item hash
        self.conf.compute_hash()

        # We removed templates, and so we must recompute the
        # search lists
        self.conf.create_reversed_list()

        # Overrides sepecific service instaces properties
        self.conf.override_properties()

        # Pythonize values
        self.conf.pythonize()

        # Linkify objects to each other
        self.conf.linkify()

        # applying dependencies
        self.conf.apply_dependencies()

        # Hacking some global parameters inherited from Nagios to create
        # on the fly some Broker modules like for status.dat parameters
        # or nagios.log one if there are none already available
        self.conf.hack_old_nagios_parameters()

        # Raise warning about currently unmanaged parameters
        if self.verify_only:
            self.conf.warn_about_unmanaged_parameters()

        # Explode global conf parameters into Classes
        self.conf.explode_global_conf()

        # set our own timezone and propagate it to other satellites
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

        # Maybe some elements where not wrong, so we must clean if possible
        self.conf.clean()

        # If the conf is not correct, we must get out now
        # if not self.conf.conf_is_correct:
        #    sys.exit("Configuration is incorrect, sorry, I bail out")

        # REF: doc/shinken-conf-dispatching.png (2)
        logger.info("Cutting the hosts and services into parts")
        self.confs = self.conf.cut_into_parts()

        # The conf can be incorrect here if the cut into parts see errors like
        # a realm with hosts and not schedulers for it
        if not self.conf.conf_is_correct:
            self.conf.show_errors()
            err = "Configuration is incorrect, sorry, I bail out"
            logger.error(err)
            sys.exit(err)

        logger.info('Things look okay - No serious problems were detected during the pre-flight check')

        # Clean objects of temporary/unnecessary attributes for live work:
        self.conf.clean()

        # Exit if we are just here for config checking
        if self.verify_only:
            sys.exit(0)

        if self.analyse:
            self.launch_analyse()
            sys.exit(0)

        # Some properties need to be "flatten" (put in strings)
        # before being send, like realms for hosts for example
        # BEWARE: after the cutting part, because we stringify some properties
        self.conf.prepare_for_sending()

        # Ok, here we must check if we go on or not.
        # TODO: check OK or not
        self.log_level = self.conf.log_level
        self.use_local_log = self.conf.use_local_log
        self.local_log = self.conf.local_log
        self.pidfile = os.path.abspath(self.conf.lock_file)
        self.idontcareaboutsecurity = self.conf.idontcareaboutsecurity
        self.user = self.conf.shinken_user
        self.group = self.conf.shinken_group
        self.daemon_enabled = self.conf.daemon_enabled
        self.daemon_thread_pool_size = self.conf.daemon_thread_pool_size
        self.http_backend = self.conf.http_backend

        # If the user sets a workdir, lets use it. If not, use the
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
        self.port = self.me.port

        logger.info("Configuration Loaded")


    def launch_analyse(self):
        try:
            import json
        except ImportError:
            logger.error("Error: json is need for statistics file saving. Please update your python version to 2.6")
            sys.exit(2)

        logger.info("We are doing an statistic analysis on the dump file" % self.analyse)
        stats = {}
        types = ['hosts', 'services', 'contacts', 'timeperiods', 'commands', 'arbiters',
                 'schedulers', 'pollers', 'reactionners', 'brokers', 'receivers', 'modules',
                 'realms']
        for t in types:
            lst = getattr(self.conf, t)
            nb = len([i for i in lst])
            stats['nb_' + t] = nb
            logger.info("Got %s for %s" % (nb, t))

        max_srv_by_host = max([len(h.services) for h in self.conf.hosts])
        logger.info("Max srv by host" % max_srv_by_host)
        stats['max_srv_by_host'] = max_srv_by_host

        f = open(self.analyse, 'w')
        s = json.dumps(stats)
        logger.info("Saving stats data to a file" % s)
        f.write(s)
        f.close()


    def go_migrate(self):
        print "***********"*5
        print "WARNING : this feature is NOT supported in this version!"
        print "***********"*5

        migration_module_name = self.migrate.strip()
        mig_mod = self.conf.modules.find_by_name(migration_module_name)
        if not mig_mod:
            print "Cannot find the migration module %s. Please configure it" % migration_module_name
            sys.exit(2)

        print self.modules_manager.instances
        # Ok now all we need is the import module
        self.modules_manager.set_modules([mig_mod])
        self.do_load_modules()
        print self.modules_manager.instances
        if len(self.modules_manager.instances) == 0:
            print "Error during the initialization of the import module. Bailing out"
            sys.exit(2)
        print "Configuration migrating in progress..."
        mod  = self.modules_manager.instances[0]
        f = getattr(mod, 'import_objects', None)
        if not f or not callable(f):
            print "Import module is missing the import_objects function. Bailing out"
            sys.exit(2)

        objs = {}
        types = ['hosts', 'services', 'commands', 'timeperiods', 'contacts']
        for t in types:
            print "New type", t
            objs[t] = []
            for i in getattr(self.conf, t):
                d = i.get_raw_import_values()
                if d:
                    objs[t].append(d)
            f(objs)
        # Ok we can exit now
        sys.exit(0)



    # Main loop function
    def main(self):
        try:
            # Log will be broks
            for line in self.get_header():
                logger.info(line)

            self.load_config_file()

            # Maybe we are in a migration phase. If so, we will bailout here
            if self.migrate:
                self.go_migrate()

            # Look if we are enabled or not. If ok, start the daemon mode
            self.look_for_early_exit()
            self.do_daemon_init_and_start()

            self.uri_arb = self.http_daemon.register(self.interface)#, "ForArbiter")

            # ok we are now fully daemonized (if requested)
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
            logger.critical("Exception trace follows: %s" % (traceback.format_exc()))
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
                arb.is_me = lambda x: True  # we now definitively know who we are, just keep it.
            else:
                arb.is_me = lambda x: False  # and we know who we are not, just keep it.


    def do_loop_turn(self):
        # If I am a spare, I wait for the master arbiter to send me
        # true conf.
        if self.me.spare:
            logger.debug("I wait for master")
            self.wait_for_master_death()

        if self.must_run:
            # Main loop
            self.run()


    # Get 'objects' from external modules
    # It can be used to get external commands for example
    def get_objects_from_from_queues(self):
        for f in self.modules_manager.get_external_from_queues():
            #print "Groking from module instance %s" % f
            while True:
                try:
                    o = f.get(block=False)
                    self.add(o)
                except Empty:
                    break
                # Maybe the queue had problems
                # log it and quit it
                except (IOError, EOFError), exp:
                    logger.error("An external module queue got a problem '%s'" % str(exp))
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
                logger.info("Arbiter Master is dead. The arbiter %s take the lead" % self.me.get_name())
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
                logger.debug("Sending %d commands to scheduler %s" % (len(cmds), sched.get_name()))
                sched.run_external_commands(cmds)
            # clean them
            sched.external_commands = []


    # We will log if there are time period activations
    # change as NOTICE in logs.
    def check_and_log_tp_activation_change(self):
        for tp in self.conf.timeperiods:
            tp.check_and_log_activation_change()


    # Main function
    def run(self):
        # Before running, I must be sure who am I
        # The arbiters change, so we must re-discover the new self.me
        for arb in self.conf.arbiters:
            if arb.is_me(self.arb_name):
                self.me = arb

        if self.conf.human_timestamp_log:
            logger.set_human_format()
        logger.info("Begin to dispatch configurations to satellites")
        self.dispatcher = Dispatcher(self.conf, self.me)
        self.dispatcher.check_alive()
        self.dispatcher.check_dispatch()
        # REF: doc/shinken-conf-dispatching.png (3)
        self.dispatcher.dispatch()

        # Now we can get all initial broks for our satellites
        self.get_initial_broks_from_satellitelinks()

        suppl_socks = None

        # Now create the external commander. It's just here to dispatch
        # the commands to schedulers
        e = ExternalCommandManager(self.conf, 'dispatcher')
        e.load_arbiter(self)
        self.external_command = e

        logger.debug("Run baby, run...")
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

            # Look for logging timeperiods activation change (active/inactive)
            self.check_and_log_tp_activation_change()

            # Now the dispatcher job
            self.dispatcher.check_alive()
            self.dispatcher.check_dispatch()
            # REF: doc/shinken-conf-dispatching.png (3)
            self.dispatcher.dispatch()
            self.dispatcher.check_bad_dispatch()

            # Now get things from our module instances
            self.get_objects_from_from_queues()

            # Maybe our satellites links raise new broks. Must reap them
            self.get_broks_from_satellitelinks()

            # One broker is responsible for our broks,
            # we must give him our broks
            self.push_broks_to_broker()
            self.get_external_commands_from_satellites()
            #self.get_external_commands_from_receivers()
            # send_conf_to_schedulers()

            if self.nb_broks_send != 0:
                logger.debug("Nb Broks send: %d" % self.nb_broks_send)
            self.nb_broks_send = 0

            self.push_external_commands_to_schedulers()

            # It's sent, do not keep them
            # TODO: check if really sent. Queue by scheduler?
            self.external_commands = []

            # If asked to dump my memory, I will do it
            if self.need_dump_memory:
                self.dump_memory()
                self.need_dump_memory = False


    def get_daemons(self, daemon_type):
        """ Returns the daemons list defined in our conf for the given type """
        # shouldn't the 'daemon_types' (whatever it is above) be always present?
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
