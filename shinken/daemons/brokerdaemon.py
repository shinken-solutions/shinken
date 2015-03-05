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
import sys
import time
import traceback
import cPickle
import base64
import zlib
import threading
from multiprocessing import active_children

from shinken.satellite import BaseSatellite
from shinken.property import PathProp, IntegerProp
from shinken.util import sort_by_ids
from shinken.log import logger
from shinken.stats import statsmgr
from shinken.external_command import ExternalCommand
from shinken.http_client import HTTPClient, HTTPExceptions
from shinken.daemon import Daemon, Interface

class IStats(Interface):
    """
    Interface for various stats about broker activity
    """

    doc = 'Get raw stats from the daemon'
    def get_raw_stats(self):
        app = self.app
        res = []

        insts = [inst for inst in app.modules_manager.instances if inst.is_external]
        for inst in insts:
            try:
                res.append({'module_name': inst.get_name(), 'queue_size': inst.to_q.qsize()})
            except Exception, exp:
                res.append({'module_name': inst.get_name(), 'queue_size': 0})

        return res
    get_raw_stats.doc = doc


# Our main APP class
class Broker(BaseSatellite):

    properties = BaseSatellite.properties.copy()
    properties.update({
        'pidfile':   PathProp(default='brokerd.pid'),
        'port':      IntegerProp(default=7772),
        'local_log': PathProp(default='brokerd.log'),
    })

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file, profile=''):

        super(Broker, self).__init__('broker', config_file, is_daemon, do_replace, debug,
                                     debug_file)

        # Our arbiters
        self.arbiters = {}

        # Our pollers, reactionners and receivers
        self.pollers = {}
        self.reactionners = {}
        self.receivers = {}

        # Modules are load one time
        self.have_modules = False

        # Can have a queue of external_commands given by modules
        # will be processed by arbiter
        self.external_commands = []

        # All broks to manage
        self.broks = []  # broks to manage
        # broks raised this turn and that needs to be put in self.broks
        self.broks_internal_raised = []
        # broks raised by the arbiters, we need a lock so the push can be in parallel
        # to our current activities and won't lock the arbiter
        self.arbiter_broks = []
        self.arbiter_broks_lock = threading.RLock()

        self.timeout = 1.0

        self.istats = IStats(self)


    # Schedulers have some queues. We can simplify the call by adding
    # elements into the proper queue just by looking at their type
    # Brok -> self.broks
    # TODO: better tag ID?
    # External commands -> self.external_commands
    def add(self, elt):
        cls_type = elt.__class__.my_type
        if cls_type == 'brok':
            # For brok, we TAG brok with our instance_id
            elt.instance_id = 0
            self.broks_internal_raised.append(elt)
            return
        elif cls_type == 'externalcommand':
            logger.debug("Enqueuing an external command '%s'", str(ExternalCommand.__dict__))
            self.external_commands.append(elt)
        # Maybe we got a Message from the modules, it's way to ask something
        # like from now a full data from a scheduler for example.
        elif cls_type == 'message':
            # We got a message, great!
            logger.debug(str(elt.__dict__))
            if elt.get_type() == 'NeedData':
                data = elt.get_data()
                # Full instance id means: I got no data for this scheduler
                # so give me all dumbass!
                if 'full_instance_id' in data:
                    c_id = data['full_instance_id']
                    source = elt.source
                    logger.info('The module %s is asking me to get all initial data '
                                'from the scheduler %d',
                                source, c_id)
                    # so we just reset the connection and the running_id,
                    # it will just get all new things
                    try:
                        self.schedulers[c_id]['con'] = None
                        self.schedulers[c_id]['running_id'] = 0
                    except KeyError:  # maybe this instance was not known, forget it
                        logger.warning("the module %s ask me a full_instance_id "
                                       "for an unknown ID (%d)!", source, c_id)
            # Maybe a module tells me that it's dead, I must log it's last words...
            if elt.get_type() == 'ICrash':
                data = elt.get_data()
                logger.error('the module %s just crash! Please look at the traceback:',
                             data['name'])
                logger.error(data['trace'])

                # The module death will be looked for elsewhere and restarted.


    # Get the good tabs for links by the kind. If unknown, return None
    def get_links_from_type(self, d_type):
        t = {'scheduler': self.schedulers,
             'arbiter': self.arbiters,
             'poller': self.pollers,
             'reactionner': self.reactionners,
             'receiver': self.receivers
             }
        if d_type in t:
            return t[d_type]
        return None



    # Check if we do not connect to often to this
    def is_connection_try_too_close(self, elt):
        now = time.time()
        last_connection = elt['last_connection']
        if now - last_connection < 5:
            return True
        return False


    # wrapper function for the real function do_
    # just for timing the connection
    def pynag_con_init(self, id, type='scheduler'):
        _t = time.time()
        r = self.do_pynag_con_init(id, type)
        statsmgr.incr('con-init.%s' % type, time.time() - _t)
        return r


    # initialize or re-initialize connection with scheduler or
    # arbiter if type == arbiter
    def do_pynag_con_init(self, id, type='scheduler'):
        # Get the good links tab for looping..
        links = self.get_links_from_type(type)
        if links is None:
            logger.debug('Type unknown for connection! %s', type)
            return

        # default timeout for daemons like pollers/reactionners/...
        timeout = 3
        data_timeout = 120

        if type == 'scheduler':
            # If sched is not active, I do not try to init
            # it is just useless
            is_active = links[id]['active']
            if not is_active:
                return
            # schedulers also got real timeout to respect
            timeout = links[id]['timeout']
            data_timeout = links[id]['data_timeout']

        # If we try to connect too much, we slow down our tests
        if self.is_connection_try_too_close(links[id]):
            return

        # Ok, we can now update it
        links[id]['last_connection'] = time.time()

        # DBG: print "Init connection with", links[id]['uri']
        running_id = links[id]['running_id']
        # DBG: print "Running id before connection", running_id
        uri = links[id]['uri']
        try:
            con = links[id]['con'] = HTTPClient(uri=uri,
                                                strong_ssl=links[id]['hard_ssl_name_check'],
                                                timeout=timeout, data_timeout=data_timeout)
        except HTTPExceptions, exp:
            # But the multiprocessing module is not compatible with it!
            # so we must disable it immediately after
            logger.info("Connection problem to the %s %s: %s", type, links[id]['name'], str(exp))
            links[id]['con'] = None
            return


        try:
            # initial ping must be quick
            con.get('ping')
            new_run_id = con.get('get_running_id')
            new_run_id = float(new_run_id)
            # data transfer can be longer

            # The schedulers have been restarted: it has a new run_id.
            # So we clear all verifs, they are obsolete now.
            if new_run_id != running_id:
                logger.debug("[%s] New running id for the %s %s: %s (was %s)",
                             self.name, type, links[id]['name'], new_run_id, running_id)
                links[id]['broks'].clear()
                # we must ask for a new full broks if
                # it's a scheduler
                if type == 'scheduler':
                    logger.debug("[%s] I ask for a broks generation to the scheduler %s",
                                 self.name, links[id]['name'])
                    con.get('fill_initial_broks', {'bname': self.name}, wait='long')
            # Ok all is done, we can save this new running id
            links[id]['running_id'] = new_run_id
        except HTTPExceptions, exp:
            logger.info("Connection problem to the %s %s: %s", type, links[id]['name'], str(exp))
            links[id]['con'] = None
            return
        except KeyError, exp:
            logger.info("the %s '%s' is not initialized: %s", type, links[id]['name'], str(exp))
            links[id]['con'] = None
            traceback.print_stack()
            return

        logger.info("Connection OK to the %s %s", type, links[id]['name'])


    # Get a brok. Our role is to put it in the modules
    # DO NOT CHANGE data of b!!!
    # REF: doc/broker-modules.png (4-5)
    def manage_brok(self, b):
        # Call all modules if they catch the call
        for mod in self.modules_manager.get_internal_instances():
            try:
                mod.manage_brok(b)
            except Exception, exp:
                logger.debug(str(exp.__dict__))
                logger.warning("The mod %s raise an exception: %s, I'm tagging it to restart later",
                               mod.get_name(), str(exp))
                logger.warning("Exception type: %s", type(exp))
                logger.warning("Back trace of this kill: %s", traceback.format_exc())
                self.modules_manager.set_to_restart(mod)


    # Add broks (a tab) to different queues for
    # internal and external modules
    def add_broks_to_queue(self, broks):
        # Ok now put in queue broks to be managed by
        # internal modules
        self.broks.extend(broks)


    # Each turn we get all broks from
    # self.broks_internal_raised and we put them in
    # self.broks
    def interger_internal_broks(self):
        self.add_broks_to_queue(self.broks_internal_raised)
        self.broks_internal_raised = []


    # We will get in the broks list the broks from the arbiters,
    # but as the arbiter_broks list can be push by arbiter without Global lock,
    # we must protect this with he list lock
    def interger_arbiter_broks(self):
        with self.arbiter_broks_lock:
            self.add_broks_to_queue(self.arbiter_broks)
            self.arbiter_broks = []


    # We get new broks from schedulers
    # REF: doc/broker-modules.png (2)
    def get_new_broks(self, type='scheduler'):
        # Get the good links tab for looping..
        links = self.get_links_from_type(type)
        if links is None:
            logger.debug('Type unknown for connection! %s', type)
            return

        # We check for new check in each schedulers and put
        # the result in new_checks
        for sched_id in links:
            try:
                con = links[sched_id]['con']
                if con is not None:  # None = not initialized
                    t0 = time.time()
                    # Before ask a call that can be long, do a simple ping to be sure it is alive
                    con.get('ping')
                    tmp_broks = con.get('get_broks', {'bname': self.name}, wait='long')
                    try:
                        _t = base64.b64decode(tmp_broks)
                        _t = zlib.decompress(_t)
                        tmp_broks = cPickle.loads(_t)
                    except (TypeError, zlib.error, cPickle.PickleError), exp:
                        logger.error('Cannot load broks data from %s : %s',
                                     links[sched_id]['name'], exp)
                        links[sched_id]['con'] = None
                        continue
                    logger.debug("%s Broks get in %s", len(tmp_broks), time.time() - t0)
                    for b in tmp_broks.values():
                        b.instance_id = links[sched_id]['instance_id']
                    # Ok, we can add theses broks to our queues
                    self.add_broks_to_queue(tmp_broks.values())

                else:  # no con? make the connection
                    self.pynag_con_init(sched_id, type=type)
            # Ok, con is not known, so we create it
            except KeyError, exp:
                logger.debug("Key error for get_broks : %s", str(exp))
                self.pynag_con_init(sched_id, type=type)
            except HTTPExceptions, exp:
                logger.warning("Connection problem to the %s %s: %s",
                               type, links[sched_id]['name'], str(exp))
                links[sched_id]['con'] = None
            # scheduler must not #be initialized
            except AttributeError, exp:
                logger.warning("The %s %s should not be initialized: %s",
                               type, links[sched_id]['name'], str(exp))
            # scheduler must not have checks
            #  What the F**k? We do not know what happened,
            # so.. bye bye :)
            except Exception, x:
                logger.error(str(x))
                logger.error(traceback.format_exc())
                sys.exit(1)


    # Helper function for module, will give our broks
    def get_retention_data(self):
        return self.broks


    # Get back our broks from a retention module
    def restore_retention_data(self, data):
        self.broks.extend(data)


    def do_stop(self):
        act = active_children()
        for a in act:
            a.terminate()
            a.join(1)
        super(Broker, self).do_stop()


    def setup_new_conf(self):
        conf = self.new_conf
        self.new_conf = None
        self.cur_conf = conf
        # Got our name from the globals
        g_conf = conf['global']
        if 'broker_name' in g_conf:
            name = g_conf['broker_name']
        else:
            name = 'Unnamed broker'
        self.name = name
        self.api_key = g_conf['api_key']
        self.secret = g_conf['secret']
        self.http_proxy = g_conf['http_proxy']
        self.statsd_host = g_conf['statsd_host']
        self.statsd_port = g_conf['statsd_port']
        self.statsd_prefix = g_conf['statsd_prefix']
        self.statsd_enabled = g_conf['statsd_enabled']

        # We got a name so we can update the logger and the stats global objects
        logger.load_obj(self, name)
        statsmgr.register(self, name, 'broker',
                          api_key=self.api_key, secret=self.secret, http_proxy=self.http_proxy,
                          statsd_host=self.statsd_host, statsd_port=self.statsd_port,
                          statsd_prefix=self.statsd_prefix, statsd_enabled=self.statsd_enabled)

        logger.debug("[%s] Sending us configuration %s", self.name, conf)
        # If we've got something in the schedulers, we do not
        # want it anymore
        # self.schedulers.clear()
        for sched_id in conf['schedulers']:
            # Must look if we already have it to do not overdie our broks
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
                broks = self.schedulers[sched_id]['broks']
                running_id = self.schedulers[sched_id]['running_id']
            else:
                broks = {}
                running_id = 0
            s = conf['schedulers'][sched_id]
            self.schedulers[sched_id] = s

            # replacing scheduler address and port by those defined in satellitemap
            if s['name'] in g_conf['satellitemap']:
                s = dict(s)  # make a copy
                s.update(g_conf['satellitemap'][s['name']])
            proto = 'http'
            if s['use_ssl']:
                proto = 'https'
            uri = '%s://%s:%s/' % (proto, s['address'], s['port'])
            self.schedulers[sched_id]['uri'] = uri

            self.schedulers[sched_id]['broks'] = broks
            self.schedulers[sched_id]['instance_id'] = s['instance_id']
            self.schedulers[sched_id]['running_id'] = running_id
            self.schedulers[sched_id]['active'] = s['active']
            self.schedulers[sched_id]['last_connection'] = 0
            self.schedulers[sched_id]['timeout'] = s['timeout']
            self.schedulers[sched_id]['data_timeout'] = s['data_timeout']

        logger.info("We have our schedulers: %s ", self.schedulers)

        # Now get arbiter
        for arb_id in conf['arbiters']:
            # Must look if we already have it
            already_got = arb_id in self.arbiters
            if already_got:
                broks = self.arbiters[arb_id]['broks']
            else:
                broks = {}
            a = conf['arbiters'][arb_id]
            self.arbiters[arb_id] = a

            # replacing arbiter address and port by those defined in satellitemap
            if a['name'] in g_conf['satellitemap']:
                a = dict(a)  # make a copy
                a.update(g_conf['satellitemap'][a['name']])

            proto = 'http'
            if a['use_ssl']:
                proto = 'https'
            uri = '%s://%s:%s/' % (proto, a['address'], a['port'])
            self.arbiters[arb_id]['uri'] = uri

            self.arbiters[arb_id]['broks'] = broks
            self.arbiters[arb_id]['instance_id'] = 0  # No use so all to 0
            self.arbiters[arb_id]['running_id'] = 0
            self.arbiters[arb_id]['last_connection'] = 0

            # We do not connect to the arbiter. Connection hangs

        logger.info("We have our arbiters: %s ", self.arbiters)

        # Now for pollers
        for pol_id in conf['pollers']:
            # Must look if we already have it
            already_got = pol_id in self.pollers
            if already_got:
                broks = self.pollers[pol_id]['broks']
                running_id = self.schedulers[sched_id]['running_id']
            else:
                broks = {}
                running_id = 0
            p = conf['pollers'][pol_id]
            self.pollers[pol_id] = p

            # replacing poller address and port by those defined in satellitemap
            if p['name'] in g_conf['satellitemap']:
                p = dict(p)  # make a copy
                p.update(g_conf['satellitemap'][p['name']])

            proto = 'http'
            if p['use_ssl']:
                proto = 'https'

            uri = '%s://%s:%s/' % (proto, p['address'], p['port'])
            self.pollers[pol_id]['uri'] = uri

            self.pollers[pol_id]['broks'] = broks
            self.pollers[pol_id]['instance_id'] = 0  # No use so all to 0
            self.pollers[pol_id]['running_id'] = running_id
            self.pollers[pol_id]['last_connection'] = 0

#                    #And we connect to it
#                    self.app.pynag_con_init(pol_id, 'poller')

        logger.info("We have our pollers: %s", self.pollers)

        # Now reactionners
        for rea_id in conf['reactionners']:
            # Must look if we already have it
            already_got = rea_id in self.reactionners
            if already_got:
                broks = self.reactionners[rea_id]['broks']
                running_id = self.schedulers[sched_id]['running_id']
            else:
                broks = {}
                running_id = 0

            r = conf['reactionners'][rea_id]
            self.reactionners[rea_id] = r

            # replacing reactionner address and port by those defined in satellitemap
            if r['name'] in g_conf['satellitemap']:
                r = dict(r)  # make a copy
                r.update(g_conf['satellitemap'][r['name']])

            proto = 'http'
            if r['use_ssl']:
                proto = 'https'
            uri = '%s://%s:%s/' % (proto, r['address'], r['port'])
            self.reactionners[rea_id]['uri'] = uri

            self.reactionners[rea_id]['broks'] = broks
            self.reactionners[rea_id]['instance_id'] = 0  # No use so all to 0
            self.reactionners[rea_id]['running_id'] = running_id
            self.reactionners[rea_id]['last_connection'] = 0

#                    #And we connect to it
#                    self.app.pynag_con_init(rea_id, 'reactionner')

        logger.info("We have our reactionners: %s", self.reactionners)

        # Now receivers
        for rec_id in conf['receivers']:
            # Must look if we already have it
            already_got = rec_id in self.receivers
            if already_got:
                broks = self.receivers[rec_id]['broks']
                running_id = self.schedulers[sched_id]['running_id']
            else:
                broks = {}
                running_id = 0

            r = conf['receivers'][rec_id]
            self.receivers[rec_id] = r

            # replacing reactionner address and port by those defined in satellitemap
            if r['name'] in g_conf['satellitemap']:
                r = dict(r)  # make a copy
                r.update(g_conf['satellitemap'][r['name']])

            proto = 'http'
            if r['use_ssl']:
                proto = 'https'
            uri = '%s://%s:%s/' % (proto, r['address'], r['port'])
            self.receivers[rec_id]['uri'] = uri

            self.receivers[rec_id]['broks'] = broks
            self.receivers[rec_id]['instance_id'] = 0  # No use so all to 0
            self.receivers[rec_id]['running_id'] = running_id
            self.receivers[rec_id]['last_connection'] = 0

        if not self.have_modules:
            self.modules = mods = conf['global']['modules']
            self.have_modules = True
            logger.info("We received modules %s ", mods)

            # Ok now start, or restart them!
            # Set modules, init them and start external ones
            self.modules_manager.set_modules(self.modules)
            self.do_load_modules()
            self.modules_manager.start_external_instances()



        # Set our giving timezone from arbiter
        use_timezone = conf['global']['use_timezone']
        if use_timezone != 'NOTSET':
            logger.info("Setting our timezone to %s", use_timezone)
            os.environ['TZ'] = use_timezone
            time.tzset()

        # Connection init with Schedulers
        for sched_id in self.schedulers:
            self.pynag_con_init(sched_id, type='scheduler')

        for pol_id in self.pollers:
            self.pynag_con_init(pol_id, type='poller')

        for rea_id in self.reactionners:
            self.pynag_con_init(rea_id, type='reactionner')


    # An arbiter ask us to wait for a new conf, so we must clean
    # all our mess we did, and close modules too
    def clean_previous_run(self):
        # Clean all lists
        self.schedulers.clear()
        self.pollers.clear()
        self.reactionners.clear()
        self.broks = self.broks[:]
        self.broks_internal_raised = self.broks_internal_raised[:]
        with self.arbiter_broks_lock:
            self.arbiter_broks = self.arbiter_broks[:]
        self.external_commands = self.external_commands[:]

        # And now modules
        self.have_modules = False
        self.modules_manager.clear_instances()



    # stats threads is asking us a main structure for stats
    def get_stats_struct(self):
        now = int(time.time())
        # call the daemon one
        res = super(Broker, self).get_stats_struct()
        res.update({'name': self.name, 'type': 'broker'})
        metrics = res['metrics']
        # metrics specific
        metrics.append('broker.%s.external-commands.queue %d %d' % (
            self.name, len(self.external_commands), now))
        metrics.append('broker.%s.broks.queue %d %d' % (self.name, len(self.broks), now))

        return res


    def do_loop_turn(self):
        logger.debug("Begin Loop: managing old broks (%d)", len(self.broks))

        # Dump modules Queues size
        insts = [inst for inst in self.modules_manager.instances if inst.is_external]
        for inst in insts:
            try:
                logger.debug("External Queue len (%s): %s", inst.get_name(), inst.to_q.qsize())
            except Exception, exp:
                logger.debug("External Queue len (%s): Exception! %s", inst.get_name(), exp)

        # Begin to clean modules
        self.check_and_del_zombie_modules()

        # Maybe the arbiter ask us to wait for a new conf
        # If true, we must restart all...
        if self.cur_conf is None:
            # Clean previous run from useless objects
            # and close modules
            self.clean_previous_run()

            self.wait_for_initial_conf()
            # we may have been interrupted or so; then
            # just return from this loop turn
            if not self.new_conf:
                return
            self.setup_new_conf()

        # Now we check if arbiter speak to us in the pyro_daemon.
        # If so, we listen for it
        # When it pushes conf to us, we reinit connections
        self.watch_for_new_conf(0.0)
        if self.new_conf:
            self.setup_new_conf()

        # Maybe the last loop we raised some broks internally
        # we should integrate them in broks
        self.interger_internal_broks()
        # Also reap broks sent from the arbiters
        self.interger_arbiter_broks()

        # Main job, go get broks in our distants daemons
        types = ['scheduler', 'poller', 'reactionner', 'receiver']
        for _type in types:
            _t = time.time()
            # And from schedulers
            self.get_new_broks(type=_type)
            statsmgr.incr('get-new-broks.%s' % _type, time.time() - _t)

        # Sort the brok list by id
        self.broks.sort(sort_by_ids)

        # and for external queues
        # REF: doc/broker-modules.png (3)
        # We put to external queues broks that was not already send
        t0 = time.time()
        # We are sending broks as a big list, more efficient than one by one
        ext_modules = self.modules_manager.get_external_instances()
        to_send = [b for b in self.broks if getattr(b, 'need_send_to_ext', True)]

        # Send our pack to all external modules to_q queue so they can get the wole packet
        # beware, the sub-process/queue can be die/close, so we put to restart the whole module
        # instead of killing ourself :)
        for mod in ext_modules:
            try:
                mod.to_q.put(to_send)
            except Exception, exp:
                # first we must find the modules
                logger.debug(str(exp.__dict__))
                logger.warning("The mod %s queue raise an exception: %s, "
                               "I'm tagging it to restart later",
                               mod.get_name(), str(exp))
                logger.warning("Exception type: %s", type(exp))
                logger.warning("Back trace of this kill: %s", traceback.format_exc())
                self.modules_manager.set_to_restart(mod)


        # No more need to send them
        for b in to_send:
            b.need_send_to_ext = False
        statsmgr.incr('core.put-to-external-queue', time.time() - t0)
        logger.debug("Time to send %s broks (%d secs)", len(to_send), time.time() - t0)

        # We must had new broks at the end of the list, so we reverse the list
        self.broks.reverse()

        start = time.time()
        while len(self.broks) != 0:
            now = time.time()
            # Do not 'manage' more than 1s, we must get new broks
            # every 1s
            if now - start > 1:
                break

            b = self.broks.pop()
            # Ok, we can get the brok, and doing something with it
            # REF: doc/broker-modules.png (4-5)
            # We un serialize the brok before consume it
            b.prepare()
            _t = time.time()
            self.manage_brok(b)
            statsmgr.incr('core.manage-brok', time.time() - _t)

            nb_broks = len(self.broks)

            # Ok we manage brok, but we still want to listen to arbiter
            self.watch_for_new_conf(0.0)

            # if we got new broks here from arbiter, we should break the loop
            # because such broks will not be managed by the
            # external modules before this loop (we pop them!)
            if len(self.broks) != nb_broks:
                break

        # Maybe external modules raised 'objects'
        # we should get them
        self.get_objects_from_from_queues()

        # Maybe we do not have something to do, so we wait a little
        # TODO: redone the diff management....
        if len(self.broks) == 0:
            while self.timeout > 0:
                begin = time.time()
                self.watch_for_new_conf(1.0)
                end = time.time()
                self.timeout = self.timeout - (end - begin)
            self.timeout = 1.0

            # print "get new broks watch new conf 1: end", len(self.broks)

        # Say to modules it's a new tick :)
        self.hook_point('tick')


    #  Main function, will loop forever
    def main(self):
        try:
            self.load_config_file()

            # Setting log level
            logger.setLevel(self.log_level)
            # Force the debug level if the daemon is said to start with such level
            if self.debug:
                logger.setLevel('DEBUG')

            for line in self.get_header():
                logger.info(line)

            logger.info("[Broker] Using working directory: %s", os.path.abspath(self.workdir))

            # Look if we are enabled or not. If ok, start the daemon mode
            self.look_for_early_exit()
            self.do_daemon_init_and_start()
            self.load_modules_manager()

            self.uri2 = self.http_daemon.register(self.interface)
            logger.debug("The Arbiter uri it at %s", self.uri2)

            self.uri3 = self.http_daemon.register(self.istats)

            #  We wait for initial conf
            self.wait_for_initial_conf()
            if not self.new_conf:
                return

            self.setup_new_conf()


            # Do the modules part, we have our modules in self.modules
            # REF: doc/broker-modules.png (1)
            self.hook_point('load_retention')

            # Now the main loop
            self.do_mainloop()

        except Exception, exp:
            self.print_unrecoverable(traceback.format_exc())
            raise
