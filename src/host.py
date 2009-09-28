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

import pygraph

from command import CommandCall
#from pygraph import digraph
from item import Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool
import time#, random
from macroresolver import MacroResolver
from check import Check
from notification import Notification
#from brok import Brok

class Host(SchedulingItem):
    id = 1 #0 is reserved for host (primary node for parents)
    ok_up = 'UP'
    my_type = 'host'


    #properties defined by configuration
    #required : is required in conf
    #default : default value if no set in conf
    #pythonize : function to call when transfort string to python object
    #status_broker_name : if set, send to broker and put name of data.
    #If None, use the prop name.
    #Only for the inital call
    #broker_name : same for inital, but for status update call
    properties={'host_name': {'required': True, 'status_broker_name' : None, 'broker_name' : None},
                'alias': {'required':  True},
                'display_name': {'required': False, 'default':'none'},
                'address': {'required': True},
                'parents': {'required': False, 'default': '' , 'pythonize': to_split},
                'hostgroups': {'required': False, 'default' : ''},
                'check_command': {'required': False, 'default':''},
                'initial_state': {'required': False, 'default':'u', 'pythonize': to_char, 'status_broker_name' : None},
                'max_check_attempts': {'required': True , 'pythonize': to_int},
                'check_interval': {'required': False, 'default':'0', 'pythonize': to_int},
                'retry_interval': {'required': False, 'default':'0', 'pythonize': to_int},
                'active_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'passive_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'check_period': {'required': True},
                'obsess_over_host': {'required': False, 'default':'0' , 'pythonize': to_bool, 'status_broker_name' : None},
                'check_freshness': {'required': False, 'default':'0', 'pythonize': to_bool, 'status_broker_name' : None},
                'freshness_threshold': {'required': False, 'default':'0', 'pythonize': to_int, 'status_broker_name' : None},
                'event_handler': {'required': False, 'default':''},
                'event_handler_enabled': {'required': False, 'default':'0', 'pythonize': to_bool, 'status_broker_name' : None},
                'low_flap_threshold': {'required':False, 'default':'25', 'pythonize': to_int, 'status_broker_name' : None},
                'high_flap_threshold': {'required': False, 'default':'50', 'pythonize': to_int, 'status_broker_name' : None},
                'flap_detection_enabled': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'flap_detection_options': {'required': False, 'default':'o,d,u', 'pythonize': to_split},
                'process_perf_data': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'retain_status_information': {'required': False, 'default':'1', 'pythonize': to_bool},
                'retain_nonstatus_information': {'required': False, 'default':'1', 'pythonize': to_bool},
                'contacts': {'required': True},
                'contact_groups': {'required': True},
                'notification_interval': {'required': False, 'default':'60', 'pythonize': to_int},
                'first_notification_delay': {'required': False, 'default':'0', 'pythonize': to_int},
                'notification_period': {'required': True},
                'notification_options': {'required': False, 'default':'d,u,r,f', 'pythonize': to_split},
                'notifications_enabled': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'stalking_options': {'required': False, 'default':'o,d,u', 'pythonize': to_split},
                'notes': {'required': False, 'default':''},
                'notes_url': {'required': False, 'default':''},
                'action_url': {'required': False, 'default':''},
                'icon_image': {'required': False, 'default':''},
                'icon_image_alt': {'required': False, 'default':''},
                'vrml_image': {'required': False, 'default':''},
                'statusmap_image': {'required': False, 'default':''},
                '2d_coords': {'required': False, 'default':''},
                '3d_coords': {'required': False, 'default':''},
                'failure_prediction_enabled': {'required' : False, 'default' : '0', 'pythonize': to_bool}
                }

    #properties set only for running purpose
    running_properties = {
        'last_chk' : {'default' : 0, 'status_broker_name' : 'last_check', 'broker_name' : 'last_check'},
        'next_chk' : {'default' : 0, 'status_broker_name' : 'next_check'},
        'in_checking' : {'default' : False},
        'latency' : {'default' : 0, 'broker_name' : None},
        'attempt' : {'default' : 0, 'status_broker_name' : 'current_attempt', 'broker_name' : 'current_attempt'},
        'state' : {'default' : 'PENDING'},
        'state_id' :  {'default' : 0, 'status_broker_name' : 'current_state', 'broker_name' : 'current_state'},
        'state_type' : {'default' : 'SOFT'},
        'state_type_id' : {'default' : 0, 'status_broker_name' : 'state_type', 'broker_name' : 'state_type'},
        'current_event_id' :  {'default' : 0, 'status_broker_name' : None},
        'last_event_id' :  {'default' : 0, 'status_broker_name' : None},
        'last_state_id' :  {'default' : 0, 'status_broker_name' : 'last_state'},
        'last_state_change' :  {'default' : time.time(), 'status_broker_name' : None},
        'last_hard_state_change' :  {'default' : time.time(), 'status_broker_name' : None},
        'last_hard_state' :  {'default' : time.time(), 'status_broker_name' : None},
        'output' : {'default' : '', 'broker_name' : None},
        'long_output' : {'default' : '', 'broker_name' : None},
        'is_flapping' : {'default' : False, 'status_broker_name' : None},
        'is_in_downtime' : {'default' : False},
        'flapping_comment_id' : {'default' : 0, 'status_broker_name' : None},
        'act_depend_of' : {'default' : []}, #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : {'default' : []}, #dependencies for checks raise, so BEFORE checks
        'last_state_update' : {'default' : time.time()},
        'services' : {'default' : []},
        'checks_in_progress' : {'default' : []},
        'downtimes' : {'default' : []},
        'flapping_changes' : {'default' : []},
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
        'current_notification_number' : {'default' : 0, 'status_broker_name' : None},
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

    #Hosts macros and prop that give the information
    #the prop can be callable or not
    macros = {'HOSTNAME' : 'host_name',
              'HOSTDISPLAYNAME' : 'display_name',
              'HOSTALIAS' :  'alias',
              'HOSTADDRESS' : 'address',
              'HOSTSTATE' : 'state',
              'HOSTSTATEID' : 'get_stateid',
              'LASTHOSTSTATE' : 'last_state',
              'LASTHOSTSTATEID' : 'get_last_stateid',
              'HOSTSTATETYPE' : 'state_type',
              'HOSTATTEMPT' : 'attempt',
              'MAXHOSTATTEMPTS' : 'max_check_attempts',
              'HOSTEVENTID' : None,
              'LASTHOSTEVENTID' : None,
              'HOSTPROBLEMID' : None,
              'LASTHOSTPROBLEMID' : None,
              'HOSTLATENCY' : 'latency',
              'HOSTEXECUTIONTIME' : 'exec_time',
              'HOSTDURATION' : 'get_duration',
              'HOSTDURATIONSEC' : 'get_duration_sec',
              'HOSTDOWNTIME' : 'get_downtime',
              'HOSTPERCENTCHANGE' : 'get_percent_change',
              'HOSTGROUPNAME' : 'get_groupname',
              'HOSTGROUPNAMES' : 'get_groupnames',
              'LASTHOSTCHECK' : 'last_chk',
              'LASTHOSTSTATECHANGE' : 'last_state_change',
              'LASTHOSTUP' : 'last_host_up',
              'LASTHOSTDOWN' : 'last_host_down',
              'LASTHOSTUNREACHABLE' : 'last_host_unreachable',
              'HOSTOUTPUT' : 'output',
              'LONGHOSTOUTPUT' : 'long_output',
              'HOSTPERFDATA' : 'perf_data',
              'HOSTCHECKCOMMAND' : 'get_check_command',
              'HOSTACKAUTHOR' : 'ack_author',
              'HOSTACKAUTHORNAME' : 'get_ack_author_name',
              'HOSTACKAUTHORALIAS' : 'get_ack_author_alias',
              'HOSTACKCOMMENT' : 'ack_comment',
              'HOSTACTIONURL' : 'action_url',
              'HOSTNOTESURL' : 'notes_url',
              'HOSTNOTES' : 'notes',
              'TOTALHOSTSERVICES' : 'get_total_services',
              'TOTALHOSTSERVICESOK' : 'get_total_services_ok',
              'TOTALHOSTSERVICESWARNING' : 'get_total_services_warning',
              'TOTALHOSTSERVICESUNKNOWN' : 'get_total_services_unknown',
              'TOTALHOSTSERVICESCRITICAL' : 'get_total_services_critical'
        }



    def clean(self):
        pass


    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['contacts', 'contactgroups', 'check_period', \
                                  'notification_interval']
        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    print self.get_name(), " : I do not have", prop
                    state = False #Bad boy...
        #Ok now we manage special cases...
        if not hasattr(self, 'contacts') and not hasattr(self, 'contacgroups') and self.notifications_enabled == True:
            print self.get_name()," : I do not have contacts nor contacgroups"
            state = False
        if not hasattr(self, 'check_command') or not self.check_command.is_valid():
            print self.get_name()," : my check_command is invalid"
            state = False
        if not hasattr(self, 'notification_interval') and self.notifications_enabled == True:
            print self.get_name()," : I've got no notification_interval but I've got notifications enabled"
            state = False
        return state


    #Macro part
    def get_total_services(self):
        return str(len(self.services))


    #For debugging purpose only (nice name)
    def get_name(self):
        return self.host_name


    #Add a dependancy for action event handler, notification, etc)
    def add_host_act_dependancy(self, h, status, timeperiod):
        self.act_depend_of.append( (h, status, 'logic_dep', timeperiod) )


    #Add a dependancy for check (so before launch)
    def add_host_chk_dependancy(self, h, status, timeperiod):
        self.chk_depend_of.append( (h, status, 'logic_dep', timeperiod) )


    #add one of our service to services (at linkify)
    def add_service_link(self, service):
        self.services.append(service)

    
    #set the state in UP, DOWN, or UNDETERMINED
    #with the status of a check. Also update last_state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now
        self.last_state = self.state
        
        if status == 0:
            self.state = 'UP'
        elif status == 1 or status == 2 or status == 3:
            self.state = 'DOWN'
        else:
            self.state = 'UNDETERMINED'
        if status in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)


    #See if status is status. Can be low of high format (o/UP, d/DOWN, ...)
    def is_state(self, status):
        if status == self.state:
            return True
        #Now low status
        elif status == 'o' and self.state == 'UP':
            return True
        elif status == 'd' and self.state == 'DOWN':
            return True
        elif status == 'u' and self.state == 'UNREACHABLE':
            return True
        return False


    #fill act_depend_of with my parents (so network dep)
    def fill_parents_dependancie(self):
        for parent in self.parents:
            if parent is not None:
                self.act_depend_of.append( (parent, ['d', 'u', 's', 'f'], 'network_dep', None) )


    #Give data for notifications'n macros
    def get_data_for_notifications(self, contact, n):
        return [self, contact, n]


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        return now > n.t_to_go and self.state != 'UP' and contact.want_host_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    def get_new_notification_from(self, n):
        now = time.time()
        return Notification(n.type, 'scheduled', '', {'host' : n.ref['host'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'host', now + self.notification_interval * 60)


    #Check if the notificaton is still necessery
    def still_need(self, n):
        now = time.time()
        #if state != UP, the host still got a pb
        #, so notification still necessery
        if self.state != 'UP':
            return True
        #state is UP but notif is in poller, 
        #so do not remove, will be done after
        if n.status == 'inpoller':
            return True
        #we do not see why to save this notification, so...
        return False


    #return a check to check the host
    def launch_check(self, t , ref_check = None):
        c = None
        
        #if I'm already in checking, Why launch a new check?
        #If ref_check_id is not None , this is a dependancy_ check
        if self.in_checking and ref_check != None:
            c_in_progress = self.checks_in_progress[0]
            if c_in_progress.t_to_go > time.time(): #Very far?
                c_in_progress.t_to_go = time.time()
            c_in_progress.depend_on_me.append(ref_check)
            #print "****************** I prefer give you my previous check, really", c_in_progress.id
            return c_in_progress.id
        
        if not self.is_no_check_dependant():
            #Get the command to launch
            m = MacroResolver()
            data = [self]
            command_line = m.resolve_command(self.check_command, data)
            
            #Make the Check object and put the service in checking
            #print "Asking for a check with command:", command_line
            c = Check('scheduled',command_line, self.id, 'host', t, ref_check)
            
            #We keep a trace of all checks in progress
            #to know if we are in checking_or not
            self.checks_in_progress.append(c)
        self.update_in_checking()
        #We need to return the check for scheduling adding
        return c




class Hosts(Items):
    name_property = "host_name" #use for the search by name
    inner_class = Host #use for know what is in items

    #Create link between elements:
    #hosts -> timeperiods
    #hosts -> hosts (parents, etc)
    #hosts -> commands (check_command)
    #hosts -> contacts
    def linkify(self, timeperiods=None, commands=None, contacts=None):
        self.linkify_h_by_tp(timeperiods)
        self.linkify_h_by_h()
        self.linkify_h_by_cmd(commands)
        self.linkify_h_by_c(contacts)

    #Simplify notif_period and check period by timeperiod id
    def linkify_h_by_tp(self, timeperiods):
        for h in self:
            #print "Linify ", h
            try:
                #notif period
                ntp_name = h.notification_period
                ntp = timeperiods.find_by_name(ntp_name)
                h.notification_period = ntp
                #check period
                ctp_name = h.check_period
                ctp = timeperiods.find_by_name(ctp_name)
                h.check_period = ctp
            except AttributeError as exp:
                pass #Will be catch at the is_correct moment
    

    #Link host with hosts (parents)
    def linkify_h_by_h(self):
        for h in self:
            parents = h.parents
            #The new member list
            new_parents = []
            for parent in parents:
                new_parents.append(self.find_by_name(parent))
            #print "Me,", h.host_name, "define my parents", new_parents
            #We find the id, we remplace the names
            h.parents = new_parents

    
    #Link hosts with commands
    def linkify_h_by_cmd(self, commands):
        for h in self:
            h.check_command = CommandCall(commands, h.check_command)


    #Link with conacts
    def linkify_h_by_c(self, contacts):
        for h in self:
            if hasattr(h, 'contacts'):
                contacts_tab = h.contacts.split(',')
                new_contacts = []
                for c_name in contacts_tab:
                    c_name = c_name.strip()
                    c = contacts.find_by_name(c_name)
                    new_contacts.append(c)
                
                h.contacts = new_contacts


    #We look for hostgroups property in hosts and
    def explode(self, hostgroups, contactgroups):
        #Hostgroups property need to be fullfill for got the informations
        #self.apply_partial_inheritance('hostgroups')
        #self.apply_partial_inheritance('contact_groups')
        
        #Explode host in the hostgroups
        for h in self:
            if not h.is_tpl():
                hname = h.host_name
                if hasattr(h, 'hostgroups'):
                    hgs = h.hostgroups.split(',')
                    for hg in hgs:
                        hostgroups.add_member(hname, hg.strip())
        
        #We add contacts of contact groups into the contacts prop
        for h in self:#.items:
            if hasattr(h, 'contact_groups'):
                cgnames = h.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if hasattr(h, 'contacts'):
                            h.contacts += ','+cnames
                        else:
                            h.contacts = cnames

        
    #Create depenancies:
    #Parent graph: use to find quickly relations between all host, and loop
    #Depencies at the host level: host parent
    def apply_dependancies(self):
        #Create parent graph
        self.parents = pygraph.digraph()
        #0 is shinken node
        self.parents.add_node(0)
        for h in self:#.items.values():
            id = h.id
            if id not in self.parents:
                self.parents.add_node(id)
            #If there are parents, we update the parents node
            if len(h.parents) >= 1:
                for parent in h.parents:
                    if parent is not None:
                        parent_id = parent.id
                        if parent_id not in self.parents:
                            self.parents.add_node(parent_id)
                        self.parents.add_edge(parent_id, id)
                        #print "Add relation between", parent_id, id
            else: #host without parent are shinken childs
                #print "Add relation between", 0, id
                self.parents.add_edge(0, id)
        print "Loop: ", pygraph.algorithms.cycles.find_cycle(self.parents)#.find_cycle()
        #print "Fin loop check"
        
        for h in self: #.items.values():
            h.fill_parents_dependancie()
            
        #Debug
        #dot = self.parents.write(fmt='dot')
        #f = open('graph.dot', 'w')
        #f.write(dot)
        #f.close()
        #import os
        # Draw as a png (note: this requires the graphiz 'dot' program to be installed)
        #os.system('dot graph.dot -Tpng > hosts.png')
