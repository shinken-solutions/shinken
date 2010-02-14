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


import time

from command import CommandCall
from item import Items
from schedulingitem import SchedulingItem
from util import to_int, to_char, to_split, to_bool, strip_and_uniq, format_t_into_dhms_format
from check import Check
from notification import Notification
from macroresolver import MacroResolver
from log import Log

class Service(SchedulingItem):
    __slots__ = ('id', 'host_name', 'hostgroup_name', 'service_description',\
                     'display_name', 'servicegroups', 'is_volatile', 'check_command', \
                     'initial_state', 'max_check_attempts', 'check_interval',\
                     'retry_interval', 'active_checks_enabled', 'passive_checks_enabled',\
                     'check_period', 'obsess_over_service', 'check_freshness',\
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
                     'return_code', 'perf_data', 'notifications_in_progress', 'customs', 'host', \
                     'resultmodulations', 'last_update'
                 )

    id = 1 # Every service have a unique ID, and 0 is always special in database and co...
    ok_up = 'OK' # The host and service do not have the same 0 value, now yes :)

    my_type = 'service' #used by item class for format specific value like for Broks

    #properties defined by configuration
    #required : is required in conf
    #default : default value if no set in conf
    #pythonize : function to call when transfort string to python object
    #fill_brok : if set, send to broker. there are two categories: full_status for initial and update status, check_result for check results
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
        'resultmodulations' : {'required' : False, 'default' : ''}, #TODO : fix brok and deepcopy a patern is not allowed
        'escalations' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        }
    
    #properties used in the running state
    running_properties = {
        'last_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'next_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'next_schedule']},
        'in_checking' : {'default' : False, 'fill_brok' : ['full_status']},
        'latency' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'attempt' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'state' : {'default' : 'PENDING', 'fill_brok' : ['full_status']},
        'state_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'current_event_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'last_event_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'last_state_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'last_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'last_hard_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'last_hard_state' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'last_time_ok' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'last_time_warning' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'last_time_critical' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'last_time_unknown' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'duration_sec' : {'default' : 0, 'fill_brok' : ['full_status']},
        'state_type' : {'default' : 'HARD', 'fill_brok' : ['full_status']},
        'state_type_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result']},
        'long_output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result']},
        'is_flapping' : {'default' : False, 'fill_brok' : ['full_status']},
        'is_in_downtime' : {'default' : False, 'fill_brok' : ['full_status']},
        'act_depend_of' : {'default' : [] }, #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : {'default' : []}, #dependencies for checks raise, so BEFORE checks
        'last_state_update' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'checks_in_progress' : {'default' : []}, # no brok because checks are too linked
        'notifications_in_progress' : {'default' : {}}, # no broks because notifications are too linked
        'downtimes' : {'default' : [], 'fill_brok' : ['full_status']},
        'flapping_changes' : {'default' : [], 'fill_brok' : ['full_status']},
        'flapping_comment_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'percent_state_change' : {'default' : 0.0, 'fill_brok' : ['full_status']},
        'problem_has_been_acknowledged' : {'default' : False, 'fill_brok' : ['full_status']},
        'acknowledgement_type' : {'default' : 1, 'fill_brok' : ['full_status', 'check_result']},
        'check_type' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'has_been_checked' : {'default' : 1, 'fill_brok' : ['full_status', 'check_result']},
        'should_be_scheduled' : {'default' : 1, 'fill_brok' : ['full_status']},
        'last_problem_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'current_problem_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'execution_time' : {'default' : 0.0, 'fill_brok' : ['full_status', 'check_result']},
        'last_notification' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'current_notification_number' : {'default' : 0, 'fill_brok' : ['full_status']},
        'current_notification_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'check_flapping_recovery_notification' : {'default' : True, 'fill_brok' : ['full_status']},
        'scheduled_downtime_depth' : {'default' : 0, 'fill_brok' : ['full_status']},
        'pending_flex_downtime' : {'default' : 0, 'fill_brok' : ['full_status']},
        'timeout' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'start_time' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'end_time' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'early_timeout' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'return_code' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'perf_data' : {'default' : '', 'fill_brok' : ['full_status', 'check_result']},
        'host' : {'default' : None},
        'customs' : {'default' : {}},
        'notified_contacts' : {'default' : set()}, #use for having all contacts we have notified
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
        'SERVICECHECKCOMMAND' : 'get_check_command',
        'SERVICEACKAUTHOR' : 'ack_author',
        'SERVICEACKAUTHORNAME' : 'get_ack_author_name',
        'SERVICEACKAUTHORALIAS' : 'get_ack_author_alias',
        'SERVICEACKCOMMENT' : 'ack_comment',
        'SERVICEACTIONURL' : 'action_url',
        'SERVICENOTESURL' : 'notes_url',
        'SERVICENOTES' : 'notes'
        }

    #Give a nice name output
    def get_name(self):
        return self.service_description

    
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

        #Ok now we manage special cases...
        if not hasattr(self, 'contacts') and not hasattr(self, 'contacgroups') and  self.notifications_enabled == True:
            Log().log('%s : I do not have contacts nor contacgroups' % self.get_name())
            state = False
        if not hasattr(self, 'check_command') or not self.check_command.is_valid():
            Log().log('%s : my check_command is invalid' % self.get_name())
            state = False
        if not hasattr(self, 'notification_interval') and  self.notifications_enabled == True:
            Log().log("%s : I've got no notification_interval but I've got notifications enabled" % self.get_name())
            state = False
        if not hasattr(self, 'host') or self.host == None:
            Log().log("%s : I do not have and host" % self.get_name())
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


    #Set unreachable : our host is DOWN, but it mean nothing for a service
    def set_unreachable(self):
        pass


    #Set state with status return by the check
    #and update flapping state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now
        self.last_state = self.state
        
        if status == 0:
            self.state = 'OK'
            self.state_id = 0
            self.last_time_ok = int(self.last_state_update)
        elif status == 1:
            self.state = 'WARNING'
            self.state_id = 1
            self.last_time_warning = int(self.last_state_update)
            
        elif status == 2:
            self.state = 'CRITICAL'
            self.state_id = 2
            self.last_time_critical = int(self.last_state_update)
        elif status == 3:
            self.state = 'UNKNOWN'
            self.state_id = 3
            self.last_time_unknown = int(self.last_state_update)
        else:
            self.state = 'CRITICAL'#exit code UNDETERMINED
            self.state_id = 2
            self.last_time_critical = int(self.last_state_update)

        if status in self.flap_detection_options:
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


    #Add a log entry with a SERVICE ALERT like:
    #SERVICE ALERT: server;Load;UNKNOWN;HARD;1;I don't know what to say...
    def raise_alert_log_entry(self):
        Log().log('SERVICE ALERT: %s;%s;%s;%s;%d;%s' % (self.host.get_name(), self.get_name(), self.state, self.state_type, self.attempt, self.output))


    #Add a log entry with a Freshness alert like:
    #Warning: The results of host 'Server' are stale by 0d 0h 0m 58s (threshold=0d 1h 0m 0s).
    #I'm forcing an immediate check of the host.
    def raise_freshness_log_entry(self, t_stale_by, t_threshold):
        Log().log("Warning: The results of service '%s' on host '%' are stale by %s (threshold=%s).  I'm forcing an immediate check of the service." \
                      % (self.get_name(), self.host.get_name(), format_t_into_dhms_format(t_stale_by), format_t_into_dhms_format(t_threshold)))


    #Raise a log entry with a Notification alert like
    #SERVICE NOTIFICATION: superadmin;server;Load;OK;notify-by-rss;no output
    def raise_notification_log_entry(self, n):
        contact = n.contact
        command = n.command_call
        if self.__class__.log_notifications:
            Log().log("SERVICE NOTIFICATION: %s;%s;%s;%s;%s;%s" % (contact.get_name(), self.host.get_name(), self.get_name(), self.state, \
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
            if c.exit_status==0 and 'o' in self.stalking_options:
                need_stalk = True
            elif c.exit_status==1 and 'w' in self.stalking_options:
                need_stalk = True
            elif c.exit_status==2 and 'c' in self.stalking_options:
                need_stalk = True
            elif c.exit_status==3 and 'u' in self.stalking_options:
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


    #see if the notification is launchable (time is OK and contact is OK too)
    def is_notification_launchable(self, n, contact):
        now = time.time()
        if n.type == 'PROBLEM':
            return self.state != 'OK' and  contact.want_service_notification(now, self.state, n.type)
        else:
            return self.state == 'OK' and  contact.want_service_notification(now, self.state, n.type)


    def get_duration_sec(self):
        return str(int(self.duration_sec))


    def get_duration(self):
        m, s = divmod(self.get_duration_sec, 60)
        h, m = divmod(m, 60)
        return "%02dh %02dm %02ds" % (h, m, s)

            

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
            except AttributeError as exp:
                pass #Will be catch at the is_correct moment


    #Delete services by ids
    def delete_services_by_id(self, ids):
        for id in ids:
            del self.items[id]


    #Apply implicit inheritance for special properties:
    #contact_groups, notification_interval , notification_period
    #So service will take info from host if necessery
    def apply_implicit_inheritance(self, hosts):
        for prop in ['contacts', 'contact_groups', 'notification_interval', \
                         'notification_period', 'resultmodulations', 'escalations']:
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
    def explode(self, hostgroups, contactgroups, servicegroups):
        #Hostgroups property need to be fullfill for got the informations
        #self.apply_partial_inheritance('contact_groups')
        #self.apply_partial_inheritance('hostgroup_name')
        #self.apply_partial_inheritance('host_name')

        #The "old" services will be removed. All services with 
        #more than one host or a host group will be in it
        srv_to_remove = []
        

        #items::explode_host_groups_into_hosts
        #take all hosts from our hostgroup_name into our host_name property
        self.explode_host_groups_into_hosts(hostgroups)
        
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
        #self.apply_partial_inheritance('servicegroups')
        for s in self:
            if not s.is_tpl():
                sname = s.service_description
                shname = s.host_name
                if hasattr(s, 'servicegroups'):
                    sgs = s.servicegroups.split(',')
                    for sg in sgs:
                        servicegroups.add_member(shname+','+sname, sg)


