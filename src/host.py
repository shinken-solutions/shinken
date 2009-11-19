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

#import pygraph
import time

#from pygraph.digraph import digraph
import pygraph

from pygraph.algorithms.cycles import find_cycle
from command import CommandCall
from item import Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool
from macroresolver import MacroResolver
from check import Check
from notification import Notification


class Host(SchedulingItem):
    __slots__ = ('id', 'host_name', \
                     'display_name', 'hostgroups', 'check_command', \
                     'initial_state', 'max_check_attempts', 'check_interval',\
                     'retry_interval', 'active_checks_enabled', 'passive_checks_enabled',\
                     'check_period', 'obsess_over_host', 'check_freshness',\
                     'freshness_threshold', 'event_handler', 'event_handler_enabled', \
                     'low_flap_threshold', 'high_flap_threshold', 'flap_detection_enabled', \
                     'flap_detection_options', 'process_perf_data', 'retain_status_information', \
                     'retain_nonstatus_information', 'notification_interval', \
                     'first_notification_delay', 'notification_period', 'notification_options', \
                     'notifications_enabled', 'contacts', 'contact_groups', 'stalking_options', \
                     'notes', 'notes_url', 'action_url', 'icon_image', 'icon_image_alt', \
                     'failure_prediction_enabled', 'parallelize_check' ,\
                     #Now the running part
                     'last_chk', 'next_chk', 'in_checking', 'latency', 'attempt', 'state', \
                     'state_id', 'current_event_id', 'last_event_id', 'last_state_id', \
                     'last_state_change', 'last_hard_state_change', 'last_hard_state', \
                     'state_type', 'state_type_id', 'output', 'long_output', 'is_flapping', \
                     'is_in_downtime', 'act_depend_of', 'chk_depend_of', 'last_state_update', \
                     'checks_in_progress', 'downtimes', 'flapping_changes', \
                     'flapping_comment_id', 'percent_state_change', \
                     'problem_has_been_acknowledged', 'acknowledgement_type', 'check_type', \
                     'has_been_checked', 'should_be_scheduled', 'last_problem_id', \
                     'current_problem_id', 'execution_time', 'last_notification', \
                     'current_notification_number', 'current_notification_id', \
                     'check_flapping_recovery_notification', 'scheduled_downtime_depth', \
                     'pending_flex_downtime', 'timeout', 'start_time', 'end_time', 'early_timeout', \
                     'return_code', 'perf_data', 'notifications_in_progress', 'customs', 'services', \
                     'realm'
                 )

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
                'alias': {'required':  True, 'status_broker_name' : None},
                'display_name': {'required': False, 'default':'none', 'status_broker_name' : None},
                'address': {'required': True, 'status_broker_name' : None},
                'parents': {'required': False, 'default': '' , 'pythonize': to_split},
                'hostgroups': {'required': False, 'default' : ''},
                'check_command': {'required': False, 'default':''},
                'initial_state': {'required': False, 'default':'u', 'pythonize': to_char, 'status_broker_name' : None},
                'max_check_attempts': {'required': True , 'pythonize': to_int, 'status_broker_name' : None},
                'check_interval': {'required': False, 'default':'0', 'pythonize': to_int, 'status_broker_name' : None},
                'retry_interval': {'required': False, 'default':'0', 'pythonize': to_int, 'status_broker_name' : None},
                'active_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'passive_checks_enabled': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
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
                'notification_interval': {'required': False, 'default':'60', 'pythonize': to_int, 'status_broker_name' : None},
                'first_notification_delay': {'required': False, 'default':'0', 'pythonize': to_int, 'status_broker_name' : None},
                'notification_period': {'required': True},
                'notification_options': {'required': False, 'default':'d,u,r,f', 'pythonize': to_split},
                'notifications_enabled': {'required': False, 'default':'1', 'pythonize': to_bool, 'status_broker_name' : None},
                'stalking_options': {'required': False, 'default':'', 'pythonize': to_split},
                'notes': {'required': False, 'default':'', 'status_broker_name' : None},
                'notes_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'action_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'icon_image': {'required': False, 'default':''},
                'icon_image_alt': {'required': False, 'default':''},
                'vrml_image': {'required': False, 'default':''},
                'statusmap_image': {'required': False, 'default':''},
                '2d_coords': {'required': False, 'default':''},
                '3d_coords': {'required': False, 'default':''},
                'failure_prediction_enabled': {'required' : False, 'default' : '0', 'pythonize': to_bool},
                #New to shinken
                'realm' : {'required': False, 'default':None}
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
        'state_type' : {'default' : 'HARD'},
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
        'notifications_in_progress' : {'default' : {}},
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
        'perf_data' : {'default' : '', 'broker_name' : None},
        'services' : {'default' : []},
        'customs' : {'default' : {}}
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
              'HOSTEXECUTIONTIME' : 'execution_time',
              'HOSTDURATION' : 'get_duration',
              'HOSTDURATIONSEC' : 'get_duration_sec',
              'HOSTDOWNTIME' : 'get_downtime',
              'HOSTPERCENTCHANGE' : 'percent_state_change',
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


    #Call by picle for dataify service
    #Here we do not want a dict, it's too heavy
    #We create a list with properties inlined
    #The setstate function do the inverse
    def __getstate__(self):
        cls = self.__class__
        #id is not in *_properties
        res = [self.id] 
        for prop in cls.properties:
            res.append(getattr(self, prop))
        for prop in cls.running_properties:
            res.append(getattr(self, prop))
        #We reverse because we want to recreate
        #By check at properties in the same order
        res.reverse()
        return res


    #Inversed funtion of getstate
    def __setstate__(self, state):
        cls = self.__class__
        self.id = state.pop()
        for prop in cls.properties:
            setattr(self, prop, state.pop())
        for prop in cls.running_properties:
            setattr(self, prop, state.pop())



    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['contacts', 'contactgroups', 'check_period', \
                                  'notification_interval', 'check_period']
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
        #If active check is enabled with a check_interval!=0, we must have a check_timeperiod
        if (hasattr(self, 'active_checks_enabled') and self.active_checks_enabled) and (not hasattr(self, 'check_period') or self.check_period == None) and (hasattr(self, 'check_interval') and self.check_interval!=0):
            print self.active_checks_enabled, self.check_interval
            print self.get_name()," : My check_timeperiod is not correct"
            state = False
        return state


    #Search in my service if I've got the service
    def find_service_by_name(self, service_description):
        for s in self.services:
            if s.service_description == service_description:
                return s
        return None


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
            self.state_id = 0
        elif status == 1 or status == 2 or status == 3:
            self.state = 'DOWN'
            self.state_id = 2
        else:
            self.state = 'DOWN'#exit code UNDETERMINED
            self.state_id = 2
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


    #Is stalking ?
    #Launch if check is waitconsume==first time
    #and if c.status is in self.stalking_options
    def manage_stalking(self, c):
        need_stalk = False
        if c.status == 'waitconsume':
            if c.exit_status==0 and 'o' in self.stalking_options:
                need_stalk = True
            elif c.exit_status==1 and 'd' in self.stalking_options:
                need_stalk = True
            elif c.exit_status==2 and 'd' in self.stalking_options:
                need_stalk = True
            elif c.exit_status==3 and 'u' in self.stalking_options:
                need_stalk = True
            if c.output != self.output:
                need_stalk = False
        if need_stalk:
            #TODO : make a real log mangment
            print "Stalking", self.output



    #fill act_depend_of with my parents (so network dep)
    def fill_parents_dependancie(self):
        for parent in self.parents:
            if parent is not None:
                self.act_depend_of.append( (parent, ['d', 'u', 's', 'f'], 'network_dep', None) )


    #Give data for checks's macros
    def get_data_for_checks(self):
        return [self]

    #Give data for event handler's macro
    def get_data_for_event_handler(self):
        return [self]

    #Give data for notifications'n macros
    def get_data_for_notifications(self, contact, n):
        return [self, contact, n]


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        return now > n.t_to_go and self.state != 'UP' and contact.want_host_notification(now, self.state)
            

    #We just send a notification, we need new ones in notification_interval
    #def get_new_notification_from(self, n):
    #    now = time.time()
    #    return Notification(n.type, 'scheduled', '', {'host' : n.ref['host'], 'contact' : n.ref['contact'], 'command': n.ref['command']}, 'host', now + self.notification_interval * 60)


    #Check if the notificaton is still necessery
    #def still_need(self, n):
    #    now = time.time()
    #    #if state != UP, the host still got a pb
    #    #, so notification still necessery
    #    if self.state != 'UP':
    #        return True
    #    #state is UP but notif is in poller, 
    #    #so do not remove, will be done after
    #    if n.status == 'inpoller':
    #        return True
    #    #we do not see why to save this notification, so...
    #    return False




class Hosts(Items):
    name_property = "host_name" #use for the search by name
    inner_class = Host #use for know what is in items

    #Create link between elements:
    #hosts -> timeperiods
    #hosts -> hosts (parents, etc)
    #hosts -> commands (check_command)
    #hosts -> contacts
    def linkify(self, timeperiods=None, commands=None, contacts=None, realms=None):
        self.linkify_h_by_tp(timeperiods)
        self.linkify_h_by_h()
        self.linkify_h_by_cmd(commands)
        self.linkify_h_by_c(contacts)
        self.linkify_h_by_realms(realms)

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
        for h in self:
            if h.event_handler != '':
                h.event_handler = CommandCall(commands, h.event_handler)
            else:
                h.event_handler = None

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
    
    
    def linkify_h_by_realms(self, realms):
        for h in self:
            #print h.get_name(), h.realm
            if h.realm != None:
                name = h.realm
                p = realms.find_by_name(h.realm.strip())
                h.realm = p
                if p != None:
                    print "Me", h.get_name(), "have a realm", p

    
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
        parents = pygraph.digraph()
        #0 is shinken node
        parents.add_node(0)
        for h in self:#.items.values():
            id = h.id
            if id not in parents:
                parents.add_node(id)
            #If there are parents, we update the parents node
            if len(h.parents) >= 1:
                for parent in h.parents:
                    if parent is not None:
                        parent_id = parent.id
                        if parent_id not in parents:
                            parents.add_node(parent_id)
                        parents.add_edge(parent_id, id)
                        #print "Add relation between", parent_id, id
            else: #host without parent are shinken childs
                #print "Add relation between", 0, id
                parents.add_edge(0, id)
        print "Loop: ", find_cycle(parents)#.find_cycle()
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
