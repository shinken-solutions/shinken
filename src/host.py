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
from pygraph import digraph
from item import Item, Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool
import time, random
from macroresolver import MacroResolver
from check import Check
from notification import Notification

class Host(SchedulingItem):
    id = 1 #0 is reserved for host (primary node for parents)
    ok_up = 'UP'

    #defined properties (from configuration)
    properties={'host_name': {'required': True},
                'alias': {'required':  True},
                'display_name': {'required': False, 'default':'none'},
                'address': {'required': True},
                'parents': {'required': False, 'default': '' , 'pythonize': to_split},
                'hostgroups': {'required': False, 'default' : ''},
                'check_command': {'required': False, 'default':''},
                'initial_state': {'required': False, 'default':'u', 'pythonize': to_char},
                'max_check_attempts': {'required': True , 'pythonize': to_int},
                'check_interval': {'required': False, 'default':'0', 'pythonize': to_int},
                'retry_interval': {'required': False, 'default':'0', 'pythonize': to_int},
                'active_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'passive_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'check_period': {'required': True},
                'obsess_over_host': {'required': False, 'default':'0' , 'pythonize': to_bool},
                'check_freshness': {'required': False, 'default':'0', 'pythonize': to_bool},
                'freshness_threshold': {'required': False, 'default':'0', 'pythonize': to_int},
                'event_handler': {'required': False, 'default':''},
                'event_handler_enabled': {'required': False, 'default':'0', 'pythonize': to_bool},
                'low_flap_threshold': {'required':False, 'default':'25', 'pythonize': to_int},
                'high_flap_threshold': {'required': False, 'default':'50', 'pythonize': to_int},
                'flap_detection_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
                'flap_detection_options': {'required': False, 'default':'o,d,u', 'pythonize': to_split},
                'process_perf_data': {'required': False, 'default':'1', 'pythonize': to_bool},
                'retain_status_information': {'required': False, 'default':'1', 'pythonize': to_bool},
                'retain_nonstatus_information': {'required': False, 'default':'1', 'pythonize': to_bool},
                'contacts': {'required': True},
                'contact_groups': {'required': True},
                'notification_interval': {'required': True, 'pythonize': to_int},
                'first_notification_delay': {'required': False, 'default':'0', 'pythonize': to_int},
                'notification_period': {'required': True},
                'notification_options': {'required': False, 'default':'d,u,r,f', 'pythonize': to_split},
                'notifications_enabled': {'required': False, 'default':'1', 'pythonize': to_bool},
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
        'services' : [],
        'checks_in_progress' : [],
        'downtimes' : [],
        'flapping_changes' : [],
        'percent_state_change' : 0.0
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
    #template are always correct
    #contacts OR contactgroups is need
    def is_correct(self):
        if self.is_tpl:
            return True
        for prop in Host.properties:
            if not self.has(prop) and Host.properties[prop]['required']:
                if prop == 'contacts' or prop == 'contacgroups':
                    pass
                else:
                    print "I do not have", prop
                    return False
        if self.has('contacts') or self.has('contacgroups'):
            return True
        else:
            print "I do not have contacts nor contacgroups"
            return False


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
        print "Me", self.host_name, "is getting my parents"
        print "I-ve got my parents", self.parents
        print "Before", self.act_depend_of
        for parent in self.parents:
            print "I add a daddy!", parent.host_name
            self.act_depend_of.append( (parent, ['d', 'u', 's', 'f'], 'network_dep', None) )
        print "finnaly : ", self.act_depend_of


    #Create notifications but without commands. It will be update juste before being send
    def create_notifications(self, type):
        notifications = []
        now = time.time()
        t = self.notification_period.get_next_valid_time_from_t(now)
        print "HOST: We are creating a notification for", time.asctime(time.localtime(t))
        for contact in self.contacts:
            for cmd in contact.host_notification_commands:
                #create without real command, it will be update just before being send
                notifications.append(Notification(type, 'scheduled', 'VOID', {'host' : self.id, 'contact' : contact.id, 'command': cmd}, 'host', t))
        return notifications


    #We are just going to launch the notif to the poller
    #so we must actualise the command (Macros)
    def update_notification(self, n,  contact):
        m = MacroResolver()
        command = n.ref['command']
        n._command = m.resolve_command(command, self, None, contact, n)


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        return now > n.t_to_go and self.state != 'UP' and  contact.want_host_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    def get_new_notification_from(self, n):
        now = time.time()
        return Notification(n.type, 'scheduled','', {'host' : n.ref['host'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'host', now + self.notification_interval * 60)


    #Check if the notificaton is still necessery
    def still_need(self, n):
        now = time.time()
        #if state != UP, the host still got a pb, so notification still necessery
        if self.state != 'UP':
            return True
        #state is UP but notif is in poller, so do not remove, will be done after
        if n.status == 'inpoller':
            return True
        #we do not see why to save this notification, so...
        return False


    #Is in checking if and ony if there are still checks no consumed    
    def update_in_checking(self):
        self.in_checking = (len(self.checks_in_progress) != 0)
    

    #return a check to check the host
    def launch_check(self, t , ref_check_id = None):
        c = None
        if not self.is_no_check_dependant():
            #Get the command to launch
            m = MacroResolver()
            command_line = m.resolve_command(self.check_command, self, None, None, None)
            
            #Make the Check object and put the service in checking
            print "Asking for a check with command:", command_line
            c = Check('scheduled',command_line, self.id, 'host', self.next_chk, ref_check_id)
            
            #We keep a trace of all checks in progress
            #to know if we are in checking_or not
            self.checks_in_progress.append(c.id)
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
            print "Linify ", h
            try:
                #notif period
                ntp_name = h.notification_period
                ntp = timeperiods.find_by_name(ntp_name)
                h.notification_period = ntp
                #check period
                ctp_name = h.check_period
                ctp = timeperiods.find_by_name(ctp_name)
                h.check_period = ctp
            except AttributeError (exp):
                print exp
    

    #Link host with hosts (parents)
    def linkify_h_by_h(self):
        for h in self:
            parents = h.parents
            #The new member list
            new_parents = []
            for parent in parents:
                new_parents.append(self.find_by_name(parent))
            print "Me,", h.host_name, "define my parents", new_parents
            #We find the id, we remplace the names
            h.parents = new_parents

    
    #Link hosts with commands
    def linkify_h_by_cmd(self, commands):
        for h in self:
            h.check_command = CommandCall(commands, h.check_command)


    #Link with conacts
    def linkify_h_by_c(self, contacts):
        for h in self:
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
        self.apply_partial_inheritance('hostgroups')
        self.apply_partial_inheritance('contact_groups')
        
        #Explode host in the hostgroups
        for h in self:
            if not h.is_tpl():
                hname = h.host_name
                if h.has('hostgroups'):
                    hgs = h.hostgroups.split(',')
                    for hg in hgs:
                        hostgroups.add_member(hname, hg.strip())
        
        #We add contacts of contact groups into the contacts prop
        for h in self:#.items:
            if h.has('contact_groups'):
                cgnames = h.contact_groups.split(',')
                for cgname in cgnames:
                    cgname = cgname.strip()
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add hosts in the service host_name
                    if cnames != []:
                        if h.has('contacts'):
                            h.contacts += ','+cnames
                        else:
                            h.contacts = cnames

        
    #Create depenancies:
    #Parent graph: use to find quickly relations between all host, and loop
    #Depencies at the host level: host parent
    def apply_dependancies(self):
        #Create parent graph
        self.parents = digraph()
        #0 is pynag node
        self.parents.add_node(0)
        for h in self:#.items.values():
            id = h.id
            if id not in self.parents:
                self.parents.add_node(id)
            #If there are parents, we update the parents node
            if len(h.parents) >= 1:
                for parent in h.parents:
                    parent_id = parent.id
                    if parent_id not in self.parents:
                        self.parents.add_node(parent_id)
                    self.parents.add_edge(parent_id, id)
                    print "Add relation between", parent_id, id
            else:#host without parent are pynag childs
                print "Add relation between", 0, id
                self.parents.add_edge(0, id)
        print "Loop: ", self.parents.find_cycle()
        #print "Fin loop check"
        
        for h in self:#.items.values():
            h.fill_parents_dependancie()
            
        #Debug
        #dot = self.parents.write(fmt='dot')
        #f = open('graph.dot', 'w')
        #f.write(dot)
        #f.close()
        #import os
        # Draw as a png (note: this requires the graphiz 'dot' program to be installed)
        #os.system('dot graph.dot -Tpng > hosts.png')
