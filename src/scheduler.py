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
import cPickle, zlib


from check import Check
from notification import Notification
from eventhandler import EventHandler
from brok import Brok
from downtime import Downtime
from comment import Comment
from log import Log

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
            0 : (self.update_downtimes_and_comments, 1),
            1 : (self.schedule, 1), #just schedule
            2 : (self.consume_results , 1), #incorpore checks and dependancies
            3 : (self.get_new_actions, 1), #now get the news actions (checks, notif) raised
            4 : (self.get_new_broks, 1), #and broks
            5 : (self.delete_zombie_checks, 1),
            6 : (self.delete_zombie_actions, 1),
            #3 : (self.delete_unwanted_notifications, 1),
            7 : (self.check_freshness, 10),
            8 : (self.clean_caches, 1),
            9 : (self.update_retention_file, 3600),
            10 : (self.check_orphaned, 60),
            #For NagVis like tools : udpdate our status every 10s
            11 : (self.get_and_register_update_program_status_brok, 10) 
            }

        #stats part
        self.nb_checks_send = 0
        self.nb_actions_send = 0
        self.nb_broks_send = 0
        self.nb_check_received = 0

        #Log init
        self.log = Log()
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
        self.conf = conf
        self.hostgroups = conf.hostgroups
        self.services = conf.services
        #We need reversed list for search in the retention
        #file read
        self.services.create_reversed_list()
        self.services.optimize_service_search(conf.hosts)
        self.hosts = conf.hosts
        self.hosts.create_reversed_list()
        self.contacts = conf.contacts
        self.contactgroups = conf.contactgroups
        self.servicegroups = conf.servicegroups
        self.timeperiods = conf.timeperiods
        self.commands = conf.commands

        #self.status_file = StatusFile(self)        #External status file
        self.instance_id = conf.instance_id #From Arbiter. Use for 
                                            #Broker to disting betweens
                                            #schedulers
        #self for instance_name
        self.instance_name = conf.instance_name


    #Oh... Arbiter want us to die... For launch a new Scheduler
    #"Mais qu'a-t-il de plus que je n'ais pas?"
    def die(self):
        self.must_run = False


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        #self.fifo = e.open()


    #We've got activity in the fifo, we get and run commands
    def run_external_command(self, command):
        print "scheduler resolves command", command
        self.external_command.resolve_command(command)


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
            print "Add an event Handler", elt.id
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
            Log().log("WARNING: We drop %d checks, %d broks and %d actions" % (nb_checks_drops, nb_broks_drops, nb_actions_drops))

            
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
                #If the command is untagged, and the poller too, or if both are taggued
                #with same name, go for it
                if (c.poller_tag == None and poller_tags == []) or c.poller_tag in poller_tags:
                    if c.status == 'scheduled' and c.is_launchable(now):
                        c.status = 'inpoller'
                        #We do not send c, because it it link (c.ref) to 
                        #host/service and poller do not need it. It just
                        #need a shell with id, command and defaults
                        #parameters. It's the goal of copy_shell
                        res.append(c.copy_shell())

        #If poller want to notify too
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
                            if len(childnotifications) != 0:
                                # notif_nb of the master notification was already current_notification_number+1.
                                # If notifications were sent, then host/service-counter will also be incremented
                                item.current_notification_number = a.notif_nb
                        
                            if item.notification_interval != 0:
                                # We must continue to send notifications.
                                # Just leave it in the actions list and set it to "scheduled" and it will be found again later
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
            except KeyError as exp:
                Log().log("Warning : received an notification of an unknown id! %s" % str(exp))

        elif c.is_a == 'check':
            try:
                self.checks[c.id].get_return_from(c)
                self.checks[c.id].status = 'waitconsume'
            except KeyError as exp:
                Log().log("Warning : received an check of an unknown id! %s" % str(exp))
        elif c.is_a == 'eventhandler':
            #It just die
            self.actions[c.id].status = 'zombie'
        else:
            Log().log("Error : the received result type in unknown ! %s" % str(c.is_a))


    #Call by brokers to have broks
    #We give them, and clean them!
    def get_broks(self):
        res = self.broks
        #They are gone, we keep none!
        self.broks = {}
        return res
    
    
    #Update the retention file and give it all of ours data in
    #a dict so read can pickup what it wants
    #For now compression is no use, but it can be add easylly 
    #just uncomment :)
    def update_retention_file(self):
        try:
            f = open(self.conf.state_retention_file, 'wb')
            #Just put hosts/services becauses checks and notifications
            #are already link into
            all_data = {'hosts' : self.hosts, 'services' : self.services}
            #s = cPickle.dumps(all_data)
            #s_compress = zlib.compress(s)
            cPickle.dump(all_data, f)
            #f.write(s_compress)
            f.close()
        except IOError as exp:
            Log().log("Error: retention file creation failed, %s" % str(exp))
            return
        Log().log("Updating retention_file %s" % self.conf.state_retention_file)
     
   
    #Load the retention file and get status from it. It do not get all checks in progress
    #for the moment, just the status and the notifications.
    #TODO : speed up because the service lookup si VERY slow
    def retention_load(self):
        Log().log("Reading from retention_file %s" % self.conf.state_retention_file)
        try:
            f = open(self.conf.state_retention_file, 'rb')
            all_data = cPickle.load(f)
            f.close()
        except EOFError as exp:
            print exp
            return
        except ValueError as exp:
            print exp
            return
        except IOError as exp:
            print exp
            return
        except IndexError as exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            Log().log(s)
            return
        except TypeError as exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            Log().log(s)
            return

            
            
        #Now load interesting properties in hosts/services
        #Taging prop that not be directly load
        #Items will be with theirs status, but not in checking, so
        #a new check will be launch like with a normal begining (random distributed
        #scheduling)
        not_loading = ['act_depend_of', 'chk_depend_of', 'checks_in_progress', \
                           'downtimes', 'host', 'next_chk', 'act_depend_of_me', \
                           'chk_depend_of_me', 'services']

        ret_hosts = all_data['hosts']
        for ret_h in ret_hosts:
            h = self.hosts.find_by_name(ret_h.host_name)
            if h != None:
                running_properties = h.__class__.running_properties
                for prop in running_properties:
                    if prop not in not_loading:
                        setattr(h, prop, getattr(ret_h, prop))
                        for a in h.notifications_in_progress.values():
                            a.ref = h
                            self.add(a)
                        h.update_in_checking()

        ret_services = all_data['services']
        for ret_s in ret_services:
            s = self.services.find_srv_by_name_and_hostname(ret_s.host_name, ret_s.service_description)
            if s != None:
                running_properties = s.__class__.running_properties
                for prop in running_properties:
                    if prop not in not_loading:
                        setattr(s, prop, getattr(ret_s, prop))
                        for a in s.notifications_in_progress.values():
                            a.ref = s
                            self.add(a)
                        s.update_in_checking()
        Log().log("We've load data from retention")


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

        Log().log("Created initial Broks: %d" % len(self.broks))
        
    
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
                "program_start" : now,
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
                Log().log("Warning : the results of check %d never came back. I'm reenable it for polling" % c.id)
                c.status = 'scheduled'
        for a in self.actions.values():
            if a.status == 'inpoller' and a.t_to_go < now - 300:
                Log().log("Warning : the results of action %d never came back. I'm reenable it for polling" % a.id)
                a.status = 'scheduled'


    #Main function
    def run(self):
        #First we see if we've got info in the retention file
        self.retention_load()

        #Ok, now all is initilised, we can make the inital broks
        self.fill_initial_broks()

        Log().log("First scheduling")
        self.schedule()
        Log().log("Done")
        #Ticks is for recurrent function call like consume
        #del zombies etc
        ticks = 0
        timeout = 1.0 #For the select

        gogogo = time.time()

        while self.must_run :
            socks = self.daemon.getServerSockets()
            avant = time.time()
            #socks.append(self.fifo)
            # 'foreign' event loop
            ins,outs,exs = select.select(socks,[],[],timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        #If FIFO, read external command
                        #if s == self.fifo:
                        #    self.external_command.read_and_interpret()
                        #    self.fifo = self.external_command.open()
                        #Must be paquet from poller
                        #else:
                        self.daemon.handleRequests()
                        apres = time.time()
                        diff = apres-avant
                        timeout = timeout - diff
                        break    # no need to continue with the for loop
            else: #Timeout
                timeout = 1.0
                ticks += 1
                #Do reccurent works like schedule, consume
                #delete_zombie_checks
                for i in self.recurrent_works:
                    (f, nb_ticks) = self.recurrent_works[i]
                    if ticks % nb_ticks == 0:
                        #print "I run function :", f.func_name
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
