#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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
from check import Check
from notification import Notification
from status import StatusFile
from brok import Brok
from downtime import Downtime


#from guppy import hpy

class Scheduler:
    def __init__(self, daemon):
        self.daemon = daemon #Pyro daemon for incomming orders/askings
        self.must_run = True #When set to false by us, we die and 
                             #arbiter launch a new Scheduler


    #Load conf for future use
    def load_conf(self, conf):
        self.conf = conf
        self.hostgroups = conf.hostgroups
        self.services = conf.services
        self.hosts = conf.hosts
        self.contacts = conf.contacts
        self.contactgroups = conf.contactgroups
        self.servicegroups = conf.servicegroups
        self.timeperiods = conf.timeperiods
        self.commands = conf.commands
        #Ours queues
        self.checks = {}
        self.actions = {}
        self.downtimes = {}
        self.broks = {}

        self.status_file = StatusFile(self)        #External status file
        self.instance_id = conf.instance_id #From Arbiter. Use for 
                                            #Broker to disting betweens
                                            #schedulers


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
            return
        if isinstance(elt, Brok):
            #For brok, we TAG brok with our instance_id
            elt.data['instance_id'] = self.instance_id
            self.broks[elt.id] = elt
            return
        if isinstance(elt, Notification):
            self.actions[elt.id] = elt
            return
        if isinstance(elt, Downtime):
            self.downtimes[elt.id] = elt
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
            #Actions are not refered in hosts/services :) so ...
            id_to_del_actions = [i for i in self.actions if i < id_max - max_actions]
            nb_actions_drops = len(id_to_del_actions)
            for i in id_to_del_actions:
                del self.actions[i]
        else:
            nb_actions_drops = 0
        
        if nb_checks_drops !=0 or nb_broks_drops != 0 or nb_actions_drops != 0:
            print "WARNING: We drop %d checks, %d broks and %d actions" % (nb_checks_drops, nb_broks_drops, nb_actions_drops)

            
    #For tunning purpose we use caches but we do not whant them to explode
    #So we clean thems
    def clean_caches(self):
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
        dt = self.downtimes[dt_id]
        dt.ref.del_downtime(dt_id)
        del self.downtimes[dt.id]


    #Called by poller to get checks
    #Can get checks and actions (notifications and co)
    def get_to_run_checks(self, do_checks=False, do_actions=False):
        res = []
        now = time.time()

        #If poller want to do checks
        if do_checks:
            for c in self.checks.values():
                if c.status == 'scheduled' and c.is_launchable(now):
                    c.status = 'inpoller'
                    #We do not send c, because it it link (c.ref) to host/service
                    #and poller do not need it. It just need a shell with id,
                    #command and defaults parameters. It's the goal of copy_shell
                    res.append(c.copy_shell())

        #If poller want to notify too
        if do_actions:
            for a in self.actions.values():
                if a.status == 'scheduled':
                    a.status = 'inpoller'
                    res.append(a.copy_shell())
        return res


    #Caled by poller and reactionner to send result
    def put_results(self, c):
        if c.is_a == 'notification':
            self.actions[c.id].get_return_from(c)
            #print "\n\n\nGetting  a NOTIFICATION RETURN \n\n\n"
            #print c.__dict__
            #print self.actions[c.id].__dict__
            item = self.actions[c.id].ref
            a = item.get_new_notification_from(self.actions[c.id])
            if a is not None:
                self.add(a)
                #Get Brok from this new notification
                b = a.get_initial_status_brok()
                self.add(b)
            del self.actions[c.id]
        elif c.is_a == 'check':
            self.checks[c.id].get_return_from(c)
            self.checks[c.id].status = 'waitconsume'
        else:
            print "Type unknown"


    #Call by brokers to have broks
    #We give them, and clean them!
    def get_broks(self):
        res = self.broks
        #They are gone, we keep none!
        self.broks = {}
        return res


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
        initial_status_types = [self.hosts, self.hostgroups,  \
                                self.services, self.servicegroups, \
                                self.contacts, self.contactgroups]
        for tab in initial_status_types:
            for i in tab:
                b = i.get_initial_status_brok()
                self.add(b)

        print "Created initial Broks:", len(self.broks)
        
    
    #Crate a brok with program status info
    def get_and_register_program_status_brok(self):
        b = self.get_program_status_brok()
        self.add(b)


    #Get a brok with program status
    #TODO : GET REAL VALUES
    def get_program_status_brok(self):
        now = time.time()
        data = {"is_running" : 1,
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
                'global_service_event_handler' : self.conf.global_service_event_handler
                }
        b = Brok('program_status', data)
        return b



    #Called every 1sec to consume every result in services or hosts
    #with theses results, they are OK, CRITCAL, UP/DOWN, etc...
    def consume_results(self):
        print "Consume results"
        checks_to_add = []
        for c in self.checks.values():
            #print c
            if c.status == 'waitconsume':
                #print "A check to consume", c.id
                item = c.ref
                actions = item.consume_result(c)
                #The update of the host/service must have changed, we brok it
                self.get_and_register_check_result_brok(item)

                #Now we manage the actions we must do
                for a in actions:
                    if a.is_a == 'notification':
                        self.add(a)
                        #Get Brok from this new notification
                        b = a.get_initial_status_brok()
                        self.add(b)
                    elif  a.is_a == 'check':
                        print "*******Adding dep checks*****"
                        checks_to_add.append(a)

        #All 'finished' checks (no more dep) raise checks they depends on
        for c in self.checks.values():
            if c.status == 'havetoresolvedep':
                #print "I remove dep", c.id, "on the checks in ", c.depend_on_me
                #self.checks[c.depend_on_me].depend_on.remove(c.id)
                for dependant_checks in c.depend_on_me:
                    #print "So removing check", c.id, "in" , dependant_checks.id
                    #Ok, now dependant will no more wait c
                    dependant_checks.depend_on.remove(c.id)
                #REMOVE OLD DEP CHECL -> zombie
                c.status = 'zombie'

        #Now, reintegr dep checks
        for c in self.checks.values():
            if c.status == 'waitdep' and len(c.depend_on) == 0:
                #print c.id, "OK we've got all dep!, now we can resolve check"
                item = c.ref
                actions = item.consume_result(c)
                self.get_and_register_check_result_brok(item)

                #Now we manage the actions we must do
                for a in actions:
                    if a.is_a == 'notification':
                        self.add(a)
                        #Get Brok from this new notification
                        b = a.get_initial_status_brok()
                        self.add(b)
                    elif  a.is_a == 'check':
                        print "*******Adding dep checks*****"
                        checks_to_add.append(a)
        if checks_to_add != []:
            #print "We add new Dep checks", checks_to_add
            for c in checks_to_add:
                self.add(c)


    #Called every 1sec to delete all checks in a zombie state
    #zombie = not usefull anymore
    def delete_zombie_checks(self):
        id_to_del = []
        for c in self.checks.values():
            if c.status == 'zombie':
                id_to_del.append(c.id)
        #une petite tape dans le doc et tu t'en vas, merci...
        for id in id_to_del:
            del self.checks[id] # ZANKUSEN!


    #Use to update the status file.
    def update_status_file(self):
        #TODO : OPTIMIZE it because it sucks
        pass
        #self.status_file.create_or_update()
            

    #Notifications are re-scheduling, this function check if unwanted notif
    #are still here (problem notif when it is not)
    def delete_unwanted_notifications(self):
        id_to_del = []
        for a in self.actions.values():
            item = a.ref
            if not item.still_need(a):
                id_to_del.append(a.id)
        #Ok, now we DEL
        for id in id_to_del:
            del self.actions[id]


    #Main schedule function to make the regular scheduling
    def schedule(self):
        #ask for service and hosts their next check
        for type_tab in [self.services, self.hosts]:
            for i in type_tab:
                c = i.schedule()
                if c is not None:
                    self.add(c)


    #Raise checks for no fresh states for services and hosts
    def check_freshness(self):
        for type_tab in [self.services, self.hosts]:
            for i in type_tab:
                c = i.do_check_freshness()
                if c is not None:
                    self.add(c)


    #Main function
    def run(self):
        #Ok, now all is initilised, we can make the inital broks
        self.fill_initial_broks()

        print "First scheduling"
        self.schedule()

        #TODO : a better tick count
        status_tick = 0
        #schedule_tick = 0
        
        timeout = 1.0
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
                #if (schedule_tick % 5) == 0:
                print "**********Schedule********"
                self.schedule()
                #schedule_tick += 1
                print "**********Consume*********"
                self.consume_results()
                print "**********Delete zombie****"
                self.delete_zombie_checks()
                print "********** Delete unwanted******"
                self.delete_unwanted_notifications()
                print "********** Delete freshnesh******"
                self.check_freshness()
                print "********** Clean caches *********"
                self.clean_caches()

                if (status_tick % 60) == 0:
                    #print "********** Update status file******"
                    self.update_status_file()
                status_tick += 1

                #print "************** Clean queues ************"
                self.clean_queues()

                #print "******* Fin loop********"

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
                    print "Latency Moyenne:", m, m_nb,  m / m_nb
                
                print "Notifications:", nb_notifications
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
