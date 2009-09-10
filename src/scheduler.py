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

class Scheduler:
    def __init__(self, daemon):#, arbiter_daemon):
        self.daemon = daemon
        #self.arbiter_daemon = arbiter_daemon
        self.must_run = True

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
        self.checks = {}
        self.actions = {}
        self.downtimes = {}
        self.broks = {}
        self.status_file = StatusFile(self)
        self.instance_id = conf.instance_id


    def die(self):
        self.must_run = False


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        #self.fifo = e.open()


    def run_external_command(self, command):
        self.external_command.resolve_command(command)


    #And action if for service or host.
    #We just wuant the service of the host that is the ref
    #BUT: ref is int or dict... so...
    #TODO : clean this fucking ref...
    def get_ref_item_from_action(self, action):
        ref = action.ref
        if action.ref_type == 'service':
            if isinstance(ref, int):
                return self.services[ref]
            else:
                return self.services[action.ref['service']]
        if action.ref_type == 'host':
            if isinstance(ref, int):
                return self.hosts[action.ref]
            else:
                return self.hosts[action.ref['host']]


    def add_or_update_check(self, c):
        #print "Adding a NEW CHECK:", c.id
        self.checks[c.id] = c

    #We just add a brok in our broks queue
    #But before we tag it with our instance_id
    def add_brok(self, b):
        b.data['instance_id'] = self.instance_id
        self.broks[b.id] = b

    #Ask item (host or service) a update_status
    #and add it to our broks queue
    def get_and_register_status_brok(self, item):
        b = item.get_update_status_brok()
        self.add_brok(b)

    #Ask item (host or service) a check_result_brok
    #and add it to our broks queue
    def get_and_register_check_result_brok(self, item):
        b = item.get_check_result_brok()
        self.add_brok(b)


    def add_or_update_action(self, a):
        self.actions[a.id] = a


    def add_downtime(self, dt):
        self.downtimes[dt.id] = dt


    def del_downtime(self, dt_id):
        dt = self.downtimes[dt.id]
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
                    res.append(c)

        #If poller want to notify too
        if do_actions:
            for a in self.actions.values():
                #contact = self.contacts.items[a.ref['contact']]
                contact = self.contacts[a.ref['contact']]
                item = self.get_ref_item_from_action(a)
                if a.status == 'scheduled' and item.is_notification_launchable(a, contact):
                    item.update_notification(a, contact)
                    a.status = 'inpoller'
                    res.append(a)
        return res


    #Caled by poller to send result
    def put_results(self, c):
        print "Get results"
        if c.is_a == 'notification':
            item = self.get_ref_item_from_action(c)
            a = item.get_new_notification_from(c)
            if a is not None:
                self.add_or_update_action(a)
            del self.actions[c.id]
        elif c.is_a == 'check':
            c.status = 'waitconsume'
            self.add_or_update_check(c)
        else:
            print "Type unknown"


    #Call by brokers to have broks
    def get_broks(self):
        res = self.broks
        #They are gone, we keep none!
        self.broks = {}
        return res


    #Fill the self.broks with broks of self (process id, and co)
    #broks of service and hosts (initial status)
    def fill_initial_broks(self):
        #First a Brok for delete all from my instance_id
        b = Brok('clean_all_my_instance_id',{'instance_id' : self.instance_id})
        self.add_brok(b)

        #first the program status
        b = self.get_program_status_brok()
        self.add_brok(b)#broks[b.id] = b

        #We cant initial_status from all this types
        #The order is important, service need host...
        initial_status_types = [self.hosts, self.hostgroups,  \
                                self.services, self.servicegroups, \
                                self.contacts, self.contactgroups]
        for tab in initial_status_types:
            for i in tab:
                b = i.get_initial_status_brok()
                self.add_brok(b)

        print "Created initial Broks:", self.broks
        
    
    #Crate a brok with program status info
    def get_and_register_program_status_brok(self):
        b = self.get_program_status_brok()
        self.add_brok(b)


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
                "failure_prediction_enabled" : 0,#self.conf.failure_prediction_enabled,
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
            print c
            if c.status == 'waitconsume':
                print "A check to consume"
                item = self.get_ref_item_from_action(c)
                actions = item.consume_result(c)
                print "Res Action:", actions
                #The update of the host/service must have changed, we brok it
                self.get_and_register_check_result_brok(item)

                #Now we manage the actions we must do
                for a in actions:
                    if a.is_a == 'notification':
                        #print "*******Adding a notification"
                        self.add_or_update_action(a)
                    elif  a.is_a == 'check':
                        print "*******Adding dep checks*****"
                        checks_to_add.append(a)

        #All 'finished' checks (no more dep) raise checks tey depend
        for c in self.checks.values():
            if c.status == 'havetoresolvedep':
                print "I remove dep", c.id, "on the check", c.depend_on_me
                self.checks[c.depend_on_me].depend_on.remove(c.id)
                #REMOVE OLD DEP CHECL -> zombie
                c.status = 'zombie'

        #Now, reintegr dep checks
        for c in self.checks.values():
            if c.status == 'waitdep' and len(c.depend_on) == 0:
                print c.id, "OK we've got all dep!, now we can resolve check"
                item = self.get_ref_item_from_action(c)
                actions = item.consume_result(c)
                self.get_and_register_check_result_brok(item)

                #Now we manage the actions we must do
                for a in actions:
                    if a.is_a == 'notification':
                        #print "*******Adding a notification"
                        self.add_or_update_action(a)#self.actions[a.id] = a
                    elif  a.is_a == 'check':
                        print "*******Adding dep checks*****"
                        checks_to_add.append(a)
                
        print "We add new Dep checks", checks_to_add
        for c in checks_to_add:
            self.add_or_update_check(c)


    #Called every 1sec to delete all checks in a zombie state
    #zombie = not usefull anymore
    def delete_zombie_checks(self):
        id_to_del = []
        for c in self.checks.values():
            if c.status == 'zombie':
                id_to_del.append(c.id)
        #une petite tape dans le doc et tu t'en vas, merci...
        for id in id_to_del:
            del self.checks[id]


    def update_status_file(self):
        self.status_file.create_or_update()
            

    #Notifications are re-scheduling, this function check if unwanted notif
    #are still here (problem notif when it is not)
    def delete_unwanted_notifications(self):
        id_to_del = []
        for a in self.actions.values():
            if a.ref_type == 'service':
                #service = self.services.items[a.ref['service']]
                service = self.services[a.ref['service']]
                if not service.still_need(a):
                    id_to_del.append(a.id)
            if a.ref_type == 'host':
                #host = self.hosts.items[a.ref['host']]
                host = self.hosts[a.ref['host']]
                if not host.still_need(a):
                    id_to_del.append(a.id)
        #print "**********Deleting Notifications", id_to_del
        for id in id_to_del:
            del self.actions[id]


    #Main schedule function to make the regular scheduling
    def schedule(self):
        #ask for service their next check
        for s in self.services:
            c = s.schedule()
            if c is not None:
                self.add_or_update_check(c)#self.checks[c.id] = c
        for h in self.hosts:
            c = h.schedule()
            if c is not None:
                self.add_or_update_check(c)#self.checks[c.id] = c


    #Raise checks for no fresh states
    def check_freshness(self):
        checks = []
        for s in self.services:
            c = s.do_check_freshness()
        for h in self.hosts:
            c = h.do_check_freshness()
        if c is not None:
            self.add_or_update_check(c)


    #Main function
    def run(self):
        print "First scheduling"
        self.schedule()

        #Ok, now all is initilised, we can make the inital broks
        self.fill_initial_broks()
        
        timeout = 1.0
        while self.must_run :
            socks = self.daemon.getServerSockets()
            avant = time.time()
            #socks.append(self.fifo)
 
            ins,outs,exs = select.select(socks,[],[],timeout)   # 'foreign' event loop
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
                            apres=time.time()
                            diff = apres-avant
                            timeout = timeout - diff
                            break    # no need to continue with the for loop
            else:#Timeout
		timeout = 1.0
                print "**********Schedule********"
                self.schedule()
                print "**********Consume*********"
                self.consume_results()
                print "**********Delete zombie****"
                self.delete_zombie_checks()
                print "********** Delete unwanted******"
                self.delete_unwanted_notifications()
                print "********** Delete freshnesh******"
                self.check_freshness()
                print "********** Delete update status******"
                self.update_status_file()
                print "******* Fin loop********"

                #stats
                nb_scheduled = len([c for c in self.checks.values() if c.status=='scheduled'])
                nb_inpoller = len([c for c in self.checks.values() if c.status=='inpoller'])
                nb_zombies = len([c for c in self.checks.values() if c.status=='zombie'])
                nb_notifications = len(self.actions)

                print "Checks:", "scheduled", nb_scheduled, "inpoller", nb_inpoller, "zombies", nb_zombies, "notifications", nb_notifications

                m = 0.0
                m_nb = 0
                for s in self.services:
                    m += s.latency
                    m_nb += 1
                if m_nb != 0:
                    print "Latency Moyenne:", m, m_nb,  m / m_nb
                
                #print "Notifications:", nb_notifications
                #for n in  self.actions.values():
                #    if n.ref_type == 'service':
                #        print 'Service notification', n
                #    if n.ref_type == 'host':
                #        print 'Host notification', n
                print "."
                print "Service still in checking?"
                for s in self.services:
                    print s.get_name()+':'+str(s.in_checking)+str(s.checks_in_progress)
                    for i in s.checks_in_progress:
                        print self.checks[i]
                for s in self.hosts:
                    print s.get_name()+':'+str(s.in_checking)+str(s.checks_in_progress)
                    for i in s.checks_in_progress:
                        print self.checks[i]

            if timeout < 0:
		timeout = 1.0
