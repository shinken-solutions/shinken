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
This class is an interface for Reactionner and Poller daemons
A Reactionner listens to a port for the configuration from the Arbiter
The conf contains the schedulers where actionners will gather actions.

The Reactionner keeps on listening to the Arbiter
(one a timeout)

If Arbiter wants it to have a new conf, the satellite forgets the previous
 Schedulers (and actions into) and takes the new ones.
"""



# Try to see if we are in an android device or not
is_android = True
try:
    import android
except ImportError:
    is_android = False

from Queue import Empty

if not is_android:
    from multiprocessing import Queue, active_children, cpu_count
else:
    from Queue import Queue

import os
import copy
import time
import cPickle
import traceback
import zlib
import base64
import threading

from shinken.http_client import HTTPClient, HTTPExceptions

from shinken.message import Message
from shinken.worker import Worker
from shinken.load import Load
from shinken.daemon import Daemon, Interface
from shinken.log import logger
from shinken.stats import statsmgr


# Class to tell that we are facing a non worker module
# but a standard one
class NotWorkerMod(Exception):
    pass


# Interface for Arbiter, our big MASTER
# It gives us our conf
class IForArbiter(Interface):

    doc = 'Remove a scheduler connection (internal)'
    # Arbiter ask us to do not manage a scheduler_id anymore
    # I do it and don't ask why
    def remove_from_conf(self, sched_id):
        try:
            del self.app.schedulers[sched_id]
        except KeyError:
            pass
    remove_from_conf.doc = doc


    doc = 'Return the managed configuration ids (internal)'
    # Arbiter ask me which sched_id I manage, If it is not ok with it
    # It will ask me to remove one or more sched_id
    def what_i_managed(self):
        logger.debug("The arbiter asked me what I manage. It's %s", self.app.what_i_managed())
        return self.app.what_i_managed()
    what_i_managed.need_lock = False
    what_i_managed.doc = doc

    doc = 'Ask the daemon to drop its configuration and wait for a new one'
    # Call by arbiter if it thinks we are running but we must do not (like
    # if I was a spare that take a conf but the master returns, I must die
    # and wait a new conf)
    # Us: No please...
    # Arbiter: I don't care, hasta la vista baby!
    # Us: ... <- Nothing! We are dead! you don't get it or what??
    # Reading code is not a job for eyes only...
    def wait_new_conf(self):
        logger.debug("Arbiter wants me to wait for a new configuration")
        self.app.schedulers.clear()
        self.app.cur_conf = None
    wait_new_conf.doc = doc


    doc = 'Push broks objects to the daemon (internal)'
    # NB: following methods are only used by broker
    # Used by the Arbiter to push broks to broker
    def push_broks(self, broks):
        with self.app.arbiter_broks_lock:
            self.app.arbiter_broks.extend(broks.values())
    push_broks.method = 'post'
    # We are using a Lock just for NOT lock this call from the arbiter :)
    push_broks.need_lock = False
    push_broks.doc = doc

    doc = 'Get the external commands from the daemon (internal)'
    # The arbiter ask us our external commands in queue
    # Same than push_broks, we will not using Global lock here,
    # and only lock for external_commands
    def get_external_commands(self):
        with self.app.external_commands_lock:
            cmds = self.app.get_external_commands()
            raw = cPickle.dumps(cmds)
        return raw
    get_external_commands.need_lock = False
    get_external_commands.doc = doc


    doc = 'Does the daemon got configuration (receiver)'
    # NB: only useful for receiver
    def got_conf(self):
        return self.app.cur_conf is not None
    got_conf.need_lock = False
    got_conf.doc = doc


    doc = 'Push hostname/scheduler links (receiver in direct routing)'
    # Use by the receivers to got the host names managed by the schedulers
    def push_host_names(self, sched_id, hnames):
        self.app.push_host_names(sched_id, hnames)
    push_host_names.method = 'post'
    push_host_names.doc = doc


class ISchedulers(Interface):
    """Interface for Schedulers
    If we are passive, they connect to this and send/get actions

    """

    doc = 'Push new actions to the scheduler (internal)'
    # A Scheduler send me actions to do
    def push_actions(self, actions, sched_id):
        self.app.add_actions(actions, int(sched_id))
    push_actions.method = 'post'
    push_actions.doc = doc

    doc = 'Get the returns of the actions (internal)'
    # A scheduler ask us the action return value
    def get_returns(self, sched_id):
        # print "A scheduler ask me the returns", sched_id
        ret = self.app.get_return_for_passive(int(sched_id))
        # print "Send mack", len(ret), "returns"
        return cPickle.dumps(ret)
    get_returns.doc = doc


class IBroks(Interface):
    """Interface for Brokers
    They connect here and get all broks (data for brokers)
    data must be ORDERED! (initial status BEFORE update...)

    """

    doc = 'Get broks from the daemon'
    # poller or reactionner ask us actions
    def get_broks(self, bname):
        res = self.app.get_broks()
        return base64.b64encode(zlib.compress(cPickle.dumps(res), 2))
    get_broks.doc = doc


class IStats(Interface):
    """
    Interface for various stats about poller/reactionner activity
    """

    doc = 'Get raw stats from the daemon'
    def get_raw_stats(self):
        app = self.app
        res = {}

        for sched_id in app.schedulers:
            sched = app.schedulers[sched_id]
            lst = []
            res[sched_id] = lst
            for mod in app.q_by_mod:
                # In workers we've got actions send to queue - queue size
                for (i, q) in app.q_by_mod[mod].items():
                    lst.append({
                        'scheduler_name': sched['name'],
                        'module': mod,
                        'queue_number': i,
                        'queue_size': q.qsize(),
                        'return_queue_len': app.get_returns_queue_len()})
        return res
    get_raw_stats.doc = doc




class BaseSatellite(Daemon):
    """Please Add a Docstring to describe the class here"""

    def __init__(self, name, config_file, is_daemon, do_replace, debug, debug_file):
        super(BaseSatellite, self).__init__(name, config_file, is_daemon,
                                            do_replace, debug, debug_file)
        # Ours schedulers
        self.schedulers = {}

        # Now we create the interfaces
        self.interface = IForArbiter(self)
        self.istats = IStats(self)

        # Can have a queue of external_commands given by modules
        # will be taken by arbiter to process
        self.external_commands = []
        self.external_commands_lock = threading.RLock()


    # The arbiter can resent us new conf in the pyro_daemon port.
    # We do not want to loose time about it, so it's not a blocking
    # wait, timeout = 0s
    # If it send us a new conf, we reinit the connections of all schedulers
    def watch_for_new_conf(self, timeout):
        self.handleRequests(timeout)


    def do_stop(self):
        if self.http_daemon and self.interface:
            logger.info("[%s] Stopping all network connections", self.name)
            self.http_daemon.unregister(self.interface)
        super(BaseSatellite, self).do_stop()


    # Give the arbiter the data about what I manage
    # for me it's the ids of my schedulers
    def what_i_managed(self):
        r = {}
        for (k, v) in self.schedulers.iteritems():
            r[k] = v['push_flavor']
        return r


    # Call by arbiter to get our external commands
    def get_external_commands(self):
        res = self.external_commands
        self.external_commands = []
        return res




class Satellite(BaseSatellite):
    """Our main APP class"""

    def __init__(self, name, config_file, is_daemon, do_replace, debug, debug_file):

        super(Satellite, self).__init__(name, config_file, is_daemon, do_replace,
                                        debug, debug_file)

        # Keep broks so they can be eaten by a broker
        self.broks = {}

        self.workers = {}   # dict of active workers

        # Init stats like Load for workers
        self.wait_ratio = Load(initial_value=1)

        self.brok_interface = IBroks(self)
        self.scheduler_interface = ISchedulers(self)

        # Just for having these attributes defined here. explicit > implicit ;)
        self.uri2 = None
        self.uri3 = None
        self.s = None

        self.returns_queue = None
        self.q_by_mod = {}


    # Wrapper function for the true con init
    def pynag_con_init(self, id):
        _t = time.time()
        r = self.do_pynag_con_init(id)
        statsmgr.incr('con-init.scheduler', time.time() - _t)
        return r


    # Initialize or re-initialize connection with scheduler """
    def do_pynag_con_init(self, id):
        sched = self.schedulers[id]

        # If sched is not active, I do not try to init
        # it is just useless
        if not sched['active']:
            return

        sname = sched['name']
        uri = sched['uri']
        running_id = sched['running_id']
        timeout = sched['timeout']
        data_timeout = sched['data_timeout']
        logger.info("[%s] Init connection with %s at %s (%ss,%ss)",
                    self.name, sname, uri, timeout, data_timeout)

        try:
            sch_con = sched['con'] = HTTPClient(
                uri=uri, strong_ssl=sched['hard_ssl_name_check'],
                timeout=timeout, data_timeout=data_timeout)
        except HTTPExceptions, exp:
            logger.warning("[%s] Scheduler %s is not initialized or has network problem: %s",
                           self.name, sname, str(exp))
            sched['con'] = None
            return

        # timeout of 3s by default (short one)
        # and get the running id
        try:
            new_run_id = sch_con.get('get_running_id')
            new_run_id = float(new_run_id)
        except (HTTPExceptions, cPickle.PicklingError, KeyError), exp:
            logger.warning("[%s] Scheduler %s is not initialized or has network problem: %s",
                           self.name, sname, str(exp))
            sched['con'] = None
            return

        # The schedulers have been restarted: it has a new run_id.
        # So we clear all verifs, they are obsolete now.
        if sched['running_id'] != 0 and new_run_id != running_id:
            logger.info("[%s] The running id of the scheduler %s changed, "
                        "we must clear its actions",
                        self.name, sname)
            sched['wait_homerun'].clear()
        sched['running_id'] = new_run_id
        logger.info("[%s] Connection OK with scheduler %s", self.name, sname)


    # Manage action returned from Workers
    # We just put them into the corresponding sched
    # and we clean unused properties like sched_id
    def manage_action_return(self, action):
        # Maybe our workers end us something else than an action
        # if so, just add this in other queues and return
        cls_type = action.__class__.my_type
        if cls_type not in ['check', 'notification', 'eventhandler']:
            self.add(action)
            return

        # Ok, it's a result. We get it, and fill verifs of the good sched_id
        sched_id = action.sched_id

        # Now we now where to put action, we do not need sched_id anymore
        del action.sched_id

        # Unset the tag of the worker_id too
        try:
            del action.worker_id
        except AttributeError:
            pass

        # And we remove it from the actions queue of the scheduler too
        try:
            del self.schedulers[sched_id]['actions'][action.get_id()]
        except KeyError:
            pass
        # We tag it as "return wanted", and move it in the wait return queue
        # Stop, if it is "timeout" we need this information later
        # in the scheduler
        # action.status = 'waitforhomerun'
        try:
            self.schedulers[sched_id]['wait_homerun'][action.get_id()] = action
        except KeyError:
            pass


    # Wrapper function for stats
    def manage_returns(self):
        _t = time.time()
        r = self.do_manage_returns()
        statsmgr.incr('core.manage-returns', time.time() - _t)
        return r


    # Return the chk to scheduler and clean them
    # REF: doc/shinken-action-queues.png (6)
    def do_manage_returns(self):
        # For all schedulers, we check for waitforhomerun
        # and we send back results
        for sched_id in self.schedulers:
            sched = self.schedulers[sched_id]
            # If sched is not active, I do not try return
            if not sched['active']:
                continue
            # Now ret have all verifs, we can return them
            send_ok = False
            ret = sched['wait_homerun'].values()
            if ret is not []:
                try:
                    con = sched['con']
                    if con is not None:  # None = not initialized
                        send_ok = con.post('put_results', {'results': ret})
                        # Not connected or sched is gone
                except (HTTPExceptions, KeyError), exp:
                    logger.error('manage_returns exception:: %s,%s ', type(exp), str(exp))
                    self.pynag_con_init(sched_id)
                    return
                except AttributeError, exp:  # the scheduler must  not be initialized
                    logger.error('manage_returns exception:: %s,%s ', type(exp), str(exp))
                except Exception, exp:
                    logger.error("A satellite raised an unknown exception: %s (%s)", exp, type(exp))
                    raise

            # We clean ONLY if the send is OK
            if send_ok:
                sched['wait_homerun'].clear()
            else:
                self.pynag_con_init(sched_id)
                logger.warning("Sent failed!")


    # Get all returning actions for a call from a
    # scheduler
    def get_return_for_passive(self, sched_id):
        # I do not know this scheduler?
        if sched_id not in self.schedulers:
            logger.debug("I do not know this scheduler: %s", sched_id)
            return []

        sched = self.schedulers[sched_id]
        logger.debug("Preparing to return %s", str(sched['wait_homerun'].values()))

        # prepare our return
        ret = copy.copy(sched['wait_homerun'].values())

        # and clear our dict
        sched['wait_homerun'].clear()

        return ret


    # Create and launch a new worker, and put it into self.workers
    # It can be mortal or not
    def create_and_launch_worker(self, module_name='fork', mortal=True):
        # create the input queue of this worker
        try:
            if is_android:
                q = Queue()
            else:
                q = self.manager.Queue()
        # If we got no /dev/shm on linux, we can got problem here.
        # Must raise with a good message
        except OSError, exp:
            # We look for the "Function not implemented" under Linux
            if exp.errno == 38 and os.name == 'posix':
                logger.critical("Got an exception (%s). If you are under Linux, "
                                "please check that your /dev/shm directory exists and"
                                " is read-write.", str(exp))
            raise

        # If we are in the fork module, we do not specify a target
        target = None
        if module_name == 'fork':
            target = None
        else:
            for module in self.modules_manager.instances:
                if module.properties['type'] == module_name:
                    # First, see if the module is a 'worker' one or not
                    if not module.properties.get('worker_capable', False):
                        raise NotWorkerMod
                    target = module.work
            if target is None:
                return
        # We want to give to the Worker the name of the daemon (poller or reactionner)
        cls_name = self.__class__.__name__.lower()
        w = Worker(1, q, self.returns_queue, self.processes_by_worker,
                   mortal=mortal, max_plugins_output_length=self.max_plugins_output_length,
                   target=target, loaded_into=cls_name, http_daemon=self.http_daemon)
        w.module_name = module_name
        # save this worker
        self.workers[w.id] = w

        # And save the Queue of this worker, with key = worker id
        self.q_by_mod[module_name][w.id] = q
        logger.info("[%s] Allocating new %s Worker: %s", self.name, module_name, w.id)

        # Ok, all is good. Start it!
        w.start()


    # The main stop of this daemon. Stop all workers
    # modules and sockets
    def do_stop(self):
        logger.info("[%s] Stopping all workers", self.name)
        for w in self.workers.values():
            try:
                w.terminate()
                w.join(timeout=1)
            # A already dead worker or in a worker
            except (AttributeError, AssertionError):
                pass
        # Close the server socket if it was opened
        if self.http_daemon:
            if self.brok_interface:
                self.http_daemon.unregister(self.brok_interface)
            if self.scheduler_interface:
                self.http_daemon.unregister(self.scheduler_interface)
        # And then call our master stop from satellite code
        super(Satellite, self).do_stop()


    # A simple function to add objects in self
    # like broks in self.broks, etc
    # TODO: better tag ID?
    def add(self, elt):
        cls_type = elt.__class__.my_type
        if cls_type == 'brok':
            # For brok, we TAG brok with our instance_id
            elt.instance_id = 0
            self.broks[elt.id] = elt
            return
        elif cls_type == 'externalcommand':
            logger.debug("Enqueuing an external command '%s'", str(elt.__dict__))
            with self.external_commands_lock:
                self.external_commands.append(elt)


    # Someone ask us our broks. We send them, and clean the queue
    def get_broks(self):
        res = copy.copy(self.broks)
        self.broks.clear()
        return res


    # workers are processes, they can die in a numerous of ways
    # like:
    # *99.99%: bug in code, sorry:p
    # *0.005 %: a mix between a stupid admin (or an admin without coffee),
    # and a kill command
    # *0.005%: alien attack
    # So they need to be detected, and restart if need
    def check_and_del_zombie_workers(self):
        # In android, we are using threads, so there is not active_children call
        if not is_android:
            # Active children make a join with everyone, useful :)
            active_children()

        w_to_del = []
        for w in self.workers.values():
            # If a worker goes down and we did not ask him, it's not
            # good: we can think that we have a worker and it's not True
            # So we del it
            if not w.is_alive():
                logger.warning("[%s] The worker %s goes down unexpectedly!", self.name, w.id)
                # Terminate immediately
                w.terminate()
                w.join(timeout=1)
                w_to_del.append(w.id)

        # OK, now really del workers from queues
        # And requeue the actions it was managed
        for id in w_to_del:
            w = self.workers[id]

            # Del the queue of the module queue
            del self.q_by_mod[w.module_name][w.id]

            for sched_id in self.schedulers:
                sched = self.schedulers[sched_id]
                for a in sched['actions'].values():
                    if a.status == 'queue' and a.worker_id == id:
                        # Got a check that will NEVER return if we do not
                        # restart it
                        self.assign_to_a_queue(a)

            # So now we can really forgot it
            del self.workers[id]

        

    # Here we create new workers if the queue load (len of verifs) is too long
    def adjust_worker_number_by_load(self):
        to_del = []
        logger.debug("[%s] Trying to adjust worker number."
                     " Actual number : %d, min per module : %d, max per module : %d",
                     self.name, len(self.workers), self.min_workers, self.max_workers)

        # I want at least min_workers by module then if I can, I add worker for load balancing
        for mod in self.q_by_mod:
            # At least min_workers
            while len(self.q_by_mod[mod]) < self.min_workers:
                try:
                    self.create_and_launch_worker(module_name=mod)
                # Maybe this modules is not a true worker one.
                # if so, just delete if from q_by_mod
                except NotWorkerMod:
                    to_del.append(mod)
                    break
            """
            # Try to really adjust load if necessary
            if self.get_max_q_len(mod) > self.max_q_size:
                if len(self.q_by_mod[mod]) >= self.max_workers:
                    logger.info("Cannot add a new %s worker, even if load is high. "
                                "Consider changing your max_worker parameter") % mod
                else:
                    try:
                        self.create_and_launch_worker(module_name=mod)
                    # Maybe this modules is not a true worker one.
                    # if so, just delete if from q_by_mod
                    except NotWorkerMod:
                        to_del.append(mod)
            """

        for mod in to_del:
            logger.debug("[%s] The module %s is not a worker one, "
                         "I remove it from the worker list", self.name, mod)
            del self.q_by_mod[mod]
        # TODO: if len(workers) > 2*wish, maybe we can kill a worker?

        
    # Get the Queue() from an action by looking at which module
    # it wants with a round robin way to scale the load between
    # workers
    def _got_queue_from_action(self, a):
        # get the module name, if not, take fork
        mod = getattr(a, 'module_type', 'fork')
        queues = self.q_by_mod[mod].items()

        # Maybe there is no more queue, it's very bad!
        if len(queues) == 0:
            return (0, None)

        # if not get a round robin index to get a queue based
        # on the action id
        rr_idx = a.id % len(queues)
        (i, q) = queues[rr_idx]

        # return the id of the worker (i), and its queue
        return (i, q)


    # Add a list of actions to our queues
    def add_actions(self, lst, sched_id):
        for a in lst:
            # First we look if we do not already have it, if so
            # do nothing, we are already working!
            if a.id in self.schedulers[sched_id]['actions']:
                continue
            a.sched_id = sched_id
            a.status = 'queue'
            self.assign_to_a_queue(a)


    # Take an action and put it into one queue
    def assign_to_a_queue(self, a):
        msg = Message(id=0, type='Do', data=a)
        (i, q) = self._got_queue_from_action(a)
        # Tag the action as "in the worker i"
        a.worker_id = i
        if q is not None:
            q.put(msg)


    # Wrapper function for the real function
    def get_new_actions(self):
        _t = time.time()
        self.do_get_new_actions()
        statsmgr.incr('core.get-new-actions', time.time() - _t)


    # We get new actions from schedulers, we create a Message and we
    # put it in the s queue (from master to slave)
    # REF: doc/shinken-action-queues.png (1)
    def do_get_new_actions(self):
        # Here are the differences between a
        # poller and a reactionner:
        # Poller will only do checks,
        # reactionner do actions (notif + event handlers)
        do_checks = self.__class__.do_checks
        do_actions = self.__class__.do_actions

        # We check for new check in each schedulers and put the result in new_checks
        for sched_id in self.schedulers:
            sched = self.schedulers[sched_id]
            # If sched is not active, I do not try return
            if not sched['active']:
                continue

            try:
                try:
                    con = sched['con']
                except KeyError:
                    con = None
                if con is not None:  # None = not initialized
                    # OK, go for it :)
                    # Before ask a call that can be long, do a simple ping to be sure it is alive
                    con.get('ping')
                    tmp = con.get('get_checks', {
                        'do_checks': do_checks, 'do_actions': do_actions,
                        'poller_tags': self.poller_tags,
                        'reactionner_tags': self.reactionner_tags,
                        'worker_name': self.name,
                        'module_types': self.q_by_mod.keys()
                    },
                        wait='long')
                    # Explicit pickle load
                    tmp = base64.b64decode(tmp)
                    tmp = zlib.decompress(tmp)
                    tmp = cPickle.loads(str(tmp))
                    logger.debug("Ask actions to %d, got %d", sched_id, len(tmp))
                    # We 'tag' them with sched_id and put into queue for workers
                    # REF: doc/shinken-action-queues.png (2)
                    self.add_actions(tmp, sched_id)
                else:  # no con? make the connection
                    self.pynag_con_init(sched_id)
            # Ok, con is unknown, so we create it
            # Or maybe is the connection lost, we recreate it
            except (HTTPExceptions, KeyError), exp:
                logger.debug('get_new_actions exception:: %s,%s ', type(exp), str(exp))
                self.pynag_con_init(sched_id)
            # scheduler must not be initialized
            # or scheduler must not have checks
            except AttributeError, exp:
                logger.debug('get_new_actions exception:: %s,%s ', type(exp), str(exp))
            # What the F**k? We do not know what happened,
            # log the error message if possible.
            except Exception, exp:
                logger.error("A satellite raised an unknown exception: %s (%s)", exp, type(exp))
                raise


    # In android we got a Queue, and a manager list for others
    def get_returns_queue_len(self):
        return self.returns_queue.qsize()


    # In android we got a Queue, and a manager list for others
    def get_returns_queue_item(self):
        return self.returns_queue.get()


    # An arbiter ask us to wait a new conf, so we must clean
    # all the mess we did, and close modules too
    def clean_previous_run(self):
        # Clean all lists
        self.schedulers.clear()
        self.broks.clear()
        with self.external_commands_lock:
            self.external_commands = self.external_commands[:]


    def do_loop_turn(self):
        logger.debug("Loop turn")
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
        # If so, we listen to it
        # When it push a conf, we reinit connections
        # Sleep in waiting a new conf :)
        # TODO: manage the diff again.
        while self.timeout > 0:
            begin = time.time()
            self.watch_for_new_conf(self.timeout)
            end = time.time()
            if self.new_conf:
                self.setup_new_conf()
            self.timeout = self.timeout - (end - begin)

        logger.debug(" ======================== ")

        self.timeout = self.polling_interval

        # Check if zombies workers are among us :)
        # If so: KILL THEM ALL!!!
        self.check_and_del_zombie_workers()

        # But also modules
        self.check_and_del_zombie_modules()

        # Print stats for debug
        for sched_id in self.schedulers:
            sched = self.schedulers[sched_id]
            for mod in self.q_by_mod:
                # In workers we've got actions send to queue - queue size
                for (i, q) in self.q_by_mod[mod].items():
                    logger.debug("[%d][%s][%s] Stats: Workers:%d (Queued:%d TotalReturnWait:%d)",
                                 sched_id, sched['name'], mod,
                                 i, q.qsize(), self.get_returns_queue_len())
                    # also update the stats module
                    statsmgr.incr('core.worker-%s.queue-size' % mod, q.qsize())

        # Before return or get new actions, see how we manage
        # old ones: are they still in queue (s)? If True, we
        # must wait more or at least have more workers
        wait_ratio = self.wait_ratio.get_load()
        total_q = 0
        for mod in self.q_by_mod:
            for q in self.q_by_mod[mod].values():
                total_q += q.qsize()
        if total_q != 0 and wait_ratio < 2 * self.polling_interval:
            logger.debug("I decide to up wait ratio")
            self.wait_ratio.update_load(wait_ratio * 2)
            # self.wait_ratio.update_load(self.polling_interval)
        else:
            # Go to self.polling_interval on normal run, if wait_ratio
            # was >2*self.polling_interval,
            # it make it come near 2 because if < 2, go up :)
            self.wait_ratio.update_load(self.polling_interval)
        wait_ratio = self.wait_ratio.get_load()
        logger.debug("Wait ratio: %f", wait_ratio)
        statsmgr.incr('core.wait-ratio', wait_ratio)

        # We can wait more than 1s if needed,
        # no more than 5s, but no less than 1
        timeout = self.timeout * wait_ratio
        timeout = max(self.polling_interval, timeout)
        self.timeout = min(5 * self.polling_interval, timeout)
        statsmgr.incr('core.timeout', wait_ratio)

        # Maybe we do not have enough workers, we check for it
        # and launch the new ones if needed
        self.adjust_worker_number_by_load()

        # Manage all messages we've got in the last timeout
        # for queue in self.return_messages:
        while self.get_returns_queue_len() != 0:
            self.manage_action_return(self.get_returns_queue_item())


        # If we are passive, we do not initiate the check getting
        # and return
        if not self.passive:
            # Now we can get new actions from schedulers
            self.get_new_actions()

            # We send all finished checks
            # REF: doc/shinken-action-queues.png (6)
            self.manage_returns()

        # Get objects from our modules that are not worker based
        self.get_objects_from_from_queues()

        # Say to modules it's a new tick :)
        self.hook_point('tick')


    # Do this satellite (poller or reactionner) post "daemonize" init:
    # we must register our interfaces for 3 possible callers: arbiter,
    # schedulers or brokers.
    def do_post_daemon_init(self):
        # And we register them
        self.uri2 = self.http_daemon.register(self.interface)
        self.uri3 = self.http_daemon.register(self.brok_interface)
        self.uri4 = self.http_daemon.register(self.scheduler_interface)
        self.uri5 = self.http_daemon.register(self.istats)

        # self.s = Queue() # Global Master -> Slave
        # We can open the Queue for fork AFTER
        self.q_by_mod['fork'] = {}

        # Under Android, we do not have multiprocessing lib
        # so use standard Queue threads things
        # but in multiprocess, we are also using a Queue(). It's just
        # not the same
        if is_android:
            self.returns_queue = Queue()
        else:
            self.returns_queue = self.manager.Queue()

        # For multiprocess things, we should not have
        # socket timeouts.
        import socket
        socket.setdefaulttimeout(None)


    # Setup the new received conf from arbiter
    def setup_new_conf(self):
        conf = self.new_conf
        logger.debug("[%s] Sending us a configuration %s", self.name, conf)
        self.new_conf = None
        self.cur_conf = conf
        g_conf = conf['global']

        # Got our name from the globals
        if 'poller_name' in g_conf:
            name = g_conf['poller_name']
        elif 'reactionner_name' in g_conf:
            name = g_conf['reactionner_name']
        else:
            name = 'Unnamed satellite'
        self.name = name
        # kernel.io part
        self.api_key = g_conf['api_key']
        self.secret = g_conf['secret']
        self.http_proxy = g_conf['http_proxy']
        # local statsd
        self.statsd_host = g_conf['statsd_host']
        self.statsd_port = g_conf['statsd_port']
        self.statsd_prefix = g_conf['statsd_prefix']
        self.statsd_enabled = g_conf['statsd_enabled']

        # we got a name, we can now say it to our statsmgr
        if 'poller_name' in g_conf:
            statsmgr.register(self, self.name, 'poller',
                              api_key=self.api_key, secret=self.secret, http_proxy=self.http_proxy,
                              statsd_host=self.statsd_host, statsd_port=self.statsd_port,
                              statsd_prefix=self.statsd_prefix, statsd_enabled=self.statsd_enabled)
        else:
            statsmgr.register(self, self.name, 'reactionner',
                              api_key=self.api_key, secret=self.secret,
                              statsd_host=self.statsd_host, statsd_port=self.statsd_port,
                              statsd_prefix=self.statsd_prefix, statsd_enabled=self.statsd_enabled)

        self.passive = g_conf['passive']
        if self.passive:
            logger.info("[%s] Passive mode enabled.", self.name)

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
            else:
                self.schedulers[sched_id]['wait_homerun'] = {}
                self.schedulers[sched_id]['actions'] = {}
            self.schedulers[sched_id]['running_id'] = 0
            self.schedulers[sched_id]['active'] = s['active']
            self.schedulers[sched_id]['timeout'] = s['timeout']
            self.schedulers[sched_id]['data_timeout'] = s['data_timeout']

            # Do not connect if we are a passive satellite
            if not self.passive and not already_got:
                # And then we connect to it :)
                self.pynag_con_init(sched_id)

        # Now the limit part, 0 mean: number of cpu of this machine :)
        # if not available, use 4 (modern hardware)
        self.max_workers = g_conf['max_workers']
        if self.max_workers == 0 and not is_android:
            try:
                self.max_workers = cpu_count()
            except NotImplementedError:
                self.max_workers = 4
        logger.info("[%s] Using max workers: %s", self.name, self.max_workers)
        self.min_workers = g_conf['min_workers']
        if self.min_workers == 0 and not is_android:
            try:
                self.min_workers = cpu_count()
            except NotImplementedError:
                self.min_workers = 4
        logger.info("[%s] Using min workers: %s", self.name, self.min_workers)

        self.processes_by_worker = g_conf['processes_by_worker']
        self.polling_interval = g_conf['polling_interval']
        self.timeout = self.polling_interval

        # Now set tags
        # ['None'] is the default tags
        self.poller_tags = g_conf.get('poller_tags', ['None'])
        self.reactionner_tags = g_conf.get('reactionner_tags', ['None'])
        self.max_plugins_output_length = g_conf.get('max_plugins_output_length', 8192)

        # Set our giving timezone from arbiter
        use_timezone = g_conf['use_timezone']
        if use_timezone != 'NOTSET':
            logger.info("[%s] Setting our timezone to %s", self.name, use_timezone)
            os.environ['TZ'] = use_timezone
            time.tzset()

        logger.info("We have our schedulers: %s", str(self.schedulers))

        # Now manage modules
        # TODO: check how to better handle this with modules_manager..
        mods = g_conf['modules']
        for module in mods:
            # If we already got it, bypass
            if module.module_type not in self.q_by_mod:
                logger.debug("Add module object %s", str(module))
                self.modules_manager.modules.append(module)
                logger.info("[%s] Got module: %s ", self.name, module.module_type)
                self.q_by_mod[module.module_type] = {}


    # stats threads is asking us a main structure for stats
    def get_stats_struct(self):
        now = int(time.time())
        # call the daemon one
        res = super(Satellite, self).get_stats_struct()
        _type = self.__class__.my_type
        res.update({'name': self.name, 'type': _type})
        # The receiver do nto have a passie prop
        if hasattr(self, 'passive'):
            res['passive'] = self.passive
        metrics = res['metrics']
        # metrics specific
        metrics.append('%s.%s.external-commands.queue %d %d' % (
            _type, self.name, len(self.external_commands), now))

        return res


    def main(self):
        try:
            for line in self.get_header():
                logger.info(line)

            self.load_config_file()

            # Setting log level
            logger.setLevel(self.log_level)
            # Force the debug level if the daemon is said to start with such level
            if self.debug:
                logger.setLevel('DEBUG')

            # Look if we are enabled or not. If ok, start the daemon mode
            self.look_for_early_exit()
            self.do_daemon_init_and_start()

            self.do_post_daemon_init()

            self.load_modules_manager()

            # We wait for initial conf
            self.wait_for_initial_conf()
            if not self.new_conf:  # we must have either big problem or was requested to shutdown
                return
            self.setup_new_conf()

            # We can load our modules now
            self.modules_manager.set_modules(self.modules_manager.modules)
            self.do_load_modules()
            # And even start external ones
            self.modules_manager.start_external_instances()

            # Allocate Mortal Threads
            for _ in xrange(1, self.min_workers):
                to_del = []
                for mod in self.q_by_mod:
                    try:
                        self.create_and_launch_worker(module_name=mod)
                    # Maybe this modules is not a true worker one.
                    # if so, just delete if from q_by_mod
                    except NotWorkerMod:
                        to_del.append(mod)

                for mod in to_del:
                    logger.debug("The module %s is not a worker one, "
                                 "I remove it from the worker list", mod)
                    del self.q_by_mod[mod]

            # Now main loop
            self.do_mainloop()
        except Exception:
            self.print_unrecoverable(traceback.format_exc())
            raise
