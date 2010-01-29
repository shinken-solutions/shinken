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
from util import to_int, to_char, to_split, to_bool, format_t_into_dhms_format
from macroresolver import MacroResolver
from check import Check
from notification import Notification
from graph import Graph
from log import Log

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
                     'realm', 'resultmodulations'
                 )
    
    id = 1 #0 is reserved for host (primary node for parents)
    ok_up = 'UP'
    my_type = 'host'


    #properties defined by configuration
    #required : is required in conf
    #default : default value if no set in conf
    #pythonize : function to call when transfort string to python object
    #fill_brok : if set, send to broker. there are two categories: full_status for initial and update status, check_result for check results
    #Only for the inital call
    properties={
        'host_name' : {'required' : True, 'fill_brok' : ['full_status', 'check_result']},
        'alias' : {'required' : True, 'fill_brok' : ['full_status']},
        'display_name' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address' : {'required' : True, 'fill_brok' : ['full_status']},
        'parents' : {'required' : False, 'default' : '', 'pythonize' : to_split}, #TODO : find a way to brok it?
        'hostgroups' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'check_command' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'initial_state' : {'required' : False, 'default' : 'u', 'pythonize' : to_char, 'fill_brok' : ['full_status']},
        'max_check_attempts' : {'required' : True, 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'check_interval' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'retry_interval' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'active_checks_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'passive_checks_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'obsess_over_host' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'check_freshness' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'freshness_threshold' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'event_handler' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'event_handler_enabled' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'low_flap_threshold' : {'required' : False, 'default' : '25', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'high_flap_threshold' : {'required' : False, 'default' : '50', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'flap_detection_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'flap_detection_options' : {'required' : False, 'default' : 'o,d,u', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'process_perf_data' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_status_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_nonstatus_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'contacts' : {'required' : True, 'default' : '', 'fill_brok' : ['full_status']},
        'contact_groups' : {'required' : True, 'default' : '', 'fill_brok' : ['full_status']},
        'notification_interval' : {'required' : False, 'default' : '60', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'first_notification_delay' : {'required' : False, 'default' : '0', 'pythonize' : to_int, 'fill_brok' : ['full_status']},
        'notification_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'notification_options' : {'required' : False, 'default' : 'd,u,r,f', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'notifications_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'stalking_options' : {'required' : False, 'default' : '', 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'notes' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'notes_url' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'action_url' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'icon_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'icon_image_alt' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'vrml_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'statusmap_image' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        '2d_coords' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        '3d_coords' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'failure_prediction_enabled' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        #New to shinken
        'realm' : {'required' : False, 'default' : None}, #no 'fill_brok' because realm are link with every one, it's too dangerous
        #so picle things like connexions to schedulers, etc.

        #Shinken specific
        'resultmodulations' : {'required' : False, 'default' : ''}, #TODO : fix brok and deepcopy a patern is not allowed
        'escalations' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        }


    #properties set only for running purpose
    running_properties = {
        'last_chk' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'next_chk' : {'default' : 0, 'fill_brok' : ['full_status']},
        'in_checking' : {'default' : False, 'fill_brok' : ['full_status']},
        'latency' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'attempt' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'state' : {'default' : 'PENDING', 'fill_brok' : ['full_status']},
        'state_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'state_type' : {'default' : 'HARD', 'fill_brok' : ['full_status']},
        'state_type_id' : {'default' : 0, 'fill_brok' : ['full_status', 'check_result']},
        'current_event_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'last_event_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'last_state_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        'last_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'last_hard_state_change' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'last_hard_state' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'last_time_up' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'last_time_down' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'last_time_unreachable' : {'default' : int(time.time()), 'fill_brok' : ['full_status', 'check_result']},
        'duration_sec' : {'default' : 0, 'fill_brok' : ['full_status']},
        'output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result']},
        'long_output' : {'default' : '', 'fill_brok' : ['full_status', 'check_result']},
        'is_flapping' : {'default' : False, 'fill_brok' : ['full_status']},
        'is_in_downtime' : {'default' : False, 'fill_brok' : ['full_status']},
        'flapping_comment_id' : {'default' : 0, 'fill_brok' : ['full_status']},
        #No broks for _depend_of because of to much links to hsots/services
        'act_depend_of' : {'default' : []}, #dependencies for actions like notif of event handler, so AFTER check return
        'chk_depend_of' : {'default' : []}, #dependencies for checks raise, so BEFORE checks
        'last_state_update' : {'default' : time.time(), 'fill_brok' : ['full_status']},
        'services' : {'default' : []}, #no brok ,to much links
        'checks_in_progress' : {'default' : []},#No broks, it's just internal, and checks have too links
        'notifications_in_progress' : {'default' : {}},#No broks, it's just internal, and checks have too links
        'downtimes' : {'default' : [], 'fill_brok' : ['full_status']},
        'flapping_changes' : {'default' : [], 'fill_brok' : ['full_status']},
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
        'customs' : {'default' : {}},
        'notified_contacts' : {'default' : set()}, #use for having all contacts we have notified
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
              'LASTHOSTUP' : 'last_time_up',
              'LASTHOSTDOWN' : 'last_time_down',
              'LASTHOSTUNREACHABLE' : 'last_time_unreachable',
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

        special_properties = ['contacts', 'contact_groups', 'check_period', \
                                  'notification_interval', 'check_period']
        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    Log().log("%s : I do not have %s" % (self.get_name(), prop))
                    state = False #Bad boy...
        #Ok now we manage special cases...
        if not hasattr(self, 'contacts') and not hasattr(self, 'contacgroups') and self.notifications_enabled == True:
            Log().log("%s : I do not have contacts nor contacgroups" % self.get_name())
            state = False
        if not hasattr(self, 'check_command') or not self.check_command.is_valid():
            Log().log("%s : my check_command is invalid" % self.get_name())
            state = False
        if not hasattr(self, 'notification_interval') and self.notifications_enabled == True:
            Log().log("%s : I've got no notification_interval but I've got notifications enabled" % self.get_name())
            state = False
        #If active check is enabled with a check_interval!=0, we must have a check_timeperiod
        if (hasattr(self, 'active_checks_enabled') and self.active_checks_enabled) and (not hasattr(self, 'check_period') or self.check_period == None) and (hasattr(self, 'check_interval') and self.check_interval!=0):
            Log().log("%s : My check_timeperiod is not correct" % self.get_name())
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


    def get_total_services_ok(self):
        return str(len([s for s in self.services if s.state_id == 0]))


    def get_total_services_warning(self):
        return str(len([s for s in self.services if s.state_id == 1]))


    def get_total_services_critical(self):
        return str(len([s for s in self.services if s.state_id == 2]))


    def get_total_services_unknown(self):
        return str(len([s for s in self.services if s.state_id == 3]))


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


    #Set unreachable : all our parents are down!
    #We have a special state, but state was already set, we just need to
    #update it. We are still DOWN, but state id is 2
    def set_unreachable(self):
        now = time.time()
        self.state_id = 2
        self.last_time_unreachable = int(now)

    
    #set the state in UP, DOWN, or UNDETERMINED
    #with the status of a check. Also update last_state
    def set_state_from_exit_status(self, status):
        now = time.time()
        self.last_state_update = now
        self.last_state = self.state
        
        if status == 0:
            self.state = 'UP'
            self.state_id = 0
            self.last_time_up = int(self.last_state_update)
        elif status == 1 or status == 2 or status == 3:
            self.state = 'DOWN'
            self.state_id = 1
            self.last_time_down = int(self.last_state_update)
        else:
            self.state = 'DOWN'#exit code UNDETERMINED
            self.state_id = 1
            self.last_time_down = int(self.last_state_update)
        if status in self.flap_detection_options:
            self.add_flapping_change(self.state != self.last_state)
        if self.state != self.last_state:
            self.last_state_change = self.last_state_update
        self.duration_sec = now - self.last_state_change


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


    #Add a log entry with a HOST ALERT like:
    #HOST ALERT: server;DOWN;HARD;1;I don't know what to say...
    def raise_alert_log_entry(self):
        Log().log('HOST ALERT: %s;%s;%s;%d;%s' % (self.get_name(), self.state, self.state_type, self.attempt, self.output))


    #Add a log entry with a Freshness alert like:
    #Warning: The results of host 'Server' are stale by 0d 0h 0m 58s (threshold=0d 1h 0m 0s).
    #I'm forcing an immediate check of the host.
    def raise_freshness_log_entry(self, t_stale_by, t_threshold):
        Log().log("Warning: The results of host '%s' are stale by %s (threshold=%s).  I'm forcing an immediate check of the host." \
                      % (self.get_name(), format_t_into_dhms_format(t_stale_by), format_t_into_dhms_format(t_threshold)))
            

    #Raise a log entry with a Notification alert like
    #HOST NOTIFICATION: superadmin;server;UP;notify-by-rss;no output
    def raise_notification_log_entry(self, n):
        contact = n.contact
        command = n.command_call
        if self.__class__.log_notifications:
            Log().log("HOST NOTIFICATION: %s;%s;%s;%s;%s" % (contact.get_name(), self.get_name(), self.state, \
                                                                 command.get_name(), self.output))

    #Raise a log entry with a Eventhandler alert like
    #HOST NOTIFICATION: superadmin;server;UP;notify-by-rss;no output
    def raise_event_handler_log_entry(self, command):
        if self.__class__.log_event_handlers:
            Log().log("HOST EVENT HANDLER: %s;%s;%s;%s;%s" % (self.get_name(), self.state, self.state_type, self.attempt, \
                                                                 command.get_name()))


    #Raise a log entry with FLAPPING START alert like
    #HOST FLAPPING ALERT: server;STARTED; Host appears to have started flapping (50.6% change >= 50.0% threshold)
    def raise_flapping_start_log_entry(self, change_ratio, threshold):
        Log().log("HOST FLAPPING ALERT: %s;STARTED; Host appears to have started flapping (%.1f% change >= %.1% threshold)" % \
                      (self.get_name(), change_ratio, threshold))


    #Raise a log entry with FLAPPING STOP alert like
    #HOST FLAPPING ALERT: server;STOPPED; host appears to have stopped flapping (23.0% change < 25.0% threshold)
    def raise_flapping_stop_log_entry(self, change_ratio, threshold):
        Log().log("HOST FLAPPING ALERT: %s;STOPPED; Host appears to have stopped flapping (%.1f% change < %.1% threshold)" % \
                      (self.get_name(), change_ratio, threshold))


    #If there is no valid time for next check, raise a log entry
    def raise_no_next_check_log_entry(self):
        Log().log("Warning : I cannot schedule the check for the host '%s' because there is not future valid time" % \
                      (self.get_name()))


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
            Log().log("Stalking %s : %s", self.get_name(), self.output)


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
        if n.type == 'PROBLEM':
            return self.state != 'UP' and contact.want_host_notification(now, self.state, n.type)
        elif n.type == 'RECOVERY':
            return self.state == 'UP' and contact.want_host_notification(now, self.state, n.type)
        #return now > n.t_to_go and self.state != 'UP' and contact.want_host_notification(now, self.state, n.type)
            

    #MACRO PART
    def get_duration_sec(self):
        return str(int(self.duration_sec))


    def get_duration(self):
        m, s = divmod(self.get_duration_sec, 60)
        h, m = divmod(m, 60)
        return "%02dh %02dm %02ds" % (h, m, s)



class Hosts(Items):
    name_property = "host_name" #use for the search by name
    inner_class = Host #use for know what is in items

    #Create link between elements:
    #hosts -> timeperiods
    #hosts -> hosts (parents, etc)
    #hosts -> commands (check_command)
    #hosts -> contacts
    def linkify(self, timeperiods=None, commands=None, contacts=None, realms=None, resultmodulations=None, escalations=None):
        self.linkify_with_timeperiods(timeperiods, 'notification_period')
        self.linkify_with_timeperiods(timeperiods, 'check_period')
        self.linkify_h_by_h()
        self.linkify_one_command_with_commands(commands, 'check_command')
        self.linkify_one_command_with_commands(commands, 'event_handler')
        
        self.linkify_with_contacts(contacts)
        self.linkify_h_by_realms(realms)
        self.linkify_with_resultmodulations(resultmodulations)
        #WARNING: all escalations will not be link here
        #(just the escalation here, not serviceesca or hostesca).
        #This last one will be link in escalations linkify.
        self.linkify_with_escalations(escalations)
        

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

    
    def linkify_h_by_realms(self, realms):
        for h in self:
            #print h.get_name(), h.realm
            if h.realm != None:
                name = h.realm
                p = realms.find_by_name(h.realm.strip())
                h.realm = p
                if p != None:
                    print "Host", h.get_name(), "is in the realm", p.get_name()

    
    #We look for hostgroups property in hosts and
    def explode(self, hostgroups, contactgroups):
        #Hostgroups property need to be fullfill for got the informations
        #self.apply_partial_inheritance('hostgroups')
        #self.apply_partial_inheritance('contact_groups')
        
        #Register host in the hostgroups
        for h in self:
            if not h.is_tpl():
                hname = h.host_name
                if hasattr(h, 'hostgroups'):
                    hgs = h.hostgroups.split(',')
                    for hg in hgs:
                        hostgroups.add_member(hname, hg.strip())

        #items::explode_contact_groups_into_contacts
        #take all contacts from our contact_groups into our contact property
        self.explode_contact_groups_into_contacts(contactgroups)


        
    #Create depenancies:
    #Parent graph: use to find quickly relations between all host, and loop
    #Depencies at the host level: host parent
    def apply_dependancies(self):
        #Create parent graph
        parents = Graph()
        
        #With all hosts
        for h in self:
            parents.add_node(h)
            
        for h in self:
            for p in h.parents:
                parents.add_edge(p, h)

        Log().log("Hosts in a loop: %s" % parents.loop_check())
        
        for h in self:
            h.fill_parents_dependancie()
            
