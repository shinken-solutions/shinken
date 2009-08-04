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


#File for create the status.dat file
import time

from service import Service
from host import Host
from contact import Contact

from util import from_bool_to_string


class StatusFile:
    out_map = {Host : {
            'host_name' : {},#'host_name',
            'modified_attributes' : {'prop' : None, 'default' : '0'},
            'check_command' : {'depythonize' : 'get_name'},
            'check_period' : {'prop' : 'check_period' , 'depythonize' : 'get_name'},
            'notification_period' : {'prop' : 'notification_period', 'depythonize' : 'get_name'},
            'check_interval'  : {},
            'retry_interval' : {},
            'event_handler' : {'prop' : None, 'default' : ''},
            'has_been_checked' : {'prop' : None, 'default' : '0'},
            'should_be_scheduled' : {'prop' : None, 'default' : '0'},
            'check_execution_time' : {'prop' : None, 'default' : '0'},
            'check_latency' : {'prop' : 'latency'},
            'check_type' : {'prop' : None, 'default' : '0'},
            'current_state' : {'prop' : 'state'},
            'last_hard_state' : {'prop' : None, 'default' : '0'},
            'last_event_id' : {'prop' : None, 'default' : '0'},
            'current_event_id' : {'prop' : None, 'default' : '0'},
            'current_problem_id' : {'prop' : None, 'default' : '0'},
            'last_problem_id' : {'prop' : None, 'default' : '0'},
            'plugin_output' : {'prop' : 'output'},
            'long_plugin_output' : {'prop' : 'long_output'},
            'performance_data' : {'prop' : None, 'default' : '0'},
            'last_check' : {'prop' : 'last_chk'},
            'next_check' : {'prop' : 'next_chk'},
            'check_options' : {'prop' : None, 'default' : '0'},
            'current_attempt' : {'prop' : 'attempt'},
            'max_attempts' :  {'prop' : 'max_check_attempts'},
            'current_event_id' : {'prop' : None, 'default' : '0'},
            'last_event_id' : {'prop' : None, 'default' : '0'},
            'state_type' : {},
            'last_state_change' : {'prop' : None, 'default' : '0'},
            'last_hard_state_change' : {'prop' : None, 'default' : '0'},
            'last_time_up' : {'prop' : None, 'default' : '0'},
            'last_time_down' : {'prop' : None, 'default' : '0'},
            'last_time_unreachable' : {'prop' : None, 'default' : '0'},
            'last_notification' : {'prop' : None, 'default' : '0'},
            'next_notification' : {'prop' : None, 'default' : '0'},
            'no_more_notifications' : {'prop' : None, 'default' : '0'},
            'current_notification_number' : {'prop' : None, 'default' : '0'},
            'current_notification_id' : {'prop' : None, 'default' : '0'},
            'notifications_enabled' : {'depythonize' : from_bool_to_string},
            'problem_has_been_acknowledged' : {'prop' : None, 'default' : '0'},
            'acknowledgement_type' : {'prop' : None, 'default' : '0'},
            'active_checks_enabled' : {'depythonize' : from_bool_to_string},
            'passive_checks_enabled' : {'depythonize' : from_bool_to_string},
            'event_handler_enabled' : {'depythonize' : from_bool_to_string},
            'flap_detection_enabled' : {'depythonize' : from_bool_to_string},
            'failure_prediction_enabled' : {'depythonize' : from_bool_to_string},
            'process_performance_data' : {'depythonize' : from_bool_to_string},
            'obsess_over_host' : {'depythonize' : from_bool_to_string},
            'last_update' : {'prop' : None, 'default' : '0'},
            'is_flapping' : {'depythonize' : from_bool_to_string},
            'percent_state_change' : {},
            'scheduled_downtime_depth' : {'prop' : None, 'default' : '0'}
            },
               Service : {
            'host_name' : {},
            'service_description' : {},
            'modified_attributes' : {'prop' : None, 'default' : '0'},
            'check_command' : {'depythonize' : 'get_name'},
            'check_period' : {'depythonize' : 'get_name'},
            'notification_period' : {'depythonize' : 'get_name'},
            'check_interval' : {},
            'retry_interval' : {},
            'event_handler' : {'prop' : None, 'default' : ''},
            'has_been_checked' : {'prop' : None, 'default' : '0'},
            'should_be_scheduled' : {'prop' : None, 'default' : '0'},
            'check_execution_time' : {'prop' : None, 'default' : '0'},
            'check_latency' : {'prop' : 'latency'},
            'check_type' : {'prop' : None, 'default' : '0'},
            'current_state' : {'prop' : 'state'},
            'last_hard_state' : {'prop' : None, 'default' : '0'},
            'last_event_id' : {'prop' : None, 'default' : '0'},
            'current_event_id' : {'prop' : None, 'default' : '0'},
            'current_problem_id' : {'prop' : None, 'default' : '0'},
            'last_problem_id' : {'prop' : None, 'default' : '0'},
            'current_attempt' : {'prop' : 'attempt'},
            'max_attempts' : {'prop' : 'max_check_attempts'},
            'current_event_id' : {'prop' : None, 'default' : '0'},
            'last_event_id' : {'prop' : None, 'default' : '0'},
            'state_type' : {},
            'last_state_change' : {'prop' : None, 'default' : '0'},
            'last_hard_state_change' : {'prop' : None, 'default' : '0'},
            'last_time_ok' : {'prop' : None, 'default' : '0'},
            'last_time_warning' : {'prop' : None, 'default' : '0'},
            'last_time_unknown' : {'prop' : None, 'default' : '0'},
            'last_time_critical' : {'prop' : None, 'default' : '0'},
            'plugin_output' : {'prop' : 'output'},
            'long_plugin_output' : {'prop' : 'long_output'},
            'performance_data' : {'prop' : None, 'default' : ''},
            'last_check' : {'prop' : 'last_chk'},
            'next_check' : {'prop' : 'next_chk'},
            'check_options' : {'prop' : None, 'default' : '0'},
            'current_notification_number' : {'prop' : None, 'default' : '0'},
            'current_notification_id' : {'prop' : None, 'default' : '0'},
            'last_notification' : {'prop' : None, 'default' : '0'},
            'next_notification' : {'prop' : None, 'default' : '0'},
            'no_more_notifications' : {'prop' : None, 'default' : '0'},
            'notifications_enabled' : {'depythonize' : from_bool_to_string},
            'active_checks_enabled' : {'depythonize' : from_bool_to_string},
            'passive_checks_enabled' : {'depythonize' : from_bool_to_string},
            'event_handler_enabled' : {'depythonize' : from_bool_to_string},
            'problem_has_been_acknowledged' : {'prop' : None, 'default' : '0'},
            'acknowledgement_type' : {'prop' : None, 'default' : '0'},
            'flap_detection_enabled' : {'depythonize' : from_bool_to_string},
            'failure_prediction_enabled' : {'depythonize' : from_bool_to_string},
            'process_performance_data' : {'depythonize' : from_bool_to_string},
            'obsess_over_service' : {'depythonize' : from_bool_to_string},
            'last_update' : {'prop' : None, 'default' : '0'},
            'is_flapping' : {'depythonize' : from_bool_to_string},
            'percent_state_change' : {},
            'scheduled_downtime_depth' : {'prop' : None, 'default' : '0'}
            },
              
               Contact : {
            'contact_name' : {},
            'modified_attributes' : {'prop' : None, 'default' : '0'},
            'modified_host_attributes' : {'prop' : None, 'default' : '0'},
            'modified_service_attributes' : {'prop' : None, 'default' : '0'},
            'host_notification_period' : {'depythonize' : 'get_name'},
            'service_notification_period' : {'depythonize' : 'get_name'},
            'last_host_notification' : {'prop' : None, 'default' : '0'},
            'last_service_notification' : {'prop' : None, 'default' : '0'},
            'host_notifications_enabled' : {'depythonize' : from_bool_to_string},
            'service_notifications_enabled' : {'depythonize' : from_bool_to_string}
            }#,

#               Scheduler : {
#            'modified_host_attributes' : {'prop' : None, 'default' : '0'},
#            'modified_service_attributes' : {'prop' : None, 'default' : '0'},
#            'nagios_pid' : {'prop' : None, 'default' : '0'},
#            'daemon_mode' : {'prop' : None, 'default' : '0'},
#            'program_start' : {'prop' : None, 'default' : '0'},
#            'last_command_check' : {'prop' : None, 'default' : '0'},
#            'last_log_rotation' : {'prop' : None, 'default' : '0'},
#            'enable_notifications' : {'prop' : None, 'default' : '0'},
#            'active_service_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'passive_service_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'active_host_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'passive_host_checks_enabled' : {'prop' : None, 'default' : '0'},
#            'enable_event_handlers' : {'prop' : None, 'default' : '0'},
#            'obsess_over_services' : {'prop' : None, 'default' : '0'},
#            'obsess_over_hosts' : {'prop' : None, 'default' : '0'},
#            'check_service_freshness' : {'prop' : None, 'default' : '0'},
#            'check_host_freshness' : {'prop' : None, 'default' : '0'},
#            'enable_flap_detection' : {'prop' : None, 'default' : '0'},
#            'enable_failure_prediction' : {'prop' : None, 'default' : '0'},
#            'process_performance_data' : {'prop' : None, 'default' : '0'},
#            'global_host_event_handler' : {'prop' : None, 'default' : '0'},
#            'global_service_event_handler' : {'prop' : None, 'default' : '0'},
#            'next_comment_id' : {'prop' : None, 'default' : '0'},
#            'next_downtime_id' : {'prop' : None, 'default' : '0'},
#            'next_event_id' : {'prop' : None, 'default' : '0'},
#            'next_problem_id' : {'prop' : None, 'default' : '0'},
#            'next_notification_id'  : {'prop' : None, 'default' : '0'},
#            'total_external_command_buffer_slots' : {'prop' : None, 'default' : '0'},
#            'used_external_command_buffer_slots' : {'prop' : None, 'default' : '0'},
#            'high_external_command_buffer_slots' : {'prop' : None, 'default' : '0'},
#            'active_scheduled_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'active_ondemand_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'passive_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'active_scheduled_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'active_ondemand_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'passive_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'cached_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'cached_service_check_stats' : {'prop' : None, 'default' : '0'},
#            'external_command_stats' : {'prop' : None, 'default' : '0'},
#            'parallel_host_check_stats' : {'prop' : None, 'default' : '0'},
#            'serial_host_check_stats' : {'prop' : None, 'default' : '0'}
#            }
    }
               
                   

    def __init__(self, scheduler):
        self.conf = scheduler.conf
        self.scheduler = scheduler

    
    def create_output(self, elt):
        output = ''
        for elt_type in StatusFile.out_map:
            if elt_type == elt.__class__:
                type_map = StatusFile.out_map[elt_type]
                for display in type_map:
                    if 'prop' not in type_map[display]:
                        prop = display
                    else:
                        prop = type_map[display]['prop']
                        
                    if prop is not None:
                        value = getattr(elt, prop)
                        #Maybe it's not a value, but a function link
                        if callable(value):
                            value = value()
                            
                        if 'depythonize' in type_map[display]:
                            f = type_map[display]['depythonize']
                            if callable(f):
                                value = f(value)
                            else:
                                #print "Elt: ", elt, "prop", prop
                                #ok not a direct function, maybe a functin provided by value...
                                f = getattr(value, f)
                                value = f()
                    else:
                        value = type_map[display]['default']
                    output += '\t' + display + '=' + str(value) + '\n'
                        
        return output


    def create_or_update(self):
        output = ''
        now = time.time()
        output += 'info {\n' + '\tcreated=' + str(now) + '\n' + '\tversion=3.0.2\n\t}\n'
        
        for h in self.conf.hosts:
            tmp = self.create_output(h)
            output += 'hoststatus {\n' + tmp + '\t}\n'

        for s in self.conf.services:
            tmp = self.create_output(s)
            output += 'servicestatus {\n' + tmp + '\t}\n'

        for c in self.conf.contacts:
            tmp = self.create_output(c)
            output += 'contactstatus {\n' + tmp + '\t}\n'


        #print "Create output :", output
        
