#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


""" 
This class is an interface for reactionner and poller
The satallite listen configuration from Arbiter in a port
the configuration gived by arbiter is schedulers where actionner will
take actions.

When already launch and have a conf, actionner still listen to arbiter
(one a timeout)

if arbiter want it to have a new conf, satellite forgot old schedulers
(and actions into) take new ones and do the (new) job.
"""


from multiprocessing import Queue, Manager, active_children
import os
import copy
import time
import sys
import cPickle
import random


try:
    import shinken.pyro_wrapper as pyro
except ImportError:
    sys.exit("Shinken require the Python Pyro module. Please install it.")

Pyro = pyro.Pyro


from message import Message
from worker import Worker
from load import Load
from daemon import Daemon
from log import logger
from brok import Brok


# Interface for Arbiter, our big MASTER
# It put us our conf
class IForArbiter(Pyro.core.ObjBase):
    # We keep app link because we are just here for it
    def __init__(self, app):
        Pyro.core.ObjBase.__init__(self)
        self.app = app
        self.schedulers = app.schedulers
        self.app.modules = []
        

    # function called by arbiter for giving us our conf
    # conf must be a dict with:
    # 'schedulers' : schedulers dict (by id) with address and port
    # TODO: catch case where Arbiter send somethign we already have
    # (same id+add+port) -> just do nothing :)
    
    def put_conf(self, conf):
        # TODO: just save the conf, put a flag to say a new conf is there and return
        # and handle the setup of this new conf in the main satellite loop ?
        
        self.app.have_conf = True
        self.app.have_new_conf = True
        # Gout our name from the globals
        if 'poller_name' in conf['global']:
            name = conf['global']['poller_name']
        elif 'reactionner_name' in conf['global']:
            name = conf['global']['reactionner_name']
        else:
            name = 'Unnamed satellite'
        self.app.name = self.name = name

        print "[%s] Sending us a configuration %s " % (self.name, conf)
        # If we've got something in the schedulers, we do not want it anymore
        for sched_id in conf['schedulers'] :
            already_got = False
            if sched_id in self.schedulers:
                logger.log("[%s] We already got the conf %d (%s)" % (self.name, sched_id, conf['schedulers'][sched_id]['name']))
                already_got = True
                wait_homerun = self.schedulers[sched_id]['wait_homerun']
            s = conf['schedulers'][sched_id]
            self.schedulers[sched_id] = s

            uri = pyro.create_uri(s['address'], s['port'], 'Checks', self.app.use_ssl)
            print "DBG: scheduler UIR:", uri

            self.schedulers[sched_id]['uri'] = uri
            if already_got:
                self.schedulers[sched_id]['wait_homerun'] = wait_homerun
            else:
                self.schedulers[sched_id]['wait_homerun'] = {}
            self.schedulers[sched_id]['running_id'] = 0
            self.schedulers[sched_id]['active'] = s['active']

            # And then we connect to it :)
            self.app.pynag_con_init(sched_id)

        # Now the limit part
        self.app.max_workers = conf['global']['max_workers']
        self.app.min_workers = conf['global']['min_workers']
        self.app.passive = conf['global']['passive']
        print "Is passive?", self.app.passive
        self.app.processes_by_worker = conf['global']['processes_by_worker']
        self.app.polling_interval = conf['global']['polling_interval']
        if 'poller_tags' in conf['global']:
            self.app.poller_tags = conf['global']['poller_tags']
        else: # for reactionner, poler_tag is [None]
            self.app.poller_tags = []
        if 'max_plugins_output_length' in conf['global']:
            self.app.max_plugins_output_length = conf['global']['max_plugins_output_length']
        else: # for reactionner, we don't really care about it
            self.app.max_plugins_output_length = 8192
        print "Max output lenght" , self.app.max_plugins_output_length
        # Set our giving timezone from arbiter
        use_timezone = conf['global']['use_timezone']
        if use_timezone != 'NOTSET':
            logger.log("[%s] Setting our timezone to %s" %(self.name, use_timezone))
            os.environ['TZ'] = use_timezone
            time.tzset()

        logger.log("We have our schedulers : %s" % (str(self.schedulers)))

        # Now manage modules
        # TODO: check how to better handle this with modules_manager..
        mods = conf['global']['modules']
        for module in mods:
            # If we already got it, bypass
            if not module.module_type in self.app.worker_modules:
                print "Add module object", module
                self.app.modules_manager.modules.append(module)
                logger.log("[%s] Got module : %s " % (self.name, module.module_type))
                self.app.worker_modules[module.module_type] = {'to_q' : Queue()}



    # Arbiter ask us to do not manage a scheduler_id anymore
    # I do it and don't ask why
    def remove_from_conf(self, sched_id):
        try:
            del self.schedulers[sched_id]
        except KeyError:
            pass


    # Arbiter ask me which sched_id I manage, If it is not ok with it
    # It will ask me to remove one or more sched_id
    def what_i_managed(self):
        return self.schedulers.keys()


    # Use for arbiter to know if we are alive
    def ping(self):
        print "We ask us for a ping"
        return True


    # Use by arbiter to know if we have a conf or not
    # can be usefull if we must do nothing but
    # we are not because it can KILL US!
    def have_conf(self):
        return self.app.have_conf


    # Call by arbiter if it thinks we are running but we must do not (like
    # if I was a spare that take a conf but the master returns, I must die
    # and wait a new conf)
    # Us : No please...
    # Arbiter : I don't care, hasta la vista baby!
    # Us : ... <- Nothing! We are die! you don't follow
    # anything or what?? Reading code is not a job for eyes only...
    def wait_new_conf(self):
        print "Arbiter want me to wait a new conf"
        self.schedulers.clear()
        self.app.have_conf = False


# Interface for Schedulers
# If we are passive, they connect to this and
# send/get actions
class ISchedulers(Pyro.core.ObjBase):
    # we keep sched link
    def __init__(self, app):
        Pyro.core.ObjBase.__init__(self)
        self.app = app


    # Ping? Pong!
    def ping(self):
        return None


    # A Scheduler send me actions to do
    def push_actions(self, actions, sched_id):
        print "A scheduler sned me actions", actions
        self.app.add_actions(actions, sched_id)


    # A scheduler ask us its returns
    def get_returns(self, sched_id):
        print "A scheduler ask me the returns", sched_id
        ret = self.app.get_return_for_passive(sched_id)
        print "Send mack", len(ret), "returns"
        return ret


# Interface for Brokers
# They connect here and get all broks (data for brokers)
# datas must be ORDERED! (initial status BEFORE uodate...)
class IBroks(Pyro.core.ObjBase):
    # we keep sched link
    def __init__(self, app):
        Pyro.core.ObjBase.__init__(self)
        self.app = app
        self.running_id = random.random()


    # Broker need to void it's broks?
    def get_running_id(self):
        return self.running_id


    # poller or reactionner ask us actions
    def get_broks(self):
        # print "We ask us broks"
        res = self.app.get_broks()
        return res


    # Ping? Pong!
    def ping(self):
        return None



# Our main APP class
class Satellite(Daemon):
    def __init__(self, name, config_file, is_daemon, do_replace, debug, debug_file):
        
        self.check_shm()        
        
        Daemon.__init__(self, name, config_file, is_daemon, do_replace, debug, debug_file)
        
        # Keep broks so they can be eaten by a broker
        self.broks = {}

        # Ours schedulers
        self.schedulers = {}
        self.workers = {}   # dict of active workers

        self.nb_actions_in_workers = 0

        # Init stats like Load for workers
        self.wait_ratio = Load(initial_value=1)


        # Now the specific stuff
        # Bool to know if we have received conf from arbiter
        self.have_conf = False
        self.have_new_conf = False
        
        # Now we create the interfaces
        self.interface = IForArbiter(self)
        self.brok_interface = IBroks(self)
        self.scheduler_interface = ISchedulers(self)

        # Just for having these attributes defined here. explicit > implicit ;)
        self.uri2 = None
        self.uri3 = None
        self.s = None
        self.manager = None
        self.returns_queue = None

        self.worker_modules = {}


    def pynag_con_init(self, id):
        """ Initialize or re-initialize connexion with scheduler """
        sched = self.schedulers[id]
        # If sched is not active, I do not try to init
        # it is just useless
        if not sched['active']:
            return

        logger.log("[%s] Init de connexion with %s at %s" % (self.name, sched['name'], sched['uri']))
        running_id = sched['running_id']
        sch_con = sched['con'] = Pyro.core.getProxyForURI(sched['uri'])

        # timeout of 120 s
        # and get the running id
        try:
            pyro.set_timeout(sch_con, 5)
            new_run_id = sch_con.get_running_id()
        except (Pyro.errors.ProtocolError,Pyro.errors.NamingError, cPickle.PicklingError, KeyError, Pyro.errors.CommunicationError) , exp:
            logger.log("[%s] Scheduler %s is not initilised or got network problem: %s" % (self.name, sched['name'], str(exp)))
            sched['con'] = None
            return

        # The schedulers have been restart : it has a new run_id.
        # So we clear all verifs, they are obsolete now.
        if sched['running_id'] != 0 and new_run_id != running_id:
            logger.log("[%s] The running id of the scheduler %s changed, we must clear it's actions" % (self.name, sched['name']))
            sched['wait_homerun'].clear()
        sched['running_id'] = new_run_id
        logger.log("[%s] Connexion OK with scheduler %s" % (self.name, sched['name']))


    # Manage action return from Workers
    # We just put them into the sched they are for
    # and we clean unused properties like sched_id
    def manage_action_return(self, action):
        # Ok, it's a result. We get it, and fill verifs of the good sched_id
        sched_id = action.sched_id
        # Now we now where to put action, we do not need sched_id anymore
        del action.sched_id
        action.status = 'waitforhomerun'
        self.schedulers[sched_id]['wait_homerun'][action.get_id()] = action
        # We update stats
        self.nb_actions_in_workers =- 1


    # Return the chk to scheduler and clean them
    # REF: doc/shinken-action-queues.png (6)
    def manage_returns(self):
        total_sent = 0
        # Fot all schedulers, we check for waitforhomerun and we send back results
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
                except (Pyro.errors.ProtocolError, KeyError) , exp:
                    print exp
                    self.pynag_con_init(sched_id)
                    return
                except AttributeError , exp: # the scheduler must  not be initialized
                    print exp
                except Exception , exp:
                    print ''.join(Pyro.util.getPyroTraceback(exp))
                    sys.exit(0)

            # We clean ONLY if the send is OK
            if send_ok :
                sched['wait_homerun'].clear()
            else:
                self.pynag_con_init(sched_id)
                logger.log("Sent failed!")


    # Get all returning actions for a call from a
    # scheduler
    def get_return_for_passive(self, sched_id):
        # I do not know this scheduler?
        if sched_id not in self.schedulers:
            print "I do not know about the scheduler", sched_id
            return []

        sched = self.schedulers[sched_id]
        print "Preparing to return", sched['wait_homerun'].values()
        ret = copy.copy(sched['wait_homerun'].values())
        sched['wait_homerun'].clear()
        print "Finally return", ret
        return ret


    # Use to wait conf from arbiter.
    # It send us conf in our pyro_daemon. It put the have_conf prop
    # if he send us something
    # (it can just do a ping)
    def wait_for_initial_conf(self):
        logger.log("Waiting for initial configuration")
        timeout = 1.0
        # Arbiter do not already set our have_conf param
        while not self.have_conf and not self.interrupted:
            elapsed, _, _ = self.handleRequests(timeout)
            if elapsed:
                timeout -= elapsed
                if timeout > 0:
                    continue
            timeout = 1.0
            sys.stdout.write(".")
            sys.stdout.flush()
        
        if self.interrupted:
            self.request_stop()


    # The arbiter can resent us new conf in the pyro_daemon port.
    # We do not want to loose time about it, so it's not a bloking
    # wait, timeout = 0s
    # If it send us a new conf, we reinit the connexions of all schedulers
    def watch_for_new_conf(self, timeout):
        self.handleRequests(timeout)

        # have_new_conf is set with put_conf
        # so another handle will not make a con_init
        if self.have_new_conf:
            for sched_id in self.schedulers:
                print "Got a new conf"
                self.pynag_con_init(sched_id)
            self.have_new_conf = False
            

    # Create and launch a new worker, and put it into self.workers
    # It can be mortal or not
    def create_and_launch_worker(self, module_name='fork', mortal=True):
        q = self.worker_modules[module_name]['to_q']

        # If we are in the fork module, do not specify a target
        target = None
        if module_name == 'fork':
            target = None
        else:
            for module in self.modules_manager.instances:
                if module.properties['type'] == module_name:
                    target = module.work
            if target is None:
                return
        w = Worker(1, q, self.returns_queue, self.processes_by_worker, \
                   mortal=mortal,max_plugins_output_length = self.max_plugins_output_length, target=target )
        self.workers[w.id] = w
        logger.log("[%s] Allocating new %s Worker : %s" % (self.name, module_name, w.id))
        w.start()


    def do_stop(self):
        logger.log('Stopping all workers')
        for w in self.workers.values():
            try:
                w.terminate()
                w.join(timeout=1)
                # queue = w.return_queue
                # self.return_messages.remove(queue)
            except AttributeError: # A already die worker
                pass
            except AssertionError: # In a worker
                pass
        if self.pyro_daemon:
            logger.log('Stopping all network connexions')
            self.pyro_daemon.unregister(self.interface)
            self.pyro_daemon.unregister(self.brok_interface)
            self.pyro_daemon.unregister(self.scheduler_interface)
            self.pyro_daemon.shutdown(True)


    # A simple fucntion to add objects in self
    # like broks in self.broks, etc
    # TODO : better tag ID?
    def add(self, elt):
        if isinstance(elt, Brok):
            # For brok, we TAG brok with our instance_id
            elt.data['instance_id'] = 0
            self.broks[elt.id] = elt
            return


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
        # Active children make a join with every one, useful :)
        act = active_children()

        w_to_del = []
        for w in self.workers.values():
            # If a worker go down and we do not ask him, it's not
            # good : we can think having a worker and it's not True
            # So we del it
            if not w.is_alive():
                logger.log("[%s] Warning : the worker %s goes down unexpectly!" % (self.name, w.id))
                # AIM ... Press FIRE ... <B>HEAD SHOT!</B>
                w.terminate()
                w.join(timeout=1)
                w_to_del.append(w.id)
        # OK, now really del workers
        for id in w_to_del:
            del self.workers[id]


    # Here we create new workers if the queue load (len of verifs) is too long
    def adjust_worker_number_by_load(self):
        # TODO : get a real value for a load
        wish_worker = 1
        # I want at least min_workers or wish_workers (the biggest) but not more than max_workers
        while len(self.workers) < self.min_workers \
                    or (wish_worker > len(self.workers) and len(self.workers) < self.max_workers):
            for mod in self.worker_modules:
                self.create_and_launch_worker(module_name=mod)
        # TODO : if len(workers) > 2*wish, maybe we can kill a worker?


    # Get the Queue() from an action by looking at which module
    # it wants
    def _got_queue_from_action(self, a):
        if hasattr(a, 'module_type'):
            if a.module_type in self.worker_modules:
                if a.module_type != 'fork':
                    print "GOT A SPECIAL QUEUE (%s) for" % a.module_type, a.__dict__, 
                return self.worker_modules[a.module_type]['to_q']
            # Nothing found, it's not good at all!
            return None
        # If none, call the standard 'fork'
        return self.worker_modules['fork']['to_q']


    # Add to our queues a list of actions
    def add_actions(self, lst, sched_id):
        for a in lst:
            a.sched_id = sched_id
            a.status = 'queue'
            msg = Message(id=0, type='Do', data=a)
            q = self._got_queue_from_action(a)
            if q != None:
                q.put(msg)
            # Update stats
            self.nb_actions_in_workers += 1


    # We get new actions from schedulers, we create a Message ant we
    # put it in the s queue (from master to slave)
    # REF: doc/shinken-action-queues.png (1)
    def get_new_actions(self):
        # Here are the differences between a
        # poller and a reactionner:
        # Poller will only do checks,
        # reactionner do actions
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
                    tmp = con.get_checks(do_checks=do_checks, do_actions=do_actions, poller_tags=self.poller_tags)
                    print "Ask actions to", sched_id, "got", len(tmp)
                    # We 'tag' them with sched_id and put into queue for workers
                    # REF: doc/shinken-action-queues.png (2)
                    self.add_actions(tmp, sched_id)
                    #for a in tmp:
                    #    a.sched_id = sched_id
                    #    a.status = 'queue'
                    #    msg = Message(id=0, type='Do', data=a)
                    #    q = self._got_queue_from_action(a)
                    #    if q != None:
                    #        q.put(msg)
                    #    # Update stats
                    #    self.nb_actions_in_workers += 1
                else: # no con? make the connexion
                    self.pynag_con_init(sched_id)
            # Ok, con is not know, so we create it
            # Or maybe is the connexion lsot, we recreate it
            except (KeyError, Pyro.errors.ProtocolError) , exp:
                print exp
                self.pynag_con_init(sched_id)
            # scheduler must not be initialized
            # or scheduler must not have checks
            except (AttributeError, Pyro.errors.NamingError) , exp:
                print exp
            # What the F**k? We do not know what happenned,
            # so.. bye bye :)
            except Pyro.errors.ConnectionClosedError , exp:
                print exp
                self.pynag_con_init(sched_id)
            except Exception , exp:
                print ''.join(Pyro.util.getPyroTraceback(exp))
                sys.exit(0)


    def do_loop_turn(self):
        begin_loop = time.time()

        # Maybe the arbiter ask us to wait for a new conf
        # If true, we must restart all...
        if self.have_conf == False:
            print "Begin wait initial"
            self.wait_for_initial_conf()
            print "End wait initial"
            if not self.have_conf:  # we may have been interrupted or so; then just return from this loop turn
                return

            
        # Now we check if arbiter speek to us in the pyro_daemon.
        # If so, we listen for it
        # When it push us conf, we reinit connexions
        # Sleep in waiting a new conf :)
        self.watch_for_new_conf(self.timeout)

        # Manage a possible time change (our before will be change with the diff)
        diff = self.check_for_system_time_change()
        begin_loop += diff
        
        after = time.time()
        self.timeout -= after - begin_loop

        if self.timeout >= 0:
            return

        print " ======================== "
        after = time.time()
        self.timeout = self.polling_interval

        # Check if zombies workers are among us :)
        # If so : KILL THEM ALL!!!
        self.check_and_del_zombie_workers()

        # Print stats for debug
        for sched_id in self.schedulers:
            sched = self.schedulers[sched_id]
            for mod in self.worker_modules:
                # In workers we've got actions send to queue - queue size
                q = self.worker_modules[mod]['to_q']
                print '[%d][%s][%s]Stats : Workers:%d (Queued:%d Processing:%d ReturnWait:%d)' % \
                    (sched_id, sched['name'], mod, len(self.workers), q.qsize(), \
                         self.nb_actions_in_workers - q.qsize(), len(self.returns_queue))


        # Before return or get new actions, see how we manage
        # old ones : are they still in queue (s)? If True, we
        # must wait more or at least have more workers
        wait_ratio = self.wait_ratio.get_load()
        total_q = 0
        for mod in self.worker_modules:
            q = self.worker_modules[mod]['to_q']
            total_q += q.qsize()
        if total_q != 0 and wait_ratio < 5*self.polling_interval:
            print "I decide to up wait ratio"
            self.wait_ratio.update_load(wait_ratio * 2)
        else:
            # Go to self.polling_interval on normal run, if wait_ratio
            # was >5*self.polling_interval,
            # it make it come near 5 because if < 5, go up :)
            self.wait_ratio.update_load(self.polling_interval)
        wait_ratio = self.wait_ratio.get_load()
        print "Wait ratio:", wait_ratio

        # We can wait more than 1s if need,
        # no more than 5s, but no less than 1
        timeout = self.timeout * wait_ratio
        timeout = max(self.polling_interval, timeout)
        self.timeout = min(5*self.polling_interval, timeout)

        # Maybe we do not have enouth workers, we check for it
        # and launch new ones if need
        self.adjust_worker_number_by_load()

        # Manage all messages we've got in the last timeout
        # for queue in self.return_messages:
        while len(self.returns_queue) != 0:
            self.manage_action_return(self.returns_queue.pop())
            
        # If we are passive, we do not initiate the check getting
        # and return
        print "Am I passive?", self.passive
        if not self.passive:
            print "I try to get new actions!"
            # Now we can get new actions from schedulers
            self.get_new_actions()

            # We send all finished checks
            # REF: doc/shinken-action-queues.png (6)
            self.manage_returns()


    def do_post_daemon_init(self):
        """ Do this satellite (poller or reactionner) post "daemonize" init:
we must register our interfaces for 3 possible callers: arbiter, schedulers or brokers. """
        # And we register them
        self.uri2 = self.pyro_daemon.register(self.interface, "ForArbiter")
        self.uri3 = self.pyro_daemon.register(self.brok_interface, "Broks")
        self.uri4 = self.pyro_daemon.register(self.scheduler_interface, "Schedulers")
        
        # self.s = Queue() # Global Master -> Slave
        # We can open the Queeu for fork AFTER
        self.worker_modules['fork'] = {'to_q' : Queue()}
        self.manager = Manager()
        self.returns_queue = self.manager.list()


    def setup_new_conf(self):
        """ Setup the new received conf """
        pass


    def main(self):

        for line in self.get_header():
            self.log.log(line)

        self.do_load_config()
        
        self.do_daemon_init_and_start()
        
        self.do_post_daemon_init()

        # We wait for initial conf
        self.wait_for_initial_conf()

        if not self.have_conf: # we must have either big problem or was requested to shutdown
            return
        # We can load our modules now
        self.modules_manager.set_modules(self.modules)
        self.modules_manager.load_and_init()

        # Connexion init with scheduler servers
        for sched_id in self.schedulers:
            print "Init main"
            self.pynag_con_init(sched_id)
        self.have_new_conf = False

        # Allocate Mortal Threads
        for _ in xrange(1, self.min_workers):
            for mod in self.worker_modules:
                self.create_and_launch_worker(module_name=mod)

        # Now main loop
        self.timeout = self.polling_interval


        self.do_mainloop()

