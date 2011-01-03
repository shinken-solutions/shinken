#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


import select, time, os

import shinken.pyro_wrapper as pyro

from shinken.external_command import ExternalCommand
from shinken.check import Check
from shinken.notification import Notification
from shinken.eventhandler import EventHandler
from shinken.brok import Brok
from shinken.downtime import Downtime
from shinken.comment import Comment
from shinken.log import logger



#from guppy import hpy

class Scheduler:
    def __init__(self, daemon):
        self.daemon = daemon #Pyro daemon for incomming orders/askings
        self.must_run = True #When set to false by us, we die and
                             #arbiter launch a new Scheduler

        self.waiting_results = [] #satellites returns us results
        #and for not waiting them, we are putting them here and
        #consume thems later

        #Every N seconds we call functions like consume, del zombies
        #etc. All of theses functions are in recurrent_works with the
        #every tick to run. So must be integer and > 0
        #The order is important, so make key a int.
        #TODO : at load, change value by configuration one (like reaper time, etc)
        self.recurrent_works = {
            0 : ('update_downtimes_and_comments', self.update_downtimes_and_comments, 1),
            1 : ('schedule', self.schedule, 1), #just schedule
            2 : ('consume_results', self.consume_results , 1), #incorpore checks and dependancies
            3 : ('get_new_actions', self.get_new_actions, 1), #now get the news actions (checks, notif) raised
            4 : ('get_new_broks', self.get_new_broks, 1), #and broks
            5 : ('delete_zombie_checks', self.delete_zombie_checks, 1),
            6 : ('delete_zombie_actions', self.delete_zombie_actions, 1),
            #3 : (self.delete_unwanted_notifications, 1),
            7 : ('check_freshness', self.check_freshness, 10),
            8 : ('clean_caches', self.clean_caches, 1),
            9 : ('update_retention_file', self.update_retention_file, 3600),
            10 : ('check_orphaned', self.check_orphaned, 60),
            #For NagVis like tools : udpdate our status every 10s
            11 : ('get_and_register_update_program_status_brok', self.get_and_register_update_program_status_brok, 10),
            #Check for system time change. And AFTER get new checks
            #so they are changed too.
            12 : ('check_for_system_time_change', self.check_for_system_time_change, 1),
            #launch if need all internal checks
            13 : ('manage_internal_checks', self.manage_internal_checks, 1),
            }

        #stats part
        self.nb_checks_send = 0
        self.nb_actions_send = 0
        self.nb_broks_send = 0
        self.nb_check_received = 0

        #Log init
        self.log = logger
        self.log.load_obj(self)

        self.instance_id = 0 # Temporary set. Will be erase later
        #Ours queues
        self.checks = {}
        self.actions = {}
        self.downtimes = {}
        self.comments = {}
        self.broks = {}
        self.has_full_broks = False #have a initial_broks in broks queue?



    #Load conf for future use
    def load_conf(self, conf):
        self.program_start = int(time.time())
        self.conf = conf
        self.hostgroups = conf.hostgroups
        self.hostgroups.create_reversed_list()
        self.services = conf.services
        #We need reversed list for search in the retention
        #file read
        self.services.create_reversed_list()
        self.services.optimize_service_search(conf.hosts)
        self.hosts = conf.hosts
        #DBG:
#        for h in self.hosts:
#            print h.get_name(), h.parents
        self.hosts.create_reversed_list()

        self.notificationways = conf.notificationways
        self.contacts = conf.contacts
        self.contacts.create_reversed_list()
        self.contactgroups = conf.contactgroups
        self.contactgroups.create_reversed_list()
        self.servicegroups = conf.servicegroups
        self.servicegroups.create_reversed_list()
        self.timeperiods = conf.timeperiods
        self.timeperiods.create_reversed_list()
        self.commands = conf.commands

        #self.status_file = StatusFile(self)        #External status file
        self.instance_id = conf.instance_id #From Arbiter. Use for
                                            #Broker to disting betweens
                                            #schedulers
        #self for instance_name
        self.instance_name = conf.instance_name

        #Now we can updte our 'ticks' for special calls
        #like the retention one, etc
        self.update_recurrent_works_tick('update_retention_file', self.conf.retention_update_interval)


    #Update the 'tick' for a function call in our
    #recurrent work
    def update_recurrent_works_tick(self, f_name, new_tick):
        for i in self.recurrent_works:
            (name, f, old_tick) = self.recurrent_works[i]
            if name == f_name:
                print "Changing the tick for the function", name, new_tick
                self.recurrent_works[i] = (name, f, new_tick)


    #Load the modules from our app master
    def load_modules(self, modules_manager, mod_instances):
        self.modules_manager = modules_manager
        self.mod_instances = mod_instances


    #Oh... Arbiter want us to die... For launch a new Scheduler
    #"Mais qu'a-t-il de plus que je n'ais pas?"
    def die(self):
        #first update our retention data
        self.update_retention_file(forced=True)
        self.must_run = False


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e


    #We've got activity in the fifo, we get and run commands
    def run_external_command(self, command):
        print "scheduler resolves command", command
        ext_cmd = ExternalCommand(command)
        self.external_command.resolve_command(ext_cmd)


    #Schedulers have some queues. We can simplify call by adding
    #elements into the proper queue just by looking at their type
    #Brok -> self.broks
    #Check -> self.checks
    #Notification -> self.actions
    #Downtime -> self.downtimes
    def add(self, elt):
        #For checks and notif, add is also an update function
        if isinstance(elt, Check):
            self.checks[elt.id] = elt
            #A new check mean the host/service change it's next_check
            #need to be refresh
            b = elt.ref.get_next_schedule_brok()
            self.add(b)
            return
        if isinstance(elt, Brok):
            #For brok, we TAG brok with our instance_id
            elt.data['instance_id'] = self.instance_id
            self.broks[elt.id] = elt
            return
        if isinstance(elt, Notification):
            self.actions[elt.id] = elt
            #A notification ask for a brok
            if elt.contact != None:
                b = elt.get_initial_status_brok()
                self.add(b)
            return
        if isinstance(elt, EventHandler):
            #print "Add an event Handler", elt.id
            self.actions[elt.id] = elt
            return
        if isinstance(elt, Downtime):
            self.downtimes[elt.id] = elt
            self.add(elt.extra_comment)
            return
        if isinstance(elt, Comment):
            self.comments[elt.id] = elt
            b = elt.ref.get_update_status_brok()
            self.add(b)
            return


    #Ours queues may explode if noone ask us for elements
    #It's very dangerous : you can crash your server... and it's a bad thing :)
    #So we 'just' keep last elements : 2 of max is a good overhead
    def clean_queues(self):
        max_checks = 2 * (len(self.hosts) + len(self.services))
        max_broks = 2 * (len(self.hosts) + len(self.services))
        max_actions = 2* len(self.contacts) * (len(self.hosts) + len(self.services))

        #For checks, it's not very simple:
        #For checks, they may be referred to their host/service
        #We do not just del them in checks, but also in their service/host
        #We want id of less than max_id - 2*max_checks
        if len(self.checks) > max_checks:
            id_max = self.checks.keys()[-1] #The max id is the last id
                                            #: max is SO slow!
            to_del_checks = [c for c in self.checks.values() if c.id < id_max - max_checks]
            nb_checks_drops = len(to_del_checks)
            if nb_checks_drops > 0:
                print "I have to del some checks..., sorry", to_del_checks
            for c in to_del_checks:
                i = c.id
                elt = c.ref
                #First remove the link in host/service
                elt.remove_in_progress_check(c)
                #Then in dependant checks (I depend on, or check
                #depend on me)
                for dependant_checks in c.depend_on_me:
                    dependant_checks.depend_on.remove(c.id)
                for c_temp in c.depend_on:
                    c_temp.depen_on_me.remove(c)
                del self.checks[i] #Final Bye bye ...
        else:
            nb_checks_drops = 0

        #For broks and actions, it's more simple
        if len(self.broks) > max_broks:
            id_max = self.broks.keys()[-1]
            id_to_del_broks = [i for i in self.broks if i < id_max - max_broks]
            nb_broks_drops = len(id_to_del_broks)
            for i in id_to_del_broks:
                del self.broks[i]
        else:
            nb_broks_drops = 0

        if len(self.actions) > max_actions:
            id_max = self.actions.keys()[-1]
            id_to_del_actions = [i for i in self.actions if i < id_max - max_actions]
            nb_actions_drops = len(id_to_del_actions)
            for i in id_to_del_actions:
                #Remeber to delete reference of notification in service/host
                if i.is_a == 'notification':
                    item = self.actions[i].ref
                    item.remove_in_progress_notification(self.actions[i])
                    del self.actions[i]
        else:
            nb_actions_drops = 0

        if nb_checks_drops != 0 or nb_broks_drops != 0 or nb_actions_drops != 0:
            print "WARNING: We drop %d checks, %d broks and %d actions" % (nb_checks_drops, nb_broks_drops, nb_actions_drops)
            logger.log("WARNING: We drop %d checks, %d broks and %d actions" % (nb_checks_drops, nb_broks_drops, nb_actions_drops))


    #For tunning purpose we use caches but we do not whant them to explode
    #So we clean thems
    def clean_caches(self):
        #print "********** Clean caches *********"
        for tp in self.timeperiods:
            tp.clean_cache()


    #Ask item (host or service) a update_status
    #and add it to our broks queue
    def get_and_register_status_brok(self, item):
        b = item.get_update_status_brok()
        self.add(b)


    #Ask item (host or service) a check_result_brok
    #and add it to our broks queue
    def get_and_register_check_result_brok(self, item):
        b = item.get_check_result_brok()
        self.add(b)


    #We do not want this downtime id
    def del_downtime(self, dt_id):
        if dt_id in self.downtimes:
            self.downtimes[dt_id].ref.del_downtime(dt_id)
            del self.downtimes[dt_id]


    #We do not want this comment id
    def del_comment(self, c_id):
        if c_id in self.comments:
            self.comments[c_id].ref.del_comment(c_id)
            del self.comments[c_id]


    #Called by poller to get checks
    #Can get checks and actions (notifications and co)
    def get_to_run_checks(self, do_checks=False, do_actions=False, poller_tags=[]):
        res = []
        now = time.time()

        #If poller want to do checks
        if do_checks:
            for c in self.checks.values():
                # If the command is untagged, and the poller too, or if both are taggued
                # with same name, go for it
                if (c.poller_tag == None and poller_tags == []) or c.poller_tag in poller_tags:
                    # must be ok to launch, and not an internal one (business rules based)
                    if c.status == 'scheduled' and c.is_launchable(now) and not c.internal:
                        c.status = 'inpoller'
                        # We do not send c, because it it link (c.ref) to
                        # host/service and poller do not need it. It just
                        # need a shell with id, command and defaults
                        # parameters. It's the goal of copy_shell
                        res.append(c.copy_shell())

        #If reactionner want to notify too
        if do_actions:
            for a in self.actions.values():
                if a.status == 'scheduled' and a.is_launchable(now):
                    a.status = 'inpoller'
                    if a.is_a == 'notification' and not a.contact:
                        # This is a "master" notification created by create_notifications. It will not be sent itself because it has no contact.
                        # We use it to create "child" notifications (for the contacts and notification_commands) which are executed in the reactionner.
                        item = a.ref
                        childnotifications = []
                        if not item.notification_is_blocked_by_item(a.type, now):
                            # If it is possible to send notifications of this type at the current time, then create
                            # a single notification for each contact of this item.
                            childnotifications = item.scatter_notification(a)
                            for c in childnotifications:
                                c.status = 'inpoller'
                                self.add(c) # this will send a brok
                                new_c = c.copy_shell()
                                res.append(new_c)

                        # If we have notification_interval then schedule the next notification (problems only)
                        if a.type == 'PROBLEM':
                            # Update the ref notif number after raise the one of the notification
                            if len(childnotifications) != 0:
                                # notif_nb of the master notification was already current_notification_number+1.
                                # If notifications were sent, then host/service-counter will also be incremented
                                item.current_notification_number = a.notif_nb
                            
                            if item.notification_interval != 0 and a.t_to_go != None:
                                # We must continue to send notifications.
                                # Just leave it in the actions list and set it to "scheduled" and it will be found again later
#                               if a.t_to_go == None or item.notification_interval == None:
#                                       print "A to go", a, a.t_to_go, item.notification_interval
                                a.t_to_go = a.t_to_go + item.notification_interval * item.__class__.interval_length
                                
                                a.notif_nb = item.current_notification_number + 1
                                a.status = 'scheduled'
                            else:
                                # Wipe out this master notification. One problem notification is enough.
                                item.remove_in_progress_notification(a)
                                self.actions[a.id].status = 'zombie'

                        else:
                            # Wipe out this master notification. We don't repeat recover/downtime/flap/etc...
                            item.remove_in_progress_notification(a)
                            self.actions[a.id].status = 'zombie'
                    else:
                        # This is for child notifications and eventhandlers
                        new_a = a.copy_shell()
                        res.append(new_a)
        return res


    #Called by poller and reactionner to send result
    def put_results(self, c):
        if c.is_a == 'notification':
            # We will only see childnotifications here
            try:
                self.actions[c.id].get_return_from(c)
                item = self.actions[c.id].ref
                item.remove_in_progress_notification(c)
                self.actions[c.id].status = 'zombie'
                item.last_notification = c.check_time
                #If we' ve got a problem with the notification, raise a Warning log
                if c.exit_status != 0:
                    logger.log("Warning : the notification command '%s' raised an error (exit code=%d) : '%s'" % (c.command, c.exit_status, c.output))
            except KeyError , exp:
                logger.log("Warning : received an notification of an unknown id! %s" % str(exp))

        elif c.is_a == 'check':
            try:
                self.checks[c.id].get_return_from(c)
                self.checks[c.id].status = 'waitconsume'
            except KeyError , exp:
                logger.log("Warning : received an check of an unknown id! %s" % str(exp))
        elif c.is_a == 'eventhandler':
            # It just die
            try:
                self.actions[c.id].status = 'zombie'
            # Maybe we reveied a return of a old even handler, so we can forget it
            except KeyError:
                pass
        else:
            logger.log("Error : the received result type in unknown ! %s" % str(c.is_a))


    # Some checks are purely internal, like business based one
    # simply ask their ref to manage it when it's ok to run
    def manage_internal_checks(self):
        now = time.time()
        for c in self.checks.values():
            # must be ok to launch, and not an internal one (business rules based)
            if c.status == 'scheduled' and c.is_launchable(now) and c.internal:
                c.ref.manage_internal_check(c)
                # it manage it, now just ask to consume it
                # like for all checks
                c.status = 'waitconsume'



    #Call by brokers to have broks
    #We give them, and clean them!
    def get_broks(self):
        res = self.broks
        #They are gone, we keep none!
        self.broks = {}
#       print "returning broks"
#       for b in res:
#               print b, res[b]
        return res


    #Update the retention file and give it all of ours data in
    #a dict so read can pickup what it wants
    #For now compression is no use, but it can be add easylly
    #just uncomment :)
    def update_retention_file(self, forced=False):
        #If we set the update to 0, we do not want of this
        #if we do not forced (like at stopping)
        if self.conf.retention_update_interval == 0 and not forced:
            return

        #Do the job for all modules that do the retention
        for inst in self.mod_instances:
            if 'retention' in inst.properties['phases']:
                #Ask it with self to they have full access, and a log object
                #so they can easily raise log
                inst.update_retention_objects(self, logger)



    #Load the retention file and get status from it. It do not get all checks in progress
    #for the moment, just the status and the notifications.
    def retention_load(self):
        #Do this job with modules too
        for inst in self.mod_instances:
            if 'retention' in inst.properties['phases']:
                #give us ourself (full control!) and a log manager object
                b = inst.load_retention_objects(self, logger)
                #Stop at the first module that succeed to load the retention
                if b:
                    return


    def check_for_system_time_change(self):
        now = time.time()
        difference = now - self.t_each_loop
        #If we have more than 15 min time change, we need to compensate
        #it
        if abs(difference) > 900:
            self.compensate_system_time_change(difference)

        #Now set the new value for the tick loop
        self.t_each_loop = now


    #If we've got a system time change, we need to compensate it
    #So change our value, and all checks/notif ones
    def compensate_system_time_change(self, difference):
        logger.log('Warning: A system time change of %s has been detected.  Compensating...' % difference)
        #We only need to change some value
        self.program_start = max(0, self.program_start + difference)

        #Then we compasate all host/services
        for h in self.hosts:
            h.compensate_system_time_change(difference)
        for s in self.services:
            s.compensate_system_time_change(difference)

        #Now all checks and actions
        for c in self.checks.values():
            #Already launch checks should not be touch
            if c.status == 'scheduled':
                t_to_go = c.t_to_go
                ref = c.ref
                new_t = max(0, t_to_go + difference)
                #But it's no so simple, we must match the timeperiod
                new_t = ref.check_period.get_next_valid_time_from_t(new_t)
                #But maybe no there is no more new value! Not good :(
                #Say as error, with error output
                if new_t == None:
                    c.state = 'waitconsume'
                    c.exit_status = 2
                    c.output = '(Error: there is no available check time after time change!)'
                    c.check_time = time.time()
                    c.execution_time == 0
                else:
                    c.t_to_go = new_t
                    ref.next_chk = new_t

        #Now all checks and actions
        for c in self.actions.values():
            #Already launch checks should not be touch
            if c.status == 'scheduled':
                t_to_go = c.t_to_go

                # Event handler do not have ref
                ref = getattr(c, 'ref', None)
                new_t = max(0, t_to_go + difference)

                #Notification should be check with notification_period
                if c.is_a == 'notification':
                    #But it's no so simple, we must match the timeperiod
                    new_t = ref.notification_period.get_next_valid_time_from_t(new_t)

                #But maybe no there is no more new value! Not good :(
                #Say as error, with error output
                if new_t == None:
                    c.state = 'waitconsume'
                    c.exit_status = 2
                    c.output = '(Error: there is no available check time after time change!)'
                    c.check_time = time.time()
                    c.execution_time == 0
                else:
                    c.t_to_go = new_t


    #Fill the self.broks with broks of self (process id, and co)
    #broks of service and hosts (initial status)
    def fill_initial_broks(self):
        #First a Brok for delete all from my instance_id
        b = Brok('clean_all_my_instance_id', {'instance_id' : self.instance_id})
        self.add(b)

        #first the program status
        b = self.get_program_status_brok()
        self.add(b)

        #We cant initial_status from all this types
        #The order is important, service need host...
        initial_status_types = [self.timeperiods, self.commands, \
                                    self.contacts, self.contactgroups, \
                                    self.hosts, self.hostgroups,  \
                                    self.services, self.servicegroups]

        for tab in initial_status_types:
            for i in tab:
                b = i.get_initial_status_brok()
                self.add(b)

        #We now have all full broks
        self.has_full_broks = True

        logger.log("[%s] Created initial Broks: %d" % (self.instance_name, len(self.broks)))


    #Crate a brok with program status info
    def get_and_register_program_status_brok(self):
        b = self.get_program_status_brok()
        self.add(b)


    #Crate a brok with program status info
    def get_and_register_update_program_status_brok(self):
        b = self.get_program_status_brok()
        b.type = 'update_program_status'
        self.add(b)


    #Get a brok with program status
    #TODO : GET REAL VALUES
    def get_program_status_brok(self):
        now = int(time.time())
        data = {"is_running" : 1,
                "instance_id" : self.instance_id,
                "instance_name": self.instance_name,
                "last_alive" : now,
                "program_start" : self.program_start,
                "pid" : os.getpid(),
                "daemon_mode" : 1,
                "last_command_check" : now,
                "last_log_rotation" : now,
                "notifications_enabled" : self.conf.enable_notifications,
                "active_service_checks_enabled" : self.conf.execute_service_checks,
                "passive_service_checks_enabled" : self.conf.accept_passive_service_checks,
                "active_host_checks_enabled" : self.conf.execute_host_checks,
                "passive_host_checks_enabled" : self.conf.accept_passive_host_checks,
                "event_handlers_enabled" : self.conf.enable_event_handlers,
                "flap_detection_enabled" : self.conf.enable_flap_detection,
                "failure_prediction_enabled" : 0,
                "process_performance_data" : self.conf.process_performance_data,
                "obsess_over_hosts" : self.conf.obsess_over_hosts,
                "obsess_over_services" : self.conf.obsess_over_services,
                "modified_host_attributes" : 0,
                "modified_service_attributes" : 0,
                "global_host_event_handler" : self.conf.global_host_event_handler,
                'global_service_event_handler' : self.conf.global_service_event_handler,
                'command_file' : self.conf.command_file
                }
        b = Brok('program_status', data)
        return b



    #Called every 1sec to consume every result in services or hosts
    #with theses results, they are OK, CRITCAL, UP/DOWN, etc...
    def consume_results(self):
        #All results are in self.waiting_results
        #We need to get thems first
        for c in self.waiting_results:
            self.put_results(c)
        self.waiting_results = []

        #Then we consume thems
        #print "**********Consume*********"
        for c in self.checks.values():
            if c.status == 'waitconsume':
                item = c.ref
                item.consume_result(c)


        #All 'finished' checks (no more dep) raise checks they depends on
        for c in self.checks.values():
            if c.status == 'havetoresolvedep':
                for dependant_checks in c.depend_on_me:
                    #Ok, now dependant will no more wait c
                    dependant_checks.depend_on.remove(c.id)
                #REMOVE OLD DEP CHECL -> zombie
                c.status = 'zombie'

        #Now, reinteger dep checks
        for c in self.checks.values():
            if c.status == 'waitdep' and len(c.depend_on) == 0:
                item = c.ref
                item.consume_result(c)



    #Called every 1sec to delete all checks in a zombie state
    #zombie = not usefull anymore
    def delete_zombie_checks(self):
        #print "**********Delete zombies checks****"
        id_to_del = []
        for c in self.checks.values():
            if c.status == 'zombie':
                id_to_del.append(c.id)
        #une petite tape dans le dot et tu t'en vas, merci...
        for id in id_to_del:
            del self.checks[id] # ZANKUSEN!


    #Called every 1sec to delete all actions in a zombie state
    #zombie = not usefull anymore
    def delete_zombie_actions(self):
        #print "**********Delete zombies actions****"
        id_to_del = []
        for a in self.actions.values():
            if a.status == 'zombie':
                id_to_del.append(a.id)
        #une petite tape dans le doc et tu t'en vas, merci...
        for id in id_to_del:
            del self.actions[id] # ZANKUSEN!


    #Check for downtimes start and stop, and register
    #them if need
    def update_downtimes_and_comments(self):
        broks = []
        now = time.time()

        #Check maintenance periods
        for elt in [y for y in [x for x in self.hosts] + [x for x in self.services] if y.maintenance_period != None]:
            if not hasattr(elt, 'in_maintenance'):
                setattr(elt, 'in_maintenance', False)
            if not elt.in_maintenance:
                if elt.maintenance_period.is_time_valid(now):
                    start_dt = elt.maintenance_period.get_next_valid_time_from_t(now)
                    end_dt = elt.maintenance_period.get_next_invalid_time_from_t(start_dt + 1) - 1
                    dt = Downtime(elt, start_dt, end_dt, 1, 0, 0, "system", "this downtime was automatically scheduled through a maintenance_period")
                    elt.add_downtime(dt)
                    self.add(dt)
                    self.get_and_register_status_brok(elt)
                    elt.in_maintenance = dt.id
            else:
                if not elt.in_maintenance in self.downtimes:
                    # the maint downtimes has expired or was manually deleted
                    elt.in_maintenance = False

        #A loop where those downtimes are removed
        #which were marked for deletion (mostly by dt.exit())
        for dt in self.downtimes.values():
            if dt.can_be_deleted == True:
                ref = dt.ref
                self.del_downtime(dt.id)
                broks.append(ref.get_update_status_brok())

        #Downtimes are usually accompanied by a comment.
        #An exiting downtime also invalidates it's comment.
        for c in self.comments.values():
            if c.can_be_deleted == True:
                ref = c.ref
                self.del_comment(c.id)
                broks.append(ref.get_update_status_brok())

        #Check start and stop times
        for dt in self.downtimes.values():
            if dt.real_end_time < now:
                #this one has expired
                broks.extend(dt.exit()) # returns downtimestop notifications
            elif now >= dt.start_time and dt.fixed and not dt.is_in_effect:
                #this one has to start now
                broks.extend(dt.enter()) # returns downtimestart notifications
                broks.append(dt.ref.get_update_status_brok())

        for b in broks:
            self.add(b)


    #Main schedule function to make the regular scheduling
    def schedule(self):
        #ask for service and hosts their next check
        for type_tab in [self.services, self.hosts]:
            for i in type_tab:
                i.schedule()


    #Main actions reaper function : it get all new checks,
    #notification and event handler from hosts and services
    def get_new_actions(self):
        #ask for service and hosts their next check
        for type_tab in [self.services, self.hosts]:
            for i in type_tab:
                for a in i.actions:
                    self.add(a)
                #We take all, we can clear it
                i.actions = []


    #Same the just upper, but for broks
    def get_new_broks(self):
        #ask for service and hosts their broks waiting
        #be eaten
        for type_tab in [self.services, self.hosts]:
            for i in type_tab:
                for b in i.broks:
                    self.add(b)
                #We take all, we can clear it
                i.broks = []


    #Raise checks for no fresh states for services and hosts
    def check_freshness(self):
        #print "********** Check freshnesh******"
        for type_tab in [self.services, self.hosts]:
            for i in type_tab:
                c = i.do_check_freshness()
                if c is not None:
                    self.add(c)


    #Check for orphaned checks : checks that never returns back
    #so if inpoller and t_to_go < now - 300s : pb!
    def check_orphaned(self):
        now = int(time.time())
        for c in self.checks.values():
            if c.status == 'inpoller' and c.t_to_go < now - 300:
                logger.log("Warning : the results of check %d never came back. I'm reenable it for polling" % c.id)
                c.status = 'scheduled'
        for a in self.actions.values():
            if a.status == 'inpoller' and a.t_to_go < now - 300:
                logger.log("Warning : the results of action %d never came back. I'm reenable it for polling" % a.id)
                a.status = 'scheduled'





    #Main function
    def run(self):
        #Then we see if we've got info in the retention file
        self.retention_load()

        #Ok, now all is initilised, we can make the inital broks
        self.fill_initial_broks()

        logger.log("[%s] First scheduling launched" % self.instance_name)
        self.schedule()
        logger.log("[%s] First scheduling done" % self.instance_name)
        #Ticks is for recurrent function call like consume
        #del zombies etc
        ticks = 0
        timeout = 1.0 #For the select

        gogogo = time.time()
        self.t_each_loop = time.time() #use to track system time change

        while self.must_run :
            socks = pyro.get_sockets(self.daemon)
            t_begin = time.time()
            #socks.append(self.fifo)
            # 'foreign' event loop
            ins,outs,exs = select.select(socks,[],[],timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        pyro.handleRequests(self.daemon, s)
                        t_after = time.time()
                        diff = t_after-t_begin
                        timeout = timeout - diff
                        break    # no need to continue with the for loop
            else: #Timeout
                timeout = 1.0
                ticks += 1

                #Do reccurent works like schedule, consume
                #delete_zombie_checks
                for i in self.recurrent_works:
                    (name, f, nb_ticks) = self.recurrent_works[i]
                    #A 0 in the tick will just disable it
                    if nb_ticks != 0:
                        if ticks % nb_ticks == 0:
                            #print "I run function :", name
                            f()

                #if  ticks % 10 == 0:
                #    self.conf.quick_debug()

                #stats
                nb_scheduled = len([c for c in self.checks.values() if c.status=='scheduled'])
                nb_inpoller = len([c for c in self.checks.values() if c.status=='inpoller'])
                nb_zombies = len([c for c in self.checks.values() if c.status=='zombie'])
                nb_notifications = len(self.actions)

                print "Checks:", "total", len(self.checks), "scheduled", nb_scheduled, "inpoller", nb_inpoller, "zombies", nb_zombies, "notifications", nb_notifications

                m = 0.0
                m_nb = 0
                for s in self.services:
                    m += s.latency
                    m_nb += 1
                if m_nb != 0:
                    print "Average latency:", m, m_nb,  m / m_nb

                #print "Notifications:", nb_notifications
                now = time.time()
                #for a in self.actions.values():
                #    if a.is_a == 'notification':
                #        print "Notif:", a.id, a.type, a.status, a.ref.get_name(), a.ref.state, a.contact.get_name(), 'level:%d' % a.notif_nb, 'launch in', int(a.t_to_go - now)
                #    else:
                #        print "Event:", a.id, a.status
                print "Nb checks send:", self.nb_checks_send
                self.nb_checks_send = 0
                print "Nb Broks send:", self.nb_broks_send
                self.nb_broks_send = 0

                time_elapsed = now - gogogo
                print "Check average =", int(self.nb_check_received / time_elapsed), "checks/s"

                #for n in  self.actions.values():
                #    if n.ref_type == 'service':
                #        print 'Service notification', n
                #    if n.ref_type == 'host':
                #        print 'Host notification', n
                #print "."
                #print "Service still in checking?"
                #for s in self.services:
                #    print s.get_name()+':'+str(s.in_checking)
                #    for i in s.checks_in_progress:
                #        print i, i.t_to_go
                #for s in self.hosts:
                #    print s.get_name()+':'+str(s.in_checking)+str(s.checks_in_progress)
                #    for i in s.checks_in_progress:
                #        print i#self.checks[i]

                #for c in self.checks.values():
                #    if c.ref_type == 'host':
                #        print c.id, ":", c.status, 'Depend_on_me:', len(c.depend_on_me), 'depend_on', c.depend_on
                #hp=hpy()
                #print hp.heap()
                #print hp.heapu()


            if timeout < 0:
                timeout = 1.0
