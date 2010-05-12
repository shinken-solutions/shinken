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


#File for a Livestatus class which can be used by the status-dat-broker
import time
import os
import re
import tempfile
import Queue

from service import Service
from host import Host
from contact import Contact
from hostgroup import Hostgroup
from servicegroup import Servicegroup
from contactgroup import Contactgroup
from timeperiod import Timeperiod
from command import Command
from comment import Comment
from downtime import Downtime
from config import Config

from util import from_bool_to_string,from_list_to_split,from_float_to_int,to_int

#This is a dirty hack. Service.get_name only returns service_description.
#For the servicegroup config we need more. host_name + service_description
def get_full_name(self):
    return [self.host_name, self.service_description]
Service.get_full_name = get_full_name


class LiveStatus:
    #prop : is the internal name if it is different than the name in the output file
    #required : 
    #depythonize : 
    #default :
    out_map = {Host : { # needs rewrite
            'name' : { 'prop' : 'host_name' },
            'alias' : {},
            'address' : {},
            'state' : { 'prop' : 'state_id' },
            'parents' : { 'depythonize' : 'get_name' },
            'check_period' : { 'depythonize' : 'get_name' },
            'check_command' : { 'depythonize' : 'call' },
            #'contact_groups' : ,
            'contacts' : { 'depythonize' : 'contact_name' },
            'notification_period' : { 'depythonize' : 'get_name' },
            'initial_state' : {},
            'check_interval' : {},
            'retry_interval' : {},
            'max_check_attempts' : {},
            'active_checks_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'passive_checks_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'obsess_over_host' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'event_handler_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'low_flap_threshold' : { 'default' : '0' },
            'high_flap_threshold' : { 'default' : '0' },
            'flap_detection_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'flap_detection_options' : { 'depythonize' : from_list_to_split},
            'freshness_threshold' : { 'default' : '0' },
            'check_freshness' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'notification_options' : { 'depythonize' : from_list_to_split},
            'notifications_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'notification_interval' : {},
            'first_notification_delay' : { 'default' : '0' },
            'stalking_options' : { 'depythonize' : from_list_to_split, 'default' : 'n' },
            'process_perf_data' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'failure_prediction_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'retain_status_information' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'retain_nonstatus_information' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'comments' : { 'depythonize' : 'comment_id', 'default' : '' },
            'is_flapping' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'last_check' : { 'prop' : 'last_chk', 'depythonize' : from_float_to_int, 'default' : 0},
            'next_check' : { 'prop' : 'next_chk', 'depythonize' : from_float_to_int, 'default' : 0},
            'last_state_change' : { 'depythonize' : from_float_to_int, 'default' : 0},
            'last_notification' : { 'depythonize' : to_int, 'default' : 0},
            'childs' : { 'depythonize' : from_list_to_split, 'default' : '' },
            'groups' : { 'prop' : 'hostgroups', 'default' : '' },
            'current_attempt' : { 'prop' : 'attempt', 'default' : 0},
            'acknowledged' : { 'prop' : 'problem_has_been_acknowledged', 'depythonize' : from_bool_to_string, 'default' : 0},
            'scheduled_downtime_depth' : { 'default' : 0},
            'has_been_checked' : { 'default' : 0, 'depythonize' : from_bool_to_string},
            'checks_enabled' : { 'default' : 0, 'prop' : 'active_checks_enabled', 'depythonize' : from_bool_to_string}, # this may be not correct
            },
        Service : { # needs rewrite
            'host_name' : {},
            'description' : { 'prop' : 'service_description' },
            'state' : { 'prop' : 'state_id' },
            'check_period' : { 'depythonize' : 'get_name' },
            'check_command' : { 'depythonize' : 'call' },
            #'contact_groups' : { 'depythonize' : 'get_name' },
            'contacts' : { 'depythonize' : 'contact_name' },
            'notification_period' : { 'depythonize' : 'get_name' },
            'initial_state' : {},
            'check_interval' : {},
            'retry_interval' : {},
            'max_check_attempts' : {},
            'is_volatile' : { 'default' : '0' },
            'parallelize_check' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'active_checks_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'passive_checks_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'obsess_over_service' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'event_handler_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'low_flap_threshold' : { 'default' : '0' },
            'high_flap_threshold' : { 'default' : '0' },
            'flap_detection_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'flap_detection_options' : { 'depythonize' : from_list_to_split},
            'freshness_threshold' : { 'default' : '0' },
            'check_freshness' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'notification_options' : { 'depythonize' : from_list_to_split},
            'notifications_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'notification_interval' : {},
            'first_notification_delay' : { 'default' : '0' },
            'stalking_options' : { 'depythonize' : from_list_to_split, 'default' : 'n' },
            'process_perf_data' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'failure_prediction_enabled' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'notes_url' : {},
            'action_url' : {},
            'retain_status_information' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'retain_nonstatus_information' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'latency' : { 'depythonize' : to_int, 'default' : 0},
            

            'in_notification_period' : { 'default' : '1' },
            'comments' : { 'depythonize' : 'comment_id', 'default' : '' },
            'is_flapping' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'host_is_flapping' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'last_check' : { 'prop' : 'last_chk', 'depythonize' : from_float_to_int, 'default' : 0},
            'next_check' : { 'prop' : 'next_chk', 'depythonize' : from_float_to_int, 'default' : 0},
            'last_state_change' : { 'depythonize' : from_float_to_int, 'default' : 0},
            'has_been_checked' : { 'depythonize' : to_int, 'default' : 0},
            'last_notification' : { 'depythonize' : to_int, 'default' : 0},
            'current_attempt' : { 'prop' : 'attempt', 'default' : 0},
            'groups' : { 'prop' : 'servicegroups', 'default' : '' },
            },
              
        Contact : { # needs rewrite
            'name' : { 'prop' : 'contact_name', 'default' : '0' },
            'alias' : { 'default' : '0' },
            'host_notifications_enabled' : { 'depythonize' : from_bool_to_string},
            'service_notifications_enabled' : { 'depythonize' : from_bool_to_string},
            'host_notification_period' : { 'depythonize' : 'get_name' },
            'service_notification_period' : { 'depythonize' : 'get_name' },
            'host_notification_options' : { 'depythonize' : from_list_to_split, 'default' : 'd,u,r,f,s,n' },
            'service_notification_options' : { 'depythonize' : from_list_to_split, 'default' : 'w,u,c,r,f,s,n' },
            'host_notification_commands' : { 'depythonize' : 'call' },
            'service_notification_commands' : { 'depythonize' : 'call' },
            'email' : {},
            'pager' : {},
            'address1' : {},
            'address2' : {},
            'address3' : {},
            'address4' : {},
            'address5' : {},
            'address6' : {},
            'can_submit_commands' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'retain_status_information' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            'retain_nonstatus_information' : { 'depythonize' : from_bool_to_string, 'default' : '0' },
            },

        Hostgroup : { # in progress
            'action_url' : {},
            'alias' : {},
            'members' : { 'depythonize' : 'get_name' },
            'name' : { 'prop' : 'hostgroup_name' },
            'notes' : {},
            'notes_url' : {},
            'num_hosts' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: len(x) },
            'num_hosts_down' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: len(filter(lambda y: y.state == 'DOWN', x)) },
            'num_hosts_pending' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: len(filter(lambda y: y.state == 'PENDING', x)) },
            'num_hosts_unreach' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: len(filter(lambda y: y.state == 'UNREACHABLE', x)) },
            'num_hosts_up' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: len(filter(lambda y: y.state == 'UP', x)) },
            'num_services' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: sum((len(y.service_ids) for y in x)) },
            'num_services_crit' : {},
            #'num_services_crit' : { 'prop' : 'get_hosts', 'depythonize' : lambda x: sum(len(filter(lambda z: z.state == 'CRITICAL', [y.services for y in x]))) },
            'num_services_hard_crit' : {},
            'num_services_hard_ok' : {},
            'num_services_hard_unknown' : {},
            'num_services_hard_warn' : {},
            'num_services_ok' : {},
            'num_services_pending' : {},
            'num_services_unknown' : {},
            'num_services_warn' : {},
            'worst_host_state' : {},
            'worst_service_hard_state' : {},
            'worst_service_state' : {},
        },

        Servicegroup : { # needs rewrite
            'name' : { 'prop' : 'servicegroup_name' },
            'alias' : {},
            'members' : { 'depythonize' : 'get_full_name' },
        },

        Contactgroup : { # needs rewrite
            'contactgroup_name' : {},
            'alias' : {},
            'members' : { 'depythonize' : 'get_name' },
        },

        Timeperiod : { # needs rewrite
            'timeperiod_name' : {},
            'alias' : {},
        },

        Command : { # needs rewrite
            'command_name' : {},
            'command_line' : {},
        },

        Downtime : { # needs rewrite
            'host_name' : { 'prop' : 'ref', 'depythonize' : lambda x: x.host_name },
            'service_description' : { 'prop' : 'ref', 'depythonize' : lambda x: x.service_description if hasattr(x, 'service_description') else '' },
            'downtime_id' : { 'prop' : 'id', 'default' : '0' },
            'entry_time' : { 'default' : '0' },
            'start_time' : { 'default' : '0' },
            'end_time' : { 'default' : '0' },
            'triggered_by' : { 'prop' : 'trigger_id', 'default' : '0' },
            'fixed' : { 'default' : '0', 'depythonize' : from_bool_to_string},
            'duration' : { 'default' : '0' },
            'author' : { 'default' : 'nobody' },
            'comment' : { 'default' : '0' },
        },

        Comment : { # needs rewrite
            'host_name' : { 'prop' : 'ref', 'depythonize' : lambda x: x.host_name },
            'service_description' : { 'prop' : 'ref', 'depythonize' : lambda x: x.service_description if hasattr(x, 'service_description') else '' },
            'comment_id' : { 'prop' : 'id', 'default' : '0' },
            'source' : { 'prop' : None, 'default' : '0' },
            'type' : { 'prop' : 'comment_type', 'default' : '1' },
            'entry_type' : { 'prop' : 'entry_type', 'default' : '0' },
            'persistent' : { 'prop' : None, 'depythonize' : from_bool_to_string},
            'expires' : { 'prop' : None, 'depythonize' : from_bool_to_string},
            'expire_time' : { 'prop' : None, 'default' : '0' },
            'author' : {},
            'comment' : {},
        },

        Config : {
            #Creating config: 0 {
            'accept_passive_host_checks' : { 'prop' : 'passive_host_checks_enabled', 'default' : '0', 'depythonize' : from_bool_to_string},
            'accept_passive_service_checks' : { 'prop' : 'passive_service_checks_enabled', 'default' : '0', 'depythonize' : from_bool_to_string},
            'cached_log_messages' : { 'prop' : None, 'default' : '0' },
            'check_external_commands' : { 'prop' : None, 'default' : '0', 'depythonize' : from_bool_to_string},
            'check_host_freshness' : { 'prop' : None, 'default' : '0', 'depythonize' : from_bool_to_string},
            'check_service_freshness' : { 'prop' : None, 'default' : '0', 'depythonize' : from_bool_to_string},
            'connections' : { 'prop' : None, 'default' : '0' }, #todo
            'connections_rate' : { 'prop' : None, 'default' : '0' }, #todo
            'enable_event_handlers' : { 'prop' : 'event_handlers_enabled', 'default' : '0', 'depythonize' : from_bool_to_string},
            'enable_flap_detection' : { 'prop' : 'flap_detection_enabled', 'default' : '0', 'depythonize' : from_bool_to_string},
            'enable_notifications' : { 'prop' : 'notifications_enabled', 'default' : '0', 'depythonize' : from_bool_to_string},
            'execute_host_checks' : { 'prop' : 'active_host_checks_enabled', 'default' : '1', 'depythonize' : from_bool_to_string},
            'execute_service_checks' : { 'prop' : 'active_service_checks_enabled', 'default' : '1', 'depythonize' : from_bool_to_string},
            'host_checks' : { 'prop' : None, 'default' : '0' }, #todo counter for all host checks executed ever
            'host_checks_rate' : { 'prop' : None, 'default' : '0' }, #todo
            'interval_length' : { 'prop' : None, 'default' : '0' }, #todo
            'last_command_check' : { 'prop' : None, 'default' : '0' },
            'last_log_rotation' : { 'prop' : None, 'default' : '0' },
            'livestatus_version' : { 'prop' : None, 'default' : '0' }, #todo
            'nagios_pid' : { 'prop' : 'pid', 'default' : '0' },
            'neb_callbacks' : { 'prop' : None, 'default' : '0' }, #not for shinken
            'neb_callbacks_rate' : { 'prop' : None, 'default' : '0' }, #not for shinken
            'obsess_over_hosts' : { 'prop' : None, 'default' : '0', 'depythonize' : from_bool_to_string},
            'obsess_over_services' : { 'prop' : None, 'default' : '0', 'depythonize' : from_bool_to_string},
            'process_performance_data' : { 'prop' : None, 'default' : '0', 'depythonize' : from_bool_to_string},
            'program_start' : { 'prop' : None, 'default' : '0' },
            'program_version' : { 'prop' : None, 'default' : '0.1' }, # Shinken version
            'requests' : { 'prop' : None, 'default' : '0' }, #todo number of livestatus requests
            'requests_rate' : { 'prop' : None, 'default' : '0' }, #todo
            'service_checks' : { 'prop' : None, 'default' : '0' }, #todo counter for all service checks executed ever
            'service_checks_rate' : { 'prop' : None, 'default' : '0' }, #todo
        },

    }

    default_attributes = {
        Host : [
            'accept_passive_checks',
            'acknowledged',
            'acknowledgement_type',
            'action_url',
            'action_url_expanded',
            'active_checks_enabled',
            'address',
            'alias',
            'check_command',
            'check_freshness',
            'check_interval',
            'check_options',
            'check_period',
            'check_type',
            'checks_enabled',
            'childs',
            'comments',
            'contacts',
            'current_attempt',
            'current_notification_number',
            'custom_variable_names',
            'custom_variable_values',
            'display_name',
            'downtimes',
            'event_handler_enabled',
            'execution_time',
            'first_notification_delay',
            'flap_detection_enabled',
            'groups',
            'hard_state',
            'has_been_checked',
            'high_flap_threshold',
            'icon_image',
            'icon_image_alt',
            'icon_image_expanded',
            'in_check_period',
            'in_notification_period',
            'initial_state',
            'is_executing',
            'is_flapping',
            'last_check',
            'last_hard_state',
            'last_hard_state_change',
            'last_notification',
            'last_state',
            'last_state_change',
            'latency',
            'long_plugin_output',
            'low_flap_threshold',
            'max_check_attempts',
            'name',
            'next_check',
            'next_notification',
            'notes',
            'notes_expanded',
            'notes_url',
            'notes_url_expanded',
            'notification_interval',
            'notification_period',
            'notifications_enabled',
            'num_services',
            'num_services_crit',
            'num_services_hard_crit',
            'num_services_hard_ok',
            'num_services_hard_unknown',
            'num_services_hard_warn',
            'num_services_ok',
            'num_services_pending',
            'num_services_unknown',
            'num_services_warn',
            'obsess_over_host',
            'parents',
            'pending_flex_downtime',
            'percent_state_change',
            'perf_data',
            'plugin_output',
            'process_performance_data',
            'retry_interval',
            'scheduled_downtime_depth',
            'state',
            'state_type',
            'statusmap_image',
            'total_services',
            'worst_service_hard_state',
            'worst_service_state',
            'x_3d',
            'y_3d',
            'z_3d',
        ],
        Service : [
            'accept_passive_checks',
            'acknowledged',
            'acknowledgement_type',
            'action_url',
            'action_url_expanded',
            'active_checks_enabled',
            'check_command',
            'check_interval',
            'check_options',
            'check_period',
            'check_type',
            'checks_enabled',
            'comments',
            'contacts',
            'current_attempt',
            'current_notification_number',
            'custom_variable_names',
            'custom_variable_values',
            'description',
            'display_name',
            'downtimes',
            'event_handler',
            'event_handler_enabled',
            'execution_time',
            'first_notification_delay',
            'flap_detection_enabled',
            'groups',
            'has_been_checked',
            'high_flap_threshold',
            'host_accept_passive_checks',
            'host_acknowledged',
            'host_acknowledgement_type',
            'host_action_url',
            'host_action_url_expanded',
            'host_active_checks_enabled',
            'host_address',
            'host_alias',
            'host_check_command',
            'host_check_freshness',
            'host_check_interval',
            'host_check_options',
            'host_check_period',
            'host_check_type',
            'host_checks_enabled',
            'host_childs',
            'host_comments',
            'host_contacts',
            'host_current_attempt',
            'host_current_notification_number',
            'host_custom_variable_names',
            'host_custom_variable_values',
            'host_display_name',
            'host_downtimes',
            'host_event_handler_enabled',
            'host_execution_time',
            'host_first_notification_delay',
            'host_flap_detection_enabled',
            'host_groups',
            'host_hard_state',
            'host_has_been_checked',
            'host_high_flap_threshold',
            'host_icon_image',
            'host_icon_image_alt',
            'host_icon_image_expanded',
            'host_in_check_period',
            'host_in_notification_period',
            'host_initial_state',
            'host_is_executing',
            'host_is_flapping',
            'host_last_check',
            'host_last_hard_state',
            'host_last_hard_state_change',
            'host_last_notification',
            'host_last_state',
            'host_last_state_change',
            'host_latency',
            'host_long_plugin_output',
            'host_low_flap_threshold',
            'host_max_check_attempts',
            'host_name',
            'host_next_check',
            'host_next_notification',
            'host_notes',
            'host_notes_expanded',
            'host_notes_url',
            'host_notes_url_expanded',
            'host_notification_interval',
            'host_notification_period',
            'host_notifications_enabled',
            'host_num_services',
            'host_num_services_crit',
            'host_num_services_hard_crit',
            'host_num_services_hard_ok',
            'host_num_services_hard_unknown',
            'host_num_services_hard_warn',
            'host_num_services_ok',
            'host_num_services_pending',
            'host_num_services_unknown',
            'host_num_services_warn',
            'host_obsess_over_host',
            'host_parents',
            'host_pending_flex_downtime',
            'host_percent_state_change',
            'host_perf_data',
            'host_plugin_output',
            'host_process_performance_data',
            'host_retry_interval',
            'host_scheduled_downtime_depth',
            'host_state',
            'host_state_type',
            'host_statusmap_image',
            'host_total_services',
            'host_worst_service_hard_state',
            'host_worst_service_state',
            'host_x_3d',
            'host_y_3d',
            'host_z_3d',
            'icon_image',
            'icon_image_alt',
            'icon_image_expanded',
            'in_check_period',
            'in_notification_period',
            'initial_state',
            'is_executing',
            'is_flapping',
            'last_check',
            'last_hard_state',
            'last_hard_state_change',
            'last_notification',
            'last_state',
            'last_state_change',
            'latency',
            'long_plugin_output',
            'low_flap_threshold',
            'max_check_attempts',
            'next_check',
            'next_notification',
            'notes',
            'notes_expanded',
            'notes_url',
            'notes_url_expanded',
            'notification_interval',
            'notification_period',
            'notifications_enabled',
            'obsess_over_service',
            'percent_state_change',
            'perf_data',
            'plugin_output',
            'process_performance_data',
            'retry_interval',
            'scheduled_downtime_depth',
            'state',
            'state_type',
        ],
        Contact : [
            'address1',
            'address2',
            'address3',
            'address4',
            'address5',
            'address6',
            'alias',
            'can_submit_commands',
            'custom_variable_names',
            'custom_variable_values',
            'email',
            'host_notification_period',
            'host_notifications_enabled',
            'in_host_notification_period',
            'in_service_notification_period',
            'name',
            'pager',
            'service_notification_period',
            'service_notifications_enabled',
        ],
        Hostgroup : [
            'action_url',
            'alias',
            'members',
            'name',
            'notes',
            'notes_url',
            'num_hosts',
            'num_hosts_down',
            'num_hosts_pending',
            'num_hosts_unreach',
            'num_hosts_up',
            'num_services',
            'num_services_crit',
            'num_services_hard_crit',
            'num_services_hard_ok',
            'num_services_hard_unknown',
            'num_services_hard_warn',
            'num_services_ok',
            'num_services_pending',
            'num_services_unknown',
            'num_services_warn',
            'worst_host_state',
            'worst_service_hard_state',
            'worst_service_state',
        ],
        Servicegroup : [
            'action_url',
            'alias',
            'members',
            'name',
            'notes',
            'notes_url',
            'num_services',
            'num_services_crit',
            'num_services_hard_crit',
            'num_services_hard_ok',
            'num_services_hard_unknown',
            'num_services_hard_warn',
            'num_services_ok',
            'num_services_pending',
            'num_services_unknown',
            'num_services_warn',
            'worst_service_state',
        ],
        Contactgroup : [
            'alias',
            'members',
            'name',
        ],
        Timeperiod : [
            'alias',
            'name',
        ],
        Downtime : [
            'author',
            'comment',
            'duration',
            'end_time',
            'entry_time',
            'fixed',
            'host_accept_passive_checks',
            'host_acknowledged',
            'host_acknowledgement_type',
            'host_action_url',
            'host_action_url_expanded',
            'host_active_checks_enabled',
            'host_address',
            'host_alias',
            'host_check_command',
            'host_check_freshness',
            'host_check_interval',
            'host_check_options',
            'host_check_period',
            'host_check_type',
            'host_checks_enabled',
            'host_childs',
            'host_comments',
            'host_contacts',
            'host_current_attempt',
            'host_current_notification_number',
            'host_custom_variable_names',
            'host_custom_variable_values',
            'host_display_name',
            'host_downtimes',
            'host_event_handler_enabled',
            'host_execution_time',
            'host_first_notification_delay',
            'host_flap_detection_enabled',
            'host_groups',
            'host_hard_state',
            'host_has_been_checked',
            'host_high_flap_threshold',
            'host_icon_image',
            'host_icon_image_alt',
            'host_icon_image_expanded',
            'host_in_check_period',
            'host_in_notification_period',
            'host_initial_state',
            'host_is_executing',
            'host_is_flapping',
            'host_last_check',
            'host_last_hard_state',
            'host_last_hard_state_change',
            'host_last_notification',
            'host_last_state',
            'host_last_state_change',
            'host_latency',
            'host_long_plugin_output',
            'host_low_flap_threshold',
            'host_max_check_attempts',
            'host_name',
            'host_next_check',
            'host_next_notification',
            'host_notes',
            'host_notes_expanded',
            'host_notes_url',
            'host_notes_url_expanded',
            'host_notification_interval',
            'host_notification_period',
            'host_notifications_enabled',
            'host_num_services',
            'host_num_services_crit',
            'host_num_services_hard_crit',
            'host_num_services_hard_ok',
            'host_num_services_hard_unknown',
            'host_num_services_hard_warn',
            'host_num_services_ok',
            'host_num_services_pending',
            'host_num_services_unknown',
            'host_num_services_warn',
            'host_obsess_over_host',
            'host_parents',
            'host_pending_flex_downtime',
            'host_percent_state_change',
            'host_perf_data',
            'host_plugin_output',
            'host_process_performance_data',
            'host_retry_interval',
            'host_scheduled_downtime_depth',
            'host_state',
            'host_state_type',
            'host_statusmap_image',
            'host_total_services',
            'host_worst_service_hard_state',
            'host_worst_service_state',
            'host_x_3d',
            'host_y_3d',
            'host_z_3d',
            'id',
            'service_accept_passive_checks',
            'service_acknowledged',
            'service_acknowledgement_type',
            'service_action_url',
            'service_action_url_expanded',
            'service_active_checks_enabled',
            'service_check_command',
            'service_check_interval',
            'service_check_options',
            'service_check_period',
            'service_check_type',
            'service_checks_enabled',
            'service_comments',
            'service_contacts',
            'service_current_attempt',
            'service_current_notification_number',
            'service_custom_variable_names',
            'service_custom_variable_values',
            'service_description',
            'service_display_name',
            'service_downtimes',
            'service_event_handler',
            'service_event_handler_enabled',
            'service_execution_time',
            'service_first_notification_delay',
            'service_flap_detection_enabled',
            'service_groups',
            'service_has_been_checked',
            'service_high_flap_threshold',
            'service_icon_image',
            'service_icon_image_alt',
            'service_icon_image_expanded',
            'service_in_check_period',
            'service_in_notification_period',
            'service_initial_state',
            'service_is_executing',
            'service_is_flapping',
            'service_last_check',
            'service_last_hard_state',
            'service_last_hard_state_change',
            'service_last_notification',
            'service_last_state',
            'service_last_state_change',
            'service_latency',
            'service_long_plugin_output',
            'service_low_flap_threshold',
            'service_max_check_attempts',
            'service_next_check',
            'service_next_notification',
            'service_notes',
            'service_notes_expanded',
            'service_notes_url',
            'service_notes_url_expanded',
            'service_notification_interval',
            'service_notification_period',
            'service_notifications_enabled',
            'service_obsess_over_service',
            'service_percent_state_change',
            'service_perf_data',
            'service_plugin_output',
            'service_process_performance_data',
            'service_retry_interval',
            'service_scheduled_downtime_depth',
            'service_state',
            'service_state_type',
            'start_time',
            'triggered_by',
            'type',
        ],
        Comment : [
            'author',
            'comment',
            'entry_time',
            'entry_type',
            'expire_time',
            'expires',
            'host_accept_passive_checks',
            'host_acknowledged',
            'host_acknowledgement_type',
            'host_action_url',
            'host_action_url_expanded',
            'host_active_checks_enabled',
            'host_address',
            'host_alias',
            'host_check_command',
            'host_check_freshness',
            'host_check_interval',
            'host_check_options',
            'host_check_period',
            'host_check_type',
            'host_checks_enabled',
            'host_childs',
            'host_comments',
            'host_contacts',
            'host_current_attempt',
            'host_current_notification_number',
            'host_custom_variable_names',
            'host_custom_variable_values',
            'host_display_name',
            'host_downtimes',
            'host_event_handler_enabled',
            'host_execution_time',
            'host_first_notification_delay',
            'host_flap_detection_enabled',
            'host_groups',
            'host_hard_state',
            'host_has_been_checked',
            'host_high_flap_threshold',
            'host_icon_image',
            'host_icon_image_alt',
            'host_icon_image_expanded',
            'host_in_check_period',
            'host_in_notification_period',
            'host_initial_state',
            'host_is_executing',
            'host_is_flapping',
            'host_last_check',
            'host_last_hard_state',
            'host_last_hard_state_change',
            'host_last_notification',
            'host_last_state',
            'host_last_state_change',
            'host_latency',
            'host_long_plugin_output',
            'host_low_flap_threshold',
            'host_max_check_attempts',
            'host_name',
            'host_next_check',
            'host_next_notification',
            'host_notes',
            'host_notes_expanded',
            'host_notes_url',
            'host_notes_url_expanded',
            'host_notification_interval',
            'host_notification_period',
            'host_notifications_enabled',
            'host_num_services',
            'host_num_services_crit',
            'host_num_services_hard_crit',
            'host_num_services_hard_ok',
            'host_num_services_hard_unknown',
            'host_num_services_hard_warn',
            'host_num_services_ok',
            'host_num_services_pending',
            'host_num_services_unknown',
            'host_num_services_warn',
            'host_obsess_over_host',
            'host_parents',
            'host_pending_flex_downtime',
            'host_percent_state_change',
            'host_perf_data',
            'host_plugin_output',
            'host_process_performance_data',
            'host_retry_interval',
            'host_scheduled_downtime_depth',
            'host_state',
            'host_state_type',
            'host_statusmap_image',
            'host_total_services',
            'host_worst_service_hard_state',
            'host_worst_service_state',
            'host_x_3d',
            'host_y_3d',
            'host_z_3d',
            'id',
            'persistent',
            'service_accept_passive_checks',
            'service_acknowledged',
            'service_acknowledgement_type',
            'service_action_url',
            'service_action_url_expanded',
            'service_active_checks_enabled',
            'service_check_command',
            'service_check_interval',
            'service_check_options',
            'service_check_period',
            'service_check_type',
            'service_checks_enabled',
            'service_comments',
            'service_contacts',
            'service_current_attempt',
            'service_current_notification_number',
            'service_custom_variable_names',
            'service_custom_variable_values',
            'service_description',
            'service_display_name',
            'service_downtimes',
            'service_event_handler',
            'service_event_handler_enabled',
            'service_execution_time',
            'service_first_notification_delay',
            'service_flap_detection_enabled',
            'service_groups',
            'service_has_been_checked',
            'service_high_flap_threshold',
            'service_icon_image',
            'service_icon_image_alt',
            'service_icon_image_expanded',
            'service_in_check_period',
            'service_in_notification_period',
            'service_initial_state',
            'service_is_executing',
            'service_is_flapping',
            'service_last_check',
            'service_last_hard_state',
            'service_last_hard_state_change',
            'service_last_notification',
            'service_last_state',
            'service_last_state_change',
            'service_latency',
            'service_long_plugin_output',
            'service_low_flap_threshold',
            'service_max_check_attempts',
            'service_next_check',
            'service_next_notification',
            'service_notes',
            'service_notes_expanded',
            'service_notes_url',
            'service_notes_url_expanded',
            'service_notification_interval',
            'service_notification_period',
            'service_notifications_enabled',
            'service_obsess_over_service',
            'service_percent_state_change',
            'service_perf_data',
            'service_plugin_output',
            'service_process_performance_data',
            'service_retry_interval',
            'service_scheduled_downtime_depth',
            'service_state',
            'service_state_type',
            'source',
            'type',
        ],
        Config : [
            'accept_passive_host_checks',
            'accept_passive_service_checks',
            'cached_log_messages',
            'check_external_commands',
            'check_host_freshness',
            'check_service_freshness',
            'connections',
            'connections_rate',
            'enable_event_handlers',
            'enable_flap_detection',
            'enable_notifications',
            'execute_host_checks',
            'execute_service_checks',
            'host_checks',
            'host_checks_rate',
            'interval_length',
            'last_command_check',
            'last_log_rotation',
            'livestatus_version',
            'nagios_pid',
            'neb_callbacks',
            'neb_callbacks_rate',
            'obsess_over_hosts',
            'obsess_over_services',
            'process_performance_data',
            'program_start',
            'program_version',
            'requests',
            'requests_rate',
            'service_checks',
            'service_checks_rate',
        ],
        Command : [
            'line',
            'name',
        ],
        'Log' : [
            'attempt',
            'class',
            'command_name',
            'comment',
            'contact_name',
            'current_command_line',
            'current_command_name',
            'current_contact_address1',
            'current_contact_address2',
            'current_contact_address3',
            'current_contact_address4',
            'current_contact_address5',
            'current_contact_address6',
            'current_contact_alias',
            'current_contact_can_submit_commands',
            'current_contact_custom_variable_names',
            'current_contact_custom_variable_values',
            'current_contact_email',
            'current_contact_host_notification_period',
            'current_contact_host_notifications_enabled',
            'current_contact_in_host_notification_period',
            'current_contact_in_service_notification_period',
            'current_contact_name',
            'current_contact_pager',
            'current_contact_service_notification_period',
            'current_contact_service_notifications_enabled',
            'current_host_accept_passive_checks',
            'current_host_acknowledged',
            'current_host_acknowledgement_type',
            'current_host_action_url',
            'current_host_action_url_expanded',
            'current_host_active_checks_enabled',
            'current_host_address',
            'current_host_alias',
            'current_host_check_command',
            'current_host_check_freshness',
            'current_host_check_interval',
            'current_host_check_options',
            'current_host_check_period',
            'current_host_check_type',
            'current_host_checks_enabled',
            'current_host_childs',
            'current_host_comments',
            'current_host_contacts',
            'current_host_current_attempt',
            'current_host_current_notification_number',
            'current_host_custom_variable_names',
            'current_host_custom_variable_values',
            'current_host_display_name',
            'current_host_downtimes',
            'current_host_event_handler_enabled',
            'current_host_execution_time',
            'current_host_first_notification_delay',
            'current_host_flap_detection_enabled',
            'current_host_groups',
            'current_host_hard_state',
            'current_host_has_been_checked',
            'current_host_high_flap_threshold',
            'current_host_icon_image',
            'current_host_icon_image_alt',
            'current_host_icon_image_expanded',
            'current_host_in_check_period',
            'current_host_in_notification_period',
            'current_host_initial_state',
            'current_host_is_executing',
            'current_host_is_flapping',
            'current_host_last_check',
            'current_host_last_hard_state',
            'current_host_last_hard_state_change',
            'current_host_last_notification',
            'current_host_last_state',
            'current_host_last_state_change',
            'current_host_latency',
            'current_host_long_plugin_output',
            'current_host_low_flap_threshold',
            'current_host_max_check_attempts',
            'current_host_name',
            'current_host_next_check',
            'current_host_next_notification',
            'current_host_notes',
            'current_host_notes_expanded',
            'current_host_notes_url',
            'current_host_notes_url_expanded',
            'current_host_notification_interval',
            'current_host_notification_period',
            'current_host_notifications_enabled',
            'current_host_num_services',
            'current_host_num_services_crit',
            'current_host_num_services_hard_crit',
            'current_host_num_services_hard_ok',
            'current_host_num_services_hard_unknown',
            'current_host_num_services_hard_warn',
            'current_host_num_services_ok',
            'current_host_num_services_pending',
            'current_host_num_services_unknown',
            'current_host_num_services_warn',
            'current_host_obsess_over_host',
            'current_host_parents',
            'current_host_pending_flex_downtime',
            'current_host_percent_state_change',
            'current_host_perf_data',
            'current_host_plugin_output',
            'current_host_process_performance_data',
            'current_host_retry_interval',
            'current_host_scheduled_downtime_depth',
            'current_host_state',
            'current_host_state_type',
            'current_host_statusmap_image',
            'current_host_total_services',
            'current_host_worst_service_hard_state',
            'current_host_worst_service_state',
            'current_host_x_3d',
            'current_host_y_3d',
            'current_host_z_3d',
            'current_service_accept_passive_checks',
            'current_service_acknowledged',
            'current_service_acknowledgement_type',
            'current_service_action_url',
            'current_service_action_url_expanded',
            'current_service_active_checks_enabled',
            'current_service_check_command',
            'current_service_check_interval',
            'current_service_check_options',
            'current_service_check_period',
            'current_service_check_type',
            'current_service_checks_enabled',
            'current_service_comments',
            'current_service_contacts',
            'current_service_current_attempt',
            'current_service_current_notification_number',
            'current_service_custom_variable_names',
            'current_service_custom_variable_values',
            'current_service_description',
            'current_service_display_name',
            'current_service_downtimes',
            'current_service_event_handler',
            'current_service_event_handler_enabled',
            'current_service_execution_time',
            'current_service_first_notification_delay',
            'current_service_flap_detection_enabled',
            'current_service_groups',
            'current_service_has_been_checked',
            'current_service_high_flap_threshold',
            'current_service_icon_image',
            'current_service_icon_image_alt',
            'current_service_icon_image_expanded',
            'current_service_in_check_period',
            'current_service_in_notification_period',
            'current_service_initial_state',
            'current_service_is_executing',
            'current_service_is_flapping',
            'current_service_last_check',
            'current_service_last_hard_state',
            'current_service_last_hard_state_change',
            'current_service_last_notification',
            'current_service_last_state',
            'current_service_last_state_change',
            'current_service_latency',
            'current_service_long_plugin_output',
            'current_service_low_flap_threshold',
            'current_service_max_check_attempts',
            'current_service_next_check',
            'current_service_next_notification',
            'current_service_notes',
            'current_service_notes_expanded',
            'current_service_notes_url',
            'current_service_notes_url_expanded',
            'current_service_notification_interval',
            'current_service_notification_period',
            'current_service_notifications_enabled',
            'current_service_obsess_over_service',
            'current_service_percent_state_change',
            'current_service_perf_data',
            'current_service_plugin_output',
            'current_service_process_performance_data',
            'current_service_retry_interval',
            'current_service_scheduled_downtime_depth',
            'current_service_state',
            'current_service_state_type',
            'host_name',
            'lineno',
            'message',
            'options',
            'plugin_output',
            'service_description',
            'state',
            'state_type',
            'time',
            'type',
        ],
    }


    def __init__(self, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands):
        #self.conf = scheduler.conf
        #self.scheduler = scheduler
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.debuglevel = 2


    def debug(self, debuglevel, message):
        f = open("/tmp/livestatus.debug", "a")
        f.write(message)
        f.write("\n")
        f.close()
        if self.debuglevel >= debuglevel:
            print message


    def create_output(self, elt, attributes):
        output = {}
        elt_type = elt.__class__
        if elt_type in LiveStatus.out_map:
            type_map = LiveStatus.out_map[elt_type]
            if not attributes:
                # There was no Columns: statement, so we need the complete list of attributes
                attributes = LiveStatus.default_attributes[elt_type]
            for display in attributes:
                value = ''
                if display not in type_map:
                    # no mapping, use it as a direct attribute
                    if hasattr(elt, display):
                        value = getattr(elt, display)
                    else:
                        value = ''
                else:
                    if 'prop' not in type_map[display] or type_map[display]['prop'] == None:
                        # display is listed, but prop is not set. this must be a direct attribute
                        prop = display
                    else:
                        # We have a prop, this means some kind of mapping between the display name (livestatus column)
                        # and an internal name must happen
                        prop = type_map[display]['prop']
                    if hasattr(elt, prop) and getattr(elt, prop) != None:
                        # The name/function listed in prop exists
                        value = getattr(elt, prop)
                        #Maybe it's not a value, but a function link
                        if callable(value):
                            value = value()
                        if display in type_map and 'depythonize' in type_map[display]:
                            f = type_map[display]['depythonize']
                            if callable(f):
                                print "i can depython", display
                                #for example "from_list_to_split". value is an array and f takes the array as an argument
                                print "first we have", value
                                value = f(value)
                                print "then we have", value
                                
                            else:
                                if isinstance(value, list):
                                    #depythonize's argument might be an attribute or a method
                                    #example: members is an array of hosts and we want get_name() of each element
                                    value = [getattr(item, f)() for item in value if callable(getattr(item, f)) ] \
                                          + [getattr(item, f) for item in value if not callable(getattr(item, f)) ]
                                    #at least servicegroups are nested [host,service],.. The need some flattening
                                    value = ','.join(['%s' % y for x in value if isinstance(x, list) for y in x] + \
                                        ['%s' % x for x in value if not isinstance(x, list)])
                                else:
                                    #ok not a direct function, maybe a functin provided by value...
                                    f = getattr(value, f)
                                    if callable(f):
                                        value = f()
                                    else:
                                        value = f

                        if len(str(value)) == 0:
                            value = ''
                    elif 'default' in type_map[display]:
                        # display is not a known attribute, there is no prop for mapping, but
                        # at least we have a default value
                        value = type_map[display]['default']
                    else:
                        value = ''
                output[display] = str(value)    
        return output


    def get_live_data(self, table, columns, filter_stack, stats_filter_stack, stats_postprocess_stack):
        result = []
        if table in ['hosts', 'services', 'downtimes', 'comments', 'hostgroups', 'servicegroups']:
            #Scan through the objects and apply the Filter: rules
            if table == 'hosts':
                filtresult = [y for y in [self.create_output(x, columns) for x in self.hosts.values()] if filter_stack(y)]
            elif table == 'services':
                filtresult = [y for y in [self.create_output(x, columns) for x in self.services.values()] if filter_stack(y)]
            elif table == 'downtimes':
                filtresult = [self.create_output(y, columns) for y in reduce(list.__add__, [x.downtimes for x in self.services.values() +self.hosts.values() if len(x.downtimes) > 0], [])]
            elif table == 'comments':
                filtresult = [self.create_output(y, columns) for y in reduce(list.__add__, [x.comments for x in self.services.values() +self.hosts.values() if len(x.comments) > 0], [])]
            elif table == 'hostgroups':
                filtresult = [y for y in [self.create_output(x, columns) for x in self.hostgroups.values()] if filter_stack(y)]
            elif table == 'servicegroups':
                filtresult = [y for y in [self.create_output(x, columns) for x in self.servicegroups.values()] if filter_stack(y)]
            if stats_filter_stack.qsize() > 0:
                #The number of Stats: statements
                #For each statement there is one function on the stack
                maxidx = stats_filter_stack.qsize()
                resultarr = {}
                for i in range(maxidx):
                    #First, get a filter for the attributes mentioned in Stats: statements
                    filtfunc = stats_filter_stack.get()
                    #Then, postprocess (sum, max, min,...) the results
                    postprocess = stats_postprocess_stack.get()
                    resultarr[maxidx - i - 1] = str(postprocess(filter(filtfunc, filtresult)))
                result = [resultarr]
            else:
                #Results are host/service/etc dicts with the requested attributes 
                #Columns: = keys of the dicts
                result = filtresult
        elif table == 'contacts':
            for c in self.contacts.values():
                result.append(self.create_output(c, columns))
        elif table == 'status':
            for c in self.configs.values():
                result.append(self.create_output(c, columns))
        return result


    def format_live_data(self, result, columns, outputformat, columnheaders, separators, aliases):
        output = ''
        if outputformat == 'CSV':
            lines = []
            if len(result) > 0:
                if columnheaders != 'off':
                    if len(aliases) > 0:
                        #This is for statements like "Stats: .... as alias_column
                        lines.append(separators[1].join([aliases[col] for col in columns]))
                    else:
                        if (len(columns) == 0):
                            # Show all available columns
                            columns = sorted(result[0].keys())
                        lines.append(separators[1].join(columns))
                for object in result:
                    #construct one line of output for each object found
                    lines.append(separators[1].join([object[c] for c in columns]))
            else:
                if columnheaders == 'on':
                    if len(aliases) > 0:
                        lines.append(separators[1].join([aliases[col] for col in columns]))
                    else:
                        lines.append(separators[1].join(columns))
            return separators[0].join(lines)


    def make_filter(self, operator, attribute, reference):
        #The filters are closures. 
        def equal_filter(ref):
            return ref[attribute] == reference

        def ne_filter(ref):
            return ref[attribute] != reference

        def gt_filter(ref):
            return ref[attribute] > reference

        def ge_filter(ref):
            return ref[attribute] >= reference

        def lt_filter(ref):
            return ref[attribute] < reference

        def le_filter(ref):
            return ref[attribute] <= reference

        def contains_filter(ref):
            return reference in ref[attribute].split(',')

        def dummy_filter(ref):
            return True

        def count_postproc(ref):
            return len(ref)

        def extract_postproc(ref):
            return [float(obj[attribute]) for obj in ref]

        def sum_postproc(ref):
            return sum(float(obj[attribute]) for obj in ref)

        def max_postproc(ref):
            return max(float(obj[attribute]) for obj in ref)

        def min_postproc(ref):
            return min(float(obj[attribute]) for obj in ref)

        def avg_postproc(ref):
            return sum(float(obj[attribute]) for obj in ref) / len(ref)

        def std_postproc(ref):
            return 0
        
        ##print "check operator", operator
        if operator == '=':
            return equal_filter
        elif operator == '!=':
            return ne_filter
        elif operator == '>':
            return gt_filter
        elif operator == '>=':
            if True:
                # if attribute is a list
                return contains_filter
            else:
                return ge_filter
        elif operator == 'dummy':
            return dummy_filter
        elif operator == 'sum':
            return sum_postproc
        elif operator == 'max':
            return max_postproc
        elif operator == 'min':
            return min_postproc
        elif operator == 'avg':
            return avg_postproc
        elif operator == 'std':
            return std_postproc
        elif operator == 'count':
            # postprocess for stats
            return count_postproc
        elif operator == 'extract':
            # postprocess for max,min,...
            return extract_postproc
        else:
            raise "wrong operation", operator


    def get_filter_stack(self, filter_stack):
        if filter_stack.qsize() == 0:
            return lambda x : True
        else:
            return filter_stack.get()
        pass


    def and_filter_stack(self, num, filter_stack):
        filters = []
        for i in range(int(num)):
            filters.append(filter_stack.get())
        # Take from the stack:
        # List of functions taking parameter ref
        # Make a combined anded function
        # Put it on the stack
        def and_filter(ref):
            myfilters = filters
            failed = False
            for filter in myfilters:
                if not filter(ref):
                    failed = True
                    break
                else:
                    pass
            return not failed
        filter_stack.put(and_filter)
        return filter_stack


    def or_filter_stack(self, num, filter_stack):
        filters = []
        for i in range(int(num)):
            filters.append(filter_stack.get())
        # Take from the stack:
        # List of functions taking parameter ref
        # Make a combined ored function
        # Put it on the stack
        def or_filter(ref):
            myfilters = filters
            failed = True
            for filter in myfilters:
                if filter(ref):
                    failed = False
                    break
                else:
                    pass
            return not failed
        filter_stack.put(or_filter)
        return filter_stack


    def handle_request(self, data):
        title = ''
        content = ''
        response = ''
        columns = []
        filtercolumns = []
        responseheader = 'off'
        outputformat = 'CSV'
        columnheaders = 'off'
        groupby = False
        aliases = []
        # Set the default values for the separators
        separators = map(lambda x: chr(int(x)), [10, 59, 44, 124])
        # Initialize the stacks which are needed for the Filter: and Stats:
        # filter- and count-operations
        filter_stack = Queue.LifoQueue()
        stats_filter_stack = Queue.LifoQueue()
        stats_postprocess_stack = Queue.LifoQueue()
        for line in data.splitlines():
            line = line.strip()
            if line.find('GET ') != -1:
                # Get the name of the base table
                cmd, table = line.split(' ', 1)
            elif line.find('Columns: ') != -1:
                # Get the names of the desired columns
                p = re.compile(r'\s+')
                cmd, columns = p.split(line, 1)
                columns = p.split(columns)
                columnheaders = 'off'
            elif line.find('ResponseHeader: ') != -1:
                cmd, responseheader = line.split(' ', 1)
            elif line.find('OutputFormat: ') != -1:
                cmd, outputformat = line.split(' ', 1)
            elif line.find('ColumnHeaders: ') != -1:
                cmd, columnheaders = line.split(' ', 1)
            elif line.find('Filter: ') != -1:
                try:
                    cmd, attribute, operator, reference = line.split(' ', 3)
                except:
                    cmd, attribute, operator = line.split(' ', 3)
                    reference = ''
                if operator in ['=', '!=', '>', '>=', '<', '<=']:
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    filtercolumns.append(attribute)
                    filter_stack.put(self.make_filter(operator, attribute, reference))
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif line.find('And: ', 0, 5) != -1:
                cmd, andnum = line.split(' ', 1)
                # Take the last andnum functions from the stack
                # Construct a new function which makes a logical and
                # Put the function back onto the stack
                filter_stack = self.and_filter_stack(andnum, filter_stack)
            elif line.find('Or: ', 0, 4) != -1:
                cmd, ornum = line.split(' ', 1)
                # Take the last ornum functions from the stack
                # Construct a new function which makes a logical or
                # Put the function back onto the stack
                filter_stack = self.or_filter_stack(ornum, filter_stack)
            elif line.find('StatsGroupBy: ') != -1:
                cmd, groupby = line.split(' ', 1)
                filtercolumns.append(groupby)
            elif line.find('Stats: ') != -1:
                try:
                    cmd, attribute, operator, reference = line.split(' ', 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference.find('as ', 3):
                        attribute, operator = operator, attribute
                        asas, alias = reference.split(' ')
                        aliases.append(alias)
                except:
                    cmd, attribute, operator = line.split(' ', 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std']:
                        attribute, operator = operator, attribute
                    reference = ''
                if operator in ['=', '!=', '>', '>=']:
                    filtercolumns.append(attribute)
                    stats_filter_stack.put(self.make_filter(operator, attribute, reference))
                    stats_postprocess_stack.put(self.make_filter('count', attribute, groupby))
                elif operator in ['sum', 'min', 'max', 'avg', 'std']:
                    filtercolumns.append(attribute)
                    stats_filter_stack.put(self.make_filter('dummy', attribute, None))
                    stats_postprocess_stack.put(self.make_filter(operator, attribute, groupby))
                else:
                    print "illegal operation", operator
                    pass # illegal operation

            elif line.find('StatsAnd: ') != -1:
                cmd, andnum = line.split(' ', 1)
                stats_filter_stack = self.and_filter_stack(andnum, stats_filter_stack)
            elif line.find('StatsOr: ') != -1:
                cmd, ornum = line.split(' ', 1)
                stats_filter_stack = self.or_filter_stack(ornum, stats_filter_stack)
            elif line.find('Separators: ') != -1:
                # check Class.attribute exists
                cmd, sep1, sep2, sep3, sep4 = line.split(' ', 5)
                separators = map(lambda x: chr(int(x)), [sep1, sep2, sep3, sep4])
            else:
                # This line is not valid or not implemented
                pass
        
        if filter_stack.qsize() > 1:
            #If we have Filter: statements but no FilterAnd/Or statements
            #Make one big filter where the single filters are anded
            filter_stack = self.and_filter_stack(filter_stack.qsize(), filter_stack)
        try:
            #Get the function which implements the Filter: statements
            simplefilter_stack = self.get_filter_stack(filter_stack)
            #Get the function which implements the Stats: statements
            stats = stats_filter_stack.qsize()
            #Apply the filters on the broker's host/service/etc elements
            #Deduplicate the columns with a list(set(<list>)) hack
            result = self.get_live_data(table, list(set(columns + filtercolumns)), simplefilter_stack, stats_filter_stack, stats_postprocess_stack)
            if stats > 0:
                columns = range(stats)
                if len(aliases) == 0:
                    #If there were Stats: staments without "as", show no column headers at all
                    columnheaders = 'off'
                else:
                    columnheaders = 'on'
            #Now bring the retrieved information to a form which can be sent back to the client
            response = self.format_live_data(result, columns, outputformat, columnheaders, separators, aliases) + "\n"
        except BaseException as e:
            exit
            print "REQUEST produces an exception", data, e


        if responseheader == 'fixed16':
            statuscode = 200
            responselength = len(response) # no error
            response = '%3d %11d\n' % (statuscode, responselength) + response

        print "REQUEST", data
        print "RESPONSE\n%s\n" % response
        return response


