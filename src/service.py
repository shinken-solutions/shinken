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


from command import CommandCall
from copy import deepcopy
from item import Item, Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool
import random
import time
from check import Check
from notification import Notification
#from timeperiod import Timeperiod
from macroresolver import MacroResolver




class Service(SchedulingItem):
    id = 0 # Every service have a unique ID
    ok_up = 'OK'

    #properties defined by configuration
    properties={'host_name' : {'required':True},
            'hostgroup_name' : {'required':True},
            'service_description' : {'required':True},
            'display_name' : {'required':False , 'default':None},
            'servicegroups' : {'required':False, 'default':''},
            'is_volatile' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'check_command' : {'required':True},
            'initial_state' : {'required':False, 'default':'o', 'pythonize': to_char},
            'max_check_attempts' : {'required':True, 'pythonize': to_int},
            'check_interval' : {'required':True, 'pythonize': to_int},
            'retry_interval' : {'required':True, 'pythonize': to_int},
            'active_checks_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'passive_checks_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'check_period' : {'required':True},
            'obsess_over_service' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'check_freshness' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'freshness_threshold' : {'required':False, 'default':'0', 'pythonize': to_int},
            'event_handler' : {'required':False, 'default':''},
            'event_handler_enabled' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'low_flap_threshold' : {'required':False, 'default':'-1', 'pythonize': to_int},
            'high_flap_threshold' : {'required':False, 'default':'-1', 'pythonize': to_int},
            'flap_detection_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'flap_detection_options' : {'required':False, 'default':'o,w,c,u', 'pythonize': to_split},
            'process_perf_data' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'retain_status_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'retain_nonstatus_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'notification_interval' : {'required':True, 'pythonize': to_int},
            'first_notification_delay' : {'required':False, 'default':'0', 'pythonize': to_int},
            'notification_period' : {'required':True},
            'notification_options' : {'required':False, 'default':'w,u,c,r,f,s', 'pythonize': to_split},
            'notifications_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'contacts' : {'required':True},
            'contact_groups' : {'required':True},
            'stalking_options' : {'required':False, 'default':'o,w,u,c', 'pythonize': to_split},
            'notes' : {'required':False, 'default':''},
            'notes_url' : {'required':False, 'default':''},
            'action_url' : {'required':False, 'default':''},
            'icon_image' : {'required':False, 'default':''},
            'icon_image_alt' : {'required':False, 'default':''},
            'failure_prediction_enabled' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'parallelize_check' : {'required':False, 'default':'1', 'pythonize': to_bool}
            }
    
    #properties used in the running state
    running_properties = {
        'last_chk' : 0,
        'next_chk' : 0,
        'in_checking' : False,
        'latency' : 0,
        'attempt' : 0,
        'state' : 'PENDING',
        'state_type' : 'SOFT',
        'output' : '',
        'long_output' : '',
        'is_flapping' : False,
        'is_in_downtime' : False,
        'act_depend_of' : [], #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : [], #dependencies for checks raise, so BEFORE checks
        'last_state_update' : time.time(),
        'checks_in_progress' : [],
        'downtimes' : [],
        'flapping_changes' : [],
        'percent_state_change' : 0.0
        }

    #Mapping between Macros and properties (can be prop or a function)
    macros = {
        'SERVICEDESC' : 'service_description',
        'SERVICEDISPLAYNAME' : 'display_name',
        'SERVICESTATE' : 'state',
        'SERVICESTATEID' : 'get_state_id',
        'LASTSERVICESTATE' : 'last_state',
        'LASTSERVICESTATEID' : 'get_last_state_id',
        'SERVICESTATETYPE' : 'state_type',
        'SERVICEATTEMPT' : 'attempt',
        'MAXSERVICEATTEMPTS' : 'max_check_attempts',
        'SERVICEISVOLATILE' : 'is_volatile',
        'SERVICEEVENTID' : None,
        'LASTSERVICEEVENTID' : None,
        'SERVICEPROBLEMID' : None,
        'LASTSERVICEPROBLEMID' : None,
        'SERVICELATENCY' : 'latency',
        'SERVICEEXECUTIONTIME' : 'exec_time',
        'SERVICEDURATION' : 'get_duration',
        'SERVICEDURATIONSEC' : 'get_duration_sec',
        'SERVICEDOWNTIME' : 'get_downtime',
        'SERVICEPERCENTCHANGE' : 'get_percent_change',
        'SERVICEGROUPNAME' : 'get_groupname',
        'SERVICEGROUPNAMES' : 'get_groupnames',
        'LASTSERVICECHECK' : 'last_chk',
        'LASTSERVICESTATECHANGE' : 'last_state_change',
        'LASTSERVICEOK' : 'last_service_ok',
        'LASTSERVICEWARNING' : 'last_service_warning',
        'LASTSERVICEUNKNOWN' : 'last_service_unknown',
        'LASTSERVICECRITICAL' : 'last_service_critical',
        'SERVICEOUTPUT' : 'output',
        'LONGSERVICEOUTPUT' : 'long_output',
        'SERVICEPERFDATA' : 'perf_data',
        'SERVICECHECKCOMMAND' : 'get_check_command',
        'SERVICEACKAUTHOR' : 'ack_author',
        'SERVICEACKAUTHORNAME' : 'get_ack_author_name',
        'SERVICEACKAUTHORALIAS' : 'get_ack_author_alias',
        'SERVICEACKCOMMENT' : 'ack_comment',
        'SERVICEACTIONURL' : 'action_url',
        'SERVICENOTESURL' : 'notes_url',
        'SERVICENOTES' : 'notes'
        }

    #Give a nice name output, for debbuging purpose
    #(Yes, debbuging can happen...)
    def get_name(self):
        return self.host_name+'/'+self.service_description


    #The service is dependent of his father dep
    #Must be AFTER linkify
    def fill_daddy_dependancy(self):
        #Depend of host, all status, is a networkdep and do not have timeperiod
        if self.host is not None:
            self.act_depend_of.append( (self.host, ['d', 'u', 's', 'f'], 'network_dep', None) )

            
    def add_service_act_dependancy(self, srv, status, timeperiod):
        self.act_depend_of.append( (srv, status, 'logic_dep', timeperiod) )


    def add_service_chk_dependancy(self, srv, status, timeperiod):
        self.chk_depend_of.append( (srv, status, 'logic_dep', timeperiod) )


    #Set state with status return by the check
    #and update flapping state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now

        self.last_state = self.state
        if status == 0:
            self.state = 'OK'
        elif status == 1:
            self.state = 'WARNING'
        elif status == 2:
            self.state = 'CRITICAL'
        elif status == 3:
            self.state = 'UNKNOWN'
        else:
            self.state = 'UNDETERMINED'
        if status in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)



    #Return True if status is the state (like OK) or small form like 'o'
    def is_state(self, status):
        if status == self.state:
            return True
        #Now low status
        elif status == 'o' and self.state == 'OK':
            return True
        elif status == 'c' and self.state == 'CRITICAL':
            return True
        elif status == 'w' and self.state == 'WARNING':
            return True
        elif status == 'u' and self.state == 'UNKNOWN':
            return True
        return False


    #Create notifications but without commands. It will be update juste before being send
    def create_notifications(self, type):
        #if notif is disabled, not need to go thurser
        cls = self.__class__
        if not self.notifications_enabled or self.is_in_downtime or not cls.enable_notifications:
            return []
        
        notifications = []
        now = time.time()
        t = self.notification_period.get_next_valid_time_from_t(now)
        
        for contact in self.contacts:
            for cmd in contact.service_notification_commands:
                print "SRV: Raise notification"
                #create without real command, it will be update just before being send
                notifications.append(Notification(type, 'scheduled', 'VOID', {'service' : self.id, 'contact' : contact.id, 'command': cmd}, 'service', t))
        return notifications


    #We are just going to launch the notif to the poller
    #so we must actualise the command (Macros)
    def update_notification(self, n,  contact):
        m = MacroResolver()
        command = n.ref['command']
        n._command = m.resolve_command(command, self.host_name, self, contact, n)


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        if n.type == 'PROBLEM':
            return now > n.t_to_go and self.state != 'OK' and  contact.want_service_notification(now, self.state)
        else:
            return now > n.t_to_go and self.state == 'OK' and  contact.want_service_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    def get_new_notification_from(self, n):
        now = time.time()
        #a recovery notif is send ony one time
        if n.type == 'RECOVERY':
            return None
        return Notification(n.type, 'scheduled','', {'service' : n.ref['service'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'service', now + self.notification_interval * 60)


    #Check if the notificaton is still necessery
    def still_need(self, n):
        now = time.time()
        #if state != OK, te service still got a pb, so notification still necessery
        if self.state != 'OK':
            return True
        #state is OK but notif is in poller, so do not remove, will be done after
        if n.status == 'inpoller':
            return True
        #we do not see why to save this notification, so...
        return False


    #Is in checking if and ony if there are still checks no consumed
    def update_in_checking(self):
        self.in_checking = (len(self.checks_in_progress) != 0)


    #return a check to check the service
    def launch_check(self, t, ref_check_id = None):
        c = None
        if not self.is_no_check_dependant():
            #Get the command to launch
            m = MacroResolver()
            command_line = m.resolve_command(self.check_command, self.host_name, self, None, None)
            
            #Make the Check object and put the service in checking
            #print "Asking for a check with command:", command_line
            c = Check('scheduled',command_line, self.id, 'service', self.next_chk, ref_check_id)
            #We keep a trace of all checks in progress
            #to know if we are in checking_or not
            self.checks_in_progress.append(c.id)
            print self.get_name()+" we ask me for a check" + str(c.id)
        self.update_in_checking()
        #We need to return the check for scheduling adding
        return c


class Services(Items):
    #Search a service id by it's name and hot_name
    def find_srv_id_by_name_and_hostname(self, host_name, name):
        for s in self:
            #Runtinme first, available only after linkify
            if s.has('service_description') and s.has('host'):
                if s.service_description == name and s.host == host_name:
                        return s.id
            #At config part, available before linkify
            if s.has('service_description') and s.has('host_name'):
                if s.service_description == name and s.host_name == host_name:
                    return s.id
        return None


    #Search a service by it's name and hot_name
    def find_srv_by_name_and_hostname(self, host_name, name):
        id = self.find_srv_id_by_name_and_hostname(host_name, name)
        if id is not None:
            return self.items[id]
        else:
            return None


    #Make link between elements:
    #service -> host
    #service -> command
    #service -> timepriods
    #service -> contacts
    def linkify(self, hosts, commands, timeperiods, contacts):
        self.linkify_s_by_hst(hosts)
        self.linkify_s_by_cmd(commands)
        self.linkify_s_by_tp(timeperiods)
        self.linkify_s_by_c(contacts)


    #We just search for each host the id of the host
    #and replace the name by the id
    #+ inform the host we are a service of him
    def linkify_s_by_hst(self, hosts):
        for s in self:
            try:
                hst_name = s.host_name
                #The new member list, in id
                hst = hosts.find_by_name(hst_name)
                s.host = hst
                #Let the host know we are his service
                hst.add_service_link(s)
            except AttributeError as exp:
                print exp


    #Link the service with a command for the check command
    def linkify_s_by_cmd(self, commands):
        for s in self:
            s.check_command = CommandCall(commands, s.check_command)


    #Link service with timepriods (notifs and check)
    def linkify_s_by_tp(self, timeperiods):
        for s in self:
            try:
                #notif period
                ntp_name = s.notification_period
                ntp = timeperiods.find_by_name(ntp_name)
                s.notification_period = ntp
            except:
                pass
            try:
                #Check period
                ctp_name = s.check_period
                ctp = timeperiods.find_by_name(ctp_name)
                s.check_period = ctp
            except:
                pass #problem will be check at is_correct fucntion


    #Make link between service and it's contacts
    def linkify_s_by_c(self, contacts):
        for s in self:
            contacts_tab = s.contacts.split(',')
            new_contacts = []
            for c_name in contacts_tab:
                c_name = c_name.strip()
                c = contacts.find_by_name(c_name)
                new_contacts.append(c)
            s.contacts = new_contacts


    #Delete services by ids
    def delete_services_by_id(self, ids):
        for id in ids:
            del self.items[id]


    #Apply implicit inheritance for special properties:
    #contact_groups, notification_interval , notification_period
    #So service will take info from host if necessery
    def apply_implicit_inheritance(self, hosts):
        for prop in ['contact_groups', 'notification_interval' , 'notification_period']:
            for s in self:
                if not s.is_tpl():
                    if not s.has(prop) and s.has('host_name'):
                        h = hosts.find_by_name(s.host_name)
                        if h is not None and h.has(prop):
                            setattr(s, prop, getattr(h, prop))


    #Apply inheritance for all properties
    def apply_inheritance(self, hosts):
        #We check for all Host properties if the host has it
        #if not, it check all host templates for a value
        for prop in Service.properties:
            self.apply_partial_inheritance(prop)

        #Then implicit inheritance
        self.apply_implicit_inheritance(hosts)
        for s in self:
            s.get_customs_properties_by_inheritance(self)

    #Create dependancies for services (daddy ones)
    def apply_dependancies(self):
        for s in self:
            s.fill_daddy_dependancy()


    #We create new service if necessery (host groups and co)
    def explode(self, hostgroups, contactgroups, servicegroups):
        #Hostgroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('contact_groups')
        self.apply_partial_inheritance('hostgroup_name')
        self.apply_partial_inheritance('host_name')

        #The "old" services will be removed. All services with 
        #more than one host or a host group will be in it
        srv_to_remove = []
        
        #We adding all hosts of the hostgroups into the host_name property
        #because we add the hostgroup one AFTER the host, they are before and 
        #hostgroup one will NOT be created
        for s in self:
            if s.has('hostgroup_name'):
                hgnames = s.hostgroup_name.split(',')
                for hgname in hgnames:
                    print "Doing a hgname", hgname
                    hgname = hgname.strip()
                    hnames = hostgroups.get_members_by_name(hgname)
                    #We add hosts in the service host_name
                    print s.host_name, hgname
                    if s.has('host_name') and hnames != []:
                        s.host_name += ',' + str(hnames)
                    else:
                        s.host_name = str(hnames)

        #We adding all hosts of the hostgroups into the host_name property
        #because we add the hostgroup one AFTER the host, they are before and 
        #hostgroup one will NOT be created
        for s in self:
            if s.has('contact_groups'):
                cgnames = s.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if s.has('contacts'):
                            s.contacts += ','+cnames
                        else:
                            s.contacts = cnames
        
        #Then for every host create a copy of the service with just the host
        service_to_check = self.items.keys() #because we are adding services, we can't just loop in it
        for id in service_to_check:
            s = self.items[id]
            if not s.is_tpl(): #Exploding template is useless
                hnames = s.host_name.split(',')
                if len(hnames) >= 2:
                    for hname in hnames:
                        hname = hname.strip()
                        new_s = s.copy()
                        new_s.host_name = hname
                        self.items[new_s.id] = new_s
                    srv_to_remove.append(id)
        
        self.delete_services_by_id(srv_to_remove)

        #Servicegroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('servicegroups')
        for s in self:
            if not s.is_tpl():
                sname = s.service_description
                shname = s.host_name
                if s.has('servicegroups'):
                    sgs = s.servicegroups.split(',')
                    for sg in sgs:
                        servicegroups.add_member(shname+','+sname, sg)
        
