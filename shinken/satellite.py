#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012 :
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
This class is an interface for reactionner and poller
The satallite listens to a port the configuration from the Arbiter
The conf contains the schedulers where actionners will gather actions.

The actionner keeps on listening the arbiter
(one a timeout)

if arbiter wants it to have a new conf, the satellite forget the previous
 schedulers (and actions into) and take the new ones.
"""

# Try to see if we are in an android device or not
is_android = True
try:
   import android
except ImportError:
   is_android = False

from Queue import Empty

if not is_android:
   from multiprocessing import Queue, Manager, active_children, cpu_count
else:
   from Queue import Queue

import os
import copy
import time
import sys
import cPickle
import traceback
import socket
from util import if_else

try:
    import shinken.pyro_wrapper as pyro
except ImportError:
    sys.exit("Shinken require the Python Pyro module. Please install it.")

Pyro = pyro.Pyro
PYRO_VERSION = pyro.PYRO_VERSION


from shinken.message import Message
from shinken.worker import Worker
from shinken.load import Load
from shinken.daemon import Daemon, Interface
from shinken.log import logger
from shinken.brok import Brok
from shinken.check import Check
from shinken.notification import Notification
from shinken.eventhandler import EventHandler
from shinken.external_command import ExternalCommand

# Pack of common Pyro exceptions
from shinken.pyro_wrapper import Pyro_exp_pack


# Class to tell that we are facing a non worker module
# but a standard one
class NotWorkerMod(Exception):
   pass


# Interface for Arbiter, our big MASTER
# It gives us our conf
class IForArbiter(Interface):

    # Arbiter ask us to do not manage a scheduler_id anymore
    # I do it and don't ask why
    def remove_from_conf(self, sched_id):
        try:
            del self.app.schedulers[sched_id]
        except KeyError:
            pass


    # Arbiter ask me which sched_id I manage, If it is not ok with it
    # It will ask me to remove one or more sched_id
    def what_i_managed(self):
        logger.debug("The arbiter ask me what I manage. It's %s" % self.app.what_i_managed())
        return self.app.what_i_managed()#self.app.schedulers.keys()


    # Call by arbiter if it thinks we are running but we must do not (like
    # if I was a spare that take a conf but the master returns, I must die
    # and wait a new conf)
    # Us : No please...
    # Arbiter : I don't care, hasta la vista baby!
    # Us : ... <- Nothing! We are dead! you don't get it or what?? 
    # Reading code is not a job for eyes only...
    def wait_new_conf(self):
        logger.debug("Arbiter want me to wait for a new conf")
        self.app.schedulers.clear()
        self.app.cur_conf = None


    #<WTF??> Inconsistent comments!
    # methods are only used by the arbiter or the broker?
    # NB: following methods are only used by broker
    # Used by the Arbiter to push broks to broker
    #</WTF??>
    def push_broks(self, broks):
        self.app.add_broks_to_queue(broks.values())
        return True


    # The arbiter ask us our external commands in queue
    def get_external_commands(self):
        return self.app.get_external_commands()

    
    ### NB : only useful for receiver
    def got_conf(self):
        return self.app.cur_conf != None


class ISchedulers(Interface):
    """Interface for Schedulers
    If we are passive, they connect to this and send/get actions

    """


    # A Scheduler send me actions to do
    def push_actions(self, actions, sched_id):
        #print "A scheduler sned me actions", actions
        self.app.add_actions(actions, sched_id)


    # A scheduler ask us its returns
    def get_returns(self, sched_id):
        #print "A scheduler ask me the returns", sched_id
        ret = self.app.get_return_for_passive(sched_id)
        #print "Send mack", len(ret), "returns"
        return ret



class IBroks(Interface):
    """Interface for Brokers
    They connect here and get all broks (data for brokers)
    datas must be ORDERED! (initial status BEFORE uodate...)

    """

    # poller or reactionner ask us actions
    def get_broks(self):
        res = self.app.get_broks()
        return res



class BaseSatellite(Daemon):
    """Please Add a Docstring to describe the class here"""
    
    
    def __init__(self, name, config_file, is_daemon, do_replace, debug, debug_file):     
        
        super(BaseSatellite, self).__init__(name, config_file, is_daemon, \
                                                do_replace, debug, debug_file)

        # Ours schedulers
        self.schedulers = {}
        
        # Now we create the interfaces
        self.interface = IForArbiter(self)

    # The arbiter can resent us new conf in the pyro_daemon port.
    # We do not want to loose time about it, so it's not a bloking
    # wait, timeout = 0s
    # If it send us a new conf, we reinit the connections of all schedulers
    def watch_for_new_conf(self, timeout):
        self.handleRequests(timeout)

    def do_stop(self):
        if self.pyro_daemon and self.interface:
            logger.debug("Stopping all network connections")
            self.pyro_daemon.unregister(self.interface)
        super(BaseSatellite, self).do_stop()



    # Give the arbiter the data about what I manage
    # for me it's the ids of my schedulers
    def what_i_managed(self):
       r = {}
       for (k,v) in self.schedulers.iteritems():
          r[k] = v['push_flavor']
       return r
        


class Satellite(BaseSatellite):
    """Our main APP class"""
    
    def __init__(self, name, config_file, is_daemon, do_replace, debug, debug_file):
        
        super(Satellite, self).__init__(name, config_file, is_daemon, do_replace,\
                                            debug, debug_file)
        
        # Keep broks so they can be eaten by a broker
        self.broks = {}

        self.workers = {}   # dict of active workers

        self.nb_actions_in_workers = 0

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

        # Can have a queue of external_commands given by modules
        # will be taken by arbiter to process
        self.external_commands = []


    # Initialize or re-initialize connection with scheduler """
    def pynag_con_init(self, id):
        sched = self.schedulers[id]

        # If sched is not active, I do not try to init
        # it is just useless
        if not sched['active']:
            return

        sname = sched['name']
        uri = sched['uri']
        running_id = sched['running_id']
        logger.info("[%s] Init de connection with %s at %s" % (self.name, sname, uri))

        try:
            socket.setdefaulttimeout(3)
            sch_con = sched['con'] = Pyro.core.getProxyForURI(uri)
            socket.setdefaulttimeout(None)
        except Pyro_exp_pack , exp:
            # But the multiprocessing module is not copatible with it!
            # so we must disable it imadiatly after
            socket.setdefaulttimeout(None)
            logger.warning("[%s] Scheduler %s is not initilised or got network problem: %s" % (self.name, sname, str(exp)))
            sched['con'] = None
            return


        # timeout of 120 s
        # and get the running id
        try:
            pyro.set_timeout(sch_con, 5)
            new_run_id = sch_con.get_running_id()
        except (Pyro.errors.ProtocolError, Pyro.errors.NamingError, cPickle.PicklingError, KeyError, Pyro.errors.CommunicationError, Pyro.errors.DaemonError) , exp:
            logger.warning("[%s] Scheduler %s is not initilised or got network problem: %s" % (self.name, sname, str(exp)))
            sched['con'] = None
            return

        # The schedulers have been restarted : it has a new run_id.
        # So we clear all verifs, they are obsolete now.
        if sched['running_id'] != 0 and new_run_id != running_id:
            logger.info("[%s] The running id of the scheduler %s changed, we must clear it's actions" % (self.name, sname))
            sched['wait_homerun'].clear()
        sched['running_id'] = new_run_id
        logger.info("[%s] Connection OK with scheduler %s" % (self.name, sname))


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
        #action.status = 'waitforhomerun'
        try:
            self.schedulers[sched_id]['wait_homerun'][action.get_id()] = action
        except KeyError:
            pass

        # We update stats
        self.nb_actions_in_workers =- 1


    # Return the chk to scheduler and clean them
    # REF: doc/shinken-action-queues.png (6)
    def manage_returns(self):
        #return
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
                    if con is not None: # None = not initialized
                        send_ok = con.put_results(ret)
                # Not connected or sched is gone
                except (Pyro_exp_pack, KeyError) , exp:
                    logger.debug(str(exp))
                    self.pynag_con_init(sched_id)
                    return
                except AttributeError , exp: # the scheduler must  not be initialized
                    logger.debug(str(exp))
                except Exception, exp:
                    logger.debug("A satellite raised an unknown exception : %s (%s)" % (exp, type(exp)))
                    try:
                        logger.debug(''.join(if_else(PYRO_VERSION < "4.0", Pyro.util.getPyroTraceback(exp), Pyro.util.getPyroTraceback())))
                    except:
                        pass
                    raise


            # We clean ONLY if the send is OK
            if send_ok :
                sched['wait_homerun'].clear()
            else:
                self.pynag_con_init(sched_id)
                logger.warning("Sent failed!")


    # Get all returning actions for a call from a
    # scheduler
    def get_return_for_passive(self, sched_id):
        # I do not know this scheduler?
        if sched_id not in self.schedulers:
            logger.debug("I do not know this scheduler : %s" % sched_id)
            return []

        sched = self.schedulers[sched_id]
        logger.debug("Preparing to return %s" % str(sched['wait_homerun'].values()))
        
        # prepare our return
        ret = copy.copy(sched['wait_homerun'].values())

        # and clear our dict
        sched['wait_homerun'].clear()

        return ret


    # Create and launch a new worker, and put it into self.workers
    # It can be mortal or not
    def create_and_launch_worker(self, module_name='fork', mortal=True):
        # ceate the input queue of this worker
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
                logger.error("Got an exception (%s). If you are under Linux, please check that your /dev/shm directory exists." % (str(exp)))
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
        w = Worker(1, q, self.returns_queue, self.processes_by_worker, \
                   mortal=mortal, max_plugins_output_length = self.max_plugins_output_length, target=target )
        w.module_name = module_name
        # save this worker
        self.workers[w.id] = w
        
        # And save the Queue of this worker, with key = worker id
        self.q_by_mod[module_name][w.id] = q
        logger.info("[%s] Allocating new %s Worker : %s" % (self.name, module_name, w.id))
        
        # Ok, all is good. Start it!
        w.start()


    # The main stop of this daemon. Stop all workers
    # modules and sockets
    def do_stop(self):
        logger.info("Stopping all workers")
        for w in self.workers.values():
            try:
                w.terminate()
                w.join(timeout=1)
            # A already dead worker or in a worker
            except (AttributeError, AssertionError): 
                pass
        # Close the pyro server socket if it was opened
        if self.pyro_daemon:
            logger.info("Stopping all network connections")
            if self.brok_interface:
                self.pyro_daemon.unregister(self.brok_interface)
            if self.scheduler_interface:
                self.pyro_daemon.unregister(self.scheduler_interface)
        # And then call our master stop from satellite code
        super(Satellite, self).do_stop()


    # Call by arbiter to get our external commands
    def get_external_commands(self):
        res = self.external_commands
        self.external_commands = []
        return res


    # A simple function to add objects in self
    # like broks in self.broks, etc
    # TODO : better tag ID?
    def add(self, elt):
        cls_type = elt.__class__.my_type
        if cls_type == 'brok':
            # For brok, we TAG brok with our instance_id
            elt.instance_id = 0
            self.broks[elt.id] = elt
            return
        elif cls_type == 'externalcommand':
            logger.debug("Enqueuing an external command '%s'" % str(elt.__dict__))
            self.external_commands.append(elt)


    # Someone ask us our broks. We send them, and clean the queue
    def get_broks(self):
        res = copy.copy(self.broks)
        self.broks.clear()
        return res


    # workers are processes, they can die in a numerous of ways
    # like :
    # *99.99% : bug in code, sorry :p
    # *0.005 % : a mix between a stupid admin (or an admin without coffee),
    # and a kill command
    # *0.005% : alien attack
    # So they need to be detected, and restart if need
    def check_and_del_zombie_workers(self):
        # In android, we are using threads, so there is not active_children call
        if not is_android:
           # Active children make a join with everyone, useful :)
           active_children()

        w_to_del = []
        for w in self.workers.values():
            # If a worker goes down and we did not ask him, it's not
            # good : we can think that we have a worker and it's not True
            # So we del it
            if not w.is_alive():
                logger.warning("[%s] The worker %s goes down unexpectly!" % (self.name, w.id))
                # AIM ... Press FIRE ... <B>HEAD SHOT!</B>
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
        # TODO : get a real value for a load
        wish_worker = 1
        # I want at least min_workers or wish_workers (the biggest)
        # but not more than max_workers
        while len(self.workers) < self.min_workers \
                    or (wish_worker > len(self.workers) \
                            and len(self.workers) < self.max_workers):
            for mod in self.q_by_mod:
                self.create_and_launch_worker(module_name=mod)
        # TODO : if len(workers) > 2*wish, maybe we can kill a worker?


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

            # Update stats
            self.nb_actions_in_workers += 1


    # Take an action and put it into one queue
    def assign_to_a_queue(self, a):
        msg = Message(id=0, type='Do', data=a)
        (i, q) = self._got_queue_from_action(a)
        # Tag the action as "in the worker i"
        a.worker_id = i
        if q is not None:
            q.put(msg)


    # We get new actions from schedulers, we create a Message and we
    # put it in the s queue (from master to slave)
    # REF: doc/shinken-action-queues.png (1)
    def get_new_actions(self):
        now = time.time()

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
                con = sched['con']
                if con is not None: # None = not initilized
                    pyro.set_timeout(con, 120)
                    # OK, go for it :)
                    tmp = con.get_checks(do_checks=do_checks, do_actions=do_actions, \
                                             poller_tags=self.poller_tags, \
                                             reactionner_tags=self.reactionner_tags, \
                                             worker_name=self.name, \
                                             module_types=self.q_by_mod.keys())
                    logger.debug("Ask actions to %d, got %d" % (sched_id, len(tmp)))
                    # We 'tag' them with sched_id and put into queue for workers
                    # REF: doc/shinken-action-queues.png (2)
                    self.add_actions(tmp, sched_id)
                else: # no con? make the connection
                    self.pynag_con_init(sched_id)
            # Ok, con is unknown, so we create it
            # Or maybe is the connection lost, we recreate it
            except (Pyro_exp_pack, KeyError) , exp:
                logger.debug(str(exp))
                self.pynag_con_init(sched_id)
            # scheduler must not be initialized
            # or scheduler must not have checks
            except (AttributeError, Pyro.errors.NamingError) , exp:
                pass
            # What the F**k? We do not know what happenned,
            # so.. bye bye :)
            except Exception , exp:
                logger.debug("A satellite raised an unknown exception : %s (%s)" % (exp, type(exp)))
                try:
                    logger.debug(''.join(if_else(PYRO_VERSION < "4.0", Pyro.util.getPyroTraceback(exp), Pyro.util.getPyroTraceback())))
                except:
                    pass
                raise



    # In android we got a Queue, and a manager list for others
    def get_returns_queue_len(self):
        return self.returns_queue.qsize()
        
        
    # In android we got a Queue, and a manager list for others
    def get_returns_queue_item(self):
        return self.returns_queue.get()


    # Get 'objects' from external modules
    # from now nobody use it, but it can be useful
    # for a module like livestatus to raise external
    # commands for example
    def get_objects_from_from_queues(self):
        for f in self.modules_manager.get_external_from_queues():
            full_queue = True
            while full_queue:
                try:
                    o = f.get(block=False)
                    self.add(o)
                except Empty :
                    full_queue = False



    # An arbiter ask us to wait a new conf, so we must clean
    # all the mess we did, and close modules too
    def clean_previous_run(self):
        # Clean all lists
        self.schedulers.clear()
        self.broks.clear()
        self.external_commands = self.external_commands[:]


    def do_loop_turn(self):
        print "Loop turn"
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
        # TODO : manage the diff again.
        while self.timeout > 0:
            begin = time.time()
            self.watch_for_new_conf(self.timeout)
            end = time.time()
            if self.new_conf:
                self.setup_new_conf()
            self.timeout = self.timeout - (end - begin)

        print " ======================== "

        self.timeout = self.polling_interval

        # Check if zombies workers are among us :)
        # If so : KILL THEM ALL!!!
        self.check_and_del_zombie_workers()

        # But also modules
        self.check_and_del_zombie_modules()

        # Print stats for debug
        for sched_id in self.schedulers:
            sched = self.schedulers[sched_id]
            for mod in self.q_by_mod:
                # In workers we've got actions send to queue - queue size
                for (i, q) in self.q_by_mod[mod].items():
                    logger.debug("[%d][%s][%s] Stats : Workers:%d (Queued:%d TotalReturnWait:%d)" % \
                        (sched_id, sched['name'], mod, i, q.qsize(), self.get_returns_queue_len()))


        # Before return or get new actions, see how we manage
        # old ones : are they still in queue (s)? If True, we
        # must wait more or at least have more workers
        wait_ratio = self.wait_ratio.get_load()
        total_q = 0
        for mod in self.q_by_mod:
            for q in self.q_by_mod[mod].values():
                total_q += q.qsize()
        if total_q != 0 and wait_ratio < 2*self.polling_interval:
            logger.debug("I decide to up wait ratio")
            self.wait_ratio.update_load(wait_ratio * 2)
            #self.wait_ratio.update_load(self.polling_interval)
        else:
            # Go to self.polling_interval on normal run, if wait_ratio
            # was >2*self.polling_interval,
            # it make it come near 2 because if < 2, go up :)
            self.wait_ratio.update_load(self.polling_interval)
        wait_ratio = self.wait_ratio.get_load()
        logger.debug("Wait ratio: %f" % wait_ratio)

        # We can wait more than 1s if needed,
        # no more than 5s, but no less than 1
        timeout = self.timeout * wait_ratio
        timeout = max(self.polling_interval, timeout)
        self.timeout = min(5*self.polling_interval, timeout)

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

        # Get objects from our modules that are not wroker based
        self.get_objects_from_from_queues()

        # Say to modules it's a new tick :)
        self.hook_point('tick')


    # Do this satellite (poller or reactionner) post "daemonize" init:
    # we must register our interfaces for 3 possible callers: arbiter, 
    # schedulers or brokers.
    def do_post_daemon_init(self):
        
        # And we register them
        self.uri2 = self.pyro_daemon.register(self.interface, "ForArbiter")
        self.uri3 = self.pyro_daemon.register(self.brok_interface, "Broks")
        self.uri4 = self.pyro_daemon.register(self.scheduler_interface, "Schedulers")
        
        # self.s = Queue() # Global Master -> Slave
        # We can open the Queeu for fork AFTER
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
        # socket timeouts. will be set explicitly in Pyro calls
        import socket
        socket.setdefaulttimeout(None)


    # Setup the new received conf from arbiter 
    def setup_new_conf(self):
        conf = self.new_conf
        logger.debug("[%s] Sending us a configuration %s" % (self.name, conf))
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

        self.passive = g_conf['passive']
        if self.passive:
            logger.info("[%s] Passive mode enabled." % self.name)

        # If we've got something in the schedulers, we do not want it anymore
        for sched_id in conf['schedulers'] :

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
                logger.info("[%s] We already got the conf %d (%s)" % (self.name, sched_id, conf['schedulers'][sched_id]['name']))
                wait_homerun = self.schedulers[sched_id]['wait_homerun']
                actions = self.schedulers[sched_id]['actions']

            s = conf['schedulers'][sched_id]
            self.schedulers[sched_id] = s

            uri = pyro.create_uri(s['address'], s['port'], 'Checks', self.use_ssl)

            self.schedulers[sched_id]['uri'] = uri
            if already_got:
                self.schedulers[sched_id]['wait_homerun'] = wait_homerun
                self.schedulers[sched_id]['actions'] = actions
            else:
                self.schedulers[sched_id]['wait_homerun'] = {}
                self.schedulers[sched_id]['actions'] = {}
            self.schedulers[sched_id]['running_id'] = 0
            self.schedulers[sched_id]['active'] = s['active']

            # Do not connect if we are a passive satellite
            if not self.passive and not already_got:
                # And then we connect to it :)
                self.pynag_con_init(sched_id)

        # Now the limit part, 0 mean : number of cpu of this machine :)
        # if not available, use 4 (modern hardware)
        self.max_workers = g_conf['max_workers']
        if self.max_workers == 0 and not is_android:
            try:
                self.max_workers = cpu_count()
            except NotImplementedError:
                self.max_workers =4
            logger.info("Using max workers : %s" % self.max_workers)
        self.min_workers = g_conf['min_workers']
        if self.min_workers == 0 and not is_android:
            try:
                self.min_workers = cpu_count()
            except NotImplementedError:
                self.min_workers =4
            logger.info("Using min workers : %s" % self.min_workers)

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
            logger.info("[%s] Setting our timezone to %s" %(self.name, use_timezone))
            os.environ['TZ'] = use_timezone
            time.tzset()

        logger.info("We have our schedulers : %s" % (str(self.schedulers)))

        # Now manage modules
        # TODO: check how to better handle this with modules_manager..
        mods = g_conf['modules']
        for module in mods:
            # If we already got it, bypass
            if not module.module_type in self.q_by_mod:
                logger.debug("Add module object %s" % str(module))
                self.modules_manager.modules.append(module)
                logger.info("[%s] Got module : %s " % (self.name, module.module_type))
                self.q_by_mod[module.module_type] = {}



    def main(self):
        try:
            for line in self.get_header():
                self.log.info(line)

            self.load_config_file()
        
            self.do_daemon_init_and_start()
        
            self.do_post_daemon_init()

            # We wait for initial conf
            self.wait_for_initial_conf()
            if not self.new_conf: # we must have either big problem or was requested to shutdown
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
                  logger.debug("The module %s is not a worker one, I remove it from the worker list" % mod)
                  del self.q_by_mod[mod]
                     

            # Now main loop
            self.do_mainloop()
        except Exception, exp:
            logger.error("I got an unrecoverable error. I have to exit")
            logger.error("You can log a bug ticket at https://github.com/naparuba/shinken/issues/new to get help")
            logger.error("Back trace of it: %s" % (traceback.format_exc()))
            raise


