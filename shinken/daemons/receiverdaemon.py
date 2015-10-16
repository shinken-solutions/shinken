#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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

import os
import time
import traceback
import sys
import base64
import zlib
import cPickle

from multiprocessing import active_children


from shinken.satellite import Satellite
from shinken.property import PathProp, IntegerProp
from shinken.log import logger
from shinken.external_command import ExternalCommand, ExternalCommandManager
from shinken.http_client import HTTPExceptions
from shinken.daemon import Interface
from shinken.stats import statsmgr

class IStats(Interface):
    """
    Interface for various stats about broker activity
    """

    doc = '''Get raw stats from the daemon:
  * command_buffer_size: external command buffer size
'''
    def get_raw_stats(self):
        app = self.app
        res = {'command_buffer_size': len(app.external_commands)}
        return res
    get_raw_stats.doc = doc

class IBroks(Interface):
    """ Interface for Brokers:
They connect here and get all broks (data for brokers). Data must be ORDERED!
(initial status BEFORE update...) """

    # A broker ask us broks
    def get_broks(self, bname):
        res = self.app.get_broks()
        return base64.b64encode(zlib.compress(cPickle.dumps(res), 2))
    get_broks.encode = 'raw'

# Our main APP class
class Receiver(Satellite):
    my_type = 'receiver'

    properties = Satellite.properties.copy()
    properties.update({
        'pidfile':   PathProp(default='receiverd.pid'),
        'port':      IntegerProp(default=7773),
        'local_log': PathProp(default='receiverd.log'),
    })

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):

        super(Receiver, self).__init__(
            'receiver', config_file, is_daemon, do_replace, debug, debug_file)

        # Our arbiters
        self.arbiters = {}

        # Our pollers and reactionners
        self.pollers = {}
        self.reactionners = {}

        # Modules are load one time
        self.have_modules = False

        # Can have a queue of external_commands give by modules
        # will be taken by arbiter to process
        self.external_commands = []
        # and the unprocessed one, a buffer
        self.unprocessed_external_commands = []

        self.host_assoc = {}
        self.direct_routing = False
        self.accept_passive_unknown_check_results = False

        self.istats = IStats(self)
        self.ibroks = IBroks(self)

        # Now create the external commander. It's just here to dispatch
        # the commands to schedulers
        e = ExternalCommandManager(None, 'receiver')
        e.load_receiver(self)
        self.external_command = e

    # Schedulers have some queues. We can simplify call by adding
    # elements into the proper queue just by looking at their type
    # Brok -> self.broks
    # TODO: better tag ID?
    # External commands -> self.external_commands
    def add(self, elt):
        cls_type = elt.__class__.my_type
        if cls_type == 'brok':
            # For brok, we TAG brok with our instance_id
            elt.instance_id = 0
            self.broks[elt.id] = elt
            return
        elif cls_type == 'externalcommand':
            logger.debug("Enqueuing an external command: %s", str(ExternalCommand.__dict__))
            self.unprocessed_external_commands.append(elt)


    def push_host_names(self, sched_id, hnames):
        for h in hnames:
            self.host_assoc[h] = sched_id


    def get_sched_from_hname(self, hname):
        i = self.host_assoc.get(hname, None)
        e = self.schedulers.get(i, None)
        return e


    # Get a brok. Our role is to put it in the modules
    # THEY MUST DO NOT CHANGE data of b!!!
    # REF: doc/receiver-modules.png (4-5)
    def manage_brok(self, b):
        to_del = []
        # Call all modules if they catch the call
        for mod in self.modules_manager.get_internal_instances():
            try:
                mod.manage_brok(b)
            except Exception, exp:
                logger.warning("The mod %s raise an exception: %s, I kill it",
                               mod.get_name(), str(exp))
                logger.warning("Exception type: %s", type(exp))
                logger.warning("Back trace of this kill: %s", traceback.format_exc())
                to_del.append(mod)
        # Now remove mod that raise an exception
        self.modules_manager.clear_instances(to_del)


    def do_stop(self):
        act = active_children()
        for a in act:
            a.terminate()
            a.join(1)
        super(Receiver, self).do_stop()


    def setup_new_conf(self):
        conf = self.new_conf
        self.new_conf = None
        self.cur_conf = conf
        # Got our name from the globals
        if 'receiver_name' in conf['global']:
            name = conf['global']['receiver_name']
        else:
            name = 'Unnamed receiver'
        self.name = name
        self.api_key = conf['global']['api_key']
        self.secret = conf['global']['secret']
        self.http_proxy = conf['global']['http_proxy']
        self.statsd_host = conf['global']['statsd_host']
        self.statsd_port = conf['global']['statsd_port']
        self.statsd_prefix = conf['global']['statsd_prefix']
        self.statsd_enabled = conf['global']['statsd_enabled']

        statsmgr.register(self, self.name, 'receiver',
                          api_key=self.api_key, secret=self.secret, http_proxy=self.http_proxy,
                          statsd_host=self.statsd_host, statsd_port=self.statsd_port,
                          statsd_prefix=self.statsd_prefix, statsd_enabled=self.statsd_enabled)
        logger.load_obj(self, name)
        self.direct_routing = conf['global']['direct_routing']
        self.accept_passive_unknown_check_results = \
            conf['global']['accept_passive_unknown_check_results']

        g_conf = conf['global']

        # If we've got something in the schedulers, we do not want it anymore
        for sched_id in conf['schedulers']:

            already_got = False

            # We can already got this conf id, but with another address
            if sched_id in self.schedulers:
                new_addr = conf['schedulers'][sched_id]['address']
                old_addr = self.schedulers[sched_id]['address']
                new_port = conf['schedulers'][sched_id]['port']
                old_port = self.schedulers[sched_id]['port']
                # Should got all the same to be ok :)
                if new_addr == old_addr and new_port == old_port:
                    already_got = True

            if already_got:
                logger.info("[%s] We already got the conf %d (%s)",
                            self.name, sched_id, conf['schedulers'][sched_id]['name'])
                wait_homerun = self.schedulers[sched_id]['wait_homerun']
                actions = self.schedulers[sched_id]['actions']
                external_commands = self.schedulers[sched_id]['external_commands']
                con = self.schedulers[sched_id]['con']

            s = conf['schedulers'][sched_id]
            self.schedulers[sched_id] = s

            if s['name'] in g_conf['satellitemap']:
                s.update(g_conf['satellitemap'][s['name']])

            proto = 'http'
            if s['use_ssl']:
                proto = 'https'
            uri = '%s://%s:%s/' % (proto, s['address'], s['port'])

            self.schedulers[sched_id]['uri'] = uri
            if already_got:
                self.schedulers[sched_id]['wait_homerun'] = wait_homerun
                self.schedulers[sched_id]['actions'] = actions
                self.schedulers[sched_id]['external_commands'] = external_commands
                self.schedulers[sched_id]['con'] = con
            else:
                self.schedulers[sched_id]['wait_homerun'] = {}
                self.schedulers[sched_id]['actions'] = {}
                self.schedulers[sched_id]['external_commands'] = []
                self.schedulers[sched_id]['con'] = None
            self.schedulers[sched_id]['running_id'] = 0
            self.schedulers[sched_id]['active'] = s['active']
            self.schedulers[sched_id]['timeout'] = s['timeout']
            self.schedulers[sched_id]['data_timeout'] = s['data_timeout']

            # Do not connect if we are a passive satellite
            if self.direct_routing and not already_got:
                # And then we connect to it :)
                self.pynag_con_init(sched_id)



        logger.debug("[%s] Sending us configuration %s", self.name, conf)

        if not self.have_modules:
            self.modules = mods = conf['global']['modules']
            self.have_modules = True
            logger.info("We received modules %s ", mods)

        # Set our giving timezone from arbiter
        use_timezone = conf['global']['use_timezone']
        if use_timezone != 'NOTSET':
            logger.info("Setting our timezone to %s", use_timezone)
            os.environ['TZ'] = use_timezone
            time.tzset()


    # Take all external commands, make packs and send them to
    # the schedulers
    def push_external_commands_to_schedulers(self):
        # If we are not in a direct routing mode, just bailout after
        # faking resolving the commands
        if not self.direct_routing:
            self.external_commands.extend(self.unprocessed_external_commands)
            self.unprocessed_external_commands = []
            return

        commands_to_process = self.unprocessed_external_commands
        self.unprocessed_external_commands = []

        # Now get all external commands and put them into the
        # good schedulers
        for ext_cmd in commands_to_process:
            self.external_command.resolve_command(ext_cmd)

        # Now for all alive schedulers, send the commands
        for sched_id in self.schedulers:
            sched = self.schedulers[sched_id]
            extcmds = sched['external_commands']
            cmds = [extcmd.cmd_line for extcmd in extcmds]
            con = sched.get('con', None)
            sent = False
            if not con:
                logger.warning("The scheduler is not connected %s", sched)
                self.pynag_con_init(sched_id)
                con = sched.get('con', None)

            # If there are commands and the scheduler is alive
            if len(cmds) > 0 and con:
                logger.debug("Sending %d commands to scheduler %s", len(cmds), sched)
                try:
                    # con.run_external_commands(cmds)
                    con.post('run_external_commands', {'cmds': cmds})
                    sent = True
                # Not connected or sched is gone
                except (HTTPExceptions, KeyError), exp:
                    logger.debug('manage_returns exception:: %s,%s ', type(exp), str(exp))
                    self.pynag_con_init(sched_id)
                    return
                except AttributeError, exp:  # the scheduler must  not be initialized
                    logger.debug('manage_returns exception:: %s,%s ', type(exp), str(exp))
                except Exception, exp:
                    logger.error("A satellite raised an unknown exception: %s (%s)", exp, type(exp))
                    raise

            # Wether we sent the commands or not, clean the scheduler list
            self.schedulers[sched_id]['external_commands'] = []

            # If we didn't send them, add the commands to the arbiter list
            if not sent:
                for extcmd in extcmds:
                    self.external_commands.append(extcmd)


    def do_loop_turn(self):
        sys.stdout.write(".")
        sys.stdout.flush()

        # Begin to clean modules
        self.check_and_del_zombie_modules()

        # Now we check if arbiter speak to us in the pyro_daemon.
        # If so, we listen for it
        # When it push us conf, we reinit connections
        self.watch_for_new_conf(0.0)
        if self.new_conf:
            self.setup_new_conf()

        # Maybe external modules raised 'objects'
        # we should get them
        self.get_objects_from_from_queues()

        self.push_external_commands_to_schedulers()

        # print "watch new conf 1: begin", len(self.broks)
        self.watch_for_new_conf(1.0)
        # print "get enw broks watch new conf 1: end", len(self.broks)


    #  Main function, will loop forever
    def main(self):
        try:
            self.load_config_file()

            # Setting log level
            logger.setLevel(self.log_level)
            # Force the debug level if the daemon is said to start with such level
            if self.debug:
                logger.setLevel('DEBUG')

            # Look if we are enabled or not. If ok, start the daemon mode
            self.look_for_early_exit()

            for line in self.get_header():
                logger.info(line)

            logger.info("[Receiver] Using working directory: %s", os.path.abspath(self.workdir))

            self.do_daemon_init_and_start()

            self.load_modules_manager()

            self.uri2 = self.http_daemon.register(self.interface)
            logger.debug("The Arbiter uri it at %s", self.uri2)

            self.uri3 = self.http_daemon.register(self.istats)

            # Register ibroks
            if self.ibroks is not None:
                logger.debug("Deconnecting previous Broks Interface")
                self.http_daemon.unregister(self.ibroks)
            # Create and connect it
            self.http_daemon.register(self.ibroks)

            #  We wait for initial conf
            self.wait_for_initial_conf()
            if not self.new_conf:
                return

            self.setup_new_conf()
            self.modules_manager.set_modules(self.modules)
            self.do_load_modules()
            # and start external modules too
            self.modules_manager.start_external_instances()

            # Do the modules part, we have our modules in self.modules
            # REF: doc/receiver-modules.png (1)

            # Now the main loop
            self.do_mainloop()

        except Exception, exp:
            self.print_unrecoverable(traceback.format_exc())
            raise


    # stats threads is asking us a main structure for stats
    def get_stats_struct(self):
        now = int(time.time())
        # call the daemon one
        res = super(Receiver, self).get_stats_struct()
        res.update({'name': self.name, 'type': 'receiver',
                    'direct_routing': self.direct_routing})
        metrics = res['metrics']
        # metrics specific
        metrics.append('receiver.%s.external-commands.queue %d %d' % (
            self.name, len(self.external_commands), now))

        return res
