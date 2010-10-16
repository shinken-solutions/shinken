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


import time

from autoslots import AutoSlots
from command import CommandCall
from item import Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool, strip_and_uniq, format_t_into_dhms_format, to_svc_hst_distinct_lists
from check import Check
from notification import Notification
from macroresolver import MacroResolver
from eventhandler import EventHandler
from log import Log

class Service(SchedulingItem):
    #AutoSlots create the __slots__ with properties and
    #running_properties names
    __metaclass__ = AutoSlots

    id = 1 # Every service have a unique ID, and 0 is always special in database and co...
    ok_up = 'OK' # The host and service do not have the same 0 value, now yes :)

    my_type = 'service' #used by item class for format specific value like for Broks

    #properties defined by configuration
    #required : is required in conf
    #default : default value if no set in conf
    #pythonize : function to call when transfort string to python object
    #fill_brok : if set, send to broker. there are two categories: full_status for initial and update status, check_result for check results
    #no_slots : do not take this property for __slots__
    properties={
        'host_name' : {'required' : True, 'fill_brok' : ['full_status', 'check_result', 'next_schedule']},
        'hostgroup_name' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'service_description' : {'required' : True, 'fill_brok' : ['full_status', 'check_result', 'next_schedule']},
        'display_name' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'servicegroups' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'is_volatile' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_command' : {'required' : True, 'fill_brok' : ['full_status']},
        'initial_state' : {'required' : False, 'default' : 'o', 'pythonize' : to_char, 'fill_brok' : ['full_status']},
        'max_check_attempts' : {'required' : True, 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'check_interval' : {'required' : True, 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'retry_interval' : {'required' : True, 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'active_checks_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'passive_checks_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'obsess_over_service' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_freshness' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'freshness_threshold' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'event_handler' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'event_handler_enabled' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'low_flap_threshold' : {'required' : False, 'default' : '-1', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'high_flap_threshold' : {'required' : False, 'default' : '-1', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'flap_detection_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'flap_detection_options' : {'required' : False, 'default' : 'o,w,c,u', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'process_perf_data' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_status_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_nonstatus_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'notification_interval' : {'required' : False, 'default' : '60', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'first_notification_delay' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'notification_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'notification_options' : {'required' : False, 'default' : 'w,u,c,r,f,s', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'notifications_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'contacts' : {'required' : True, 'fill_brok' : ['full_status']},
        'contact_groups' : {'required' : True, 'fill_brok' : ['full_status']},
        'stalking_options' : {'required' : False, 'default' : '', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'notes' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'notes_url' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'action_url' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'icon_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'icon_image_alt' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'failure_prediction_enabled' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'parallelize_check' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},

        #Shinken specific
        'poller_tag' : {'required' : False, 'default' : None},
        
        'resultmodulations' : {'required' : False, 'default' : ''},
        'escalations' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'maintenance_period' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        }
    
    #properties used in the running state
    running_properties = {
        'last_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'next_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'next_schedule']},
        'in_checking' : {'default' : False, 'fill_brok' : ['full_status'], 'retention' : True},
        'latency' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'attempt' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'state' : {'default' : 'PENDING', 'fill_brok' : ['full_status'], 'retention' : True},
        'state_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'current_event_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_event_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_state' : {'default' : 'PENDING', 'fill_brok' : ['full_status'], 'retention' : True},
        'last_state_id' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'last_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'last_hard_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'last_hard_state' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'last_time_ok' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_time_warning' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_time_critical' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_time_unknown' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'duration_sec' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'state_type' : {'default' : 'HARD', 'fill_brok' : ['full_status'], 'retention' : True},
        'state_type_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'long_output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'is_flapping' : {'default' : False, 'fill_brok' : ['full_status'], 'retention' : True},
        'act_depend_of' : {'default' : [] }, #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : {'default' : []}, #dependencies for checks raise, so BEFORE checks

        'act_depend_of_me' : {'default' : [] }, #elements that depend of me, so the reverse than just uppper
        'chk_depend_of_me' : {'default' : []}, #elements that depend of me
        
        'last_state_update' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'checks_in_progress' : {'default' : []}, # no brok because checks are too linked
        'notifications_in_progress' : {'default' : {}, 'retention' : True}, # no broks because notifications are too linked
        'downtimes' : {'default' : [], 'fill_brok' : ['full_status']},
        'comments' : {'default' : [], 'fill_brok' : ['full_status'], 'retention' : True},
        'flapping_changes' : {'default' : [], 'fill_brok' : ['full_status'], 'retention' : True},
        'flapping_comment_id' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'percent_state_change' : {'default' : 0.0, 'fill_brok' : ['full_status'], 'retention' : True},
        'problem_has_been_acknowledged' : {'default' : False, 'fill_brok' : ['full_status'], 'retention' : True},
        'acknowledgement' : {'default' : None, 'retention' : True},
        'acknowledgement_type' : {'default' : 1, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'check_type' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'has_been_checked' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'should_be_scheduled' : {'default' : 1, 'fill_brok' : ['full_status'], 'retention' : True},
        'last_problem_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'current_problem_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'execution_time' : {'default' : 0.0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_notification' : {'default' : time.time(), 'fill_brok' : ['full_status'], 'retention' : True},
        'current_notification_number' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'current_notification_id' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'check_flapping_recovery_notification' : {'default' : True, 'fill_brok' : ['full_status'], 'retention' : True},
        'scheduled_downtime_depth' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'pending_flex_downtime' : {'default' : 0, 'fill_brok' : ['full_status'], 'retention' : True},
        'timeout' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'start_time' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'end_time' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'early_timeout' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'return_code' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'perf_data' : {'default' : '', 'fill_brok' : ['full_status', 'check_result'], 'retention' : True},
        'last_perf_data' : {'default' : '', 'retention' : True},
        'host' : {'default' : None},
        'customs' : {'default' : {}},
        'notified_contacts' : {'default' : set()}, #use for having all contacts we have notified
        'in_scheduled_downtime' : {'default' : False, 'retention' : True},
        'in_scheduled_downtime_during_last_check' : {'default' : False, 'retention' : True}, 
        'actions' : {'default' : []}, #put here checks and notif raised
        'broks' : {'default' : []}, #and here broks raised

        #All errors and warning raised during the configuration parsing
        #and taht will raised real warning/errors during the is_correct
        'configuration_warnings' : {'default' : []},
        'configuration_errors' : {'default' : []},
        
        #Problem/impact part
        'is_problem' : {'default' : False, 'fill_brok' : ['full_status']},
        'is_impact' : {'default' : False, 'fill_brok' : ['full_status']},
        'source_problems' : {'default' : [], 'fill_brok' : ['full_status'], 'brok_transformation' : to_svc_hst_distinct_lists}, # list of problems that make us an impact
        'impacts' : {'default' : [], 'fill_brok' : ['full_status'], 'brok_transformation' : to_svc_hst_distinct_lists}, #list of the impact I'm the cause of
        'state_before_impact' : {'default' : 'PENDING'}, #keep a trace of the old state before being an impact
        'state_id_before_impact' : {'default' : 0}, #keep a trace of the old state id before being an impact
        'state_changed_since_impact' : {'default' : False}, #if teh state change, we know so we do not revert it

        #Easy Service dep definition
        'service_dependencies' : {'required' : False, 'default' : '', 'pythonize' : to_split}, #TODO : find a way to brok it?
        
        }

    #Mapping between Macros and properties (can be prop or a function)
    macros = {
        'SERVICEDESC' : 'service_description',
        'SERVICEDISPLAYNAME' : 'display_name',
        'SERVICESTATE' : 'state',
        'SERVICESTATEID' : 'state_id',
        'LASTSERVICESTATE' : 'last_state',
        'LASTSERVICESTATEID' : 'last_state_id',
        'SERVICESTATETYPE' : 'state_type',
        'SERVICEATTEMPT' : 'attempt',
        'MAXSERVICEATTEMPTS' : 'max_check_attempts',
        'SERVICEISVOLATILE' : 'is_volatile',
        'SERVICEEVENTID' : 'current_event_id',
        'LASTSERVICEEVENTID' : 'last_event_id',
        'SERVICEPROBLEMID' : 'current_problem_id',
        'LASTSERVICEPROBLEMID' : 'last_problem_id',
        'SERVICELATENCY' : 'latency',
        'SERVICEEXECUTIONTIME' : 'execution_time',
        'SERVICEDURATION' : 'get_duration',
        'SERVICEDURATIONSEC' : 'get_duration_sec',
        'SERVICEDOWNTIME' : 'get_downtime',
        'SERVICEPERCENTCHANGE' : 'percent_state_change',
        'SERVICEGROUPNAME' : 'get_groupname',
        'SERVICEGROUPNAMES' : 'get_groupnames',
        'LASTSERVICECHECK' : 'last_chk',
        'LASTSERVICESTATECHANGE' : 'last_state_change',
        'LASTSERVICEOK' : 'last_time_ok',
        'LASTSERVICEWARNING' : 'last_time_warning',
        'LASTSERVICEUNKNOWN' : 'last_time_unknown',
        'LASTSERVICECRITICAL' : 'last_time_critical',
        'SERVICEOUTPUT' : 'output',
        'LONGSERVICEOUTPUT' : 'long_output',
        'SERVICEPERFDATA' : 'perf_data',
        'LASTSERVICEPERFDATA' : 'last_perf_data',
        'SERVICECHECKCOMMAND' : 'get_check_command',
        'SERVICEACKAUTHOR' : 'get_ack_author_name',
        'SERVICEACKAUTHORNAME' : 'get_ack_author_name',
        'SERVICEACKAUTHORALIAS' : 'get_ack_author_name',
        'SERVICEACKCOMMENT' : 'get_ack_comment',
        'SERVICEACTIONURL' : 'action_url',
        'SERVICENOTESURL' : 'notes_url',
        'SERVICENOTES' : 'notes'
        }

    #This tab is used to transform old parameters name into new ones
    #so from Nagios2 format, to Nagios3 ones
    old_properties = {
        'normal_check_interval' : 'check_interval',
        'retry_check_interval' : 'retry_interval'
        }
        

    #Give a nice name output
    def get_name(self):
        return self.service_description


    #Need the whole name for debugin purpose
    def get_dbg_name(self):
        return "%s/%s" % (self.host.host_name, self.service_description)

    
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
    #template are always correct
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        special_properties = ['contacts', 'contact_groups', 'check_period', \
                                  'notification_interval', 'host_name', \
                                  'hostgroup_name']
        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    Log().log('%s : I do not have %s' % (self.get_name(), prop))
                    state = False #Bad boy...

        #Raised all previously saw errors like unknown contacts and co
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                Log().log(err)

        #Ok now we manage special cases...
        if not hasattr(self, 'contacts') and not hasattr(self, 'contact_groups') and  self.notifications_enabled == True:
            Log().log('%s : I do not have contacts nor contact_groups' % self.get_name())
            state = False
        if not hasattr(self, 'check_command'):
            Log().log("%s : I've got no check_command" % self.get_name())
            state = False
        #Ok got a command, but maybe it's invalid
        else:
            if not self.check_command.is_valid():
                Log().log("%s : my check_command %s is invalid" % (self.get_name(), self.check_command.command))
                state = False
        if not hasattr(self, 'notification_interval') and  self.notifications_enabled == True:
            Log().log("%s : I've got no notification_interval but I've got notifications enabled" % self.get_name())
            state = False
        if not hasattr(self, 'host') or self.host == None:
            Log().log("%s : I do not have an host" % self.get_name())
            state = False
        if not hasattr(self, 'check_period'):
            self.check_period = None
        if hasattr(self, 'service_description'):
            for c in cls.illegal_object_name_chars:
                if c in self.service_description:
                    Log().log("%s : My service_description got the caracter %s that is not allowed." % (self.get_name(), c))
                    state = False
        return state



    #The service is dependent of his father dep
    #Must be AFTER linkify
    def fill_daddy_dependancy(self):
        #Depend of host, all status, is a networkdep and do not have timeperiod, and folow parents dep
        if self.host is not None:
            #I add the dep in MY list
            self.act_depend_of.append( (self.host, ['d', 'u', 's', 'f'], 'network_dep', None, True) )
            #I add the dep in Daddy list
            self.host.act_depend_of_me.append( (self, ['d', 'u', 's', 'f'], 'network_dep', None, True) )


    #Register the dependancy between 2 service for action (notification etc)    
    def add_service_act_dependancy(self, srv, status, timeperiod, inherits_parent):
        #first I add the other the I depend on in MY list
        self.act_depend_of.append( (srv, status, 'logic_dep', timeperiod, inherits_parent) )
        #then I register myself in the other service dep list
        srv.act_depend_of_me.append( (self, status, 'logic_dep', timeperiod, inherits_parent) )


    #Register the dependancy between 2 service for checks
    def add_service_chk_dependancy(self, srv, status, timeperiod, inherits_parent):
        #first I add the other the I depend on in MY list
        self.chk_depend_of.append( (srv, status, 'logic_dep', timeperiod, inherits_parent) )
        #then I register myself in the other service dep list
        srv.chk_depend_of_me.append( (self, status, 'logic_dep', timeperiod, inherits_parent) )


    #Set unreachable : our host is DOWN, but it mean nothing for a service
    def set_unreachable(self):
        pass


    #We just go an impact, so we go unreachable
    #but only if it's enable in the configuration
    def set_impact_state(self):
        cls = self.__class__
        if cls.enable_problem_impacts_states_change:
            #Keep a trace of the old state (problem came back before
            #a new checks)
            self.state_before_impact = self.state
            self.state_id_before_impact = self.state_id
            #this flag will know if we overide the impact state
            self.state_changed_since_impact = False
            self.state = 'UNKNOWN'#exit code UNDETERMINED
            self.state_id = 3


    #Ok, we are no more an impact, if no news checks
    #overide the impact state, we came back to old
    #states
    #And only if we enable the state change for impacts
    def unset_impact_state(self):
        cls = self.__class__
        if cls.enable_problem_impacts_states_change and not self.state_changed_since_impact:
            self.state = self.state_before_impact
            self.state_id = self.state_id_before_impact
            #print "Reverting ME %s states to %s %s" % (self.get_dbg_name(), self.state, self.state_id)


    #Set state with status return by the check
    #and update flapping state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now


        #we should put in last_state the good last state:
        #if not just change the state by an problem/impact
        #we can take current state. But if it's the case, the
        #real old state is self.state_before_impact (it's teh TRUE
        #state in fact)
        #but only if the global conf have enable the impact state change
        cls = self.__class__
        if cls.enable_problem_impacts_states_change and self.is_impact and not self.state_changed_since_impact:
            #print "Me %s take standard state %s" % (self.get_dbg_name(), self.state)
            self.last_state = self.state_before_impact
        else: #standard case
            #print "Me %s take impact state %s and not %s" % (self.get_dbg_name(), self.state_before_impact, self.state)
            self.last_state = self.state

        if status == 0:
            self.state = 'OK'
            self.state_id = 0
            self.last_time_ok = int(self.last_state_update)
            state_code = 'o'
        elif status == 1:
            self.state = 'WARNING'
            self.state_id = 1
            self.last_time_warning = int(self.last_state_update)
            state_code = 'w'
        elif status == 2:
            self.state = 'CRITICAL'
            self.state_id = 2
            self.last_time_critical = int(self.last_state_update)
            state_code = 'c'
        elif status == 3:
            self.state = 'UNKNOWN'
            self.state_id = 3
            self.last_time_unknown = int(self.last_state_update)
            state_code = 'u'
        else:
            self.state = 'CRITICAL'#exit code UNDETERMINED
            self.state_id = 2
            self.last_time_critical = int(self.last_state_update)
            state_code = 'c'

        if state_code in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)

        if self.state != self.last_state:
            self.last_state_change = self.last_state_update

        self.duration_sec = now - self.last_state_change


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


    #The last time when the state was not OK 
    def last_time_non_ok_or_up(self):
        non_ok_times = filter(lambda x: x > self.last_time_ok, [self.last_time_warning, self.last_time_critical, self.last_time_unknown])
        if len(non_ok_times) == 0:
            last_time_non_ok = 0 # program_start would be better
        else:
            last_time_non_ok = min(non_ok_times)
        return last_time_non_ok


    #Add a log entry with a SERVICE ALERT like:
    #SERVICE ALERT: server;Load;UNKNOWN;HARD;1;I don't know what to say...
    def raise_alert_log_entry(self):
        Log().log('SERVICE ALERT: %s;%s;%s;%s;%d;%s' % (self.host.get_name(), self.get_name(), self.state, self.state_type, self.attempt, self.output))


    #Add a log entry with a Freshness alert like:
    #Warning: The results of host 'Server' are stale by 0d 0h 0m 58s (threshold=0d 1h 0m 0s).
    #I'm forcing an immediate check of the host.
    def raise_freshness_log_entry(self, t_stale_by, t_threshold):
        Log().log("Warning: The results of service '%s' on host '%s' are stale by %s (threshold=%s).  I'm forcing an immediate check of the service." \
                      % (self.get_name(), self.host.get_name(), format_t_into_dhms_format(t_stale_by), format_t_into_dhms_format(t_threshold)))


    #Raise a log entry with a Notification alert like
    #SERVICE NOTIFICATION: superadmin;server;Load;OK;notify-by-rss;no output
    def raise_notification_log_entry(self, n):
        contact = n.contact
        command = n.command_call
        if n.type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED', 'CUSTOM', 'ACKNOWLEDGEMENT', 'FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            state = '%s (%s)' % (n.type, self.state)
        else:
            state = self.state
        if self.__class__.log_notifications:
            Log().log("SERVICE NOTIFICATION: %s;%s;%s;%s;%s;%s" % (contact.get_name(), self.host.get_name(), self.get_name(), state, \
                command.get_name(), self.output))


    #Raise a log entry with a Eventhandler alert like
    #SERVICE EVENT HANDLER: test_host_0;test_ok_0;OK;SOFT;4;eventhandler
    def raise_event_handler_log_entry(self, command):
        if self.__class__.log_event_handlers:
            Log().log("SERVICE EVENT HANDLER: %s;%s;%s;%s;%s;%s" % (self.host.get_name(), self.get_name(), self.state, self.state_type, self.attempt, \
                                                                       command.get_name()))

        
    #Raise a log entry with FLAPPING START alert like
    #SERVICE FLAPPING ALERT: server;LOAD;STARTED; Service appears to have started flapping (50.6% change >= 50.0% threshold)
    def raise_flapping_start_log_entry(self, change_ratio, threshold):
        Log().log("SERVICE FLAPPING ALERT: %s;%s;STARTED; Service appears to have started flapping (%.1f% change >= %.1% threshold)" % \
                      (self.host.get_name(), self.get_name(), change_ratio, threshold))


    #Raise a log entry with FLAPPING STOP alert like
    #SERVICE FLAPPING ALERT: server;LOAD;STOPPED; Service appears to have stopped flapping (23.0% change < 25.0% threshold)
    def raise_flapping_stop_log_entry(self, change_ratio, threshold):
        Log().log("SERVICE FLAPPING ALERT: %s;%s;STOPPED; Service appears to have stopped flapping (%.1f% change < %.1% threshold)" % \
                      (self.host.get_name(), self.get_name(), change_ratio, threshold))


    #If there is no valid time for next check, raise a log entry
    def raise_no_next_check_log_entry(self):
        Log().log("Warning : I cannot schedule the check for the service '%s' on host '%s' because there is not future valid time" % \
                      (self.get_name(), self.host.get_name()))


    #Raise a log entry when a downtime begins
    #SERVICE DOWNTIME ALERT: test_host_0;test_ok_0;STARTED; Service has entered a period of scheduled downtime
    def raise_enter_downtime_log_entry(self):
        Log().log("SERVICE DOWNTIME ALERT: %s;%s;STARTED; Service has entered a period of scheduled downtime" % \
                      (self.host.get_name(), self.get_name()))


    #Raise a log entry when a downtime has finished
    #SERVICE DOWNTIME ALERT: test_host_0;test_ok_0;STOPPED; Service has exited from a period of scheduled downtime
    def raise_exit_downtime_log_entry(self):
        Log().log("SERVICE DOWNTIME ALERT: %s;%s;STOPPED; Service has exited from a period of scheduled downtime" % \
                      (self.host.get_name(), self.get_name()))


    #Raise a log entry when a downtime prematurely ends
    #SERVICE DOWNTIME ALERT: test_host_0;test_ok_0;CANCELLED; Service has entered a period of scheduled downtime
    def raise_cancel_downtime_log_entry(self):
        Log().log("SERVICE DOWNTIME ALERT: %s;%s;CANCELLED; Scheduled downtime for service has been cancelled." % \
                      (self.host.get_name(), self.get_name()))


    #Is stalking ?
    #Launch if check is waitconsume==first time
    #and if c.status is in self.stalking_options
    def manage_stalking(self, c):
        need_stalk = False
        if c.status == 'waitconsume':
            if c.exit_status == 0 and 'o' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 1 and 'w' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 2 and 'c' in self.stalking_options:
                need_stalk = True
            elif c.exit_status == 3 and 'u' in self.stalking_options:
                need_stalk = True
            if c.output == self.output:
                need_stalk = False
        if need_stalk:
            Log().log("Stalking %s : %s" % (self.get_name(), c.output))


    #Give data for checks's macros
    def get_data_for_checks(self):
        return [self.host, self]


    #Give data for evetn handlers's macros
    def get_data_for_event_handler(self):
        return [self.host, self]


    #Give data for notifications'n macros
    def get_data_for_notifications(self, contact, n):
        return [self.host, self, contact, n]


    #See if the notification is launchable (time is OK and contact is OK too)
    def notification_is_blocked_by_contact(self, n, contact):
        return not contact.want_service_notification(self.last_chk, self.state, n.type)


    def get_duration_sec(self):
        return str(int(self.duration_sec))


    def get_duration(self):
        m, s = divmod(self.duration_sec, 60)
        h, m = divmod(m, 60)
        return "%02dh %02dm %02ds" % (h, m, s)


    def get_ack_author_name(self):
        if self.acknowledgement == None:
            return ''
        return self.acknowledgement.author

    def get_ack_comment(self):
        if self.acknowledgement == None:
            return ''
        return self.acknowledgement.comment


    def get_check_command(self):
        return self.check_command.get_name()


    #Check if a notification for this service is suppressed at this time
    def notification_is_blocked_by_item(self, type, t_wished = None):
        if t_wished == None:
            t_wished = time.time()

        # TODO
        # forced notification
        # pass if this is a custom notification
     
        # Block if notifications are program-wide disabled
        if not self.enable_notifications:
            return True

        # Does the notification period allow sending out this notification?
        if not self.notification_period.is_time_valid(t_wished):
            return True

        # Block if notifications are disabled for this service
        if not self.notifications_enabled:
            return True

        # Block if the current status is in the notification_options w,u,c,r,f,s
        if 'n' in self.notification_options:
            return True
        if type == 'PROBLEM' or type == 'RECOVERY':
            if self.state == 'UNKNOWN' and not 'u' in self.notification_options:
                return True
            if self.state == 'WARNING' and not 'w' in self.notification_options:
                return True
            if self.state == 'CRITICAL' and not 'c' in self.notification_options:
                return True
            if self.state == 'OK' and not 'r' in self.notification_options:
                return True
        if (type == 'FLAPPINGSTART' or type == 'FLAPPINGSTOP' or type == 'FLAPPINGDISABLED') and not 'f' in self.notification_options:
            return True
        if (type == 'DOWNTIMESTART' or type == 'DOWNTIMEEND' or type == 'DOWNTIMECANCELLED') and not 's' in self.notification_options:
            return True

        # Acknowledgements make no sense when the status is ok/up
        if type == 'ACKNOWLEDGEMENT':
            if self.state == self.ok_up:
                return True
        
        # When in downtime, only allow end-of-downtime notifications
        if self.scheduled_downtime_depth > 1 and (type != 'DOWNTIMEEND' or type != 'DOWNTIMECANCELLED'):
            return True
            
        # Block if host is in a scheduled downtime
        if self.host.scheduled_downtime_depth > 0:
            return True

        # Block if in a scheduled downtime and a problem arises
        if self.scheduled_downtime_depth > 0 and (type == 'PROBLEM' or type == 'RECOVERY'):
            return True

        # Block if the status is SOFT
        if self.state_type == 'SOFT' and type == 'PROBLEM':
            return True

        # Block if the problem has already been acknowledged
        if self.problem_has_been_acknowledged and type != 'ACKNOWLEDGEMENT':
            return True

        # Block if flapping
        if self.is_flapping:
            return True

        # Block if host is down
        if self.host.state != self.host.ok_up:
            return True

        return False
    
    
            

    #Get a oc*p command if item has obsess_over_*  
    #command. It must be enabled locally and globally
    def get_obsessive_compulsive_processor_command(self):
        cls = self.__class__
        print "class", cls.obsess_over
        if not cls.obsess_over or not hasattr(self, 'obsess_over_service') or not self.obsess_over_service:
            return

        #print self.ocsp_command.__dict__
        print "cmd", cls.ocsp_command
        m = MacroResolver()
        data = self.get_data_for_event_handler()
        cmd = m.resolve_command(cls.ocsp_command, data)
        e = EventHandler(cmd, timeout=cls.ocsp_timeout)
        print "DBG: Event handler call created"
        print "DBG: ",e.__dict__
        #self.raise_event_handler_log_entry(self.event_handler)

        #ok we can put it in our temp action queue
        self.actions.append(e)
        

    @classmethod
    def linkify(cls, config):
        cls.linkify_one_command_with_commands(config.commands, 'ocsp_command')



class Services(Items):
    inner_class = Service #use for know what is in items
    #Create the reversed list for speedup search by host_name/name
    #We also tag service already in list : they are twins. It'a a bad things.
    #Hostgroups service have an ID higer thant host service. So it we tag 
    #an id that already are in the list, this service is already
    #exist, and is a host,
    #or a previous hostgroup, but define before.
    def create_reversed_list(self):
        self.reversed_list = {}
        self.twins = []
        for s in self:
            if hasattr(s, 'service_description') and hasattr(s, 'host_name'):
                s_desc = getattr(s, 'service_description')
                s_host_name = getattr(s, 'host_name')
                key = (s_host_name, s_desc)
                if key not in self.reversed_list:
                    self.reversed_list[key] = s.id
                else:
                    self.twins.append(s.id)
        #For service, the reversed_list is not used for
        #search, so we del it
        del self.reversed_list
                    


    #TODO : finish serach to use reversed
    #Search a service id by it's name and host_name
    def find_srv_id_by_name_and_hostname(self, host_name, name):
        #key = (host_name, name)
        #if key in self.reversed_list:
        #    return self.reversed_list[key]

        #if not, maybe in the whole list?
        for s in self:
            #Runtinme first, available only after linkify
            if hasattr(s, 'service_description') and hasattr(s, 'host'):
                if s.service_description == name and s.host == host_name:
                        return s.id
            #At config part, available before linkify
            if hasattr(s, 'service_description') and hasattr(s, 'host_name'):
                if s.service_description == name and s.host_name == host_name:
                    return s.id
        return None


    #Search a service by it's name and hot_name
    def find_srv_by_name_and_hostname(self, host_name, name):
        if hasattr(self, 'hosts'):
            h = self.hosts.find_by_name(host_name)
            if h == None:
                return None
            return h.find_service_by_name(name)

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
    def linkify(self, hosts, commands, timeperiods, contacts, resultmodulations, escalations):
        self.linkify_with_timeperiods(timeperiods, 'notification_period')
        self.linkify_with_timeperiods(timeperiods, 'check_period')
        self.linkify_with_timeperiods(timeperiods, 'maintenance_period')
        self.linkify_s_by_hst(hosts)
        self.linkify_one_command_with_commands(commands, 'check_command')
        self.linkify_one_command_with_commands(commands, 'event_handler')
        self.linkify_with_contacts(contacts)
        self.linkify_with_resultmodulations(resultmodulations)
        #WARNING: all escalations will not be link here
        #(just the escalation here, not serviceesca or hostesca).
        #This last one will be link in escalations linkify.
        self.linkify_with_escalations(escalations)
    
    
    #We can link services with hosts so
    #We can search in O(hosts) instead
    #of O(services) for common cases
    def optimize_service_search(self, hosts):
        self.hosts = hosts
    
    
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
            except AttributeError , exp:
                pass #Will be catch at the is_correct moment


    #Delete services by ids
    def delete_services_by_id(self, ids):
        for id in ids:
            del self.items[id]

            
    #It's used to change old Nagios2 names to
    #Nagios3 ones
    def old_properties_names_to_new(self):
        for s in self:
            s.old_properties_names_to_new()


    #Apply implicit inheritance for special properties:
    #contact_groups, notification_interval , notification_period
    #So service will take info from host if necessery
    def apply_implicit_inheritance(self, hosts):
        for prop in ['contacts', 'contact_groups', 'notification_interval', \
                         'notification_period', 'resultmodulations', 'escalations', \
                         'poller_tag', 'check_period']:
            for s in self:
                if not s.is_tpl():
                    if not hasattr(s, prop) and hasattr(s, 'host_name'):
                        h = hosts.find_by_name(s.host_name)
                        if h is not None and hasattr(h, prop):
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
    def explode(self, hosts, hostgroups, contactgroups, servicegroups, servicedependencies):
        #The "old" services will be removed. All services with 
        #more than one host or a host group will be in it
        srv_to_remove = []
        

        #items::explode_host_groups_into_hosts
        #take all hosts from our hostgroup_name into our host_name property
        self.explode_host_groups_into_hosts(hosts, hostgroups)
        
        #items::explode_contact_groups_into_contacts
        #take all contacts from our contact_groups into our contact property
        self.explode_contact_groups_into_contacts(contactgroups)
 
        #Then for every host create a copy of the service with just the host
        #because we are adding services, we can't just loop in it
        service_to_check = self.items.keys()
        
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
                else: #Maybe the hnames was full of same host,
                      #so we must reset the name
                    for hname in hnames: #So even if len == 0, we are protected
                        s.host_name = hname

        self.delete_services_by_id(srv_to_remove)

        #Servicegroups property need to be fullfill for got the informations
        #And then just register to this service_group
        for s in self:
            if not s.is_tpl():
                sname = s.service_description
                shname = s.host_name
                if hasattr(s, 'servicegroups'):
                    sgs = s.servicegroups.split(',')
                    for sg in sgs:
                        servicegroups.add_member(shname+','+sname, sg)


        #Now we explode service_dependencies into Servicedependency
        #We just create serviceDep with goods values (as STRING!),
        #the link pass will be done after
        for s in self:
            #Templates are useless here
            if not s.is_tpl():
                if hasattr(s, 'service_dependencies'):
                    if s.service_dependencies != '':
                        sdeps = s.service_dependencies.split(',')
                        #%2=0 are for hosts, !=0 are for service_decription
                        i = 0
                        hname = ''
                        for elt in sdeps:
                            if i % 2 == 0: #host
                                hname = elt
                            else: #description
                                desc = elt
                                #we can register it (s) (depend on) -> (hname, desc)
                                #If we do not have enouth data for s, it's no use
                                if hasattr(s, 'service_description') and hasattr(s, 'host_name'):
                                    #print "DBG : registering", hname, desc, "for", s.host_name, s.service_description
                                    servicedependencies.add_service_dependency(s.host_name, s.service_description, hname, desc)
                            i += 1
