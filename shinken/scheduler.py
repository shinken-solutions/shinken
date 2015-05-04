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

import time
import os
import cStringIO
import tempfile
import traceback
import cPickle

import threading
from Queue import Empty

from shinken.external_command import ExternalCommand
from shinken.check import Check
from shinken.notification import Notification
from shinken.eventhandler import EventHandler
from shinken.brok import Brok
from shinken.downtime import Downtime
from shinken.contactdowntime import ContactDowntime
from shinken.comment import Comment
from shinken.acknowledge import Acknowledge
from shinken.log import logger
from shinken.util import nighty_five_percent
from shinken.load import Load
from shinken.http_client import HTTPClient, HTTPExceptions
from shinken.stats import statsmgr
from shinken.misc.common import DICT_MODATTR

class Scheduler(object):
    """Please Add a Docstring to describe the class here"""

    def __init__(self, scheduler_daemon):
        '''
        :type scheduler_daemon: shinken.daemons.schedulerdaemon.Shinken
        '''
        self.sched_daemon = scheduler_daemon
        # When set to false by us, we die and arbiter launch a new Scheduler
        self.must_run = True

        # protect this uniq list
        self.waiting_results_lock = threading.RLock()
        self.waiting_results = []  # satellites returns us results
        # and to not wait for them, we put them here and
        # use them later

        # Every N seconds we call functions like consume, del zombies
        # etc. All of theses functions are in recurrent_works with the
        # every tick to run. So must be an integer > 0
        # The order is important, so make key an int.
        # TODO: at load, change value by configuration one (like reaper time, etc)
        self.recurrent_works = {
            0: ('update_downtimes_and_comments', self.update_downtimes_and_comments, 1),
            1: ('schedule', self.schedule, 1),  # just schedule
            2: ('consume_results', self.consume_results, 1),  # incorporate checks and dependencies

            # now get the news actions (checks, notif) raised
            3: ('get_new_actions', self.get_new_actions, 1),
            4: ('get_new_broks', self.get_new_broks, 1),  # and broks
            5: ('scatter_master_notifications', self.scatter_master_notifications, 1),
            6: ('delete_zombie_checks', self.delete_zombie_checks, 1),
            7: ('delete_zombie_actions', self.delete_zombie_actions, 1),
            # 3: (self.delete_unwanted_notifications, 1),
            8: ('check_freshness', self.check_freshness, 10),
            9: ('clean_caches', self.clean_caches, 1),
            10: ('update_retention_file', self.update_retention_file, 3600),
            11: ('check_orphaned', self.check_orphaned, 60),
            # For NagVis like tools: update our status every 10s
            12: ('get_and_register_update_program_status_brok',
                 self.get_and_register_update_program_status_brok, 10),
            # Check for system time change. And AFTER get new checks
            # so they are changed too.
            13: ('check_for_system_time_change', self.sched_daemon.check_for_system_time_change, 1),
            # launch if need all internal checks
            14: ('manage_internal_checks', self.manage_internal_checks, 1),
            # clean some times possible overridden Queues, to do not explode in memory usage
            # every 1/4 of hour
            15: ('clean_queues', self.clean_queues, 1),
            # Look for new business_impact change by modulation every minute
            16: ('update_business_values', self.update_business_values, 60),
            # Reset the topology change flag if need
            17: ('reset_topology_change_flag', self.reset_topology_change_flag, 1),
            18: ('check_for_expire_acknowledge', self.check_for_expire_acknowledge, 1),
            19: ('send_broks_to_modules', self.send_broks_to_modules, 1),
            20: ('get_objects_from_from_queues', self.get_objects_from_from_queues, 1),
        }

        # stats part
        self.nb_checks_send = 0
        self.nb_actions_send = 0
        self.nb_broks_send = 0
        self.nb_check_received = 0

        # Log init
        logger.load_obj(self)

        self.instance_id = 0  # Temporary set. Will be erase later

        # Ours queues
        self.checks = {}
        self.actions = {}
        self.downtimes = {}
        self.contact_downtimes = {}
        self.comments = {}
        self.broks = {}

        # Some flags
        self.has_full_broks = False  # have a initial_broks in broks queue?
        self.need_dump_memory = False  # set by signal 1
        self.need_objects_dump = False  # set by signal 2

        # And a dummy push flavor
        self.push_flavor = 0

        # Now fake initialize for our satellites
        self.brokers = {}
        self.pollers = {}
        self.reactionners = {}


    def reset(self):
        self.must_run = True
        with self.waiting_results_lock:
            del self.waiting_results[:]
        for o in self.checks, self.actions, self.downtimes,\
                self.contact_downtimes, self.comments,\
                self.broks, self.brokers:
            o.clear()

    def iter_hosts_and_services(self):
        for what in (self.hosts, self.services):
            for elt in what:
                yield elt

    # Load conf for future use
    # we are in_test if the data are from an arbiter object like,
    # so only for tests
    def load_conf(self, conf, in_test=False):
        self.program_start = int(time.time())
        self.conf = conf
        self.hostgroups = conf.hostgroups
        self.services = conf.services
        # We need reversed list for search in the retention
        # file read
        self.services.optimize_service_search(conf.hosts)
        self.hosts = conf.hosts

        self.notificationways = conf.notificationways
        self.checkmodulations = conf.checkmodulations
        self.macromodulations = conf.macromodulations
        self.contacts = conf.contacts
        self.contactgroups = conf.contactgroups
        self.servicegroups = conf.servicegroups
        self.timeperiods = conf.timeperiods
        self.commands = conf.commands
        self.triggers = conf.triggers
        self.triggers.compile()
        self.triggers.load_objects(self)


        if not in_test:
            # Commands in the host/services/contacts are not real one
            # we must relink them
            t0 = time.time()
            self.conf.late_linkify()
            logger.debug("Late command relink in %d", time.time() - t0)

        # self.status_file = StatusFile(self)
        #  External status file
        # From Arbiter. Use for Broker to differentiate schedulers
        self.instance_id = conf.instance_id
        # Tag our hosts with our instance_id
        for h in self.hosts:
            h.instance_id = conf.instance_id
        for s in self.services:
            s.instance_id = conf.instance_id
        # self for instance_name
        self.instance_name = conf.instance_name
        # and push flavor
        self.push_flavor = conf.push_flavor

        # Now we can update our 'ticks' for special calls
        # like the retention one, etc
        self.update_recurrent_works_tick('update_retention_file',
                                         self.conf.retention_update_interval * 60)
        self.update_recurrent_works_tick('clean_queues', self.conf.cleaning_queues_interval)


    # Update the 'tick' for a function call in our
    # recurrent work
    def update_recurrent_works_tick(self, f_name, new_tick):
        for i in self.recurrent_works:
            (name, f, old_tick) = self.recurrent_works[i]
            if name == f_name:
                logger.debug("Changing the tick to %d for the function %s", new_tick, name)
                self.recurrent_works[i] = (name, f, new_tick)


    # Load the pollers from our app master
    def load_satellites(self, pollers, reactionners):
        self.pollers = pollers
        self.reactionners = reactionners


    # Oh... Arbiter want us to die... To launch a new Scheduler
    # "Mais qu'a-t-il de plus que je n'ais pas?"
    # "But.. On which point it is better than me?"
    def die(self):
        self.must_run = False


    def dump_objects(self):
        d = tempfile.gettempdir()
        p = os.path.join(d, 'scheduler-obj-dump-%d' % time.time())
        logger.info('Opening the DUMP FILE %s', p)
        try:
            f = open(p, 'w')
            f.write('Scheduler DUMP at %d\n' % time.time())
            for c in self.checks.values():
                s = 'CHECK: %s:%s:%s:%s:%s:%s\n' % \
                    (c.id, c.status, c.t_to_go, c.poller_tag, c.command, c.worker)
                f.write(s)
            for a in self.actions.values():
                s = '%s: %s:%s:%s:%s:%s:%s\n' % \
                    (a.__class__.my_type.upper(), a.id, a.status,
                     a.t_to_go, a.reactionner_tag, a.command, a.worker)
                f.write(s)
            for b in self.broks.values():
                s = 'BROK: %s:%s\n' % (b.id, b.type)
                f.write(s)
            f.close()
        except Exception, exp:
            logger.error("Error in writing the dump file %s : %s", p, str(exp))


    def dump_config(self):
        d = tempfile.gettempdir()
        p = os.path.join(d, 'scheduler-conf-dump-%d' % time.time())
        logger.info('Opening the DUMP FILE %s', p)
        try:
            f = open(p, 'w')
            f.write('Scheduler config DUMP at %d\n' % time.time())
            self.conf.dump(f)
            f.close()
        except Exception, exp:
            logger.error("Error in writing the dump file %s : %s", p, str(exp))

    # Load the external command
    def load_external_command(self, e):
        self.external_command = e


    # We've got activity in the fifo, we get and run commands
    def run_external_commands(self, cmds):
        for command in cmds:
            self.run_external_command(command)


    def run_external_command(self, command):
        logger.debug("scheduler resolves command '%s'", command)
        ext_cmd = ExternalCommand(command)
        self.external_command.resolve_command(ext_cmd)


    # Add_Brok is a bit more complex than the others, because
    # on starting, the broks are put in a global queue : self.broks
    # then when the first broker connect, it will generate initial_broks
    # in it's own queue (so bname != None).
    # and when in "normal" run, we just need to put the brok to all queues
    def add_Brok(self, brok, bname=None):
        # For brok, we TAG brok with our instance_id
        brok.instance_id = self.instance_id
        # Maybe it's just for one broker
        if bname:
            broks = self.brokers[bname]['broks']
            broks[brok.id] = brok
        else:
            # If there are known brokers, give it to them
            if len(self.brokers) > 0:
                # Or maybe it's for all
                for bname in self.brokers:
                    broks = self.brokers[bname]['broks']
                    broks[brok.id] = brok
            else:  # no brokers? maybe at startup for logs
                # we will put in global queue, that the first broker
                # connection will get all
                self.broks[brok.id] = brok


    def add_Notification(self, notif):
        self.actions[notif.id] = notif
        # A notification ask for a brok
        if notif.contact is not None:
            b = notif.get_initial_status_brok()
            self.add(b)


    def add_Check(self, c):
        self.checks[c.id] = c
        # A new check means the host/service changes its next_check
        # need to be refreshed
        b = c.ref.get_next_schedule_brok()
        self.add(b)


    def add_EventHandler(self, action):
        # print "Add an event Handler", elt.id
        self.actions[action.id] = action


    def add_Downtime(self, dt):
        self.downtimes[dt.id] = dt
        if dt.extra_comment:
            self.add_Comment(dt.extra_comment)


    def add_ContactDowntime(self, contact_dt):
        self.contact_downtimes[contact_dt.id] = contact_dt


    def add_Comment(self, comment):
        self.comments[comment.id] = comment
        b = comment.ref.get_update_status_brok()
        self.add(b)


    # Ok one of our modules send us a command? just run it!
    def add_ExternalCommand(self, ext_cmd):
        self.external_command.resolve_command(ext_cmd)


    # Schedulers have some queues. We can simplify call by adding
    # elements into the proper queue just by looking at their type
    # Brok -> self.broks
    # Check -> self.checks
    # Notification -> self.actions
    # Downtime -> self.downtimes
    # ContactDowntime -> self.contact_downtimes
    def add(self, elt):
        f = self.__add_actions.get(elt.__class__, None)
        if f:
            # print("found action for %s: %s" % (elt.__class__.__name__, f.__name__))
            f(self, elt)

    __add_actions = {
        Check:              add_Check,
        Brok:               add_Brok,
        Notification:       add_Notification,
        EventHandler:       add_EventHandler,
        Downtime:           add_Downtime,
        ContactDowntime:    add_ContactDowntime,
        Comment:            add_Comment,
        ExternalCommand:    add_ExternalCommand,
    }


    # We call the function of modules that got the
    # hook function
    # TODO: find a way to merge this and the version in daemon.py
    def hook_point(self, hook_name):
        for inst in self.sched_daemon.modules_manager.instances:
            full_hook_name = 'hook_' + hook_name
            logger.debug("hook_point: %s: %s %s",
                         inst.get_name(), str(hasattr(inst, full_hook_name)), hook_name)

            if hasattr(inst, full_hook_name):
                f = getattr(inst, full_hook_name)
                try:
                    f(self)
                except Exception, exp:
                    logger.error("The instance %s raise an exception %s."
                                 "I disable it and set it to restart it later",
                                 inst.get_name(), str(exp))
                    output = cStringIO.StringIO()
                    traceback.print_exc(file=output)
                    logger.error("Exception trace follows: %s", output.getvalue())
                    output.close()
                    self.sched_daemon.modules_manager.set_to_restart(inst)


    # Ours queues may explode if no one ask us for elements
    # It's very dangerous: you can crash your server... and it's a bad thing :)
    # So we 'just' keep last elements: 5 of max is a good overhead
    def clean_queues(self):
        # if we set the interval at 0, we bail out
        if self.conf.cleaning_queues_interval == 0:
            return

        max_checks = 5 * (len(self.hosts) + len(self.services))
        max_broks = 5 * (len(self.hosts) + len(self.services))
        max_actions = 5 * len(self.contacts) * (len(self.hosts) + len(self.services))

        # For checks, it's not very simple:
        # For checks, they may be referred to their host/service
        # We do not just del them in the check list, but also in their service/host
        # We want id of lower than max_id - 2*max_checks
        if len(self.checks) > max_checks:
            # keys does not ensure sorted keys. Max is slow but we have no other way.
            id_max = max(self.checks.keys())
            to_del_checks = [c for c in self.checks.values() if c.id < id_max - max_checks]
            nb_checks_drops = len(to_del_checks)
            if nb_checks_drops > 0:
                logger.info("I have to del some checks (%d)..., sorry", nb_checks_drops)
            for c in to_del_checks:
                i = c.id
                elt = c.ref
                # First remove the link in host/service
                elt.remove_in_progress_check(c)
                # Then in dependent checks (I depend on, or check
                # depend on me)
                for dependent_checks in c.depend_on_me:
                    dependent_checks.depend_on.remove(c.id)
                for c_temp in c.depend_on:
                    c_temp.depen_on_me.remove(c)
                del self.checks[i]  # Final Bye bye ...
        else:
            nb_checks_drops = 0

        # For broks and actions, it's more simple
        # or brosk, manage global but also all brokers queue
        b_lists = [self.broks]
        for (bname, e) in self.brokers.iteritems():
            b_lists.append(e['broks'])
        for broks in b_lists:
            if len(broks) > max_broks:
                id_max = max(broks.keys())
                id_to_del_broks = [i for i in broks if i < id_max - max_broks]
                nb_broks_drops = len(id_to_del_broks)
                for i in id_to_del_broks:
                    del broks[i]
            else:
                nb_broks_drops = 0

        if len(self.actions) > max_actions:
            id_max = max(self.actions.keys())
            id_to_del_actions = [i for i in self.actions if i < id_max - max_actions]
            nb_actions_drops = len(id_to_del_actions)
            for i in id_to_del_actions:
                # Remember to delete reference of notification in service/host
                a = self.actions[i]
                if a.is_a == 'notification':
                    a.ref.remove_in_progress_notification(a)
                del self.actions[i]
        else:
            nb_actions_drops = 0

        if nb_checks_drops != 0 or nb_broks_drops != 0 or nb_actions_drops != 0:
            logger.warning("We drop %d checks, %d broks and %d actions",
                           nb_checks_drops, nb_broks_drops, nb_actions_drops)


    # For tunning purpose we use caches but we do not want them to explode
    # So we clean them
    def clean_caches(self):
        for tp in self.timeperiods:
            tp.clean_cache()


    # Ask item (host or service) an update_status
    # and add it to our broks queue
    def get_and_register_status_brok(self, item):
        b = item.get_update_status_brok()
        self.add(b)


    # Ask item (host or service) a check_result_brok
    # and add it to our broks queue
    def get_and_register_check_result_brok(self, item):
        b = item.get_check_result_brok()
        self.add(b)


    # We do not want this downtime id
    def del_downtime(self, dt_id):
        if dt_id in self.downtimes:
            self.downtimes[dt_id].ref.del_downtime(dt_id)
            del self.downtimes[dt_id]


    # We do not want this downtime id
    def del_contact_downtime(self, dt_id):
        if dt_id in self.contact_downtimes:
            self.contact_downtimes[dt_id].ref.del_downtime(dt_id)
            del self.contact_downtimes[dt_id]


    # We do not want this comment id
    def del_comment(self, c_id):
        if c_id in self.comments:
            self.comments[c_id].ref.del_comment(c_id)
            del self.comments[c_id]


    # We are looking for outdated acks, and if so, remove them
    def check_for_expire_acknowledge(self):
        for elt in self.iter_hosts_and_services():
            elt.check_for_expire_acknowledge()


    # We update all business_impact to look at new modulation
    # start for impacts, and so update broks status and
    # problems value too
    def update_business_values(self):
        for elt in self.iter_hosts_and_services():
            if not elt.is_problem:
                was = elt.business_impact
                elt.update_business_impact_value()
                new = elt.business_impact
                # Ok, the business_impact change, we can update the broks
                if new != was:
                    # print "The elements", i.get_name(), "change it's business_impact value"
                    self.get_and_register_status_brok(elt)

        # When all impacts and classic elements are updated,
        # we can update problems (their value depend on impacts, so
        # they must be done after)
        for elt in self.iter_hosts_and_services():
            # We first update impacts and classic elements
            if elt.is_problem:
                was = elt.business_impact
                elt.update_business_impact_value()
                new = elt.business_impact
                # Maybe one of the impacts change it's business_impact to a high value
                # and so ask for the problem to raise too
                if new != was:
                    # print "The elements", i.get_name(),
                    # print "change it's business_impact value from", was, "to", new
                    self.get_and_register_status_brok(elt)


    # Each second we search for master notification that are scatterisable and we do the job
    # we take the sons and we put them into our actions queue
    def scatter_master_notifications(self):
        now = time.time()
        for a in self.actions.values():
            # We only want notifications
            if a.is_a != 'notification':
                continue
            if a.status == 'scheduled' and a.is_launchable(now):
                if not a.contact:
                    # This is a "master" notification created by create_notifications.
                    # It wont sent itself because it has no contact.
                    # We use it to create "child" notifications (for the contacts and
                    # notification_commands) which are executed in the reactionner.
                    item = a.ref
                    childnotifications = []
                    if not item.notification_is_blocked_by_item(a.type, now):
                        # If it is possible to send notifications
                        # of this type at the current time, then create
                        # a single notification for each contact of this item.
                        childnotifications = item.scatter_notification(a)
                        for c in childnotifications:
                            c.status = 'scheduled'
                            self.add(c)  # this will send a brok

                    # If we have notification_interval then schedule
                    # the next notification (problems only)
                    if a.type == 'PROBLEM':
                        # Update the ref notif number after raise the one of the notification
                        if len(childnotifications) != 0:
                            # notif_nb of the master notification
                            # was already current_notification_number+1.
                            # If notifications were sent,
                            # then host/service-counter will also be incremented
                            item.current_notification_number = a.notif_nb

                        if item.notification_interval != 0 and a.t_to_go is not None:
                            # We must continue to send notifications.
                            # Just leave it in the actions list and set it to "scheduled"
                            # and it will be found again later
                            # Ask the service/host to compute the next notif time. It can be just
                            # a.t_to_go + item.notification_interval*item.__class__.interval_length
                            # or maybe before because we have an
                            # escalation that need to raise up before
                            a.t_to_go = item.get_next_notification_time(a)

                            a.notif_nb = item.current_notification_number + 1
                            a.status = 'scheduled'
                        else:
                            # Wipe out this master notification. One problem notification is enough.
                            item.remove_in_progress_notification(a)
                            self.actions[a.id].status = 'zombie'

                    else:
                        # Wipe out this master notification.
                        # We don't repeat recover/downtime/flap/etc...
                        item.remove_in_progress_notification(a)
                        self.actions[a.id].status = 'zombie'


    # Called by poller to get checks
    # Can get checks and actions (notifications and co)
    def get_to_run_checks(self, do_checks=False, do_actions=False,
                          poller_tags=['None'], reactionner_tags=['None'],
                          worker_name='none', module_types=['fork']
                          ):
        res = []
        now = time.time()

        # If poller want to do checks
        if do_checks:
            for c in self.checks.values():
                #  If the command is untagged, and the poller too, or if both are tagged
                #  with same name, go for it
                # if do_check, call for poller, and so poller_tags by default is ['None']
                # by default poller_tag is 'None' and poller_tags is ['None']
                # and same for module_type, the default is the 'fork' type
                if c.poller_tag in poller_tags and c.module_type in module_types:
                    # must be ok to launch, and not an internal one (business rules based)
                    if c.status == 'scheduled' and c.is_launchable(now) and not c.internal:
                        c.status = 'inpoller'
                        c.worker = worker_name
                        # We do not send c, because it is a link (c.ref) to
                        # host/service and poller do not need it. It only
                        # need a shell with id, command and defaults
                        # parameters. It's the goal of copy_shell
                        res.append(c.copy_shell())

        # If reactionner want to notify too
        if do_actions:
            for a in self.actions.values():
                is_master = (a.is_a == 'notification' and not a.contact)

                if not is_master:
                    # if do_action, call the reactionner,
                    # and so reactionner_tags by default is ['None']
                    # by default reactionner_tag is 'None' and reactionner_tags is ['None'] too
                    # So if not the good one, loop for next :)
                    if a.reactionner_tag not in reactionner_tags:
                        continue

                    # same for module_type
                    if a.module_type not in module_types:
                        continue

                # And now look for can launch or not :)
                if a.status == 'scheduled' and a.is_launchable(now):
                    if not is_master:
                        # This is for child notifications and eventhandlers
                        a.status = 'inpoller'
                        a.worker = worker_name
                        new_a = a.copy_shell()
                        res.append(new_a)
        return res


    # Called by poller and reactionner to send result
    def put_results(self, c):
        if c.is_a == 'notification':
            # We will only see childnotifications here
            try:
                timeout = False
                if c.status == 'timeout':
                    # Unfortunately the remove_in_progress_notification
                    # sets the status to zombie, so we need to save it here.
                    timeout = True
                    execution_time = c.execution_time

                # Add protection for strange charset
                if isinstance(c.output, str):
                    c.output = c.output.decode('utf8', 'ignore')

                self.actions[c.id].get_return_from(c)
                item = self.actions[c.id].ref
                item.remove_in_progress_notification(c)
                self.actions[c.id].status = 'zombie'
                item.last_notification = c.check_time

                # And we ask the item to update it's state
                self.get_and_register_status_brok(item)

                # If we' ve got a problem with the notification, raise a Warning log
                if timeout:
                    logger.warning("Contact %s %s notification command '%s ' "
                                   "timed out after %d seconds",
                                   self.actions[c.id].contact.contact_name,
                                   self.actions[c.id].ref.__class__.my_type,
                                   self.actions[c.id].command,
                                   int(execution_time))
                elif c.exit_status != 0:
                    logger.warning("The notification command '%s' raised an error "
                                   "(exit code=%d): '%s'", c.command, c.exit_status, c.output)

            except KeyError, exp:  # bad number for notif, not that bad
                logger.warning('put_results:: get unknown notification : %s ', str(exp))

            except AttributeError, exp:  # bad object, drop it
                logger.warning('put_results:: get bad notification : %s ', str(exp))
        elif c.is_a == 'check':
            try:
                if c.status == 'timeout':
                    c.output = "(%s Check Timed Out)" %\
                               self.checks[c.id].ref.__class__.my_type.capitalize()
                    c.long_output = c.output
                    c.exit_status = self.conf.timeout_exit_status
                self.checks[c.id].get_return_from(c)
                self.checks[c.id].status = 'waitconsume'
            except KeyError, exp:
                pass


        elif c.is_a == 'eventhandler':
            try:
                old_action = self.actions[c.id]
                old_action.status = 'zombie'
            except KeyError:  # cannot find old action
                return
            if c.status == 'timeout':
                _type = 'event handler'
                if c.is_snapshot:
                    _type = 'snapshot'
                logger.warning("%s %s command '%s ' timed out after %d seconds" %
                               (self.actions[c.id].ref.__class__.my_type.capitalize(),
                                _type,
                                self.actions[c.id].command,
                                int(c.execution_time)))

            # If it's a snapshot we should get the output an export it
            if c.is_snapshot:
                old_action.get_return_from(c)
                b = old_action.ref.get_snapshot_brok(old_action.output, old_action.exit_status)
                self.add(b)
        else:
            logger.error("The received result type in unknown! %s", str(c.is_a))


    # Get the good tabs for links regarding to the kind. If unknown, return None
    def get_links_from_type(self, type):
        t = {'poller': self.pollers, 'reactionner': self.reactionners}
        if type in t:
            return t[type]
        return None


    # Check if we do not connect to often to this
    def is_connection_try_too_close(self, elt):
        now = time.time()
        last_connection = elt['last_connection']
        if now - last_connection < 5:
            return True
        return False


    # initialize or re-initialize connection with a poller
    # or a reactionner
    def pynag_con_init(self, id, type='poller'):
        # Get good links tab for looping..
        links = self.get_links_from_type(type)
        if links is None:
            logger.debug("Unknown '%s' type for connection!", type)
            return

        # We want only to initiate connections to the passive
        # pollers and reactionners
        passive = links[id]['passive']
        if not passive:
            return

        # If we try to connect too much, we slow down our tests
        if self.is_connection_try_too_close(links[id]):
            return

        # Ok, we can now update it
        links[id]['last_connection'] = time.time()

        logger.debug("Init connection with %s", links[id]['uri'])

        uri = links[id]['uri']
        try:
            links[id]['con'] = HTTPClient(uri=uri, strong_ssl=links[id]['hard_ssl_name_check'])
            con = links[id]['con']
        except HTTPExceptions, exp:
            logger.warning("Connection problem to the %s %s: %s", type, links[id]['name'], str(exp))
            links[id]['con'] = None
            return

        try:
            # initial ping must be quick
            con.get('ping')
        except HTTPExceptions, exp:
            logger.warning("Connection problem to the %s %s: %s", type, links[id]['name'], str(exp))
            links[id]['con'] = None
            return
        except KeyError, exp:
            logger.warning("The %s '%s' is not initialized: %s", type, links[id]['name'], str(exp))
            links[id]['con'] = None
            return

        logger.info("Connection OK to the %s %s", type, links[id]['name'])


    # We should push actions to our passives satellites
    def push_actions_to_passives_satellites(self):
        # We loop for our passive pollers or reactionners
        for p in filter(lambda p: p['passive'], self.pollers.values()):
            logger.debug("I will send actions to the poller %s", str(p))
            con = p['con']
            poller_tags = p['poller_tags']
            if con is not None:
                # get actions
                lst = self.get_to_run_checks(True, False, poller_tags, worker_name=p['name'])
                try:
                    # initial ping must be quick
                    logger.debug("Sending %s actions", len(lst))
                    con.post('push_actions', {'actions': lst, 'sched_id': self.instance_id})
                    self.nb_checks_send += len(lst)
                except HTTPExceptions, exp:
                    logger.warning("Connection problem to the %s %s: %s", type, p['name'], str(exp))
                    p['con'] = None
                    return
                except KeyError, exp:
                    logger.warning("The %s '%s' is not initialized: %s", type, p['name'], str(exp))
                    p['con'] = None
                    return
            else:  # no connection? try to reconnect
                self.pynag_con_init(p['instance_id'], type='poller')

        # TODO:factorize
        # We loop for our passive reactionners
        for p in filter(lambda p: p['passive'], self.reactionners.values()):
            logger.debug("I will send actions to the reactionner %s", str(p))
            con = p['con']
            reactionner_tags = p['reactionner_tags']
            if con is not None:
                # get actions
                lst = self.get_to_run_checks(False, True,
                                             reactionner_tags=reactionner_tags,
                                             worker_name=p['name'])
                try:
                    # initial ping must be quick
                    logger.debug("Sending %d actions", len(lst))
                    con.post('push_actions', {'actions': lst, 'sched_id': self.instance_id})
                    self.nb_checks_send += len(lst)
                except HTTPExceptions, exp:
                    logger.warning("Connection problem to the %s %s: %s", type, p['name'], str(exp))
                    p['con'] = None
                    return
                except KeyError, exp:
                    logger.warning("The %s '%s' is not initialized: %s", type, p['name'], str(exp))
                    p['con'] = None
                    return
            else:  # no connection? try to reconnect
                self.pynag_con_init(p['instance_id'], type='reactionner')


    # We should get returns from satellites
    def get_actions_from_passives_satellites(self):
        # We loop for our passive pollers
        for p in [p for p in self.pollers.values() if p['passive']]:
            logger.debug("I will get actions from the poller %s", str(p))
            con = p['con']
            poller_tags = p['poller_tags']
            if con is not None:
                try:
                    # initial ping must be quick
                    # Before ask a call that can be long, do a simple ping to be sure it is alive
                    con.get('ping')
                    results = con.get('get_returns', {'sched_id': self.instance_id}, wait='long')
                    try:
                        results = str(results)
                    except UnicodeEncodeError:  # ascii not working, switch to utf8 so
                        # if not eally utf8 will be a real problem
                        results = results.encode("utf8", 'ignore')
                        # and data will be invalid, socatch by the pickle.

                    # now go the cpickle pass, and catch possible errors from it
                    try:
                        results = cPickle.loads(results)
                    except Exception, exp:
                        logger.error('Cannot load passive results from satellite %s : %s',
                                     p['name'], str(exp))
                        continue

                    nb_received = len(results)
                    self.nb_check_received += nb_received
                    logger.debug("Received %d passive results", nb_received)
                    for result in results:
                        result.set_type_passive()
                    with self.waiting_results_lock:
                        self.waiting_results.extend(results)
                except HTTPExceptions, exp:
                    logger.warning("Connection problem to the %s %s: %s", type, p['name'], str(exp))
                    p['con'] = None
                    continue
                except KeyError, exp:
                    logger.warning("The %s '%s' is not initialized: %s", type, p['name'], str(exp))
                    p['con'] = None
                    continue
            else:  # no connection, try reinit
                self.pynag_con_init(p['instance_id'], type='poller')

        # We loop for our passive reactionners
        for p in [p for p in self.reactionners.values() if p['passive']]:
            logger.debug("I will get actions from the reactionner %s", str(p))
            con = p['con']
            reactionner_tags = p['reactionner_tags']
            if con is not None:
                try:
                    # initial ping must be quick
                    # Before ask a call that can be long, do a simple ping to be sure it is alive
                    con.get('ping')
                    results = con.get('get_returns', {'sched_id': self.instance_id}, wait='long')
                    results = cPickle.loads(str(results))
                    nb_received = len(results)
                    self.nb_check_received += nb_received
                    logger.debug("Received %d passive results", nb_received)
                    for result in results:
                        result.set_type_passive()
                    with self.waiting_results_lock:
                        self.waiting_results.extend(results)
                except HTTPExceptions, exp:
                    logger.warning("Connection problem to the %s %s: %s", type, p['name'], str(exp))
                    p['con'] = None
                    return
                except KeyError, exp:
                    logger.warning("The %s '%s' is not initialized: %s", type, p['name'], str(exp))
                    p['con'] = None
                    return
            else:  # no connection, try reinit
                self.pynag_con_init(p['instance_id'], type='reactionner')


    # Some checks are purely internal, like business based one
    # simply ask their ref to manage it when it's ok to run
    def manage_internal_checks(self):
        now = time.time()
        for c in self.checks.values():
            # must be ok to launch, and not an internal one (business rules based)
            if c.internal and c.status == 'scheduled' and c.is_launchable(now):
                c.ref.manage_internal_check(self.hosts, self.services, c)
                # it manage it, now just ask to consume it
                # like for all checks
                c.status = 'waitconsume'


    # Call by brokers to have broks
    # We give them, and clean them!
    def get_broks(self, bname):
        # If we are here, we are sure the broker entry exists
        res = self.brokers[bname]['broks']
        # They are gone, we keep none!
        self.brokers[bname]['broks'] = {}

        # Also put in the result the possible first log broks if so
        res.update(self.broks)
        # and clean the global broks too now
        self.broks.clear()

        return res


    # An element can have its topology changed by an external command
    # if so a brok will be generated with this flag. No need to reset all of
    # them.
    def reset_topology_change_flag(self):
        for i in self.hosts:
            i.topology_change = False
        for i in self.services:
            i.topology_change = False


    # Update the retention file and give all te data in
    # a dict so the read function can pickup what it wants
    # For now compression is not used, but it can be added easily
    # just uncomment :)
    def update_retention_file(self, forced=False):
        # If we set the update to 0, we do not want of this
        # if we do not forced (like at stopping)
        if self.conf.retention_update_interval == 0 and not forced:
            return

        self.hook_point('save_retention')


    # Load the retention file and get status from it. It does not get all checks in progress
    # for the moment, just the status and the notifications.
    def retention_load(self):
        self.hook_point('load_retention')


    # Helper function for module, will give the host and service
    # data
    def get_retention_data(self):
        # We create an all_data dict with list of useful retention data dicts
        # of our hosts and services
        all_data = {'hosts': {}, 'services': {}}
        for h in self.hosts:
            d = {}
            running_properties = h.__class__.running_properties
            for prop, entry in running_properties.items():
                if entry.retention:
                    v = getattr(h, prop)
                    # Maybe we should "prepare" the data before saving it
                    # like get only names instead of the whole objects
                    f = entry.retention_preparation
                    if f:
                        v = f(h, v)
                    d[prop] = v
            # and some properties are also like this, like
            # active checks enabled or not
            properties = h.__class__.properties
            for prop, entry in properties.items():
                if entry.retention:
                    v = getattr(h, prop)
                    # Maybe we should "prepare" the data before saving it
                    # like get only names instead of the whole objects
                    f = entry.retention_preparation
                    if f:
                        v = f(h, v)
                    d[prop] = v
            all_data['hosts'][h.host_name] = d

        # Same for services
        for s in self.services:
            d = {}
            running_properties = s.__class__.running_properties
            for prop, entry in running_properties.items():
                if entry.retention:
                    v = getattr(s, prop)
                    # Maybe we should "prepare" the data before saving it
                    # like get only names instead of the whole objects
                    f = entry.retention_preparation
                    if f:
                        v = f(s, v)
                    d[prop] = v

            # We consider the service ONLY if it has modified attributes.
            # If not, then no non-running attributes will be saved for this service.
            if s.modified_attributes > 0:
                # Same for properties, like active checks enabled or not
                properties = s.__class__.properties

                for prop, entry in properties.items():
                    # We save the value only if the attribute
                    # is selected for retention AND has been modified.
                    if entry.retention and \
                            not (prop in DICT_MODATTR and
                                 not DICT_MODATTR[prop].value & s.modified_attributes):
                        v = getattr(s, prop)
                        # Maybe we should "prepare" the data before saving it
                        # like get only names instead of the whole objects
                        f = entry.retention_preparation
                        if f:
                            v = f(s, v)
                        d[prop] = v
            all_data['services'][(s.host.host_name, s.service_description)] = d
        return all_data


    # Get back our broks from a retention module :)
    def restore_retention_data(self, data):
        # Now load interesting properties in hosts/services
        # Tagging retention=False prop that not be directly load
        # Items will be with theirs status, but not in checking, so
        # a new check will be launched like with a normal beginning (random distributed
        # scheduling)

        ret_hosts = data['hosts']
        for ret_h_name in ret_hosts:
            # We take the dict of our value to load
            d = data['hosts'][ret_h_name]
            h = self.hosts.find_by_name(ret_h_name)
            if h is not None:
                # First manage all running properties
                running_properties = h.__class__.running_properties
                for prop, entry in running_properties.items():
                    if entry.retention:
                        # Maybe the saved one was not with this value, so
                        # we just bypass this
                        if prop in d:
                            setattr(h, prop, d[prop])
                # Ok, some are in properties too (like active check enabled
                # or not. Will OVERRIDE THE CONFIGURATION VALUE!
                properties = h.__class__.properties
                for prop, entry in properties.items():
                    if entry.retention:
                        # Maybe the saved one was not with this value, so
                        # we just bypass this
                        if prop in d:
                            setattr(h, prop, d[prop])
                # Now manage all linked objects load from previous run
                for a in h.notifications_in_progress.values():
                    a.ref = h
                    self.add(a)
                    # Also raises the action id, so do not overlap ids
                    a.assume_at_least_id(a.id)
                h.update_in_checking()
                # And also add downtimes and comments
                for dt in h.downtimes:
                    dt.ref = h
                    if hasattr(dt, 'extra_comment'):
                        dt.extra_comment.ref = h
                    else:
                        dt.extra_comment = None
                    # raises the downtime id to do not overlap
                    Downtime.id = max(Downtime.id, dt.id + 1)
                    self.add(dt)
                for c in h.comments:
                    c.ref = h
                    self.add(c)
                    # raises comment id to do not overlap ids
                    Comment.id = max(Comment.id, c.id + 1)
                if h.acknowledgement is not None:
                    h.acknowledgement.ref = h
                    # Raises the id of future ack so we don't overwrite
                    # these one
                    Acknowledge.id = max(Acknowledge.id, h.acknowledgement.id + 1)
                # Relink the notified_contacts as a set() of true contacts objects
                # it it was load from the retention, it's now a list of contacts
                # names
                if 'notified_contacts' in d:
                    new_notified_contacts = set()
                    for cname in h.notified_contacts:
                        c = self.contacts.find_by_name(cname)
                        # Maybe the contact is gone. Skip it
                        if c:
                            new_notified_contacts.add(c)
                    h.notified_contacts = new_notified_contacts

        # SAme for services
        ret_services = data['services']
        for (ret_s_h_name, ret_s_desc) in ret_services:
            # We take our dict to load
            d = data['services'][(ret_s_h_name, ret_s_desc)]
            s = self.services.find_srv_by_name_and_hostname(ret_s_h_name, ret_s_desc)

            if s is not None:
                # Load the major values from running properties
                running_properties = s.__class__.running_properties
                for prop, entry in running_properties.items():
                    if entry.retention:
                        # Maybe the saved one was not with this value, so
                        # we just bypass this
                        if prop in d:
                            setattr(s, prop, d[prop])
                # And some others from properties dict too
                properties = s.__class__.properties
                for prop, entry in properties.items():
                    if entry.retention:
                        # Maybe the saved one was not with this value, so
                        # we just bypass this
                        if prop in d:
                            setattr(s, prop, d[prop])
                # Ok now manage all linked objects
                for a in s.notifications_in_progress.values():
                    a.ref = s
                    self.add(a)
                    # Also raises the action id, so do not overlap id
                    a.assume_at_least_id(a.id)
                s.update_in_checking()
                # And also add downtimes and comments
                for dt in s.downtimes:
                    dt.ref = s
                    if hasattr(dt, 'extra_comment'):
                        dt.extra_comment.ref = s
                    else:
                        dt.extra_comment = None
                    # raises the downtime id to do not overlap
                    Downtime.id = max(Downtime.id, dt.id + 1)
                    self.add(dt)
                for c in s.comments:
                    c.ref = s
                    self.add(c)
                    # raises comment id to do not overlap ids
                    Comment.id = max(Comment.id, c.id + 1)
                if s.acknowledgement is not None:
                    s.acknowledgement.ref = s
                    # Raises the id of future ack so we don't overwrite
                    # these one
                    Acknowledge.id = max(Acknowledge.id, s.acknowledgement.id + 1)
                # Relink the notified_contacts as a set() of true contacts objects
                # it it was load from the retention, it's now a list of contacts
                # names
                if 'notified_contacts' in d:
                    new_notified_contacts = set()
                    for cname in s.notified_contacts:
                        c = self.contacts.find_by_name(cname)
                        # Maybe the contact is gone. Skip it
                        if c:
                            new_notified_contacts.add(c)
                    s.notified_contacts = new_notified_contacts


    # Fill the self.broks with broks of self (process id, and co)
    # broks of service and hosts (initial status)
    def fill_initial_broks(self, bname, with_logs=False):
        # First a Brok for delete all from my instance_id
        b = Brok('clean_all_my_instance_id', {'instance_id': self.instance_id})
        self.add_Brok(b, bname)

        # first the program status
        b = self.get_program_status_brok()
        self.add_Brok(b, bname)

        #  We can't call initial_status from all this types
        #  The order is important, service need host...
        initial_status_types = (self.timeperiods, self.commands,
                                self.contacts, self.contactgroups,
                                self.hosts, self.hostgroups,
                                self.services, self.servicegroups)

        self.conf.skip_initial_broks = getattr(self.conf, 'skip_initial_broks', False)
        logger.debug("Skipping initial broks? %s", str(self.conf.skip_initial_broks))
        if not self.conf.skip_initial_broks:
            for tab in initial_status_types:
                for i in tab:
                    b = i.get_initial_status_brok()
                    self.add_Brok(b, bname)

        # Only raises the all logs at the scheduler startup
        if with_logs:
            # Ask for INITIAL logs for services and hosts
            for i in self.hosts:
                i.raise_initial_state()
            for i in self.services:
                i.raise_initial_state()

        # Add a brok to say that we finished all initial_pass
        b = Brok('initial_broks_done', {'instance_id': self.instance_id})
        self.add_Brok(b, bname)

        # We now have all full broks
        self.has_full_broks = True

        logger.info("[%s] Created %d initial Broks for broker %s",
                    self.instance_name, len(self.brokers[bname]['broks']), bname)


    # Crate a brok with program status info
    def get_and_register_program_status_brok(self):
        b = self.get_program_status_brok()
        self.add(b)


    # Crate a brok with program status info
    def get_and_register_update_program_status_brok(self):
        b = self.get_program_status_brok()
        b.type = 'update_program_status'
        self.add(b)


    # Get a brok with program status
    # TODO: GET REAL VALUES
    def get_program_status_brok(self):
        now = int(time.time())
        data = {"is_running": 1,
                "instance_id": self.instance_id,
                "instance_name": self.instance_name,
                "last_alive": now,
                "interval_length": self.conf.interval_length,
                "program_start": self.program_start,
                "pid": os.getpid(),
                "daemon_mode": 1,
                "last_command_check": now,
                "last_log_rotation": now,
                "notifications_enabled": self.conf.enable_notifications,
                "active_service_checks_enabled": self.conf.execute_service_checks,
                "passive_service_checks_enabled": self.conf.accept_passive_service_checks,
                "active_host_checks_enabled": self.conf.execute_host_checks,
                "passive_host_checks_enabled": self.conf.accept_passive_host_checks,
                "event_handlers_enabled": self.conf.enable_event_handlers,
                "flap_detection_enabled": self.conf.enable_flap_detection,
                "failure_prediction_enabled": 0,
                "process_performance_data": self.conf.process_performance_data,
                "obsess_over_hosts": self.conf.obsess_over_hosts,
                "obsess_over_services": self.conf.obsess_over_services,
                "modified_host_attributes": 0,
                "modified_service_attributes": 0,
                "global_host_event_handler": self.conf.global_host_event_handler,
                'global_service_event_handler': self.conf.global_service_event_handler,
                'check_external_commands': self.conf.check_external_commands,
                'check_service_freshness': self.conf.check_service_freshness,
                'check_host_freshness': self.conf.check_host_freshness,
                'command_file': self.conf.command_file
                }
        b = Brok('program_status', data)
        return b


    # Called every 1sec to consume every result in services or hosts
    # with these results, they are OK, CRITICAL, UP/DOWN, etc...
    def consume_results(self):
        # All results are in self.waiting_results
        # We need to get them first
        with self.waiting_results_lock:
            waiting_results = self.waiting_results
            self.waiting_results = []

        for c in waiting_results:
            self.put_results(c)

        # Then we consume them
        # print "**********Consume*********"
        for c in self.checks.values():
            if c.status == 'waitconsume':
                item = c.ref
                item.consume_result(c)


        # All 'finished' checks (no more dep) raise checks they depends on
        for c in self.checks.values():
            if c.status == 'havetoresolvedep':
                for dependent_checks in c.depend_on_me:
                    # Ok, now dependent will no more wait c
                    dependent_checks.depend_on.remove(c.id)
                # REMOVE OLD DEP CHECK -> zombie
                c.status = 'zombie'

        # Now, reinteger dep checks
        for c in self.checks.values():
            if c.status == 'waitdep' and len(c.depend_on) == 0:
                item = c.ref
                item.consume_result(c)


    # Called every 1sec to delete all checks in a zombie state
    # zombie = not useful anymore
    def delete_zombie_checks(self):
        # print "**********Delete zombies checks****"
        id_to_del = []
        for c in self.checks.values():
            if c.status == 'zombie':
                id_to_del.append(c.id)
        # une petite tape dans le dos et tu t'en vas, merci...
        # *pat pat* GFTO, thks :)
        for id in id_to_del:
            del self.checks[id]  # ZANKUSEN!


    # Called every 1sec to delete all actions in a zombie state
    # zombie = not useful anymore
    def delete_zombie_actions(self):
        # print "**********Delete zombies actions****"
        id_to_del = []
        for a in self.actions.values():
            if a.status == 'zombie':
                id_to_del.append(a.id)
        # une petite tape dans le dos et tu t'en vas, merci...
        # *pat pat* GFTO, thks :)
        for id in id_to_del:
            del self.actions[id]  # ZANKUSEN!

    # Check for downtimes start and stop, and register
    # them if needed
    def update_downtimes_and_comments(self):
        broks = []
        now = time.time()

        # Look for in objects comments, and look if we already got them
        for elt in self.iter_hosts_and_services():
            for c in elt.comments:
                if c.id not in self.comments:
                    self.comments[c.id] = c

        # Check maintenance periods
        for elt in self.iter_hosts_and_services():
            if elt.maintenance_period is None:
                continue

            if elt.in_maintenance is None:
                if elt.maintenance_period.is_time_valid(now):
                    start_dt = elt.maintenance_period.get_next_valid_time_from_t(now)
                    end_dt = elt.maintenance_period.get_next_invalid_time_from_t(start_dt + 1) - 1
                    dt = Downtime(elt, start_dt, end_dt, 1, 0, 0,
                                  "system",
                                  "this downtime was automatically scheduled"
                                  "through a maintenance_period")
                    elt.add_downtime(dt)
                    self.add(dt)
                    self.get_and_register_status_brok(elt)
                    elt.in_maintenance = dt.id
            else:
                if elt.in_maintenance not in self.downtimes:
                    # the main downtimes has expired or was manually deleted
                    elt.in_maintenance = None

        #  Check the validity of contact downtimes
        for elt in self.contacts:
            for dt in elt.downtimes:
                dt.check_activation()

        # A loop where those downtimes are removed
        # which were marked for deletion (mostly by dt.exit())
        for dt in self.downtimes.values():
            if dt.can_be_deleted is True:
                ref = dt.ref
                self.del_downtime(dt.id)
                broks.append(ref.get_update_status_brok())

        # Same for contact downtimes:
        for dt in self.contact_downtimes.values():
            if dt.can_be_deleted is True:
                ref = dt.ref
                self.del_contact_downtime(dt.id)
                broks.append(ref.get_update_status_brok())

        # Downtimes are usually accompanied by a comment.
        # An exiting downtime also invalidates it's comment.
        for c in self.comments.values():
            if c.can_be_deleted is True:
                ref = c.ref
                self.del_comment(c.id)
                broks.append(ref.get_update_status_brok())

        # Check start and stop times
        for dt in self.downtimes.values():
            if dt.real_end_time < now:
                # this one has expired
                broks.extend(dt.exit())  # returns downtimestop notifications
            elif now >= dt.start_time and dt.fixed and not dt.is_in_effect:
                # this one has to start now
                broks.extend(dt.enter())  # returns downtimestart notifications
                broks.append(dt.ref.get_update_status_brok())

        for b in broks:
            self.add(b)


    # Main schedule function to make the regular scheduling
    def schedule(self):
        # ask for service and hosts their next check
        for elt in self.iter_hosts_and_services():
            elt.schedule()

    # Main actions reaper function: it get all new checks,
    # notification and event handler from hosts and services
    def get_new_actions(self):
        self.hook_point('get_new_actions')
        # ask for service and hosts their next check
        for elt in self.iter_hosts_and_services():
            for a in elt.actions:
                self.add(a)
            # We take all, we can clear it
            elt.actions = []


    # Similar as above, but for broks
    def get_new_broks(self):
        # ask for service and hosts their broks waiting
        # be eaten
        for elt in self.iter_hosts_and_services():
            for b in elt.broks:
                self.add(b)
            # We take all, we can clear it
            elt.broks = []


    # Raises checks for no fresh states for services and hosts
    def check_freshness(self):
        # print "********** Check freshness******"
        for elt in self.iter_hosts_and_services():
            c = elt.do_check_freshness()
            if c is not None:
                self.add(c)


    # Check for orphaned checks: checks that never returns back
    # so if inpoller and t_to_go < now - 300s: pb!
    # Warn only one time for each "worker"
    # XXX I think we should make "time_to_orphanage" configurable
    #     each action type, each for notification, event_handler & check
    #     I think it will be a little more useful that way, not sure tho
    def check_orphaned(self):
        worker_names = {}
        now = int(time.time())
        for c in self.checks.values():
            time_to_orphanage = c.ref.get_time_to_orphanage()
            if time_to_orphanage:
                if c.status == 'inpoller' and c.t_to_go < now - time_to_orphanage:
                    c.status = 'scheduled'
                    if c.worker not in worker_names:
                        worker_names[c.worker] = 1
                        continue
                    worker_names[c.worker] += 1
        for a in self.actions.values():
            time_to_orphanage = a.ref.get_time_to_orphanage()
            if time_to_orphanage:
                if a.status == 'inpoller' and a.t_to_go < now - time_to_orphanage:
                    a.status = 'scheduled'
                    if a.worker not in worker_names:
                        worker_names[a.worker] = 1
                        continue
                    worker_names[a.worker] += 1

        for w in worker_names:
            logger.warning("%d actions never came back for the satellite '%s'."
                           "I reenable them for polling", worker_names[w], w)


    # Each loop we are going to send our broks to our modules (if need)
    def send_broks_to_modules(self):
        t0 = time.time()
        nb_sent = 0
        for mod in self.sched_daemon.modules_manager.get_external_instances():
            logger.debug("Look for sending to module %s", mod.get_name())
            q = mod.to_q
            to_send = [b for b in self.broks.values()
                       if not getattr(b, 'sent_to_sched_externals', False) and mod.want_brok(b)]
            q.put(to_send)
            nb_sent += len(to_send)

        # No more need to send them
        for b in self.broks.values():
            b.sent_to_sched_externals = True
        logger.debug("Time to send %s broks (after %d secs)", nb_sent, time.time() - t0)


    # special one for scheduler ; see Daemon.get_objects_from_from_queues()
    def get_objects_from_from_queues(self):
        ''' Same behavior than Daemon.get_objects_from_from_queues(). '''
        return self.sched_daemon.get_objects_from_from_queues()


    # stats threads is asking us a main structure for stats
    def get_stats_struct(self):
        now = int(time.time())

        res = self.sched_daemon.get_stats_struct()
        res.update({'name': self.instance_name, 'type': 'scheduler'})

        # Get a overview of the latencies with just
        # a 95 percentile view, but lso min/max values
        latencies = [s.latency for s in self.services]
        lat_avg, lat_min, lat_max = nighty_five_percent(latencies)
        res['latency'] = (0.0, 0.0, 0.0)
        if lat_avg:
            res['latency'] = {'avg': lat_avg, 'min': lat_min, 'max': lat_max}

        res['hosts'] = len(self.hosts)
        res['services'] = len(self.services)
        # metrics specific
        metrics = res['metrics']
        metrics.append('scheduler.%s.checks.scheduled %d %d' %
                       (self.instance_name,
                        len([c for c in self.checks.values() if c.status == 'scheduled']), now))
        metrics.append('scheduler.%s.checks.inpoller %d %d' %
                       (self.instance_name,
                        len([c for c in self.checks.values() if c.status == 'scheduled']), now))
        metrics.append('scheduler.%s.checks.zombie %d %d' %
                       (self.instance_name,
                        len([c for c in self.checks.values() if c.status == 'scheduled']), now))
        metrics.append('scheduler.%s.actions.queue %d %d' %
                       (self.instance_name,
                        len(self.actions), now))
        metrics.append('scheduler.%s.broks.queue %d %d' %
                       (self.instance_name, len(self.broks), now))
        metrics.append('scheduler.%s.downtimes %d %d' %
                       (self.instance_name, len(self.downtimes), now))
        metrics.append('scheduler.%s.comments %d %d' %
                       (self.instance_name, len(self.comments), now))
        if lat_min:
            metrics.append('scheduler.%s.latency.min %f %d' % (self.instance_name, lat_min, now))
            metrics.append('scheduler.%s.latency.avg %f %d' % (self.instance_name, lat_avg, now))
            metrics.append('scheduler.%s.latency.max %f %d' % (self.instance_name, lat_max, now))

        all_commands = {}
        # compute some stats
        for elt in self.iter_hosts_and_services():
            last_cmd = elt.last_check_command
            if not last_cmd:
                continue
            interval = elt.check_interval
            if interval == 0:
                interval = 1
            cmd = os.path.split(last_cmd.split(' ', 1)[0])[1]
            u_time = elt.u_time
            s_time = elt.s_time
            old_u_time, old_s_time = all_commands.get(cmd, (0.0, 0.0))
            old_u_time += u_time / interval
            old_s_time += s_time / interval
            all_commands[cmd] = (old_u_time, old_s_time)
        # now sort it
        p = []
        for (c, e) in all_commands.iteritems():
            u_time, s_time = e
            p.append({'cmd': c, 'u_time': u_time, 's_time': s_time})
        def p_sort(e1, e2):
            if e1['u_time'] > e2['u_time']:
                return 1
            if e1['u_time'] < e2['u_time']:
                return -1
            return 0
        p.sort(p_sort)
        # takethe first 10 ones for the put
        res['commands'] = p[:10]
        return res


    # Main function
    def run(self):
        # Then we see if we've got info in the retention file
        self.retention_load()

        # Finally start the external modules now we got our data
        self.hook_point('pre_scheduler_mod_start')
        self.sched_daemon.modules_manager.start_external_instances(late_start=True)

        # Ok, now all is initialized, we can make the initial broks
        logger.info("[%s] First scheduling launched", self.instance_name)
        self.schedule()
        logger.info("[%s] First scheduling done", self.instance_name)

        # Now connect to the passive satellites if needed
        for p_id in self.pollers:
            self.pynag_con_init(p_id, type='poller')

        for r_id in self.reactionners:
            self.pynag_con_init(r_id, type='reactionner')

        # Ticks are for recurrent function call like consume
        # del zombies etc
        ticks = 0
        timeout = 1.0  # For the select

        gogogo = time.time()

        # We must reset it if we received a new conf from the Arbiter.
        # Otherwise, the stat check average won't be correct
        self.nb_check_received = 0

        self.load_one_min = Load(initial_value=1)
        logger.debug("First loop at %d", time.time())
        while self.must_run:
            # print "Loop"
            # Before answer to brokers, we send our broks to modules
            # Ok, go to send our broks to our external modules
            # self.send_broks_to_modules()

            elapsed, _, _ = self.sched_daemon.handleRequests(timeout)
            if elapsed:
                timeout -= elapsed
                if timeout > 0:
                    continue

            self.load_one_min.update_load(self.sched_daemon.sleep_time)

            # load of the scheduler is the percert of time it is waiting
            l = min(100, 100.0 - self.load_one_min.get_load() * 100)
            logger.debug("Load: (sleep) %.2f (average: %.2f) -> %d%%",
                         self.sched_daemon.sleep_time, self.load_one_min.get_load(), l)

            self.sched_daemon.sleep_time = 0.0

            # Timeout or time over
            timeout = 1.0
            ticks += 1

            # Do recurrent works like schedule, consume
            # delete_zombie_checks
            for i in self.recurrent_works:
                (name, f, nb_ticks) = self.recurrent_works[i]
                # A 0 in the tick will just disable it
                if nb_ticks != 0:
                    if ticks % nb_ticks == 0:
                        # Call it and save the time spend in it
                        _t = time.time()
                        f()
                        statsmgr.incr('loop.%s' % name, time.time() - _t)

            # DBG: push actions to passives?
            self.push_actions_to_passives_satellites()
            self.get_actions_from_passives_satellites()

            # stats
            nb_scheduled = len([c for c in self.checks.values() if c.status == 'scheduled'])
            nb_inpoller = len([c for c in self.checks.values() if c.status == 'inpoller'])
            nb_zombies = len([c for c in self.checks.values() if c.status == 'zombie'])
            nb_notifications = len(self.actions)

            logger.debug("Checks: total %s, scheduled %s,"
                         "inpoller %s, zombies %s, notifications %s",
                         len(self.checks), nb_scheduled, nb_inpoller, nb_zombies, nb_notifications)

            # Get a overview of the latencies with just
            # a 95 percentile view, but lso min/max values
            latencies = [s.latency for s in self.services]
            lat_avg, lat_min, lat_max = nighty_five_percent(latencies)
            if lat_avg is not None:
                logger.debug("Latency (avg/min/max): %.2f/%.2f/%.2f", lat_avg, lat_min, lat_max)

            # print "Notifications:", nb_notifications
            now = time.time()

            if self.nb_checks_send != 0:
                logger.debug("Nb checks/notifications/event send: %s", self.nb_checks_send)
            self.nb_checks_send = 0
            if self.nb_broks_send != 0:
                logger.debug("Nb Broks send: %s", self.nb_broks_send)
            self.nb_broks_send = 0

            time_elapsed = now - gogogo
            logger.debug("Check average = %d checks/s", int(self.nb_check_received / time_elapsed))

            if self.need_dump_memory:
                self.sched_daemon.dump_memory()
                self.need_dump_memory = False

            if self.need_objects_dump:
                logger.debug('I need to dump my objects!')
                self.dump_objects()
                self.dump_config()
                self.need_objects_dump = False



        # WE must save the retention at the quit BY OURSELF
        # because our daemon will not be able to do it for us
        self.update_retention_file(True)
