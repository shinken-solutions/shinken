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

import random
import time

from command import CommandCall
from copy import deepcopy
from item import Item, Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool, strip_and_uniq
from check import Check
from notification import Notification
from macroresolver import MacroResolver
from brok import Brok


class Service(SchedulingItem):
    id = 1 # Every service have a unique ID, and 0 is always special in database and co...
    ok_up = 'OK' # The host and service do not have the same 0 value, now yes :)

    my_type = 'service' #used by item class for format specific value like for Broks

    #properties defined by configuration
    #required : is required in conf
    #default : default value if no set in conf
    #pythonize : function to call when transfort string to python object
    #status_broker_name : if set, send to broker and put name of data. If None, use the prop name.
    #Only for the inital call
    #broker_name : same for status, but for status update call
    properties={'host_name' : {'required':True, 'status_broker_name' : None, 'broker_name' : None},
            'hostgroup_name' : {'required':True},
            'service_description' : {'required':True, 'status_broker_name' : None, 'broker_name' : None},
            'display_name' : {'required':False , 'default':None},
            'servicegroups' : {'required':False, 'default':''},
            'is_volatile' : {'required':False, 'default':'0', 'pythonize': to_bool},
            'check_command' : {'required':True},
            'initial_state' : {'required':False, 'default':'o', 'pythonize': to_char, 'status_broker_name' : None},
            'max_check_attempts' : {'required':True, 'pythonize': to_int},
            'check_interval' : {'required':True, 'pythonize': to_int},
            'retry_interval' : {'required':True, 'pythonize': to_int},
            'active_checks_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
            'passive_checks_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'check_period' : {'required':True},
            'obsess_over_service' : {'required':False, 'default':'0', 'pythonize': to_bool, 'status_broker_name' : None},
            'check_freshness' : {'required':False, 'default':'0', 'pythonize': to_bool, 'status_broker_name' : None},
            'freshness_threshold' : {'required':False, 'default':'0', 'pythonize': to_int, 'status_broker_name' : None},
            'event_handler' : {'required':False, 'default':''},
            'event_handler_enabled' : {'required':False, 'default':'0', 'pythonize': to_bool, 'status_broker_name' : None},
            'low_flap_threshold' : {'required':False, 'default':'-1', 'pythonize': to_int, 'status_broker_name' : None},
            'high_flap_threshold' : {'required':False, 'default':'-1', 'pythonize': to_int, 'status_broker_name' : None},
            'flap_detection_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
            'flap_detection_options' : {'required':False, 'default':'o,w,c,u', 'pythonize': to_split},
            'process_perf_data' : {'required':False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
            'retain_status_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'retain_nonstatus_information' : {'required':False, 'default':'1', 'pythonize': to_bool},
            'notification_interval' : {'required':False, 'default':'60', 'pythonize': to_int},
            'first_notification_delay' : {'required':False, 'default':'0', 'pythonize': to_int},
            'notification_period' : {'required':True},
            'notification_options' : {'required':False, 'default':'w,u,c,r,f,s', 'pythonize': to_split},
            'notifications_enabled' : {'required':False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
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
        'last_chk' : {'default' : 0, 'status_broker_name' : 'last_check', 'broker_name' : 'last_check'},
        'next_chk' : {'default' : 0, 'status_broker_name' : 'next_check'},
        'in_checking' : {'default' : False},
        'latency' : {'default' : 0, 'broker_name' : None},
        'attempt' : {'default' : 0, 'status_broker_name' : 'current_attempt', 'broker_name' : 'current_attempt' },
        'state' : {'default' : 'PENDING'},
        'state_id' :  {'default' : 0, 'status_broker_name' : 'current_state', 'broker_name' : 'current_state'},
        'current_event_id' :  {'default' : 0, 'status_broker_name' : None},
        'last_event_id' :  {'default' : 0, 'status_broker_name' : None},
        'last_state_id' :  {'default' : 0, 'status_broker_name' : 'last_state'},
        'last_state_change' :  {'default' : time.time(), 'status_broker_name' : None},
        'last_hard_state_change' :  {'default' : time.time(), 'status_broker_name' : None},
        'last_hard_state' :  {'default' : time.time(), 'status_broker_name' : None},
        'state_type' : {'default' : 'SOFT'},
        'state_type_id' : {'default' : 0, 'status_broker_name' : 'state_type', 'broker_name' : 'state_type'},
        'output' : {'default' : '', 'broker_name' : None},
        'long_output' : {'default' : '', 'broker_name' : None},
        'is_flapping' : {'default' : False, 'status_broker_name' : None},
        'is_in_downtime' : {'default' : False},
        'act_depend_of' : {'default' : []}, #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : {'default' : []}, #dependencies for checks raise, so BEFORE checks
        'last_state_update' : {'default' : time.time()},
        'checks_in_progress' : {'default' : []},
        'downtimes' : {'default' : []},
        'flapping_changes' : {'default' : []},
        'flapping_comment_id' : {'default' : 0, 'status_broker_name' : None},
        'percent_state_change' : {'default' : 0.0, 'status_broker_name' : None},
        'problem_has_been_acknowledged' : {'default' : False, 'status_broker_name' : None},
        'acknowledgement_type' : {'default' : 1, 'status_broker_name' : None, 'broker_name' : None},
        'check_type' : {'default' : 0, 'status_broker_name' : None, 'broker_name' : None},
        'has_been_checked' : {'default' : 1, 'status_broker_name' : None},
        'should_be_scheduled' : {'default' : 1, 'status_broker_name' : None},
        'last_problem_id' : {'default' : 0, 'status_broker_name' : None},
        'current_problem_id' : {'default' : 0, 'status_broker_name' : None},
        'execution_time' : {'default' : 0.0, 'status_broker_name' : None, 'broker_name' : None},
        'last_notification' : {'default' : time.time(), 'status_broker_name' : None},
        'current_notification_number' : {'default' : 0, 'status_broker_name' : None}      ,
        'current_notification_id' : {'default' : 0, 'status_broker_name' : None},
        'check_flapping_recovery_notification' : {'default' : True, 'status_broker_name' : None},
        'scheduled_downtime_depth' : {'default' : 0, 'status_broker_name' : None},
        'pending_flex_downtime' : {'default' : 0, 'status_broker_name' : None},
        'timeout' : {'default' : 0, 'broker_name' : None},
        'start_time' : {'default' : 0, 'broker_name' : None},
        'end_time' : {'default' : 0, 'broker_name' : None},
        'early_timeout' : {'default' : 0, 'broker_name' : None},
        'return_code' : {'default' : 0, 'broker_name' : None},
        'perf_data' : {'default' : '', 'broker_name' : None}
        
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
    #(Yes, debbuging CAN happen...)
    def get_name(self):
        return self.host_name+'/'+self.service_description


    #Check is required prop are set:
    #template are always correct
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['contacts', 'contactgroups', 'check_period', 'notification_interval',
                              'host_name', 'hostgroup_name']
        for prop in cls.properties:
            if prop not in special_properties:
                if not self.has(prop) and cls.properties[prop]['required']:
                    print self.get_name()," : I do not have", prop
                    state = False #Bad boy...

        #Ok now we manage special cases...
        if not self.has('contacts') and not self.has('contacgroups') and  self.notifications_enabled == True:
            print self.get_name()," : I do not have contacts nor contacgroups"
            state = False
        if not self.has('check_command') or not self.check_command.is_valid():
            print self.get_name()," : my check_command is invalid"
            state = False
        if not self.has('notification_interval') and  self.notifications_enabled == True:
            print self.get_name()," : I've got no notification_interval but I've got notifications enabled"
            state = False
        if not self.has('host') or self.host == None:
            #if not self.has('host_name') and not self.has('hostgroup_name'):
            print self.get_name(),": I do not have and host"
            state = False
        return state



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
        m = MacroResolver()
        
        for contact in self.contacts:
            for cmd in contact.service_notification_commands:
                print "SRV: Raise notification"
                n = Notification(type, 'scheduled', 'VOID', {'service' : self.id, 'contact' : contact.id, 'command': cmd}, 'service', t)

                #The notif must be fill with current data, so we create the commmand now
                command = n.ref['command']
                n._command = m.resolve_command(command, self.host_name, self, contact, n)
                #Maybe the contact do not want this notif? Arg!
                if self.is_notification_launchable(n, contact):
                    notifications.append(n)
        return notifications


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        if n.type == 'PROBLEM':
            return self.state != 'OK' and  contact.want_service_notification(now, self.state)
        else:
            return self.state == 'OK' and  contact.want_service_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    def get_new_notification_from(self, n):
        now = time.time()
        #a recovery notif is send ony one time
        if n.type == 'RECOVERY':
            return None
        new_n = Notification(n.type, 'scheduled','', {'service' : n.ref['service'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'service', now + self.notification_interval * 60)
        #m = MacroResolver()
        #command = new_n.ref['command']
        #new_n._command = m.resolve_command(command, self.host_name, self, contact, n)
        return new_n


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
            #print self.get_name()+" we ask me for a check" + str(c.id)
        self.update_in_checking()
        #We need to return the check for scheduling adding
        return c



class Services(Items):
    #Create the reversed list for speedup search by host_name/name
    #We also tag service already in list : they are twins. It'a a bad things.
    #Hostgroups service have an ID higer thant host service. So it we tag 
    #an id that already are in the list, this service is already exist, and is a host,
    #or a previous hostgroup, but define before.
    def create_reversed_list(self):
        self.reversed_list = {}
        self.twins = []
        for s in self:
            if s.has('service_description') and s.has('host_name'):
                s_desc = getattr(s, 'service_description')
                s_host_name = getattr(s, 'host_name')
                key = (s_host_name, s_desc)
                if key not in self.reversed_list:
                    self.reversed_list[key] = s.id
                else:
                    self.twins.append(s.id)


    #TODO : finish serach to use reversed
    #Search a service id by it's name and host_name
    def find_srv_id_by_name_and_hostname(self, host_name, name):
        #key = (host_name, name)
        #if key in self.reversed_list:
        #    return self.reversed_list[key]

        #if not, maybe in the whole list?
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
                if s.host is not None:
                    hst.add_service_link(s)
            except AttributeError as exp:
                pass #Will be catch at the is_correct moment


    #Link the service with a command for the check command
    def linkify_s_by_cmd(self, commands):
        for s in self:
            #print "Linkify s by cmd", s.get_name(), s.check_command
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
            if s.has('contacts'):
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
        for prop in ['contacts', 'contact_groups', 'notification_interval' , 'notification_period']:
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
        #self.apply_implicit_inheritance(hosts)
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
                    hgname = hgname.strip()
                    hnames = hostgroups.get_members_by_name(hgname)
                    #We add hosts in the service host_name
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
                hnames = strip_and_uniq(hnames)
                if len(hnames) >= 2:
                    for hname in hnames:
                        hname = hname.strip()
                        new_s = s.copy()
                        new_s.host_name = hname
                        self.items[new_s.id] = new_s
                    #Multiple host_name -> the original service
                    #must be delete
                    srv_to_remove.append(id)                    
                else: #Maybe the hnames was full of same host, so we must reset the name
                    for hname in hnames: #So even if len == 0, we are protected
                        s.host_name = hname

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


