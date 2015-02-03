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

"""
 This is the class of the dispatcher. Its role is to dispatch
 configurations to other elements like schedulers, reactionner,
 pollers, receivers and brokers. It is responsible for high availability part. If an
 element dies and the element type has a spare, it sends the config of the
 dead one to the spare
"""

import time
import random

from shinken.util import alive_then_spare_then_deads
from shinken.log import logger

# Always initialize random :)
random.seed()


# Dispatcher Class
class Dispatcher:

    # Load all elements, set them as not assigned
    # and add them to elements, so loop will be easier :)
    def __init__(self, conf, arbiter):
        self.arbiter = arbiter
        # Pointer to the whole conf
        self.conf = conf
        self.realms = conf.realms
        # Direct pointer to important elements for us

        for sat_type in ('arbiters', 'schedulers', 'reactionners',
                         'brokers', 'receivers', 'pollers'):
            setattr(self, sat_type, getattr(self.conf, sat_type))

            # for each satellite, we look if current arbiter have a specific
            # satellitemap value set for this satellite.
            # if so, we give this map to the satellite (used to build satellite URI later)
            if arbiter is None:
                continue

            key = sat_type[:-1] + '_name'  # i.e: schedulers -> scheduler_name
            for satellite in getattr(self, sat_type):
                sat_name = getattr(satellite, key)
                satellite.set_arbiter_satellitemap(arbiter.satellitemap.get(sat_name, {}))

        self.dispatch_queue = {'schedulers': [], 'reactionners': [],
                               'brokers': [], 'pollers': [], 'receivers': []}
        self.elements = []  # all elements, sched and satellites
        self.satellites = []  # only satellites not schedulers

        for cfg in self.conf.confs.values():
            cfg.is_assigned = False
            cfg.assigned_to = None
            # We try to remember each "push", so we
            # can know with configuration ids+flavor
            # if a satellite already got it or not :)
            cfg.push_flavor = 0

        # Add satellites in the good lists
        self.elements.extend(self.schedulers)

        # Others are in 2 lists
        self.elements.extend(self.reactionners)
        self.satellites.extend(self.reactionners)
        self.elements.extend(self.pollers)
        self.satellites.extend(self.pollers)
        self.elements.extend(self.brokers)
        self.satellites.extend(self.brokers)
        self.elements.extend(self.receivers)
        self.satellites.extend(self.receivers)

        # Some flag about dispatch need or not
        self.dispatch_ok = False
        self.first_dispatch_done = False

        # Prepare the satellites confs
        for satellite in self.satellites:
            satellite.prepare_for_conf()

        # Some properties must be given to satellites from global
        # configuration, like the max_plugins_output_length to pollers
        parameters = {'max_plugins_output_length': self.conf.max_plugins_output_length}
        for poller in self.pollers:
            poller.add_global_conf_parameters(parameters)

        # Reset need_conf for all schedulers.
        for s in self.schedulers:
            s.need_conf = True
        # Same for receivers
        for rec in self.receivers:
            rec.need_conf = True


    # checks alive elements
    def check_alive(self):
        for elt in self.elements:
            # print "Updating elements", elt.get_name(), elt.__dict__
            elt.update_infos()

            # Not alive needs new need_conf
            # and spare too if they do not have already a conf
            # REF: doc/shinken-scheduler-lost.png (1)
            if not elt.alive or hasattr(elt, 'conf') and elt.conf is None:
                elt.need_conf = True

        for arb in self.arbiters:
            # If not me, but not the master too
            if arb != self.arbiter and arb.spare:
                arb.update_infos()
                # print "Arb", arb.get_name(), "alive?", arb.alive, arb.__dict__


    # Check if all active items are still alive
    # the result goes into self.dispatch_ok
    # TODO: finish need conf
    def check_dispatch(self):
        # Check if the other arbiter has a conf, but only if I am a master
        for arb in self.arbiters:
            # If not me and I'm a master
            if arb != self.arbiter and self.arbiter and not self.arbiter.spare:
                if not arb.have_conf(self.conf.magic_hash):
                    if not hasattr(self.conf, 'whole_conf_pack'):
                        logger.error('CRITICAL: the arbiter try to send a configureion but '
                                     'it is not a MASTER one?? Look at your configuration.')
                        continue
                    arb.put_conf(self.conf.whole_conf_pack)
                    # Remind it that WE are the master here!
                    arb.do_not_run()
                else:
                    # Ok, it already has the conf. I remember that
                    # it does not have to run, I'm still alive!
                    arb.do_not_run()

        # We check for confs to be dispatched on alive scheds. If not dispatched, need dispatch :)
        # and if dispatch on a failed node, remove the association, and need a new dispatch
        for r in self.realms:
            for cfg_id in r.confs:
                push_flavor = r.confs[cfg_id].push_flavor
                sched = r.confs[cfg_id].assigned_to
                if sched is None:
                    if self.first_dispatch_done:
                        logger.info("Scheduler configuration %d is unmanaged!!", cfg_id)
                    self.dispatch_ok = False
                else:
                    if not sched.alive:
                        self.dispatch_ok = False  # so we ask a new dispatching
                        logger.warning("Scheduler %s had the configuration %d but is dead, "
                                       "I am not happy.", sched.get_name(), cfg_id)
                        sched.conf.assigned_to = None
                        sched.conf.is_assigned = False
                        sched.conf.push_flavor = 0
                        sched.push_flavor = 0
                        sched.conf = None
                    # Maybe the scheduler restarts, so is alive but without
                    # the conf we think it was managing so ask it what it is
                    # really managing, and if not, put the conf unassigned
                    if not sched.do_i_manage(cfg_id, push_flavor):
                        self.dispatch_ok = False  # so we ask a new dispatching
                        logger.warning("Scheduler %s did not managed its configuration %d, "
                                       "I am not happy.", sched.get_name(), cfg_id)
                        if sched.conf:
                            sched.conf.assigned_to = None
                            sched.conf.is_assigned = False
                            sched.conf.push_flavor = 0
                        sched.push_flavor = 0
                        sched.need_conf = True
                        sched.conf = None
                    # Else: ok the conf is managed by a living scheduler

        # Maybe satellites are alive, but do not have a cfg yet.
        # I think so. It is not good. I ask a global redispatch for
        # the cfg_id I think is not correctly dispatched.
        for r in self.realms:
            for cfg_id in r.confs:
                push_flavor = r.confs[cfg_id].push_flavor
                try:
                    for kind in ('reactionner', 'poller', 'broker', 'receiver'):
                        # We must have the good number of satellite or we are not happy
                        # So we are sure to raise a dispatch every loop a satellite is missing
                        if (len(r.to_satellites_managed_by[kind][cfg_id])
                                < r.get_nb_of_must_have_satellites(kind)):
                            logger.warning("Missing satellite %s for configuration %d:",
                                           kind, cfg_id)

                            # TODO: less violent! Must only resent to who need?
                            # must be caught by satellite who sees that
                            # it already has the conf (hash) and do nothing
                            self.dispatch_ok = False  # so we will redispatch all
                            r.to_satellites_need_dispatch[kind][cfg_id] = True
                            r.to_satellites_managed_by[kind][cfg_id] = []
                        for satellite in r.to_satellites_managed_by[kind][cfg_id]:
                            # Maybe the sat was marked as not alive, but still in
                            # to_satellites_managed_by. That means that a new dispatch
                            # is needed
                            # Or maybe it is alive but I thought that this reactionner
                            # managed the conf and it doesn't.
                            # I ask a full redispatch of these cfg for both cases

                            if push_flavor == 0 and satellite.alive:
                                logger.warning('[%s] The %s %s manage a unmanaged configuration',
                                               r.get_name(), kind, satellite.get_name())
                                continue
                            if not satellite.alive or (
                                    satellite.reachable
                                    and not satellite.do_i_manage(cfg_id, push_flavor)):
                                logger.warning('[%s] The %s %s seems to be down, '
                                               'I must re-dispatch its role to someone else.',
                                               r.get_name(), kind, satellite.get_name())
                                self.dispatch_ok = False  # so we will redispatch all
                                r.to_satellites_need_dispatch[kind][cfg_id] = True
                                r.to_satellites_managed_by[kind][cfg_id] = []
                # At the first pass, there is no cfg_id in to_satellites_managed_by
                except KeyError:
                    pass

        # Look for receivers. If they got conf, it's ok, if not, need a simple
        # conf
        for r in self.realms:
            for rec in r.receivers:
                # If the receiver does not have a conf, must got one :)
                if rec.reachable and not rec.got_conf():
                    self.dispatch_ok = False  # so we will redispatch all
                    rec.need_conf = True


    # Imagine a world where... oh no, wait...
    # Imagine a master got the conf and the network is down
    # a spare takes it (good :) ). Like the Empire, the master
    # strikes back! It was still alive! (like Elvis). It still got conf
    # and is running! not good!
    # Bad dispatch: a link that has a conf but I do not allow this
    # so I ask it to wait a new conf and stop kidding.
    def check_bad_dispatch(self):
        for elt in self.elements:
            if hasattr(elt, 'conf'):
                # If element has a conf, I do not care, it's a good dispatch
                # If dead: I do not ask it something, it won't respond..
                if elt.conf is None and elt.reachable:
                    # print "Ask", elt.get_name() , 'if it got conf'
                    if elt.have_conf():
                        logger.warning("The element %s have a conf and should "
                                       "not have one! I ask it to idle now",
                                       elt.get_name())
                        elt.active = False
                        elt.wait_new_conf()
                        # I do not care about order not send or not. If not,
                        # The next loop will resent it
                    # else:
                    #    print "No conf"

        # I ask satellites which sched_id they manage. If I do not agree, I ask
        # them to remove it
        for satellite in self.satellites:
            kind = satellite.get_my_type()
            if satellite.reachable:
                cfg_ids = satellite.managed_confs  # what_i_managed()
                # I do not care about satellites that do nothing, they already
                # do what I want :)
                if len(cfg_ids) != 0:
                    id_to_delete = []
                    for cfg_id in cfg_ids:
                        # DBG print kind, ":", satellite.get_name(), "manage cfg id:", cfg_id
                        # Ok, we search for realms that have the conf
                        for r in self.realms:
                            if cfg_id in r.confs:
                                # Ok we've got the realm, we check its to_satellites_managed_by
                                # to see if reactionner is in. If not, we remove he sched_id for it
                                if satellite not in r.to_satellites_managed_by[kind][cfg_id]:
                                    id_to_delete.append(cfg_id)
                    # Maybe we removed all cfg_id of this reactionner
                    # We can put it idle, no active and wait_new_conf
                    if len(id_to_delete) == len(cfg_ids):
                        satellite.active = False
                        logger.info("I ask %s to wait a new conf", satellite.get_name())
                        satellite.wait_new_conf()
                    else:
                        # It is not fully idle, just less cfg
                        for id in id_to_delete:
                            logger.info("I ask to remove configuration N%d from %s",
                                        id, satellite.get_name())
                            satellite.remove_from_conf(id)


    # Make an ORDERED list of schedulers so we can
    # send them conf in this order for a specific realm
    def get_scheduler_ordered_list(self, r):
        # get scheds, alive and no spare first
        scheds = []
        for s in r.schedulers:
            scheds.append(s)

        # now the spare scheds of higher realms
        # they are after the sched of realm, so
        # they will be used after the spare of
        # the realm
        for higher_r in r.higher_realms:
            for s in higher_r.schedulers:
                if s.spare:
                    scheds.append(s)

        # Now we sort the scheds so we take master, then spare
        # the dead, but we do not care about them
        scheds.sort(alive_then_spare_then_deads)
        scheds.reverse()  # pop is last, I need first

        print_sched = [s.get_name() for s in scheds]
        print_sched.reverse()

        return scheds


    # Manage the dispatch
    # REF: doc/shinken-conf-dispatching.png (3)
    def dispatch(self):
        # Ok, we pass at least one time in dispatch, so now errors are True errors
        self.first_dispatch_done = True

        # If no needed to dispatch, do not dispatch :)
        if not self.dispatch_ok:
            for r in self.realms:
                conf_to_dispatch = [cfg for cfg in r.confs.values() if not cfg.is_assigned]
                nb_conf = len(conf_to_dispatch)
                if nb_conf > 0:
                    logger.info("Dispatching Realm %s", r.get_name())
                    logger.info('[%s] Dispatching %d/%d configurations',
                                r.get_name(), nb_conf, len(r.confs))

                # Now we get in scheds all scheduler of this realm and upper so
                # we will send them conf (in this order)
                scheds = self.get_scheduler_ordered_list(r)

                if nb_conf > 0:
                    print_string = '[%s] Schedulers order: %s' % (
                        r.get_name(), ','.join([s.get_name() for s in scheds]))
                    logger.info(print_string)

                # Try to send only for alive members
                scheds = [s for s in scheds if s.alive]

                # Now we do the real job
                # every_one_need_conf = False
                for conf in conf_to_dispatch:
                    logger.info('[%s] Dispatching configuration %s', r.get_name(), conf.id)

                    # If there is no alive schedulers, not good...
                    if len(scheds) == 0:
                        logger.info('[%s] but there a no alive schedulers in this realm!',
                                    r.get_name())

                    # we need to loop until the conf is assigned
                    # or when there are no more schedulers available
                    while True:
                        try:
                            sched = scheds.pop()
                        except IndexError:  # No more schedulers.. not good, no loop
                            # need_loop = False
                            # The conf does not need to be dispatch
                            cfg_id = conf.id
                            for kind in ('reactionner', 'poller', 'broker', 'receiver'):
                                r.to_satellites[kind][cfg_id] = None
                                r.to_satellites_need_dispatch[kind][cfg_id] = False
                                r.to_satellites_managed_by[kind][cfg_id] = []
                            break

                        logger.info('[%s] Trying to send conf %d to scheduler %s',
                                    r.get_name(), conf.id, sched.get_name())
                        if not sched.need_conf:
                            logger.info('[%s] The scheduler %s do not need conf, sorry',
                                        r.get_name(), sched.get_name())
                            continue

                        # We tag conf with the instance_name = scheduler_name
                        instance_name = sched.scheduler_name
                        # We give this configuration a new 'flavor'
                        conf.push_flavor = random.randint(1, 1000000)
                        # REF: doc/shinken-conf-dispatching.png (3)
                        # REF: doc/shinken-scheduler-lost.png (2)
                        override_conf = sched.get_override_configuration()
                        satellites_for_sched = r.get_satellites_links_for_scheduler()
                        s_conf = r.serialized_confs[conf.id]
                        # Prepare the conf before sending it
                        conf_package = {
                            'conf': s_conf, 'override_conf': override_conf,
                            'modules': sched.modules, 'satellites': satellites_for_sched,
                            'instance_name': sched.scheduler_name, 'push_flavor': conf.push_flavor,
                            'skip_initial_broks': sched.skip_initial_broks,
                            'accept_passive_unknown_check_results':
                                sched.accept_passive_unknown_check_results,
                            # shiken.io part
                            'api_key': self.conf.api_key,
                            'secret': self.conf.secret,
                            'http_proxy': self.conf.http_proxy,
                            # statsd one too because OlivierHA love statsd
                            # and after some years of effort he manages to make me
                            # understand the powerfullness of metrics :)
                            'statsd_host': self.conf.statsd_host,
                            'statsd_port': self.conf.statsd_port,
                            'statsd_prefix': self.conf.statsd_prefix,
                            'statsd_enabled': self.conf.statsd_enabled,
                        }

                        t1 = time.time()
                        is_sent = sched.put_conf(conf_package)
                        logger.debug("Conf is sent in %d", time.time() - t1)
                        if not is_sent:
                            logger.warning('[%s] configuration dispatching error for scheduler %s',
                                           r.get_name(), sched.get_name())
                            continue

                        logger.info('[%s] Dispatch OK of conf in scheduler %s',
                                    r.get_name(), sched.get_name())

                        sched.conf = conf
                        sched.push_flavor = conf.push_flavor
                        sched.need_conf = False
                        conf.is_assigned = True
                        conf.assigned_to = sched

                        # We update all data for this scheduler
                        sched.managed_confs = {conf.id: conf.push_flavor}

                        # Now we generate the conf for satellites:
                        cfg_id = conf.id
                        for kind in ('reactionner', 'poller', 'broker', 'receiver'):
                            r.to_satellites[kind][cfg_id] = sched.give_satellite_cfg()
                            r.to_satellites_need_dispatch[kind][cfg_id] = True
                            r.to_satellites_managed_by[kind][cfg_id] = []

                        # Ok, the conf is dispatched, no more loop for this
                        # configuration
                        break

            # We pop conf to dispatch, so it must be no more conf...
            conf_to_dispatch = [cfg for cfg in self.conf.confs.values() if not cfg.is_assigned]
            nb_missed = len(conf_to_dispatch)
            if nb_missed > 0:
                logger.warning("All schedulers configurations are not dispatched, %d are missing",
                               nb_missed)
            else:
                logger.info("OK, all schedulers configurations are dispatched :)")
                self.dispatch_ok = True

            # Sched without conf in a dispatch ok are set to no need_conf
            # so they do not raise dispatch where no use
            if self.dispatch_ok:
                for sched in self.schedulers.items.values():
                    if sched.conf is None:
                        # print "Tagging sched", sched.get_name(),
                        # "so it do not ask anymore for conf"
                        sched.need_conf = False

            arbiters_cfg = {}
            for arb in self.arbiters:
                arbiters_cfg[arb.id] = arb.give_satellite_cfg()

            # We put the satellites conf with the "new" way so they see only what we want
            for r in self.realms:
                for cfg in r.confs.values():
                    cfg_id = cfg.id
                    # flavor if the push number of this configuration send to a scheduler
                    flavor = cfg.push_flavor
                    for kind in ('reactionner', 'poller', 'broker', 'receiver'):
                        if r.to_satellites_need_dispatch[kind][cfg_id]:
                            cfg_for_satellite_part = r.to_satellites[kind][cfg_id]

                            # make copies of potential_react list for sort
                            satellites = []
                            for satellite in r.get_potential_satellites_by_type(kind):
                                satellites.append(satellite)
                            satellites.sort(alive_then_spare_then_deads)

                            # Only keep alive Satellites and reachable ones
                            satellites = [s for s in satellites if s.alive and s.reachable]

                            # If we got a broker, we make the list to pop a new
                            # item first for each scheduler, so it will smooth the load
                            # But the spare must stay at the end ;)
                            # WARNING : skip this if we are in a complet broker link realm
                            if kind == "broker" and not r.broker_complete_links:
                                nospare = [s for s in satellites if not s.spare]
                                # Should look over the list, not over
                                if len(nospare) != 0:
                                    idx = cfg_id % len(nospare)
                                    spares = [s for s in satellites if s.spare]
                                    new_satellites = nospare[idx:]
                                    for _b in nospare[: -idx + 1]:
                                        if _b not in new_satellites:
                                            new_satellites.append(_b)
                                    satellites = new_satellites
                                    satellites.extend(spares)

                            # Dump the order where we will send conf
                            satellite_string = "[%s] Dispatching %s satellite with order: " % (
                                r.get_name(), kind)
                            for satellite in satellites:
                                satellite_string += '%s (spare:%s), ' % (
                                    satellite.get_name(), str(satellite.spare))
                            logger.info(satellite_string)

                            # Now we dispatch cfg to every one ask for it
                            nb_cfg_sent = 0
                            for satellite in satellites:
                                # Send only if we need, and if we can
                                if (nb_cfg_sent < r.get_nb_of_must_have_satellites(kind) and
                                        satellite.alive):
                                    satellite.cfg['schedulers'][cfg_id] = cfg_for_satellite_part
                                    if satellite.manage_arbiters:
                                        satellite.cfg['arbiters'] = arbiters_cfg

                                    # Brokers should have poller/reactionners links too
                                    if kind == "broker":
                                        r.fill_broker_with_poller_reactionner_links(satellite)

                                    is_sent = False
                                    # Maybe this satellite already got this configuration,
                                    # so skip it
                                    if satellite.do_i_manage(cfg_id, flavor):
                                        logger.info('[%s] Skipping configuration %d send '
                                                    'to the %s %s: it already got it',
                                                    r.get_name(), cfg_id, kind,
                                                    satellite.get_name())
                                        is_sent = True
                                    else:  # ok, it really need it :)
                                        logger.info('[%s] Trying to send configuration to %s %s',
                                                    r.get_name(), kind, satellite.get_name())
                                        is_sent = satellite.put_conf(satellite.cfg)

                                    if is_sent:
                                        satellite.active = True
                                        logger.info('[%s] Dispatch OK of configuration %s to %s %s',
                                                    r.get_name(), cfg_id, kind,
                                                    satellite.get_name())
                                        # We change the satellite configuration, update our data
                                        satellite.known_conf_managed_push(cfg_id, flavor)

                                        nb_cfg_sent += 1
                                        r.to_satellites_managed_by[kind][cfg_id].append(satellite)

                                        # If we got a broker, the conf_id must be sent to only ONE
                                        # broker in a classic realm.
                                        if kind == "broker" and not r.broker_complete_links:
                                            break

                                        # If receiver, we must send the hostnames
                                        # of this configuration
                                        if kind == 'receiver':
                                            hnames = [h.get_name() for h in cfg.hosts]
                                            logger.debug("[%s] Sending %s hostnames to the "
                                                         "receiver %s",
                                                         r.get_name(), len(hnames),
                                                         satellite.get_name())
                                            satellite.push_host_names(cfg_id, hnames)
                            # else:
                            #    #I've got enough satellite, the next ones are considered spares
                            if nb_cfg_sent == r.get_nb_of_must_have_satellites(kind):
                                logger.info("[%s] OK, no more %s sent need", r.get_name(), kind)
                                r.to_satellites_need_dispatch[kind][cfg_id] = False

            # And now we dispatch receivers. It's easier, they need ONE conf
            # in all their life :)
            for r in self.realms:
                for rec in r.receivers:
                    if rec.need_conf:
                        logger.info('[%s] Trying to send configuration to receiver %s',
                                    r.get_name(), rec.get_name())
                        is_sent = False
                        if rec.reachable:
                            is_sent = rec.put_conf(rec.cfg)
                        else:
                            logger.info('[%s] Skyping configuration sent to offline receiver %s',
                                        r.get_name(), rec.get_name())
                        if is_sent:
                            rec.active = True
                            rec.need_conf = False
                            logger.info('[%s] Dispatch OK of configuration to receiver %s',
                                        r.get_name(), rec.get_name())
                        else:
                            logger.error('[%s] Dispatching failed for receiver %s',
                                         r.get_name(), rec.get_name())
