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
import json
import sqlite3

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
from external_command import ExternalCommand

from util import from_bool_to_string,from_bool_to_int,from_list_to_split,from_float_to_int,to_int,to_split

LOGCLASS_INFO         = 0 # all messages not in any other class
LOGCLASS_ALERT        = 1 # alerts: the change service/host state
LOGCLASS_PROGRAM      = 2 # important programm events (restart, ...)
LOGCLASS_NOTIFICATION = 3 # host/service notifications
LOGCLASS_PASSIVECHECK = 4 # passive checks
LOGCLASS_COMMAND      = 5 # external commands
LOGCLASS_STATE        = 6 # initial or current states
LOGCLASS_INVALID      = -1 # never stored
LOGCLASS_ALL          = 0xffff
LOGOBJECT_INFO        = 0 
LOGOBJECT_HOST        = 1
LOGOBJECT_SERVICE     = 2
LOGOBJECT_CONTACT     = 3 

#This is a dirty hack. Service.get_name only returns service_description.
#For the servicegroup config we need more. host_name + separator + service_description
def get_full_name(self):
    return self.host_name + LiveStatus.separators[3] + self.service_description
Service.get_full_name = get_full_name


class Logline(dict):
    def __init__(self, cursor, row):
        for idx, col in enumerate(cursor.description):
            setattr(self, col[0], row[idx])

    def fill(self, hosts, services, hostname_lookup_table, servicename_lookup_table, columns):
        if self.logobject == LOGOBJECT_HOST:
            if self.host_name in hostname_lookup_table:
                setattr(self, 'log_host', hosts[hostname_lookup_table[self.host_name]])
        elif self.logobject == LOGOBJECT_SERVICE:
            if self.host_name in hostname_lookup_table:
                setattr(self, 'log_host', hosts[hostname_lookup_table[self.host_name]])
            if self.host_name + self.service_description in servicename_lookup_table:
                setattr(self, 'log_service', services[servicename_lookup_table[self.host_name + self.service_description]])
        return self


class LiveStatus:
    separators = map(lambda x: chr(int(x)), [10, 59, 44, 124])
    #prop : is the internal name if it is different than the name in the output file
    #required : 
    #depythonize : 
    #default :
    out_map = {
        'Host' : {
            'accept_passive_checks' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether passive host checks are accepted (0/1)',
                'prop' : 'passive_checks_enabled',
                'type' : 'int',
            },
            'acknowledged' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the current host problem has been acknowledged (0/1)',
                'prop' : 'problem_has_been_acknowledged',
                'type' : 'int',
            },
            'acknowledgement_type' : {
                'description' : 'Type of acknowledgement (0: none, 1: normal, 2: stick)',
                'type' : 'int',
            },
            'action_url' : {
                'description' : 'An optional URL to custom actions or information about this host',
                'type' : 'string',
            },
            'action_url_expanded' : {
                'description' : 'The same as action_url, but with the most important macros expanded',
                'type' : 'string',
            },
            'active_checks_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether active checks are enabled for the host (0/1)',
                'type' : 'int',
            },
            'address' : {
                'description' : 'IP address',
                'type' : 'string',
            },
            'alias' : {
                'description' : 'An alias name for the host',
                'type' : 'string',
            },
            'check_command' : {
                'depythonize' : 'call',
                'description' : 'Nagios command for active host check of this host',
                'type' : 'string',
            },
            'check_freshness' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether freshness checks are activated (0/1)',
                'type' : 'int',
            },
            'check_interval' : {
                'converter' : int,
                'description' : 'Number of basic interval lengths between two scheduled checks of the host',
                'type' : 'float',
            },
            'check_options' : {
                'description' : 'The current check option, forced, normal, freshness... (0-2)',
                'type' : 'int',
            },
            'check_period' : {
                'depythonize' : 'get_name',
                'description' : 'Time period in which this host will be checked. If empty then the host will always be checked.',
                'type' : 'string',
            },
            'check_type' : {
                'converter' : int,
                'description' : 'Type of check (0: active, 1: passive)',
                'type' : 'int',
            },
            'checks_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether checks of the host are enabled (0/1)',
                'prop' : 'active_checks_enabled',
                'type' : 'int',
            },
            'childs' : {
                'default' : '',
                'depythonize' : from_list_to_split,
                'description' : 'A list of all direct childs of the host',
                'type' : 'list',
            },
            'comments' : {
                'default' : '',
                'depythonize' : 'id',
                'description' : 'A list of the ids of all comments of this host',
                'type' : 'list',
            },
            'contacts' : {
                'depythonize' : 'contact_name',
                'description' : 'A list of all contacts of this host, either direct or via a contact group',
                'type' : 'list',
            },
            'current_attempt' : {
                'converter' : int,
                'default' : 0,
                'description' : 'Number of the current check attempts',
                'prop' : 'attempt',
                'type' : 'int',
            },
            'current_notification_number' : {
                'converter' : int,
                'description' : 'Number of the current notification',
                'type' : 'int',
            },
            'custom_variable_names' : {
                'description' : 'A list of the names of all custom variables',
                'type' : 'list',
            },
            'custom_variable_values' : {
                'description' : 'A list of the values of the custom variables',
                'type' : 'list',
            },
            'display_name' : {
                'description' : 'Optional display name of the host - not used by Nagios\' web interface',
                'type' : 'string',
            },
            'downtimes' : {
                'description' : 'A list of the ids of all scheduled downtimes of this host',
                'type' : 'list',
            },
            'event_handler_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether event handling is enabled (0/1)',
                'type' : 'int',
            },
            'execution_time' : {
                'converter' : float,
                'description' : 'Time the host check needed for execution',
                'type' : 'float',
            },
            'first_notification_delay' : {
                'converter' : int,
                'description' : 'Delay before the first notification',
                'type' : 'float',
            },
            'flap_detection_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether flap detection is enabled (0/1)',
                'type' : 'int',
            },
            'groups' : {
                'default' : '',
                'depythonize' : to_split,
                'description' : 'A list of all host groups this host is in',
                'prop' : 'hostgroups',
                'type' : 'list',
            },
            'hard_state' : {
                'description' : 'The effective hard state of the host (eliminates a problem in hard_state)',
                'type' : 'int',
            },
            'has_been_checked' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host has already been checked (0/1)',
                'type' : 'int',
            },
            'high_flap_threshold' : {
                'converter' : float,
                'description' : 'High threshold of flap detection',
                'type' : 'float',
            },
            'icon_image' : {
                'description' : 'The name of an image file to be used in the web pages',
                'type' : 'string',
            },
            'icon_image_alt' : {
                'description' : 'Alternative text for the icon_image',
                'type' : 'string',
            },
            'icon_image_expanded' : {
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'type' : 'string',
            },
            'in_check_period' : {
                'description' : 'Wether this host is currently in its check period (0/1)',
                'type' : 'int',
            },
            'in_notification_period' : {
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'type' : 'int',
            },
            'initial_state' : {
                'description' : 'Initial host state',
                'type' : 'int',
            },
            'is_executing' : {
                'description' : 'is there a host check currently running... (0/1)',
                'type' : 'int',
            },
            'is_flapping' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is flapping (0/1)',
                'type' : 'int',
            },
            'last_check' : {
                'converter' : int,
                'depythonize' : from_float_to_int,
                'description' : 'Time of the last check (Unix timestamp)',
                'prop' : 'last_chk',
                'type' : 'int',
            },
            'last_hard_state' : {
                'description' : 'Last hard state',
                'type' : 'int',
            },
            'last_hard_state_change' : {
                'description' : 'Time of the last hard state change (Unix timestamp)',
                'type' : 'int',
            },
            'last_notification' : {
                'converter' : int,
                'depythonize' : to_int,
                'description' : 'Time of the last notification (Unix timestamp)',
                'type' : 'int',
            },
            'last_state' : {
                'description' : 'State before last state change',
                'type' : 'int',
            },
            'last_state_change' : {
                'converter' : int,
                'depythonize' : from_float_to_int,
                'description' : 'Time of the last state change - soft or hard (Unix timestamp)',
                'type' : 'int',
            },
            'latency' : {
                'converter' : float,
                'description' : 'Time difference between scheduled check time and actual check time',
                'type' : 'float',
            },
            'long_plugin_output' : {
                'description' : 'Complete output from check plugin',
                'prop' : 'long_output',
                'type' : 'string',
            },
            'low_flap_threshold' : {
                'description' : 'Low threshold of flap detection',
                'type' : 'float',
            },
            'max_check_attempts' : {
                'description' : 'Max check attempts for active host checks',
                'type' : 'int',
            },
            'name' : {
                'description' : 'Host name',
                'prop' : 'host_name',
                'type' : 'string',
            },
            'next_check' : {
                'converter' : int,
                'depythonize' : from_float_to_int,
                'description' : 'Scheduled time for the next check (Unix timestamp)',
                'prop' : 'next_chk',
                'type' : 'int',
            },
            'next_notification' : {
                'converter' : int,
                'description' : 'Time of the next notification (Unix timestamp)',
                'type' : 'int',
            },
            'notes' : {
                'description' : 'Optional notes for this host',
                'type' : 'string',
            },
            'notes_expanded' : {
                'description' : 'The same as notes, but with the most important macros expanded',
                'type' : 'string',
            },
            'notes_url' : {
                'description' : 'An optional URL with further information about the host',
                'type' : 'string',
            },
            'notes_url_expanded' : {
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'type' : 'string',
            },
            'notification_interval' : {
                'converter' : int,
                'description' : 'Interval of periodic notification or 0 if its off',
                'type' : 'float',
            },
            'notification_period' : {
                'depythonize' : 'get_name',
                'description' : 'Time period in which problems of this host will be notified. If empty then notification will be always',
                'type' : 'string',
            },
            'notifications_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether notifications of the host are enabled (0/1)',
                'type' : 'int',
            },
            'num_services' : {
                'depythonize' : lambda x: len(x),
                'description' : 'The total number of services of the host',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_crit' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2]),
                'description' : 'The number of the host\'s services with the soft state CRIT',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_hard_crit' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state CRIT',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_hard_ok' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 0 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state OK',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_hard_unknown' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 3 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state UNKNOWN',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_hard_warn' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state WARN',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_ok' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 0]),
                'description' : 'The number of the host\'s services with the soft state OK',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_pending' : {
                'depythonize' : lambda x: len([y for y in x if y.has_been_checked == 0]),
                'description' : 'The number of the host\'s services which have not been checked yet (pending)',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_unknown' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 3]),
                'description' : 'The number of the host\'s services with the soft state UNKNOWN',
                'prop' : 'services',
                'type' : 'list',
            },
            'num_services_warn' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 1]),
                'description' : 'The number of the host\'s services with the soft state WARN',
                'prop' : 'services',
                'type' : 'list',
            },
            'obsess_over_host' : {
                'depythonize' : from_bool_to_int,
                'description' : 'The current obsess_over_host setting... (0/1)',
                'type' : 'int',
            },
            'parents' : {
                'depythonize' : lambda x: ','.join(x),
                'description' : 'A list of all direct parents of the host',
                'type' : 'list',
            },
            'pending_flex_downtime' : {
                'description' : 'Wether a flex downtime is pending (0/1)',
                'type' : 'int',
            },
            'percent_state_change' : {
                'description' : 'Percent state change',
                'type' : 'float',
            },
            'perf_data' : {
                'description' : 'Optional performance data of the last host check',
                'type' : 'string',
            },
            'plugin_output' : {
                'description' : 'Output of the last host check',
                'prop' : 'output',
                'type' : 'string',
            },
            'process_performance_data' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether processing of performance data is enabled (0/1)',
                'prop' : 'process_perf_data',
                'type' : 'int',
            },
            'retry_interval' : {
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'type' : 'float',
            },
            'scheduled_downtime_depth' : {
                'converter' : int,
                'description' : 'The number of downtimes this host is currently in',
                'type' : 'int',
            },
            'state' : {
                'converter' : int,
                'description' : 'The current state of the host (0: up, 1: down, 2: unreachable)',
                'prop' : 'state_id',
                'type' : 'int',
            },
            'state_type' : {
                'converter' : int,
                'description' : 'Type of the current state (0: soft, 1: hard)',
                'prop' : 'state_type_id',
                'type' : 'int',
            },
            'statusmap_image' : {
                'description' : 'The name of in image file for the status map',
                'type' : 'string',
            },
            'total_services' : {
                'description' : 'The total number of services of the host',
                'type' : 'int',
            },
            'worst_service_hard_state' : {
                'description' : 'The worst hard state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'list',
            },
            'worst_service_state' : {
                'description' : 'The worst soft state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'list',
            },
            'x_3d' : {
                'description' : '3D-Coordinates: X',
                'type' : 'float',
            },
            'y_3d' : {
                'description' : '3D-Coordinates: Y',
                'type' : 'float',
            },
            'z_3d' : {
                'description' : '3D-Coordinates: Z',
                'type' : 'float',
            },
        },

        'Service' : {
            'accept_passive_checks' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the service accepts passive checks (0/1)',
                'prop' : 'passive_checks_enabled',
                'type' : 'int',
            },
            'acknowledged' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the current service problem has been acknowledged (0/1)',
                'prop' : 'problem_has_been_acknowledged',
                'type' : 'int',
            },
            'acknowledgement_type' : {
                'description' : 'The type of the acknownledgement (0: none, 1: normal, 2: sticky)',
                'type' : 'int',
            },
            'action_url' : {
                'description' : 'An optional URL for actions or custom information about the service',
                'type' : 'string',
            },
            'action_url_expanded' : {
                'description' : 'The action_url with (the most important) macros expanded',
                'type' : 'string',
            },
            'active_checks_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'type' : 'int',
            },
            'check_command' : {
                'depythonize' : 'call',
                'description' : 'Nagios command used for active checks',
                'type' : 'string',
            },
            'check_interval' : {
                'description' : 'Number of basic interval lengths between two scheduled checks of the service',
                'type' : 'float',
            },
            'check_options' : {
                'description' : 'The current check option, forced, normal, freshness... (0/1)',
                'type' : 'int',
            },
            'check_period' : {
                'depythonize' : 'get_name',
                'description' : 'The name of the check period of the service. It this is empty, the service is always checked.',
                'type' : 'string',
            },
            'check_type' : {
                'converter' : int,
                'depythonize' : to_int,
                'description' : 'The type of the last check (0: active, 1: passive)',
                'type' : 'int',
            },
            'checks_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'prop' : 'active_checks_enabled',
                'type' : 'int',
            },
            'comments' : {
                'default' : '',
                'depythonize' : 'id',
                'description' : 'A list of all comment ids of the service',
                'type' : 'list',
            },
            'contacts' : {
                'depythonize' : 'contact_name',
                'description' : 'A list of all contacts of the service, either direct or via a contact group',
                'type' : 'list',
            },
            'current_attempt' : {
                'converter' : int,
                'description' : 'The number of the current check attempt',
                'prop' : 'attempt',
                'type' : 'int',
            },
            'current_notification_number' : {
                'description' : 'The number of the current notification',
                'type' : 'int',
            },
            'custom_variable_names' : {
                'description' : 'A list of the names of all custom variables of the service',
                'type' : 'list',
            },
            'custom_variable_values' : {
                'description' : 'A list of the values of all custom variable of the service',
                'type' : 'list',
            },
            'description' : {
                'description' : 'Description of the service (also used as key)',
                'prop' : 'service_description',
                'type' : 'string',
            },
            'display_name' : {
                'description' : 'An optional display name (not used by Nagios standard web pages)',
                'type' : 'string',
            },
            'downtimes' : {
                'description' : 'A list of all downtime ids of the service',
                'type' : 'list',
            },
            'event_handler' : {
                'depythonize' : 'call',
                'description' : 'Nagios command used as event handler',
                'type' : 'string',
            },
            'event_handler_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether and event handler is activated for the service (0/1)',
                'type' : 'int',
            },
            'execution_time' : {
                'converter' : float,
                'description' : 'Time the host check needed for execution',
                'type' : 'float',
            },
            'first_notification_delay' : {
                'converter' : int,
                'description' : 'Delay before the first notification',
                'type' : 'float',
            },
            'flap_detection_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether flap detection is enabled for the service (0/1)',
                'type' : 'int',
            },
            'groups' : {
                'default' : '',
                'depythonize' : to_split,
                'description' : 'A list of all service groups the service is in',
                'prop' : 'servicegroups',
                'type' : 'list',
            },
            'has_been_checked' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the service already has been checked (0/1)',
                'type' : 'int',
            },
            'high_flap_threshold' : {
                'description' : 'High threshold of flap detection',
                'type' : 'float',
            },
            'host_accept_passive_checks' : {
                'description' : 'Wether passive host checks are accepted (0/1)',
                'type' : 'int',
            },
            'host_acknowledged' : {
                'depythonize' : lambda x: from_bool_to_int(x.problem_has_been_acknowledged),
                'description' : 'Wether the current host problem has been acknowledged (0/1)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_acknowledgement_type' : {
                'description' : 'Type of acknowledgement (0: none, 1: normal, 2: stick)',
                'type' : 'int',
            },
            'host_action_url' : {
                'description' : 'An optional URL to custom actions or information about this host',
                'type' : 'string',
            },
            'host_action_url_expanded' : {
                'description' : 'The same as action_url, but with the most important macros expanded',
                'type' : 'string',
            },
            'host_active_checks_enabled' : {
                'description' : 'Wether active checks are enabled for the host (0/1)',
                'type' : 'int',
            },
            'host_address' : {
                'description' : 'IP address',
                'type' : 'string',
            },
            'host_alias' : {
                'description' : 'An alias name for the host',
                'type' : 'string',
            },
            'host_check_command' : {
                'description' : 'Nagios command for active host check of this host',
                'type' : 'string',
            },
            'host_check_freshness' : {
                'description' : 'Wether freshness checks are activated (0/1)',
                'type' : 'int',
            },
            'host_check_interval' : {
                'description' : 'Number of basic interval lengths between two scheduled checks of the host',
                'type' : 'float',
            },
            'host_check_options' : {
                'description' : 'The current check option, forced, normal, freshness... (0-2)',
                'type' : 'int',
            },
            'host_check_period' : {
                'description' : 'Time period in which this host will be checked. If empty then the host will always be checked.',
                'type' : 'string',
            },
            'host_check_type' : {
                'description' : 'Type of check (0: active, 1: passive)',
                'type' : 'int',
            },
            'host_checks_enabled' : {
                'depythonize' : lambda x: from_bool_to_int(x.active_checks_enabled),
                'description' : 'Wether checks of the host are enabled (0/1)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_childs' : {
                'description' : 'A list of all direct childs of the host',
                'type' : 'list',
            },
            'host_comments' : {
                'default' : '',
                'depythonize' : lambda h: ','.join([str(c.id) for c in h.comments]),
                'description' : 'A list of the ids of all comments of this host',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_contacts' : {
                'description' : 'A list of all contacts of this host, either direct or via a contact group',
                'type' : 'list',
            },
            'host_current_attempt' : {
                'description' : 'Number of the current check attempts',
                'type' : 'int',
            },
            'host_current_notification_number' : {
                'description' : 'Number of the current notification',
                'type' : 'int',
            },
            'host_custom_variable_names' : {
                'description' : 'A list of the names of all custom variables',
                'type' : 'list',
            },
            'host_custom_variable_values' : {
                'description' : 'A list of the values of the custom variables',
                'type' : 'list',
            },
            'host_display_name' : {
                'description' : 'Optional display name of the host - not used by Nagios\' web interface',
                'type' : 'string',
            },
            'host_downtimes' : {
                'description' : 'A list of the ids of all scheduled downtimes of this host',
                'type' : 'list',
            },
            'host_event_handler_enabled' : {
                'description' : 'Wether event handling is enabled (0/1)',
                'type' : 'int',
            },
            'host_execution_time' : {
                'description' : 'Time the host check needed for execution',
                'type' : 'float',
            },
            'host_first_notification_delay' : {
                'description' : 'Delay before the first notification',
                'type' : 'float',
            },
            'host_flap_detection_enabled' : {
                'description' : 'Wether flap detection is enabled (0/1)',
                'type' : 'int',
            },
            'host_groups' : {
                'default' : '',
                'depythonize' : lambda x: to_split(x.hostgroups),
                'description' : 'A list of all host groups this host is in',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_hard_state' : {
                'description' : 'The effective hard state of the host (eliminates a problem in hard_state)',
                'type' : 'int',
            },
            'host_has_been_checked' : {
                'depythonize' : lambda x: from_bool_to_int(x.has_been_checked),
                'description' : 'Wether the host has already been checked (0/1)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_high_flap_threshold' : {
                'description' : 'High threshold of flap detection',
                'type' : 'float',
            },
            'host_icon_image' : {
                'description' : 'The name of an image file to be used in the web pages',
                'type' : 'string',
            },
            'host_icon_image_alt' : {
                'description' : 'Alternative text for the icon_image',
                'type' : 'string',
            },
            'host_icon_image_expanded' : {
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'type' : 'string',
            },
            'host_in_check_period' : {
                'description' : 'Wether this host is currently in its check period (0/1)',
                'type' : 'int',
            },
            'host_in_notification_period' : {
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'type' : 'int',
            },
            'host_initial_state' : {
                'description' : 'Initial host state',
                'type' : 'int',
            },
            'host_is_executing' : {
                'description' : 'is there a host check currently running... (0/1)',
                'type' : 'int',
            },
            'host_is_flapping' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is flapping (0/1)',
                'type' : 'int',
            },
            'host_last_check' : {
                'description' : 'Time of the last check (Unix timestamp)',
                'type' : 'int',
            },
            'host_last_hard_state' : {
                'description' : 'Last hard state',
                'type' : 'int',
            },
            'host_last_hard_state_change' : {
                'description' : 'Time of the last hard state change (Unix timestamp)',
                'type' : 'int',
            },
            'host_last_notification' : {
                'description' : 'Time of the last notification (Unix timestamp)',
                'type' : 'int',
            },
            'host_last_state' : {
                'description' : 'State before last state change',
                'type' : 'int',
            },
            'host_last_state_change' : {
                'description' : 'Time of the last state change - soft or hard (Unix timestamp)',
                'type' : 'int',
            },
            'host_latency' : {
                'description' : 'Time difference between scheduled check time and actual check time',
                'type' : 'float',
            },
            'host_long_plugin_output' : {
                'description' : 'Complete output from check plugin',
                'type' : 'string',
            },
            'host_low_flap_threshold' : {
                'description' : 'Low threshold of flap detection',
                'type' : 'float',
            },
            'host_max_check_attempts' : {
                'description' : 'Max check attempts for active host checks',
                'type' : 'int',
            },
            'host_name' : {
                'description' : 'Host name',
                'type' : 'string',
            },
            'host_next_check' : {
                'description' : 'Scheduled time for the next check (Unix timestamp)',
                'type' : 'int',
            },
            'host_next_notification' : {
                'description' : 'Time of the next notification (Unix timestamp)',
                'type' : 'int',
            },
            'host_notes' : {
                'description' : 'Optional notes for this host',
                'type' : 'string',
            },
            'host_notes_expanded' : {
                'description' : 'The same as notes, but with the most important macros expanded',
                'type' : 'string',
            },
            'host_notes_url' : {
                'description' : 'An optional URL with further information about the host',
                'type' : 'string',
            },
            'host_notes_url_expanded' : {
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'type' : 'string',
            },
            'host_notification_interval' : {
                'description' : 'Interval of periodic notification or 0 if its off',
                'type' : 'float',
            },
            'host_notification_period' : {
                'description' : 'Time period in which problems of this host will be notified. If empty then notification will be always',
                'type' : 'string',
            },
            'host_notifications_enabled' : {
                'depythonize' : lambda x: from_bool_to_int(x.notifications_enabled),
                'description' : 'Wether notifications of the host are enabled (0/1)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_num_services' : {
                'depythonize' : lambda x: len(x.services),
                'description' : 'The total number of services of the host',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_crit' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 2]),
                'description' : 'The number of the host\'s services with the soft state CRIT',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_hard_crit' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 2 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state CRIT',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_hard_ok' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 0 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state OK',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_hard_unknown' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 3 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state UNKNOWN',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_hard_warn' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 2 and y.state_type_id == 1]),
                'description' : 'The number of the host\'s services with the hard state WARN',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_ok' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 0]),
                'description' : 'The number of the host\'s services with the soft state OK',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_pending' : {
                'depythonize' : lambda x: len([y for y in x.services if y.has_been_checked == 0]),
                'description' : 'The number of the host\'s services which have not been checked yet (pending)',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_unknown' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 3]),
                'description' : 'The number of the host\'s services with the soft state UNKNOWN',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_num_services_warn' : {
                'depythonize' : lambda x: len([y for y in x.services if y.state_id == 1]),
                'description' : 'The number of the host\'s services with the soft state WARN',
                'prop' : 'host',
                'type' : 'list',
            },
            'host_obsess_over_host' : {
                'description' : 'The current obsess_over_host setting... (0/1)',
                'type' : 'int',
            },
            'host_parents' : {
                'description' : 'A list of all direct parents of the host',
                'type' : 'list',
            },
            'host_pending_flex_downtime' : {
                'description' : 'Wether a flex downtime is pending (0/1)',
                'type' : 'int',
            },
            'host_percent_state_change' : {
                'description' : 'Percent state change',
                'type' : 'float',
            },
            'host_perf_data' : {
                'description' : 'Optional performance data of the last host check',
                'type' : 'string',
            },
            'host_plugin_output' : {
                'description' : 'Output of the last host check',
                'type' : 'string',
            },
            'host_process_performance_data' : {
                'description' : 'Wether processing of performance data is enabled (0/1)',
                'type' : 'int',
            },
            'host_retry_interval' : {
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'type' : 'float',
            },
            'host_scheduled_downtime_depth' : {
                'converter' : int,
                'depythonize' : lambda x: x.scheduled_downtime_depth,
                'description' : 'The number of downtimes this host is currently in',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_state' : {
                'converter' : int,
                'depythonize' : lambda x: x.state_id,
                'description' : 'The current state of the host (0: up, 1: down, 2: unreachable)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_state_type' : {
                'description' : 'Type of the current state (0: soft, 1: hard)',
                'type' : 'int',
            },
            'host_statusmap_image' : {
                'description' : 'The name of in image file for the status map',
                'type' : 'string',
            },
            'host_total_services' : {
                'description' : 'The total number of services of the host',
                'type' : 'int',
            },
            'host_worst_service_hard_state' : {
                'description' : 'The worst hard state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'list',
            },
            'host_worst_service_state' : {
                'description' : 'The worst soft state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'list',
            },
            'host_x_3d' : {
                'description' : '3D-Coordinates: X',
                'type' : 'float',
            },
            'host_y_3d' : {
                'description' : '3D-Coordinates: Y',
                'type' : 'float',
            },
            'host_z_3d' : {
                'description' : '3D-Coordinates: Z',
                'type' : 'float',
            },
            'icon_image' : {
                'description' : 'The name of an image to be used as icon in the web interface',
                'type' : 'string',
            },
            'icon_image_alt' : {
                'description' : 'An alternative text for the icon_image for browsers not displaying icons',
                'type' : 'string',
            },
            'icon_image_expanded' : {
                'description' : 'The icon_image with (the most important) macros expanded',
                'type' : 'string',
            },
            'in_check_period' : {
                'description' : 'Wether the service is currently in its check period (0/1)',
                'type' : 'int',
            },
            'in_notification_period' : {
                'description' : 'Wether the service is currently in its notification period (0/1)',
                'type' : 'int',
            },
            'initial_state' : {
                'description' : 'The initial state of the service',
                'type' : 'int',
            },
            'is_executing' : {
                'description' : 'is there a service check currently running... (0/1)',
                'type' : 'int',
            },
            'is_flapping' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the service is flapping (0/1)',
                'type' : 'int',
            },
            'last_check' : {
                'depythonize' : from_float_to_int,
                'description' : 'The time of the last check (Unix timestamp)',
                'prop' : 'last_chk',
                'type' : 'int',
            },
            'last_hard_state' : {
                'description' : 'The last hard state of the service',
                'type' : 'int',
            },
            'last_hard_state_change' : {
                'description' : 'The time of the last hard state change (Unix timestamp)',
                'type' : 'int',
            },
            'last_notification' : {
                'depythonize' : to_int,
                'description' : 'The time of the last notification (Unix timestamp)',
                'type' : 'int',
            },
            'last_state' : {
                'description' : 'The last state of the service',
                'type' : 'int',
            },
            'last_state_change' : {
                'depythonize' : from_float_to_int,
                'description' : 'The time of the last state change (Unix timestamp)',
                'type' : 'int',
            },
            'latency' : {
                'depythonize' : to_int,
                'description' : 'Time difference between scheduled check time and actual check time',
                'type' : 'float',
            },
            'long_plugin_output' : {
                'description' : 'Unabbreviated output of the last check plugin',
                'prop' : 'long_output',
                'type' : 'string',
            },
            'low_flap_threshold' : {
                'description' : 'Low threshold of flap detection',
                'type' : 'float',
            },
            'max_check_attempts' : {
                'description' : 'The maximum number of check attempts',
                'type' : 'int',
            },
            'next_check' : {
                'depythonize' : from_float_to_int,
                'description' : 'The scheduled time of the next check (Unix timestamp)',
                'prop' : 'next_chk',
                'type' : 'int',
            },
            'next_notification' : {
                'description' : 'The time of the next notification (Unix timestamp)',
                'type' : 'int',
            },
            'notes' : {
                'description' : 'Optional notes about the service',
                'type' : 'string',
            },
            'notes_expanded' : {
                'description' : 'The notes with (the most important) macros expanded',
                'type' : 'string',
            },
            'notes_url' : {
                'description' : 'An optional URL for additional notes about the service',
                'type' : 'string',
            },
            'notes_url_expanded' : {
                'description' : 'The notes_url with (the most important) macros expanded',
                'type' : 'string',
            },
            'notification_interval' : {
                'description' : 'Interval of periodic notification or 0 if its off',
                'type' : 'float',
            },
            'notification_period' : {
                'depythonize' : 'get_name',
                'description' : 'The name of the notification period of the service. It this is empty, service problems are always notified.',
                'type' : 'string',
            },
            'notifications_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether notifications are enabled for the service (0/1)',
                'type' : 'int',
            },
            'obsess_over_service' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether \'obsess_over_service\' is enabled for the service (0/1)',
                'type' : 'int',
            },
            'percent_state_change' : {
                'description' : 'Percent state change',
                'type' : 'float',
            },
            'perf_data' : {
                'description' : 'Performance data of the last check plugin',
                'type' : 'string',
            },
            'plugin_output' : {
                'description' : 'Output of the last check plugin',
                'prop' : 'output',
                'type' : 'string',
            },
            'process_performance_data' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether processing of performance data is enabled for the service (0/1)',
                'prop' : 'process_perf_data',
                'type' : 'int',
            },
            'retry_interval' : {
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'type' : 'float',
            },
            'scheduled_downtime_depth' : {
                'converter' : int,
                'description' : 'The number of scheduled downtimes the service is currently in',
                'type' : 'int',
            },
            'state' : {
                'converter' : int,
                'description' : 'The current state of the service (0: OK, 1: WARN, 2: CRITICAL, 3: UNKNOWN)',
                'prop' : 'state_id',
                'type' : 'int',
            },
            'state_type' : {
                'converter' : int,
                'description' : 'The type of the current state (0: soft, 1: hard)',
                'prop' : 'state_type_id',
                'type' : 'int',
            },
        },

        'Hostgroup' : {
            'action_url' : {
                'description' : 'An optional URL to custom actions or information about the hostgroup',
                'type' : 'string',
            },
            'alias' : {
                'description' : 'An alias of the hostgroup',
                'type' : 'string',
            },
            'members' : {
                'depythonize' : 'get_name',
                'description' : 'A list of all host names that are members of the hostgroup',
                'type' : 'list',
            },
            'name' : {
                'description' : 'Name of the hostgroup',
                'prop' : 'hostgroup_name',
                'type' : 'string',
            },
            'notes' : {
                'description' : 'Optional notes to the hostgroup',
                'type' : 'string',
            },
            'notes_url' : {
                'description' : 'An optional URL with further information about the hostgroup',
                'type' : 'string',
            },
            'num_hosts' : {
                'depythonize' : lambda x: len(x),
                'description' : 'The total number of hosts in the group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_hosts_down' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 1]),
                'description' : 'The number of hosts in the group that are down',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_hosts_pending' : {
                'depythonize' : lambda x: len([y for y in x if y.has_been_checked == 0]),
                'description' : 'The number of hosts in the group that are pending',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_hosts_unreach' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2]),
                'description' : 'The number of hosts in the group that are unreachable',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_hosts_up' : {
                'depythonize' : lambda x: len([y for y in x if y.state_id == 0]),
                'description' : 'The number of hosts in the group that are up',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services' : {
                'depythonize' : lambda x: sum((len(y.service_ids) for y in x)),
                'description' : 'The total number of services of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_crit' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 2]),
                'description' : 'The total number of services with the state CRIT of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_hard_crit' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 2 and z.state_type_id == 1]),
                'description' : 'The total number of services with the state CRIT of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_hard_ok' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 0 and z.state_type_id == 1]),
                'description' : 'The total number of services with the state OK of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_hard_unknown' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 3 and z.state_type_id == 1]),
                'description' : 'The total number of services with the state UNKNOWN of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_hard_warn' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 2 and z.state_type_id == 1]),
                'description' : 'The total number of services with the state WARN of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_ok' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 0]),
                'description' : 'The total number of services with the state OK of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_pending' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.has_been_checked == 0]),
                'description' : 'The total number of services with the state Pending of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_unknown' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 3]),
                'description' : 'The total number of services with the state UNKNOWN of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'num_services_warn' : {
                'depythonize' : lambda x: len([z for y in x for z in y.services if z.state_id == 1]),
                'description' : 'The total number of services with the state WARN of hosts in this group',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'worst_host_state' : {
                'depythonize' : lambda x: reduce(lambda g, c: c if g == 0 else (c if c == 1 else g), (y.state_id for y in x), 0),
                'description' : 'The worst state of all of the groups\' hosts (UP <= UNREACHABLE <= DOWN)',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'worst_service_hard_state' : {
                'depythonize' : lambda x: reduce(lambda g, c: c if g == 0 else (c if c == 2 else (c if (c == 3 and g != 2) else g)), (z.state_id for y in x for z in y.services if z.state_type_id == 1), 0),
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'worst_service_state' : {
                'depythonize' : lambda x: reduce(lambda g, c: c if g == 0 else (c if c == 2 else (c if (c == 3 and g != 2) else g)), (z.state_id for y in x for z in y.services), 0),
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
        },

        'Servicegroup' : {
            'action_url' : {
                'description' : 'An optional URL to custom notes or actions on the service group',
                'type' : 'string',
            },
            'alias' : {
                'description' : 'An alias of the service group',
                'type' : 'string',
            },
            'members' : {
                'depythonize' : 'get_full_name',
                'description' : 'A list of all members of the service group as host/service pairs ',
                'type' : 'list',
            },
            'name' : {
                'description' : 'The name of the service group',
                'prop' : 'servicegroup_name',
                'type' : 'string',
            },
            'notes' : {
                'description' : 'Optional additional notes about the service group',
                'type' : 'string',
            },
            'notes_url' : {
                'description' : 'An optional URL to further notes on the service group',
                'type' : 'string',
            },
            'num_services' : {
                'converter' : int,
                'depythonize' : lambda x: len(x),
                'description' : 'The total number of services in the group',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_crit' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2]),
                'description' : 'The number of services in the group that are CRIT',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_hard_crit' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2 and y.state_type_id == 1]),
                'description' : 'The number of services in the group that are CRIT',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_hard_ok' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 0 and y.state_type_id == 1]),
                'description' : 'The number of services in the group that are OK',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_hard_unknown' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 3 and y.state_type_id == 1]),
                'description' : 'The number of services in the group that are UNKNOWN',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_hard_warn' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 2 and y.state_type_id == 1]),
                'description' : 'The number of services in the group that are WARN',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_ok' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 0]),
                'description' : 'The number of services in the group that are OK',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_pending' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.has_been_checked == 0]),
                'description' : 'The number of services in the group that are PENDING',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_unknown' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 3]),
                'description' : 'The number of services in the group that are UNKNOWN',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'num_services_warn' : {
                'converter' : int,
                'depythonize' : lambda x: len([y for y in x if y.state_id == 1]),
                'description' : 'The number of services in the group that are WARN',
                'prop' : 'get_services',
                'type' : 'list',
            },
            'worst_service_state' : {
                'depythonize' : lambda x: reduce(lambda g, c: c if g == 0 else (c if c == 2 else (c if (c == 3 and g != 2) else g)), (y.state_id for y in x), 0),
                'description' : 'The worst soft state of all of the groups services (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : 'get_services',
                'type' : 'list',
            },
        },

        'Contact' : {
            'address1' : {
                'description' : 'The additional field address1',
                'type' : 'string',
            },
            'address2' : {
                'description' : 'The additional field address2',
                'type' : 'string',
            },
            'address3' : {
                'description' : 'The additional field address3',
                'type' : 'string',
            },
            'address4' : {
                'description' : 'The additional field address4',
                'type' : 'string',
            },
            'address5' : {
                'description' : 'The additional field address5',
                'type' : 'string',
            },
            'address6' : {
                'description' : 'The additional field address6',
                'type' : 'string',
            },
            'alias' : {
                'description' : 'The full name of the contact',
                'type' : 'string',
            },
            'can_submit_commands' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the contact is allowed to submit commands (0/1)',
                'type' : 'int',
            },
            'custom_variable_names' : {
                'description' : 'A list of all custom variables of the contact',
                'type' : 'list',
            },
            'custom_variable_values' : {
                'description' : 'A list of the values of all custom variables of the contact',
                'type' : 'list',
            },
            'email' : {
                'description' : 'The email address of the contact',
                'type' : 'string',
            },
            'host_notification_period' : {
                'depythonize' : 'get_name',
                'description' : 'The time period in which the contact will be notified about host problems',
                'type' : 'string',
            },
            'host_notifications_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the contact will be notified about host problems in general (0/1)',
                'type' : 'int',
            },
            'in_host_notification_period' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the contact is currently in his/her host notification period (0/1)',
                'type' : 'int',
            },
            'in_service_notification_period' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the contact is currently in his/her service notification period (0/1)',
                'type' : 'int',
            },
            'name' : {
                'description' : 'The login name of the contact person',
                'type' : 'string',
            },
            'pager' : {
                'description' : 'The pager address of the contact',
                'type' : 'string',
            },
            'service_notification_period' : {
                'depythonize' : 'get_name',
                'description' : 'The time period in which the contact will be notified about service problems',
                'type' : 'string',
            },
            'service_notifications_enabled' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the contact will be notified about service problems in general (0/1)',
                'type' : 'int',
            },
        },


        #Group of contacts
        'Contactgroup' : {
            'alias' : {
                'description' : 'The alias of the contactgroup',
                'type' : 'string',
            },
            'members' : {
                'depythonize' : 'get_name',
                'description' : 'A list of all members of this contactgroup',
                'type' : 'list',
            },
            'name' : {
                'description' : 'The name of the contactgroup',
                'prop' : 'contactgroup_name',
                'type' : 'string',
            },
        },

        
        #Timeperiods
        'Timeperiod' : {
            'alias' : {
                'description' : 'The alias of the timeperiod',
                'type' : 'string',
            },
            'name' : {
                'description' : 'The name of the timeperiod',
                'prop' : 'timeperiod_name',
                'type' : 'string',
            },
        },

        #All commands (checks + notifications)
        'Command' : {
            'line' : {
                'description' : 'The shell command line',
                'prop' : 'command_line',
                'type' : 'string',
            },
            'name' : {
                'description' : 'The name of the command',
                'prop' : 'command_name',
                'type' : 'string',
            },
        },


        ###Satellites 
        #Schedulers 
        'SchedulerLink' : {
            'name' : {
                'description' : 'The name of the scheduler',
                'prop' : 'scheduler_name',
                'type' : 'string',
            },
            'address' : {
                'description' : 'The ip or dns adress ofthe scheduler',
                'prop' : 'address',
                'type' : 'string',
            },
            'port' : {
                'description' : 'The TCP port of the scheduler',
                'prop' : 'port',
                'type' : 'int',
            },
            'spare' : {
                'description' : 'If the scheduler is a spare or not',
                'depythonize' : from_bool_to_int,
                'prop' : 'spare',
                'type' : 'int',
            },
            'weight' : {
                'description' : 'Weight (in terms of hosts) of the scheduler',
                'prop' : 'weight',
                'type' : 'int',
            },
            'alive' : {
                'description' : 'If the scheduler is alive or not',
                'prop' : 'alive',
                'depythonize' : from_bool_to_int,
                'type' : 'int',
            },
        },


        #Downtimes
        'Downtime' : {
            'author' : {
                'default' : 'nobody',
                'description' : 'The contact that scheduled the downtime',
                'prop' : None,
                'type' : 'string',
            },
            'comment' : {
                'default' : None,
                'description' : 'A comment text',
                'prop' : None,
                'type' : 'string',
            },
            'duration' : {
                'default' : '0',
                'description' : 'The duration of the downtime in seconds',
                'prop' : None,
                'type' : 'int',
            },
            'end_time' : {
                'default' : '0',
                'description' : 'The end time of the downtime as UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'entry_time' : {
                'default' : '0',
                'description' : 'The time the entry was made as UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'fixed' : {
                'default' : None,
                'depythonize' : from_bool_to_int,
                'description' : 'A 1 if the downtime is fixed, a 0 if it is flexible',
                'prop' : None,
                'type' : 'int',
            },
            'host_accept_passive_checks' : {
                'default' : None,
                'description' : 'Wether passive host checks are accepted (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_acknowledged' : {
                'default' : None,
                'description' : 'Wether the current host problem has been acknowledged (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_acknowledgement_type' : {
                'default' : None,
                'description' : 'Type of acknowledgement (0: none, 1: normal, 2: stick)',
                'prop' : None,
                'type' : 'int',
            },
            'host_action_url' : {
                'default' : None,
                'description' : 'An optional URL to custom actions or information about this host',
                'prop' : None,
                'type' : 'string',
            },
            'host_action_url_expanded' : {
                'default' : None,
                'description' : 'The same as action_url, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_active_checks_enabled' : {
                'default' : None,
                'description' : 'Wether active checks are enabled for the host (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_address' : {
                'default' : None,
                'description' : 'IP address',
                'prop' : None,
                'type' : 'string',
            },
            'host_alias' : {
                'default' : None,
                'description' : 'An alias name for the host',
                'prop' : None,
                'type' : 'string',
            },
            'host_check_command' : {
                'default' : None,
                'description' : 'Nagios command for active host check of this host',
                'prop' : None,
                'type' : 'string',
            },
            'host_check_freshness' : {
                'default' : None,
                'description' : 'Wether freshness checks are activated (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_check_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between two scheduled checks of the host',
                'prop' : None,
                'type' : 'float',
            },
            'host_check_options' : {
                'default' : None,
                'description' : 'The current check option, forced, normal, freshness... (0-2)',
                'prop' : None,
                'type' : 'int',
            },
            'host_check_period' : {
                'default' : None,
                'description' : 'Time period in which this host will be checked. If empty then the host will always be checked.',
                'prop' : None,
                'type' : 'string',
            },
            'host_check_type' : {
                'default' : None,
                'description' : 'Type of check (0: active, 1: passive)',
                'prop' : None,
                'type' : 'int',
            },
            'host_checks_enabled' : {
                'default' : None,
                'description' : 'Wether checks of the host are enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_childs' : {
                'default' : None,
                'description' : 'A list of all direct childs of the host',
                'prop' : None,
                'type' : 'list',
            },
            'host_comments' : {
                'default' : None,
                'description' : 'A list of the ids of all comments of this host',
                'prop' : None,
                'type' : 'list',
            },
            'host_contacts' : {
                'default' : None,
                'description' : 'A list of all contacts of this host, either direct or via a contact group',
                'prop' : None,
                'type' : 'list',
            },
            'host_current_attempt' : {
                'default' : None,
                'description' : 'Number of the current check attempts',
                'prop' : None,
                'type' : 'int',
            },
            'host_current_notification_number' : {
                'default' : None,
                'description' : 'Number of the current notification',
                'prop' : None,
                'type' : 'int',
            },
            'host_custom_variable_names' : {
                'default' : None,
                'description' : 'A list of the names of all custom variables',
                'prop' : None,
                'type' : 'list',
            },
            'host_custom_variable_values' : {
                'default' : None,
                'description' : 'A list of the values of the custom variables',
                'prop' : None,
                'type' : 'list',
            },
            'host_display_name' : {
                'default' : None,
                'description' : 'Optional display name of the host - not used by Nagios\' web interface',
                'prop' : None,
                'type' : 'string',
            },
            'host_downtimes' : {
                'default' : None,
                'description' : 'A list of the ids of all scheduled downtimes of this host',
                'prop' : None,
                'type' : 'list',
            },
            'host_event_handler_enabled' : {
                'default' : None,
                'description' : 'Wether event handling is enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_execution_time' : {
                'default' : None,
                'description' : 'Time the host check needed for execution',
                'prop' : None,
                'type' : 'float',
            },
            'host_first_notification_delay' : {
                'default' : None,
                'description' : 'Delay before the first notification',
                'prop' : None,
                'type' : 'float',
            },
            'host_flap_detection_enabled' : {
                'default' : None,
                'description' : 'Wether flap detection is enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_groups' : {
                'default' : None,
                'description' : 'A list of all host groups this host is in',
                'prop' : None,
                'type' : 'list',
            },
            'host_hard_state' : {
                'default' : None,
                'description' : 'The effective hard state of the host (eliminates a problem in hard_state)',
                'prop' : None,
                'type' : 'int',
            },
            'host_has_been_checked' : {
                'default' : None,
                'description' : 'Wether the host has already been checked (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_high_flap_threshold' : {
                'default' : None,
                'description' : 'High threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'host_icon_image' : {
                'default' : None,
                'description' : 'The name of an image file to be used in the web pages',
                'prop' : None,
                'type' : 'string',
            },
            'host_icon_image_alt' : {
                'default' : None,
                'description' : 'Alternative text for the icon_image',
                'prop' : None,
                'type' : 'string',
            },
            'host_icon_image_expanded' : {
                'default' : None,
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_in_check_period' : {
                'default' : None,
                'description' : 'Wether this host is currently in its check period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_in_notification_period' : {
                'default' : None,
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_initial_state' : {
                'default' : None,
                'description' : 'Initial host state',
                'prop' : None,
                'type' : 'int',
            },
            'host_is_executing' : {
                'default' : None,
                'description' : 'is there a host check currently running... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_is_flapping' : {
                'default' : None,
                'description' : 'Wether the host state is flapping (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_check' : {
                'default' : None,
                'description' : 'Time of the last check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_hard_state' : {
                'default' : None,
                'description' : 'Last hard state',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_hard_state_change' : {
                'default' : None,
                'description' : 'Time of the last hard state change (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_notification' : {
                'default' : None,
                'description' : 'Time of the last notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_state' : {
                'default' : None,
                'description' : 'State before last state change',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_state_change' : {
                'default' : None,
                'description' : 'Time of the last state change - soft or hard (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_latency' : {
                'default' : None,
                'description' : 'Time difference between scheduled check time and actual check time',
                'prop' : None,
                'type' : 'float',
            },
            'host_long_plugin_output' : {
                'default' : None,
                'description' : 'Complete output from check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'host_low_flap_threshold' : {
                'default' : None,
                'description' : 'Low threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'host_max_check_attempts' : {
                'default' : None,
                'description' : 'Max check attempts for active host checks',
                'prop' : None,
                'type' : 'int',
            },
            'host_name' : {
                'default' : None,
                'depythonize' : lambda x: x.host_name,
                'description' : 'Host name',
                'prop' : 'ref',
                'type' : 'string',
            },
            'host_next_check' : {
                'default' : None,
                'description' : 'Scheduled time for the next check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_next_notification' : {
                'default' : None,
                'description' : 'Time of the next notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_notes' : {
                'default' : None,
                'description' : 'Optional notes for this host',
                'prop' : None,
                'type' : 'string',
            },
            'host_notes_expanded' : {
                'default' : None,
                'description' : 'The same as notes, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_notes_url' : {
                'default' : None,
                'description' : 'An optional URL with further information about the host',
                'prop' : None,
                'type' : 'string',
            },
            'host_notes_url_expanded' : {
                'default' : None,
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_notification_interval' : {
                'default' : None,
                'description' : 'Interval of periodic notification or 0 if its off',
                'prop' : None,
                'type' : 'float',
            },
            'host_notification_period' : {
                'default' : None,
                'description' : 'Time period in which problems of this host will be notified. If empty then notification will be always',
                'prop' : None,
                'type' : 'string',
            },
            'host_notifications_enabled' : {
                'default' : None,
                'description' : 'Wether notifications of the host are enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_num_services' : {
                'default' : None,
                'description' : 'The total number of services of the host',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_crit' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state CRIT',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_crit' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state CRIT',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_ok' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state OK',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_unknown' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state UNKNOWN',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_warn' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state WARN',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_ok' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state OK',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_pending' : {
                'default' : None,
                'description' : 'The number of the host\'s services which have not been checked yet (pending)',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_unknown' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state UNKNOWN',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_warn' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state WARN',
                'prop' : None,
                'type' : 'list',
            },
            'host_obsess_over_host' : {
                'default' : None,
                'description' : 'The current obsess_over_host setting... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_parents' : {
                'default' : None,
                'description' : 'A list of all direct parents of the host',
                'prop' : None,
                'type' : 'list',
            },
            'host_pending_flex_downtime' : {
                'default' : None,
                'description' : 'Wether a flex downtime is pending (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_percent_state_change' : {
                'default' : None,
                'description' : 'Percent state change',
                'prop' : None,
                'type' : 'float',
            },
            'host_perf_data' : {
                'default' : None,
                'description' : 'Optional performance data of the last host check',
                'prop' : None,
                'type' : 'string',
            },
            'host_plugin_output' : {
                'default' : None,
                'description' : 'Output of the last host check',
                'prop' : None,
                'type' : 'string',
            },
            'host_process_performance_data' : {
                'default' : None,
                'description' : 'Wether processing of performance data is enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_retry_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'prop' : None,
                'type' : 'float',
            },
            'host_scheduled_downtime_depth' : {
                'default' : None,
                'description' : 'The number of downtimes this host is currently in',
                'prop' : None,
                'type' : 'int',
            },
            'host_state' : {
                'default' : None,
                'description' : 'The current state of the host (0: up, 1: down, 2: unreachable)',
                'prop' : None,
                'type' : 'int',
            },
            'host_state_type' : {
                'default' : None,
                'description' : 'Type of the current state (0: soft, 1: hard)',
                'prop' : None,
                'type' : 'int',
            },
            'host_statusmap_image' : {
                'default' : None,
                'description' : 'The name of in image file for the status map',
                'prop' : None,
                'type' : 'string',
            },
            'host_total_services' : {
                'default' : None,
                'description' : 'The total number of services of the host',
                'prop' : None,
                'type' : 'int',
            },
            'host_worst_service_hard_state' : {
                'default' : None,
                'description' : 'The worst hard state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : None,
                'type' : 'list',
            },
            'host_worst_service_state' : {
                'default' : None,
                'description' : 'The worst soft state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : None,
                'type' : 'list',
            },
            'host_x_3d' : {
                'default' : None,
                'description' : '3D-Coordinates: X',
                'prop' : None,
                'type' : 'float',
            },
            'host_y_3d' : {
                'default' : None,
                'description' : '3D-Coordinates: Y',
                'prop' : None,
                'type' : 'float',
            },
            'host_z_3d' : {
                'default' : None,
                'description' : '3D-Coordinates: Z',
                'prop' : None,
                'type' : 'float',
            },
            'id' : {
                'default' : None,
                'description' : 'The id of the downtime',
                'prop' : None,
                'type' : 'int',
            },
            'service_accept_passive_checks' : {
                'default' : None,
                'description' : 'Wether the service accepts passive checks (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_acknowledged' : {
                'default' : None,
                'description' : 'Wether the current service problem has been acknowledged (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_acknowledgement_type' : {
                'default' : None,
                'description' : 'The type of the acknownledgement (0: none, 1: normal, 2: sticky)',
                'prop' : None,
                'type' : 'int',
            },
            'service_action_url' : {
                'default' : None,
                'description' : 'An optional URL for actions or custom information about the service',
                'prop' : None,
                'type' : 'string',
            },
            'service_action_url_expanded' : {
                'default' : None,
                'description' : 'The action_url with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_active_checks_enabled' : {
                'default' : None,
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_check_command' : {
                'default' : None,
                'description' : 'Nagios command used for active checks',
                'prop' : None,
                'type' : 'string',
            },
            'service_check_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between two scheduled checks of the service',
                'prop' : None,
                'type' : 'float',
            },
            'service_check_options' : {
                'default' : None,
                'description' : 'The current check option, forced, normal, freshness... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_check_period' : {
                'default' : None,
                'description' : 'The name of the check period of the service. It this is empty, the service is always checked.',
                'prop' : None,
                'type' : 'string',
            },
            'service_check_type' : {
                'default' : None,
                'description' : 'The type of the last check (0: active, 1: passive)',
                'prop' : None,
                'type' : 'int',
            },
            'service_checks_enabled' : {
                'default' : None,
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_comments' : {
                'default' : None,
                'description' : 'A list of all comment ids of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_contacts' : {
                'default' : None,
                'description' : 'A list of all contacts of the service, either direct or via a contact group',
                'prop' : None,
                'type' : 'list',
            },
            'service_current_attempt' : {
                'default' : None,
                'description' : 'The number of the current check attempt',
                'prop' : None,
                'type' : 'int',
            },
            'service_current_notification_number' : {
                'default' : None,
                'description' : 'The number of the current notification',
                'prop' : None,
                'type' : 'int',
            },
            'service_custom_variable_names' : {
                'default' : None,
                'description' : 'A list of the names of all custom variables of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_custom_variable_values' : {
                'default' : None,
                'description' : 'A list of the values of all custom variable of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_description' : {
                'default' : None,
                'depythonize' : lambda x: getattr(x, 'service_description', ''),
                'description' : 'Description of the service (also used as key)',
                'prop' : 'ref',
                'type' : 'string',
            },
            'service_display_name' : {
                'default' : None,
                'description' : 'An optional display name (not used by Nagios standard web pages)',
                'prop' : None,
                'type' : 'string',
            },
            'service_downtimes' : {
                'default' : None,
                'description' : 'A list of all downtime ids of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_event_handler' : {
                'default' : None,
                'description' : 'Nagios command used as event handler',
                'prop' : None,
                'type' : 'string',
            },
            'service_event_handler_enabled' : {
                'default' : None,
                'description' : 'Wether and event handler is activated for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_execution_time' : {
                'default' : None,
                'description' : 'Time the host check needed for execution',
                'prop' : None,
                'type' : 'float',
            },
            'service_first_notification_delay' : {
                'default' : None,
                'description' : 'Delay before the first notification',
                'prop' : None,
                'type' : 'float',
            },
            'service_flap_detection_enabled' : {
                'default' : None,
                'description' : 'Wether flap detection is enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_groups' : {
                'default' : None,
                'description' : 'A list of all service groups the service is in',
                'prop' : None,
                'type' : 'list',
            },
            'service_has_been_checked' : {
                'default' : None,
                'description' : 'Wether the service already has been checked (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_high_flap_threshold' : {
                'default' : None,
                'description' : 'High threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'service_icon_image' : {
                'default' : None,
                'description' : 'The name of an image to be used as icon in the web interface',
                'prop' : None,
                'type' : 'string',
            },
            'service_icon_image_alt' : {
                'default' : None,
                'description' : 'An alternative text for the icon_image for browsers not displaying icons',
                'prop' : None,
                'type' : 'string',
            },
            'service_icon_image_expanded' : {
                'default' : None,
                'description' : 'The icon_image with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_in_check_period' : {
                'default' : None,
                'description' : 'Wether the service is currently in its check period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_in_notification_period' : {
                'default' : None,
                'description' : 'Wether the service is currently in its notification period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_initial_state' : {
                'default' : None,
                'description' : 'The initial state of the service',
                'prop' : None,
                'type' : 'int',
            },
            'service_is_executing' : {
                'default' : None,
                'description' : 'is there a service check currently running... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_is_flapping' : {
                'default' : None,
                'description' : 'Wether the service is flapping (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_check' : {
                'default' : None,
                'description' : 'The time of the last check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_hard_state' : {
                'default' : None,
                'description' : 'The last hard state of the service',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_hard_state_change' : {
                'default' : None,
                'description' : 'The time of the last hard state change (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_notification' : {
                'default' : None,
                'description' : 'The time of the last notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_state' : {
                'default' : None,
                'description' : 'The last state of the service',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_state_change' : {
                'default' : None,
                'description' : 'The time of the last state change (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_latency' : {
                'default' : None,
                'description' : 'Time difference between scheduled check time and actual check time',
                'prop' : None,
                'type' : 'float',
            },
            'service_long_plugin_output' : {
                'default' : None,
                'description' : 'Unabbreviated output of the last check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'service_low_flap_threshold' : {
                'default' : None,
                'description' : 'Low threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'service_max_check_attempts' : {
                'default' : None,
                'description' : 'The maximum number of check attempts',
                'prop' : None,
                'type' : 'int',
            },
            'service_next_check' : {
                'default' : None,
                'description' : 'The scheduled time of the next check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_next_notification' : {
                'default' : None,
                'description' : 'The time of the next notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_notes' : {
                'default' : None,
                'description' : 'Optional notes about the service',
                'prop' : None,
                'type' : 'string',
            },
            'service_notes_expanded' : {
                'default' : None,
                'description' : 'The notes with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_notes_url' : {
                'default' : None,
                'description' : 'An optional URL for additional notes about the service',
                'prop' : None,
                'type' : 'string',
            },
            'service_notes_url_expanded' : {
                'default' : None,
                'description' : 'The notes_url with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_notification_interval' : {
                'default' : None,
                'description' : 'Interval of periodic notification or 0 if its off',
                'prop' : None,
                'type' : 'float',
            },
            'service_notification_period' : {
                'default' : None,
                'description' : 'The name of the notification period of the service. It this is empty, service problems are always notified.',
                'prop' : None,
                'type' : 'string',
            },
            'service_notifications_enabled' : {
                'default' : None,
                'description' : 'Wether notifications are enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_obsess_over_service' : {
                'default' : None,
                'description' : 'Wether \'obsess_over_service\' is enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_percent_state_change' : {
                'default' : None,
                'description' : 'Percent state change',
                'prop' : None,
                'type' : 'float',
            },
            'service_perf_data' : {
                'default' : None,
                'description' : 'Performance data of the last check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'service_plugin_output' : {
                'default' : None,
                'description' : 'Output of the last check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'service_process_performance_data' : {
                'default' : None,
                'description' : 'Wether processing of performance data is enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_retry_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'prop' : None,
                'type' : 'float',
            },
            'service_scheduled_downtime_depth' : {
                'default' : None,
                'description' : 'The number of scheduled downtimes the service is currently in',
                'prop' : None,
                'type' : 'int',
            },
            'service_state' : {
                'default' : None,
                'description' : 'The current state of the service (0: OK, 1: WARN, 2: CRITICAL, 3: UNKNOWN)',
                'prop' : None,
                'type' : 'int',
            },
            'service_state_type' : {
                'default' : None,
                'description' : 'The type of the current state (0: soft, 1: hard)',
                'prop' : None,
                'type' : 'int',
            },
            'start_time' : {
                'default' : '0',
                'description' : 'The start time of the downtime as UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'triggered_by' : {
                'default' : None,
                'description' : 'The id of the downtime this downtime was triggered by or 0 if it was not triggered by another downtime',
                'prop' : 'trigger_id',
                'type' : 'int',
            },
            'type' : {
                'default' : None,
                'description' : 'The type of the downtime: 0 if it is active, 1 if it is pending',
                'prop' : None,
                'type' : 'int',
            },
        },

        #Comments

        'Comment' : {
            'author' : {
                'default' : None,
                'description' : 'The contact that entered the comment',
                'prop' : None,
                'type' : 'string',
            },
            'comment' : {
                'default' : None,
                'description' : 'A comment text',
                'prop' : None,
                'type' : 'string',
            },
            'entry_time' : {
                'default' : None,
                'description' : 'The time the entry was made as UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'entry_type' : {
                'default' : '0',
                'description' : 'The type of the comment: 1 is user, 2 is downtime, 3 is flap and 4 is acknowledgement',
                'prop' : 'entry_type',
                'type' : 'int',
            },
            'expire_time' : {
                'default' : '0',
                'description' : 'The time of expiry of this comment as a UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'expires' : {
                'default' : None,
                'depythonize' : from_bool_to_int,
                'description' : 'Whether this comment expires',
                'prop' : None,
                'type' : 'int',
            },
            'host_accept_passive_checks' : {
                'default' : None,
                'description' : 'Wether passive host checks are accepted (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_acknowledged' : {
                'default' : None,
                'description' : 'Wether the current host problem has been acknowledged (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_acknowledgement_type' : {
                'default' : None,
                'description' : 'Type of acknowledgement (0: none, 1: normal, 2: stick)',
                'prop' : None,
                'type' : 'int',
            },
            'host_action_url' : {
                'default' : None,
                'description' : 'An optional URL to custom actions or information about this host',
                'prop' : None,
                'type' : 'string',
            },
            'host_action_url_expanded' : {
                'default' : None,
                'description' : 'The same as action_url, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_active_checks_enabled' : {
                'default' : None,
                'description' : 'Wether active checks are enabled for the host (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_address' : {
                'default' : None,
                'description' : 'IP address',
                'prop' : None,
                'type' : 'string',
            },
            'host_alias' : {
                'default' : None,
                'description' : 'An alias name for the host',
                'prop' : None,
                'type' : 'string',
            },
            'host_check_command' : {
                'default' : None,
                'description' : 'Nagios command for active host check of this host',
                'prop' : None,
                'type' : 'string',
            },
            'host_check_freshness' : {
                'default' : None,
                'description' : 'Wether freshness checks are activated (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_check_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between two scheduled checks of the host',
                'prop' : None,
                'type' : 'float',
            },
            'host_check_options' : {
                'default' : None,
                'description' : 'The current check option, forced, normal, freshness... (0-2)',
                'prop' : None,
                'type' : 'int',
            },
            'host_check_period' : {
                'default' : None,
                'description' : 'Time period in which this host will be checked. If empty then the host will always be checked.',
                'prop' : None,
                'type' : 'string',
            },
            'host_check_type' : {
                'default' : None,
                'description' : 'Type of check (0: active, 1: passive)',
                'prop' : None,
                'type' : 'int',
            },
            'host_checks_enabled' : {
                'default' : None,
                'description' : 'Wether checks of the host are enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_childs' : {
                'default' : None,
                'description' : 'A list of all direct childs of the host',
                'prop' : None,
                'type' : 'list',
            },
            'host_comments' : {
                'default' : None,
                'description' : 'A list of the ids of all comments of this host',
                'prop' : None,
                'type' : 'list',
            },
            'host_contacts' : {
                'default' : None,
                'description' : 'A list of all contacts of this host, either direct or via a contact group',
                'prop' : None,
                'type' : 'list',
            },
            'host_current_attempt' : {
                'default' : None,
                'description' : 'Number of the current check attempts',
                'prop' : None,
                'type' : 'int',
            },
            'host_current_notification_number' : {
                'default' : None,
                'description' : 'Number of the current notification',
                'prop' : None,
                'type' : 'int',
            },
            'host_custom_variable_names' : {
                'default' : None,
                'description' : 'A list of the names of all custom variables',
                'prop' : None,
                'type' : 'list',
            },
            'host_custom_variable_values' : {
                'default' : None,
                'description' : 'A list of the values of the custom variables',
                'prop' : None,
                'type' : 'list',
            },
            'host_display_name' : {
                'default' : None,
                'description' : 'Optional display name of the host - not used by Nagios\' web interface',
                'prop' : None,
                'type' : 'string',
            },
            'host_downtimes' : {
                'default' : None,
                'description' : 'A list of the ids of all scheduled downtimes of this host',
                'prop' : None,
                'type' : 'list',
            },
            'host_event_handler_enabled' : {
                'default' : None,
                'description' : 'Wether event handling is enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_execution_time' : {
                'default' : None,
                'description' : 'Time the host check needed for execution',
                'prop' : None,
                'type' : 'float',
            },
            'host_first_notification_delay' : {
                'default' : None,
                'description' : 'Delay before the first notification',
                'prop' : None,
                'type' : 'float',
            },
            'host_flap_detection_enabled' : {
                'default' : None,
                'description' : 'Wether flap detection is enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_groups' : {
                'default' : None,
                'description' : 'A list of all host groups this host is in',
                'prop' : None,
                'type' : 'list',
            },
            'host_hard_state' : {
                'default' : None,
                'description' : 'The effective hard state of the host (eliminates a problem in hard_state)',
                'prop' : None,
                'type' : 'int',
            },
            'host_has_been_checked' : {
                'default' : None,
                'description' : 'Wether the host has already been checked (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_high_flap_threshold' : {
                'default' : None,
                'description' : 'High threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'host_icon_image' : {
                'default' : None,
                'description' : 'The name of an image file to be used in the web pages',
                'prop' : None,
                'type' : 'string',
            },
            'host_icon_image_alt' : {
                'default' : None,
                'description' : 'Alternative text for the icon_image',
                'prop' : None,
                'type' : 'string',
            },
            'host_icon_image_expanded' : {
                'default' : None,
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_in_check_period' : {
                'default' : None,
                'description' : 'Wether this host is currently in its check period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_in_notification_period' : {
                'default' : None,
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_initial_state' : {
                'default' : None,
                'description' : 'Initial host state',
                'prop' : None,
                'type' : 'int',
            },
            'host_is_executing' : {
                'default' : None,
                'description' : 'is there a host check currently running... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_is_flapping' : {
                'default' : None,
                'description' : 'Wether the host state is flapping (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_check' : {
                'default' : None,
                'description' : 'Time of the last check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_hard_state' : {
                'default' : None,
                'description' : 'Last hard state',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_hard_state_change' : {
                'default' : None,
                'description' : 'Time of the last hard state change (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_notification' : {
                'default' : None,
                'description' : 'Time of the last notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_state' : {
                'default' : None,
                'description' : 'State before last state change',
                'prop' : None,
                'type' : 'int',
            },
            'host_last_state_change' : {
                'default' : None,
                'description' : 'Time of the last state change - soft or hard (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_latency' : {
                'default' : None,
                'description' : 'Time difference between scheduled check time and actual check time',
                'prop' : None,
                'type' : 'float',
            },
            'host_long_plugin_output' : {
                'default' : None,
                'description' : 'Complete output from check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'host_low_flap_threshold' : {
                'default' : None,
                'description' : 'Low threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'host_max_check_attempts' : {
                'default' : None,
                'description' : 'Max check attempts for active host checks',
                'prop' : None,
                'type' : 'int',
            },
            'host_name' : {
                'default' : None,
                'depythonize' : lambda x: x.host_name,
                'description' : 'Host name',
                'prop' : 'ref',
                'type' : 'string',
            },
            'host_next_check' : {
                'default' : None,
                'description' : 'Scheduled time for the next check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_next_notification' : {
                'default' : None,
                'description' : 'Time of the next notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'host_notes' : {
                'default' : None,
                'description' : 'Optional notes for this host',
                'prop' : None,
                'type' : 'string',
            },
            'host_notes_expanded' : {
                'default' : None,
                'description' : 'The same as notes, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_notes_url' : {
                'default' : None,
                'description' : 'An optional URL with further information about the host',
                'prop' : None,
                'type' : 'string',
            },
            'host_notes_url_expanded' : {
                'default' : None,
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'host_notification_interval' : {
                'default' : None,
                'description' : 'Interval of periodic notification or 0 if its off',
                'prop' : None,
                'type' : 'float',
            },
            'host_notification_period' : {
                'default' : None,
                'description' : 'Time period in which problems of this host will be notified. If empty then notification will be always',
                'prop' : None,
                'type' : 'string',
            },
            'host_notifications_enabled' : {
                'default' : None,
                'description' : 'Wether notifications of the host are enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_num_services' : {
                'default' : None,
                'description' : 'The total number of services of the host',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_crit' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state CRIT',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_crit' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state CRIT',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_ok' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state OK',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_unknown' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state UNKNOWN',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_hard_warn' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the hard state WARN',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_ok' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state OK',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_pending' : {
                'default' : None,
                'description' : 'The number of the host\'s services which have not been checked yet (pending)',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_unknown' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state UNKNOWN',
                'prop' : None,
                'type' : 'list',
            },
            'host_num_services_warn' : {
                'default' : None,
                'description' : 'The number of the host\'s services with the soft state WARN',
                'prop' : None,
                'type' : 'list',
            },
            'host_obsess_over_host' : {
                'default' : None,
                'description' : 'The current obsess_over_host setting... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_parents' : {
                'default' : None,
                'description' : 'A list of all direct parents of the host',
                'prop' : None,
                'type' : 'list',
            },
            'host_pending_flex_downtime' : {
                'default' : None,
                'description' : 'Wether a flex downtime is pending (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_percent_state_change' : {
                'default' : None,
                'description' : 'Percent state change',
                'prop' : None,
                'type' : 'float',
            },
            'host_perf_data' : {
                'default' : None,
                'description' : 'Optional performance data of the last host check',
                'prop' : None,
                'type' : 'string',
            },
            'host_plugin_output' : {
                'default' : None,
                'description' : 'Output of the last host check',
                'prop' : None,
                'type' : 'string',
            },
            'host_process_performance_data' : {
                'default' : None,
                'description' : 'Wether processing of performance data is enabled (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'host_retry_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'prop' : None,
                'type' : 'float',
            },
            'host_scheduled_downtime_depth' : {
                'default' : None,
                'description' : 'The number of downtimes this host is currently in',
                'prop' : None,
                'type' : 'int',
            },
            'host_state' : {
                'default' : None,
                'description' : 'The current state of the host (0: up, 1: down, 2: unreachable)',
                'prop' : None,
                'type' : 'int',
            },
            'host_state_type' : {
                'default' : None,
                'description' : 'Type of the current state (0: soft, 1: hard)',
                'prop' : None,
                'type' : 'int',
            },
            'host_statusmap_image' : {
                'default' : None,
                'description' : 'The name of in image file for the status map',
                'prop' : None,
                'type' : 'string',
            },
            'host_total_services' : {
                'default' : None,
                'description' : 'The total number of services of the host',
                'prop' : None,
                'type' : 'int',
            },
            'host_worst_service_hard_state' : {
                'default' : None,
                'description' : 'The worst hard state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : None,
                'type' : 'list',
            },
            'host_worst_service_state' : {
                'default' : None,
                'description' : 'The worst soft state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : None,
                'type' : 'list',
            },
            'host_x_3d' : {
                'default' : None,
                'description' : '3D-Coordinates: X',
                'prop' : None,
                'type' : 'float',
            },
            'host_y_3d' : {
                'default' : None,
                'description' : '3D-Coordinates: Y',
                'prop' : None,
                'type' : 'float',
            },
            'host_z_3d' : {
                'default' : None,
                'description' : '3D-Coordinates: Z',
                'prop' : None,
                'type' : 'float',
            },
            'id' : {
                'default' : None,
                'description' : 'The id of the comment',
                'prop' : None,
                'type' : 'int',
            },
            'persistent' : {
                'default' : None,
                'depythonize' : from_bool_to_int,
                'description' : 'Whether this comment is persistent (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_accept_passive_checks' : {
                'default' : None,
                'description' : 'Wether the service accepts passive checks (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_acknowledged' : {
                'default' : None,
                'description' : 'Wether the current service problem has been acknowledged (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_acknowledgement_type' : {
                'default' : None,
                'description' : 'The type of the acknownledgement (0: none, 1: normal, 2: sticky)',
                'prop' : None,
                'type' : 'int',
            },
            'service_action_url' : {
                'default' : None,
                'description' : 'An optional URL for actions or custom information about the service',
                'prop' : None,
                'type' : 'string',
            },
            'service_action_url_expanded' : {
                'default' : None,
                'description' : 'The action_url with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_active_checks_enabled' : {
                'default' : None,
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_check_command' : {
                'default' : None,
                'description' : 'Nagios command used for active checks',
                'prop' : None,
                'type' : 'string',
            },
            'service_check_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between two scheduled checks of the service',
                'prop' : None,
                'type' : 'float',
            },
            'service_check_options' : {
                'default' : None,
                'description' : 'The current check option, forced, normal, freshness... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_check_period' : {
                'default' : None,
                'description' : 'The name of the check period of the service. It this is empty, the service is always checked.',
                'prop' : None,
                'type' : 'string',
            },
            'service_check_type' : {
                'default' : None,
                'description' : 'The type of the last check (0: active, 1: passive)',
                'prop' : None,
                'type' : 'int',
            },
            'service_checks_enabled' : {
                'default' : None,
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_comments' : {
                'default' : None,
                'description' : 'A list of all comment ids of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_contacts' : {
                'default' : None,
                'description' : 'A list of all contacts of the service, either direct or via a contact group',
                'prop' : None,
                'type' : 'list',
            },
            'service_current_attempt' : {
                'default' : None,
                'description' : 'The number of the current check attempt',
                'prop' : None,
                'type' : 'int',
            },
            'service_current_notification_number' : {
                'default' : None,
                'description' : 'The number of the current notification',
                'prop' : None,
                'type' : 'int',
            },
            'service_custom_variable_names' : {
                'default' : None,
                'description' : 'A list of the names of all custom variables of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_custom_variable_values' : {
                'default' : None,
                'description' : 'A list of the values of all custom variable of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_description' : {
                'default' : None,
                'depythonize' : lambda x: getattr(x, 'service_description', ''),
                'description' : 'Description of the service (also used as key)',
                'prop' : 'ref',
                'type' : 'string',
            },
            'service_display_name' : {
                'default' : None,
                'description' : 'An optional display name (not used by Nagios standard web pages)',
                'prop' : None,
                'type' : 'string',
            },
            'service_downtimes' : {
                'default' : None,
                'description' : 'A list of all downtime ids of the service',
                'prop' : None,
                'type' : 'list',
            },
            'service_event_handler' : {
                'default' : None,
                'description' : 'Nagios command used as event handler',
                'prop' : None,
                'type' : 'string',
            },
            'service_event_handler_enabled' : {
                'default' : None,
                'description' : 'Wether and event handler is activated for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_execution_time' : {
                'default' : None,
                'description' : 'Time the host check needed for execution',
                'prop' : None,
                'type' : 'float',
            },
            'service_first_notification_delay' : {
                'default' : None,
                'description' : 'Delay before the first notification',
                'prop' : None,
                'type' : 'float',
            },
            'service_flap_detection_enabled' : {
                'default' : None,
                'description' : 'Wether flap detection is enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_groups' : {
                'default' : None,
                'description' : 'A list of all service groups the service is in',
                'prop' : None,
                'type' : 'list',
            },
            'service_has_been_checked' : {
                'default' : None,
                'description' : 'Wether the service already has been checked (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_high_flap_threshold' : {
                'default' : None,
                'description' : 'High threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'service_icon_image' : {
                'default' : None,
                'description' : 'The name of an image to be used as icon in the web interface',
                'prop' : None,
                'type' : 'string',
            },
            'service_icon_image_alt' : {
                'default' : None,
                'description' : 'An alternative text for the icon_image for browsers not displaying icons',
                'prop' : None,
                'type' : 'string',
            },
            'service_icon_image_expanded' : {
                'default' : None,
                'description' : 'The icon_image with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_in_check_period' : {
                'default' : None,
                'description' : 'Wether the service is currently in its check period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_in_notification_period' : {
                'default' : None,
                'description' : 'Wether the service is currently in its notification period (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_initial_state' : {
                'default' : None,
                'description' : 'The initial state of the service',
                'prop' : None,
                'type' : 'int',
            },
            'service_is_executing' : {
                'default' : None,
                'description' : 'is there a service check currently running... (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_is_flapping' : {
                'default' : None,
                'description' : 'Wether the service is flapping (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_check' : {
                'default' : None,
                'description' : 'The time of the last check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_hard_state' : {
                'default' : None,
                'description' : 'The last hard state of the service',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_hard_state_change' : {
                'default' : None,
                'description' : 'The time of the last hard state change (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_notification' : {
                'default' : None,
                'description' : 'The time of the last notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_state' : {
                'default' : None,
                'description' : 'The last state of the service',
                'prop' : None,
                'type' : 'int',
            },
            'service_last_state_change' : {
                'default' : None,
                'description' : 'The time of the last state change (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_latency' : {
                'default' : None,
                'description' : 'Time difference between scheduled check time and actual check time',
                'prop' : None,
                'type' : 'float',
            },
            'service_long_plugin_output' : {
                'default' : None,
                'description' : 'Unabbreviated output of the last check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'service_low_flap_threshold' : {
                'default' : None,
                'description' : 'Low threshold of flap detection',
                'prop' : None,
                'type' : 'float',
            },
            'service_max_check_attempts' : {
                'default' : None,
                'description' : 'The maximum number of check attempts',
                'prop' : None,
                'type' : 'int',
            },
            'service_next_check' : {
                'default' : None,
                'description' : 'The scheduled time of the next check (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_next_notification' : {
                'default' : None,
                'description' : 'The time of the next notification (Unix timestamp)',
                'prop' : None,
                'type' : 'int',
            },
            'service_notes' : {
                'default' : None,
                'description' : 'Optional notes about the service',
                'prop' : None,
                'type' : 'string',
            },
            'service_notes_expanded' : {
                'default' : None,
                'description' : 'The notes with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_notes_url' : {
                'default' : None,
                'description' : 'An optional URL for additional notes about the service',
                'prop' : None,
                'type' : 'string',
            },
            'service_notes_url_expanded' : {
                'default' : None,
                'description' : 'The notes_url with (the most important) macros expanded',
                'prop' : None,
                'type' : 'string',
            },
            'service_notification_interval' : {
                'default' : None,
                'description' : 'Interval of periodic notification or 0 if its off',
                'prop' : None,
                'type' : 'float',
            },
            'service_notification_period' : {
                'default' : None,
                'description' : 'The name of the notification period of the service. It this is empty, service problems are always notified.',
                'prop' : None,
                'type' : 'string',
            },
            'service_notifications_enabled' : {
                'default' : None,
                'description' : 'Wether notifications are enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_obsess_over_service' : {
                'default' : None,
                'description' : 'Wether \'obsess_over_service\' is enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_percent_state_change' : {
                'default' : None,
                'description' : 'Percent state change',
                'prop' : None,
                'type' : 'float',
            },
            'service_perf_data' : {
                'default' : None,
                'description' : 'Performance data of the last check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'service_plugin_output' : {
                'default' : None,
                'description' : 'Output of the last check plugin',
                'prop' : None,
                'type' : 'string',
            },
            'service_process_performance_data' : {
                'default' : None,
                'description' : 'Wether processing of performance data is enabled for the service (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'service_retry_interval' : {
                'default' : None,
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'prop' : None,
                'type' : 'float',
            },
            'service_scheduled_downtime_depth' : {
                'default' : None,
                'description' : 'The number of scheduled downtimes the service is currently in',
                'prop' : None,
                'type' : 'int',
            },
            'service_state' : {
                'default' : None,
                'description' : 'The current state of the service (0: OK, 1: WARN, 2: CRITICAL, 3: UNKNOWN)',
                'prop' : None,
                'type' : 'int',
            },
            'service_state_type' : {
                'default' : None,
                'description' : 'The type of the current state (0: soft, 1: hard)',
                'prop' : None,
                'type' : 'int',
            },
            'source' : {
                'default' : '0',
                'description' : 'The source of the comment (0 is internal and 1 is external)',
                'prop' : None,
                'type' : 'int',
            },
            'type' : {
                'default' : '1',
                'description' : 'The type of the comment: 1 is service, 2 is host',
                'prop' : 'comment_type',
                'type' : 'int',
            },
        },


        #All the global config parameters

        'Config' : {
            'accept_passive_host_checks' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether passive host checks are accepted in general (0/1)',
                'prop' : 'passive_host_checks_enabled',
                'type' : 'int',
            },
            'accept_passive_service_checks' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether passive service checks are activated in general (0/1)',
                'prop' : 'passive_service_checks_enabled',
                'type' : 'int',
            },
            'cached_log_messages' : {
                'default' : '0',
                'description' : 'The current number of log messages MK Livestatus keeps in memory',
                'prop' : None,
                'type' : 'int',
            },
            'check_external_commands' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether Nagios checks for external commands at its command pipe (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'check_host_freshness' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether host freshness checking is activated in general (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'check_service_freshness' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether service freshness checking is activated in general (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'connections' : {
                'default' : '0',
                'description' : 'The number of client connections to Livestatus since program start',
                'prop' : None,
                'type' : 'int',
            },
            'connections_rate' : {
                'default' : '0',
                'description' : 'The averaged number of new client connections to Livestatus per second',
                'prop' : None,
                'type' : 'float',
            },
            'enable_event_handlers' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether event handlers are activated in general (0/1)',
                'prop' : 'event_handlers_enabled',
                'type' : 'int',
            },
            'enable_flap_detection' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether flap detection is activated in general (0/1)',
                'prop' : 'flap_detection_enabled',
                'type' : 'int',
            },
            'enable_notifications' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether notifications are enabled in general (0/1)',
                'prop' : 'notifications_enabled',
                'type' : 'int',
            },
            'execute_host_checks' : {
                'default' : '1',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether host checks are executed in general (0/1)',
                'prop' : 'active_host_checks_enabled',
                'type' : 'int',
            },
            'execute_service_checks' : {
                'default' : '1',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether active service checks are activated in general (0/1)',
                'prop' : 'active_service_checks_enabled',
                'type' : 'int',
            },
            'host_checks' : {
                'default' : '0',
                'description' : 'The number of host checks since program start',
                'prop' : None,
                'type' : 'int',
            },
            'host_checks_rate' : {
                'default' : '0',
                'description' : 'the averaged number of host checks per second',
                'prop' : None,
                'type' : 'float',
            },
            'interval_length' : {
                'default' : '0',
                'description' : 'The default interval length from nagios.cfg',
                'prop' : None,
                'type' : 'int',
            },
            'last_command_check' : {
                'default' : '0',
                'description' : 'The time of the last check for a command as UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'last_log_rotation' : {
                'default' : '0',
                'description' : 'Time time of the last log file rotation',
                'prop' : None,
                'type' : 'int',
            },
            'livestatus_version' : {
                'default' : '0',
                'description' : 'The version of the MK Livestatus module',
                'prop' : None,
                'type' : 'string',
            },
            'nagios_pid' : {
                'default' : '0',
                'description' : 'The process ID of the Nagios main process',
                'prop' : 'pid',
                'type' : 'int',
            },
            'neb_callbacks' : {
                'default' : '0',
                'description' : 'The number of NEB call backs since program start',
                'prop' : None,
                'type' : 'int',
            },
            'neb_callbacks_rate' : {
                'default' : '0',
                'description' : 'The averaged number of NEB call backs per second',
                'prop' : None,
                'type' : 'float',
            },
            'obsess_over_hosts' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether Nagios will obsess over host checks (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'obsess_over_services' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether Nagios will obsess over service checks and run the ocsp_command (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'process_performance_data' : {
                'default' : '0',
                'depythonize' : from_bool_to_int,
                'description' : 'Whether processing of performance data is activated in general (0/1)',
                'prop' : None,
                'type' : 'int',
            },
            'program_start' : {
                'default' : '0',
                'description' : 'The time of the last program start as UNIX timestamp',
                'prop' : None,
                'type' : 'int',
            },
            'program_version' : {
                'default' : '0.1',
                'description' : 'The version of the monitoring daemon',
                'prop' : None,
                'type' : 'string',
            },
            'requests' : {
                'default' : '0',
                'description' : 'The number of requests to Livestatus since program start',
                'prop' : None,
                'type' : 'int',
            },
            'requests_rate' : {
                'default' : '0',
                'description' : 'The averaged number of request to Livestatus per second',
                'prop' : None,
                'type' : 'float',
            },
            'service_checks' : {
                'default' : '0',
                'description' : 'The number of completed service checks since program start',
                'prop' : None,
                'type' : 'int',
            },
            'service_checks_rate' : {
                'default' : '0',
                'description' : 'The averaged number of service checks per second',
                'prop' : None,
                'type' : 'float',
            },
        },


        #Logs

        'Logline' : {
            'attempt' : {
                'description' : 'The number of the check attempt',
                'type' : 'int',
            },
            'class' : {
                'description' : 'The class of the message as integer (0:info, 1:state, 2:program, 3:notification, 4:passive, 5:command)',
                'type' : 'int',
            },
            'command_name' : {
                'description' : 'The name of the command of the log entry (e.g. for notifications)',
                'type' : 'string',
            },
            'comment' : {
                'description' : 'A comment field used in various message types',
                'type' : 'string',
            },
            'contact_name' : {
                'description' : 'The name of the contact the log entry is about (might be empty)',
                'type' : 'string',
            },
            'current_command_line' : {
                'description' : 'The shell command line',
                'type' : 'string',
            },
            'current_command_name' : {
                'description' : 'The name of the command',
                'type' : 'string',
            },
            'current_contact_address1' : {
                'description' : 'The additional field address1',
                'type' : 'string',
            },
            'current_contact_address2' : {
                'description' : 'The additional field address2',
                'type' : 'string',
            },
            'current_contact_address3' : {
                'description' : 'The additional field address3',
                'type' : 'string',
            },
            'current_contact_address4' : {
                'description' : 'The additional field address4',
                'type' : 'string',
            },
            'current_contact_address5' : {
                'description' : 'The additional field address5',
                'type' : 'string',
            },
            'current_contact_address6' : {
                'description' : 'The additional field address6',
                'type' : 'string',
            },
            'current_contact_alias' : {
                'description' : 'The full name of the contact',
                'type' : 'string',
            },
            'current_contact_can_submit_commands' : {
                'description' : 'Wether the contact is allowed to submit commands (0/1)',
                'type' : 'int',
            },
            'current_contact_custom_variable_names' : {
                'description' : 'A list of all custom variables of the contact',
                'type' : 'list',
            },
            'current_contact_custom_variable_values' : {
                'description' : 'A list of the values of all custom variables of the contact',
                'type' : 'list',
            },
            'current_contact_email' : {
                'description' : 'The email address of the contact',
                'type' : 'string',
            },
            'current_contact_host_notification_period' : {
                'description' : 'The time period in which the contact will be notified about host problems',
                'type' : 'string',
            },
            'current_contact_host_notifications_enabled' : {
                'description' : 'Wether the contact will be notified about host problems in general (0/1)',
                'type' : 'int',
            },
            'current_contact_in_host_notification_period' : {
                'description' : 'Wether the contact is currently in his/her host notification period (0/1)',
                'type' : 'int',
            },
            'current_contact_in_service_notification_period' : {
                'description' : 'Wether the contact is currently in his/her service notification period (0/1)',
                'type' : 'int',
            },
            'current_contact_name' : {
                'description' : 'The login name of the contact person',
                'type' : 'string',
            },
            'current_contact_pager' : {
                'description' : 'The pager address of the contact',
                'type' : 'string',
            },
            'current_contact_service_notification_period' : {
                'description' : 'The time period in which the contact will be notified about service problems',
                'type' : 'string',
            },
            'current_contact_service_notifications_enabled' : {
                'description' : 'Wether the contact will be notified about service problems in general (0/1)',
                'type' : 'int',
            },
            'current_host_accept_passive_checks' : {
                'description' : 'Wether passive host checks are accepted (0/1)',
                'type' : 'int',
            },
            'current_host_acknowledged' : {
                'description' : 'Wether the current host problem has been acknowledged (0/1)',
                'type' : 'int',
            },
            'current_host_acknowledgement_type' : {
                'description' : 'Type of acknowledgement (0: none, 1: normal, 2: stick)',
                'type' : 'int',
            },
            'current_host_action_url' : {
                'description' : 'An optional URL to custom actions or information about this host',
                'type' : 'string',
            },
            'current_host_action_url_expanded' : {
                'description' : 'The same as action_url, but with the most important macros expanded',
                'type' : 'string',
            },
            'current_host_active_checks_enabled' : {
                'description' : 'Wether active checks are enabled for the host (0/1)',
                'type' : 'int',
            },
            'current_host_address' : {
                'description' : 'IP address',
                'type' : 'string',
            },
            'current_host_alias' : {
                'description' : 'An alias name for the host',
                'type' : 'string',
            },
            'current_host_check_command' : {
                'description' : 'Nagios command for active host check of this host',
                'type' : 'string',
            },
            'current_host_check_freshness' : {
                'description' : 'Wether freshness checks are activated (0/1)',
                'type' : 'int',
            },
            'current_host_check_interval' : {
                'description' : 'Number of basic interval lengths between two scheduled checks of the host',
                'type' : 'float',
            },
            'current_host_check_options' : {
                'description' : 'The current check option, forced, normal, freshness... (0-2)',
                'type' : 'int',
            },
            'current_host_check_period' : {
                'description' : 'Time period in which this host will be checked. If empty then the host will always be checked.',
                'type' : 'string',
            },
            'current_host_check_type' : {
                'description' : 'Type of check (0: active, 1: passive)',
                'type' : 'int',
            },
            'current_host_checks_enabled' : {
                'description' : 'Wether checks of the host are enabled (0/1)',
                'type' : 'int',
            },
            'current_host_childs' : {
                'description' : 'A list of all direct childs of the host',
                'type' : 'list',
            },
            'current_host_comments' : {
                'description' : 'A list of the ids of all comments of this host',
                'type' : 'list',
            },
            'current_host_contacts' : {
                'description' : 'A list of all contacts of this host, either direct or via a contact group',
                'type' : 'list',
            },
            'current_host_current_attempt' : {
                'description' : 'Number of the current check attempts',
                'type' : 'int',
            },
            'current_host_current_notification_number' : {
                'description' : 'Number of the current notification',
                'type' : 'int',
            },
            'current_host_custom_variable_names' : {
                'description' : 'A list of the names of all custom variables',
                'type' : 'list',
            },
            'current_host_custom_variable_values' : {
                'description' : 'A list of the values of the custom variables',
                'type' : 'list',
            },
            'current_host_display_name' : {
                'description' : 'Optional display name of the host - not used by Nagios\' web interface',
                'type' : 'string',
            },
            'current_host_downtimes' : {
                'description' : 'A list of the ids of all scheduled downtimes of this host',
                'type' : 'list',
            },
            'current_host_event_handler_enabled' : {
                'description' : 'Wether event handling is enabled (0/1)',
                'type' : 'int',
            },
            'current_host_execution_time' : {
                'description' : 'Time the host check needed for execution',
                'type' : 'float',
            },
            'current_host_first_notification_delay' : {
                'description' : 'Delay before the first notification',
                'type' : 'float',
            },
            'current_host_flap_detection_enabled' : {
                'description' : 'Wether flap detection is enabled (0/1)',
                'type' : 'int',
            },
            'current_host_groups' : {
                'description' : 'A list of all host groups this host is in',
                'type' : 'list',
            },
            'current_host_hard_state' : {
                'description' : 'The effective hard state of the host (eliminates a problem in hard_state)',
                'type' : 'int',
            },
            'current_host_has_been_checked' : {
                'description' : 'Wether the host has already been checked (0/1)',
                'type' : 'int',
            },
            'current_host_high_flap_threshold' : {
                'description' : 'High threshold of flap detection',
                'type' : 'float',
            },
            'current_host_icon_image' : {
                'description' : 'The name of an image file to be used in the web pages',
                'type' : 'string',
            },
            'current_host_icon_image_alt' : {
                'description' : 'Alternative text for the icon_image',
                'type' : 'string',
            },
            'current_host_icon_image_expanded' : {
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'type' : 'string',
            },
            'current_host_in_check_period' : {
                'description' : 'Wether this host is currently in its check period (0/1)',
                'type' : 'int',
            },
            'current_host_in_notification_period' : {
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'type' : 'int',
            },
            'current_host_initial_state' : {
                'description' : 'Initial host state',
                'type' : 'int',
            },
            'current_host_is_executing' : {
                'description' : 'is there a host check currently running... (0/1)',
                'type' : 'int',
            },
            'current_host_is_flapping' : {
                'description' : 'Wether the host state is flapping (0/1)',
                'type' : 'int',
            },
            'current_host_last_check' : {
                'description' : 'Time of the last check (Unix timestamp)',
                'type' : 'int',
            },
            'current_host_last_hard_state' : {
                'description' : 'Last hard state',
                'type' : 'int',
            },
            'current_host_last_hard_state_change' : {
                'description' : 'Time of the last hard state change (Unix timestamp)',
                'type' : 'int',
            },
            'current_host_last_notification' : {
                'description' : 'Time of the last notification (Unix timestamp)',
                'type' : 'int',
            },
            'current_host_last_state' : {
                'description' : 'State before last state change',
                'type' : 'int',
            },
            'current_host_last_state_change' : {
                'description' : 'Time of the last state change - soft or hard (Unix timestamp)',
                'type' : 'int',
            },
            'current_host_latency' : {
                'description' : 'Time difference between scheduled check time and actual check time',
                'type' : 'float',
            },
            'current_host_long_plugin_output' : {
                'description' : 'Complete output from check plugin',
                'type' : 'string',
            },
            'current_host_low_flap_threshold' : {
                'description' : 'Low threshold of flap detection',
                'type' : 'float',
            },
            'current_host_max_check_attempts' : {
                'description' : 'Max check attempts for active host checks',
                'type' : 'int',
            },
            'current_host_name' : {
                'default' : '',
                'depythonize' : lambda x: x.get_name(),
                'description' : 'Host name',
                'prop' : 'log_host',
                'type' : 'string',
            },
            'current_host_next_check' : {
                'description' : 'Scheduled time for the next check (Unix timestamp)',
                'type' : 'int',
            },
            'current_host_next_notification' : {
                'description' : 'Time of the next notification (Unix timestamp)',
                'type' : 'int',
            },
            'current_host_notes' : {
                'description' : 'Optional notes for this host',
                'type' : 'string',
            },
            'current_host_notes_expanded' : {
                'description' : 'The same as notes, but with the most important macros expanded',
                'type' : 'string',
            },
            'current_host_notes_url' : {
                'description' : 'An optional URL with further information about the host',
                'type' : 'string',
            },
            'current_host_notes_url_expanded' : {
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'type' : 'string',
            },
            'current_host_notification_interval' : {
                'description' : 'Interval of periodic notification or 0 if its off',
                'type' : 'float',
            },
            'current_host_notification_period' : {
                'description' : 'Time period in which problems of this host will be notified. If empty then notification will be always',
                'type' : 'string',
            },
            'current_host_notifications_enabled' : {
                'description' : 'Wether notifications of the host are enabled (0/1)',
                'type' : 'int',
            },
            'current_host_num_services' : {
                'description' : 'The total number of services of the host',
                'type' : 'list',
            },
            'current_host_num_services_crit' : {
                'description' : 'The number of the host\'s services with the soft state CRIT',
                'type' : 'list',
            },
            'current_host_num_services_hard_crit' : {
                'description' : 'The number of the host\'s services with the hard state CRIT',
                'type' : 'list',
            },
            'current_host_num_services_hard_ok' : {
                'description' : 'The number of the host\'s services with the hard state OK',
                'type' : 'list',
            },
            'current_host_num_services_hard_unknown' : {
                'description' : 'The number of the host\'s services with the hard state UNKNOWN',
                'type' : 'list',
            },
            'current_host_num_services_hard_warn' : {
                'description' : 'The number of the host\'s services with the hard state WARN',
                'type' : 'list',
            },
            'current_host_num_services_ok' : {
                'description' : 'The number of the host\'s services with the soft state OK',
                'type' : 'list',
            },
            'current_host_num_services_pending' : {
                'description' : 'The number of the host\'s services which have not been checked yet (pending)',
                'type' : 'list',
            },
            'current_host_num_services_unknown' : {
                'description' : 'The number of the host\'s services with the soft state UNKNOWN',
                'type' : 'list',
            },
            'current_host_num_services_warn' : {
                'description' : 'The number of the host\'s services with the soft state WARN',
                'type' : 'list',
            },
            'current_host_obsess_over_host' : {
                'description' : 'The current obsess_over_host setting... (0/1)',
                'type' : 'int',
            },
            'current_host_parents' : {
                'description' : 'A list of all direct parents of the host',
                'type' : 'list',
            },
            'current_host_pending_flex_downtime' : {
                'description' : 'Wether a flex downtime is pending (0/1)',
                'type' : 'int',
            },
            'current_host_percent_state_change' : {
                'description' : 'Percent state change',
                'type' : 'float',
            },
            'current_host_perf_data' : {
                'description' : 'Optional performance data of the last host check',
                'type' : 'string',
            },
            'current_host_plugin_output' : {
                'description' : 'Output of the last host check',
                'type' : 'string',
            },
            'current_host_process_performance_data' : {
                'description' : 'Wether processing of performance data is enabled (0/1)',
                'type' : 'int',
            },
            'current_host_retry_interval' : {
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'type' : 'float',
            },
            'current_host_scheduled_downtime_depth' : {
                'description' : 'The number of downtimes this host is currently in',
                'type' : 'int',
            },
            'current_host_state' : {
                'description' : 'The current state of the host (0: up, 1: down, 2: unreachable)',
                'type' : 'int',
            },
            'current_host_state_type' : {
                'description' : 'Type of the current state (0: soft, 1: hard)',
                'type' : 'int',
            },
            'current_host_statusmap_image' : {
                'description' : 'The name of in image file for the status map',
                'type' : 'string',
            },
            'current_host_total_services' : {
                'description' : 'The total number of services of the host',
                'type' : 'int',
            },
            'current_host_worst_service_hard_state' : {
                'description' : 'The worst hard state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'list',
            },
            'current_host_worst_service_state' : {
                'description' : 'The worst soft state of all of the host\'s services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'list',
            },
            'current_host_x_3d' : {
                'description' : '3D-Coordinates: X',
                'type' : 'float',
            },
            'current_host_y_3d' : {
                'description' : '3D-Coordinates: Y',
                'type' : 'float',
            },
            'current_host_z_3d' : {
                'description' : '3D-Coordinates: Z',
                'type' : 'float',
            },
            'current_service_accept_passive_checks' : {
                'description' : 'Wether the service accepts passive checks (0/1)',
                'type' : 'int',
            },
            'current_service_acknowledged' : {
                'description' : 'Wether the current service problem has been acknowledged (0/1)',
                'type' : 'int',
            },
            'current_service_acknowledgement_type' : {
                'description' : 'The type of the acknownledgement (0: none, 1: normal, 2: sticky)',
                'type' : 'int',
            },
            'current_service_action_url' : {
                'description' : 'An optional URL for actions or custom information about the service',
                'type' : 'string',
            },
            'current_service_action_url_expanded' : {
                'description' : 'The action_url with (the most important) macros expanded',
                'type' : 'string',
            },
            'current_service_active_checks_enabled' : {
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'type' : 'int',
            },
            'current_service_check_command' : {
                'description' : 'Nagios command used for active checks',
                'type' : 'string',
            },
            'current_service_check_interval' : {
                'description' : 'Number of basic interval lengths between two scheduled checks of the service',
                'type' : 'float',
            },
            'current_service_check_options' : {
                'description' : 'The current check option, forced, normal, freshness... (0/1)',
                'type' : 'int',
            },
            'current_service_check_period' : {
                'description' : 'The name of the check period of the service. It this is empty, the service is always checked.',
                'type' : 'string',
            },
            'current_service_check_type' : {
                'description' : 'The type of the last check (0: active, 1: passive)',
                'type' : 'int',
            },
            'current_service_checks_enabled' : {
                'description' : 'Wether active checks are enabled for the service (0/1)',
                'type' : 'int',
            },
            'current_service_comments' : {
                'description' : 'A list of all comment ids of the service',
                'type' : 'list',
            },
            'current_service_contacts' : {
                'description' : 'A list of all contacts of the service, either direct or via a contact group',
                'type' : 'list',
            },
            'current_service_current_attempt' : {
                'description' : 'The number of the current check attempt',
                'type' : 'int',
            },
            'current_service_current_notification_number' : {
                'description' : 'The number of the current notification',
                'type' : 'int',
            },
            'current_service_custom_variable_names' : {
                'description' : 'A list of the names of all custom variables of the service',
                'type' : 'list',
            },
            'current_service_custom_variable_values' : {
                'description' : 'A list of the values of all custom variable of the service',
                'type' : 'list',
            },
            'current_service_description' : {
                'default' : '',
                'depythonize' : lambda x: x.get_name(),
                'description' : 'Description of the service (also used as key)',
                'prop' : 'log_service',
                'type' : 'string',
            },
            'current_service_display_name' : {
                'description' : 'An optional display name (not used by Nagios standard web pages)',
                'type' : 'string',
            },
            'current_service_downtimes' : {
                'description' : 'A list of all downtime ids of the service',
                'type' : 'list',
            },
            'current_service_event_handler' : {
                'description' : 'Nagios command used as event handler',
                'type' : 'string',
            },
            'current_service_event_handler_enabled' : {
                'description' : 'Wether and event handler is activated for the service (0/1)',
                'type' : 'int',
            },
            'current_service_execution_time' : {
                'description' : 'Time the host check needed for execution',
                'type' : 'float',
            },
            'current_service_first_notification_delay' : {
                'description' : 'Delay before the first notification',
                'type' : 'float',
            },
            'current_service_flap_detection_enabled' : {
                'description' : 'Wether flap detection is enabled for the service (0/1)',
                'type' : 'int',
            },
            'current_service_groups' : {
                'description' : 'A list of all service groups the service is in',
                'type' : 'list',
            },
            'current_service_has_been_checked' : {
                'description' : 'Wether the service already has been checked (0/1)',
                'type' : 'int',
            },
            'current_service_high_flap_threshold' : {
                'description' : 'High threshold of flap detection',
                'type' : 'float',
            },
            'current_service_icon_image' : {
                'description' : 'The name of an image to be used as icon in the web interface',
                'type' : 'string',
            },
            'current_service_icon_image_alt' : {
                'description' : 'An alternative text for the icon_image for browsers not displaying icons',
                'type' : 'string',
            },
            'current_service_icon_image_expanded' : {
                'description' : 'The icon_image with (the most important) macros expanded',
                'type' : 'string',
            },
            'current_service_in_check_period' : {
                'description' : 'Wether the service is currently in its check period (0/1)',
                'type' : 'int',
            },
            'current_service_in_notification_period' : {
                'description' : 'Wether the service is currently in its notification period (0/1)',
                'type' : 'int',
            },
            'current_service_initial_state' : {
                'description' : 'The initial state of the service',
                'type' : 'int',
            },
            'current_service_is_executing' : {
                'description' : 'is there a service check currently running... (0/1)',
                'type' : 'int',
            },
            'current_service_is_flapping' : {
                'description' : 'Wether the service is flapping (0/1)',
                'type' : 'int',
            },
            'current_service_last_check' : {
                'description' : 'The time of the last check (Unix timestamp)',
                'type' : 'int',
            },
            'current_service_last_hard_state' : {
                'description' : 'The last hard state of the service',
                'type' : 'int',
            },
            'current_service_last_hard_state_change' : {
                'description' : 'The time of the last hard state change (Unix timestamp)',
                'type' : 'int',
            },
            'current_service_last_notification' : {
                'description' : 'The time of the last notification (Unix timestamp)',
                'type' : 'int',
            },
            'current_service_last_state' : {
                'description' : 'The last state of the service',
                'type' : 'int',
            },
            'current_service_last_state_change' : {
                'description' : 'The time of the last state change (Unix timestamp)',
                'type' : 'int',
            },
            'current_service_latency' : {
                'description' : 'Time difference between scheduled check time and actual check time',
                'type' : 'float',
            },
            'current_service_long_plugin_output' : {
                'description' : 'Unabbreviated output of the last check plugin',
                'type' : 'string',
            },
            'current_service_low_flap_threshold' : {
                'description' : 'Low threshold of flap detection',
                'type' : 'float',
            },
            'current_service_max_check_attempts' : {
                'description' : 'The maximum number of check attempts',
                'type' : 'int',
            },
            'current_service_next_check' : {
                'description' : 'The scheduled time of the next check (Unix timestamp)',
                'type' : 'int',
            },
            'current_service_next_notification' : {
                'description' : 'The time of the next notification (Unix timestamp)',
                'type' : 'int',
            },
            'current_service_notes' : {
                'description' : 'Optional notes about the service',
                'type' : 'string',
            },
            'current_service_notes_expanded' : {
                'description' : 'The notes with (the most important) macros expanded',
                'type' : 'string',
            },
            'current_service_notes_url' : {
                'description' : 'An optional URL for additional notes about the service',
                'type' : 'string',
            },
            'current_service_notes_url_expanded' : {
                'description' : 'The notes_url with (the most important) macros expanded',
                'type' : 'string',
            },
            'current_service_notification_interval' : {
                'description' : 'Interval of periodic notification or 0 if its off',
                'type' : 'float',
            },
            'current_service_notification_period' : {
                'description' : 'The name of the notification period of the service. It this is empty, service problems are always notified.',
                'type' : 'string',
            },
            'current_service_notifications_enabled' : {
                'description' : 'Wether notifications are enabled for the service (0/1)',
                'type' : 'int',
            },
            'current_service_obsess_over_service' : {
                'description' : 'Wether \'obsess_over_service\' is enabled for the service (0/1)',
                'type' : 'int',
            },
            'current_service_percent_state_change' : {
                'description' : 'Percent state change',
                'type' : 'float',
            },
            'current_service_perf_data' : {
                'description' : 'Performance data of the last check plugin',
                'type' : 'string',
            },
            'current_service_plugin_output' : {
                'description' : 'Output of the last check plugin',
                'type' : 'string',
            },
            'current_service_process_performance_data' : {
                'description' : 'Wether processing of performance data is enabled for the service (0/1)',
                'type' : 'int',
            },
            'current_service_retry_interval' : {
                'description' : 'Number of basic interval lengths between checks when retrying after a soft error',
                'type' : 'float',
            },
            'current_service_scheduled_downtime_depth' : {
                'description' : 'The number of scheduled downtimes the service is currently in',
                'type' : 'int',
            },
            'current_service_state' : {
                'description' : 'The current state of the service (0: OK, 1: WARN, 2: CRITICAL, 3: UNKNOWN)',
                'type' : 'int',
            },
            'current_service_state_type' : {
                'description' : 'The type of the current state (0: soft, 1: hard)',
                'type' : 'int',
            },
            'host_name' : {
                'description' : 'The name of the host the log entry is about (might be empty)',
                'type' : 'string',
            },
            'lineno' : {
                'description' : 'The number of the line in the log file',
                'type' : 'int',
            },
            'message' : {
                'description' : 'The complete message line including the timestamp',
                'type' : 'string',
            },
            'options' : {
                'description' : 'The part of the message after the \':\'',
                'type' : 'string',
            },
            'plugin_output' : {
                'description' : 'The output of the check, if any is associated with the message',
                'type' : 'string',
            },
            'service_description' : {
                'description' : 'The description of the service log entry is about (might be empty)',
                'type' : 'string',
            },
            'state' : {
                'default' : 0,
                'description' : 'The state of the host or service in question',
                'prop' : 'state',
                'type' : 'int',
            },
            'state_type' : {
                'description' : 'The type of the state (varies on different log classes)',
                'type' : 'string',
            },
            'time' : {
                'default' : 0,
                'description' : 'Time of the log event (UNIX timestamp)',
                'prop' : 'time',
                'type' : 'int',
            },
            'type' : {
                'description' : 'The type of the message (text before the colon), the message itself for info messages',
                'type' : 'string',
            },
        },

    }


    def __init__(self, configs, hostname_lookup_table, servicename_lookup_table, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, dbconn, return_queue):
        #self.conf = scheduler.conf
        #self.scheduler = scheduler
        self.configs = configs
        self.hostname_lookup_table = hostname_lookup_table
        self.servicename_lookup_table = servicename_lookup_table
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.schedulers = schedulers
        self.dbconn = dbconn
        self.debuglevel = 2
        self.dbconn.row_factory = self.row_factory
        self.return_queue = return_queue


    def debug(self, debuglevel, message):
        f = open("/tmp/livestatus.debug", "a")
        f.write(message)
        f.write("\n")
        f.close()
        if self.debuglevel >= debuglevel:
            print message


    # Find the converter function for a table/attribute pair
    def find_converter(self, table, attribute):
        out_map = {
            'hosts' : LiveStatus.out_map['Host'],
            'services' : LiveStatus.out_map['Service'],
            'hostgroups' : LiveStatus.out_map['Hostgroup'],
            'servicegroups' : LiveStatus.out_map['Servicegroup'],
            'contacts' : LiveStatus.out_map['Contact'],
            'contactgroups' : LiveStatus.out_map['Contactgroup'],
            'comments' : LiveStatus.out_map['Comment'],
            'downtimes' : LiveStatus.out_map['Downtime'],
            'commands' : LiveStatus.out_map['Command'],
            'timeperiods' : LiveStatus.out_map['Timeperiod'],
            'status' : LiveStatus.out_map['Config'],
            'log' : LiveStatus.out_map['Logline'],
            'schedulers' : LiveStatus.out_map['SchedulerLink'],
        }[table]
        if attribute in out_map and 'type' in out_map[attribute]:
            if out_map[attribute]['type'] == 'int':
                return int
            elif out_map[attribute]['type'] == 'float':
                return float
        #if attribute in out_map and 'converter' in out_map[attribute]:
        #    return out_map[attribute]['converter']
        return None


    def create_output(self, elt, attributes, filterattributes):
        output = {}
        elt_type = elt.__class__.__name__
        if elt_type in LiveStatus.out_map:
            type_map = LiveStatus.out_map[elt_type]
            if len(attributes + filterattributes) == 0:
                #display_attributes = LiveStatus.default_attributes[elt_type]
                display_attributes = LiveStatus.out_map[elt_type].keys()
            else:
                display_attributes = list(set(attributes + filterattributes))
            for display in display_attributes:
                value = ''
                if display not in type_map:
                    # no mapping, use it as a direct attribute
                    value = getattr(elt, display, '')
                else:
                    if 'prop' not in type_map[display] or type_map[display]['prop'] == None:
                        # display is listed, but prop is not set. this must be a direct attribute
                        prop = display
                    else:
                        # We have a prop, this means some kind of mapping between the display name (livestatus column)
                        # and an internal name must happen
                        prop = type_map[display]['prop']
                    value = getattr(elt, prop, None)
                    if value != None:
                        # The name/function listed in prop exists
                        #Maybe it's not a value, but a function link
                        if callable(value):
                            value = value()
                        if display in type_map and 'depythonize' in type_map[display]:
                            f = type_map[display]['depythonize']
                            if callable(f):
                                #for example "from_list_to_split". value is an array and f takes the array as an argument
                                value = f(value)
                            else:
                                if isinstance(value, list):
                                    #depythonize's argument might be an attribute or a method
                                    #example: members is an array of hosts and we want get_name() of each element
                                    value = [getattr(item, f)() for item in value if callable(getattr(item, f)) ] \
                                          + [getattr(item, f) for item in value if not callable(getattr(item, f)) ]
                                    #at least servicegroups are nested [host,service],.. The need some flattening
                                    #value = ','.join(['%s' % y for x in value if isinstance(x, list) for y in x] + \
                                    #    ['%s' % x for x in value if not isinstance(x, list)])
                                    value = [y for x in value if isinstance(x, list) for y in x] + \
                                        [x for x in value if not isinstance(x, list)]
                                   
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
                output[display] = value    
        return output


    def get_live_data(self, table, columns, filtercolumns, filter_stack, stats_filter_stack, stats_postprocess_stack):
        result = []
        if table in ['hosts', 'services', 'downtimes', 'comments', 'hostgroups', 'servicegroups']:
            #Scan through the objects and apply the Filter: rules
            if table == 'hosts':
                if len(filtercolumns) == 0:
                    filtresult = [y for y in [self.create_output(x, columns, filtercolumns) for x in self.hosts.values()] if filter_stack(y)]
                else:
                    # If there we had Filter: statements, it makes sense to make two steps
                    # 1. Walk through the complete list of hosts, but only resolve those attributes
                    #    which are needed for the filtering
                    #    Hopefully after this step there are only a few host objects left
                    prefiltresult = (x for x in self.hosts.values() if filter_stack(self.create_output(x, [], filtercolumns)))
                    # 2. Then take the remaining objects and resolve the whole list of attributes (which may be a lot if there was no short Columns: list)
                    filtresult = [self.create_output(x, columns, filtercolumns) for x in prefiltresult]
            elif table == 'services':
                if len(filtercolumns) == 0:
                    filtresult = [y for y in [self.create_output(x, columns, filtercolumns) for x in self.services.values()] if filter_stack(y)]
                else:
                    prefiltresult = (x for x in self.services.values() if filter_stack(self.create_output(x, [], filtercolumns)))
                    filtresult = [self.create_output(x, columns, []) for x in prefiltresult]
            elif table == 'downtimes':
                if len(filtercolumns) == 0:
                    filtresult = [self.create_output(y, columns, filtercolumns) for y in reduce(list.__add__, [x.downtimes for x in self.services.values() +self.hosts.values() if len(x.downtimes) > 0], [])]
                else:
                    prefiltresult = [d for d in reduce(list.__add__, [x.downtimes for x in self.services.values() + self.hosts.values() if len(x.downtimes) > 0], []) if filter_stack(self.create_output(d, [], filtercolumns))]
                    filtresult = [self.create_output(x, columns, filtercolumns) for x in prefiltresult]
            elif table == 'comments':
                if len(filtercolumns) == 0:
                    filtresult = [self.create_output(y, columns, filtercolumns) for y in reduce(list.__add__, [x.comments for x in self.services.values() +self.hosts.values() if len(x.comments) > 0], [])]
                else:
                    prefiltresult = [c for c in reduce(list.__add__, [x.comments for x in self.services.values() + self.hosts.values() if len(x.comments) > 0], []) if filter_stack(self.create_output(c, [], filtercolumns))]
                    filtresult = [self.create_output(x, columns, filtercolumns) for x in prefiltresult]
            elif table == 'hostgroups':
                if len(filtercolumns) == 0:
                    filtresult = [y for y in [self.create_output(x, columns, filtercolumns) for x in self.hostgroups.values()] if filter_stack(y)]
                else:
                    prefiltresult = [x for x in self.hostgroups.values() if filter_stack(self.create_output(x, [], filtercolumns))]
                    filtresult = [self.create_output(x, columns, filtercolumns) for x in prefiltresult]
            elif table == 'servicegroups':
                if len(filtercolumns) == 0:
                    filtresult = [y for y in [self.create_output(x, columns, filtercolumns) for x in self.servicegroups.values()] if filter_stack(y)]
                else:
                    prefiltresult = [x for x in self.servicegroups.values() if filter_stack(self.create_output(x, [], filtercolumns))]
                    filtresult = [self.create_output(x, columns, filtercolumns) for x in prefiltresult]
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
                    resultarr[maxidx - i - 1] = postprocess(filter(filtfunc, filtresult))
                result = [resultarr]
            else:
                #Results are host/service/etc dicts with the requested attributes 
                #Columns: = keys of the dicts
                result = filtresult
        elif table == 'contacts':
            for c in self.contacts.values():
                result.append(self.create_output(c, columns, filtercolumns))
        elif table == 'commands':
            for c in self.commands.values():
                result.append(self.create_output(c, columns, filtercolumns))
        elif table == 'schedulers':
            for s in self.schedulers.values():
                result.append(self.create_output(s, columns, filtercolumns))
        elif table == 'status':
            for c in self.configs.values():
                result.append(self.create_output(c, columns, filtercolumns))
        elif table == 'columns':
            result.append({ 
                'description' : 'A description of the column' , 'name' : 'description' , 'table' : 'columns' , 'type' : 'string' })
            result.append({ 
                'description' : 'The name of the column within the table' , 'name' : 'name' , 'table' : 'columns' , 'type' : 'string' })
            result.append({ 
                'description' : 'The name of the table' , 'name' : 'table' , 'table' : 'columns' , 'type' : 'string' })
            result.append({ 
                'description' : 'The data type of the column (int, float, string, list)' , 'name' : 'type' , 'table' : 'columns' , 'type' : 'string' })
            tablenames = { 'Host' : 'hosts', 'Service' : 'services', 'Hostgroup' : 'hostgroups', 'Servicegroup' : 'servicegroups', 'Contact' : 'contacts', 'Contactgroup' : 'contactgroups', 'Command' : 'commands', 'Downtime' : 'downtimes', 'Comment' : 'comments', 'Timeperiod' : 'timeperiods', 'Config' : 'status', 'Logline' : 'log' }
            for obj in sorted(LiveStatus.out_map, key=lambda x: x):
                if obj in tablenames:
                    for attr in LiveStatus.out_map[obj]:
                        result.append({ 'description' : LiveStatus.out_map[obj][attr]['description'] if 'description' in LiveStatus.out_map[obj][attr] and LiveStatus.out_map[obj][attr]['description'] else 'to_do_desc', 'name' : attr, 'table' : tablenames[obj], 'type' : LiveStatus.out_map[obj][attr]['type'] })

        #print "result is", result
        return result


    def get_live_data_log(self, table, columns, filtercolumns, filter_stack, sql_filter_stack):
        result = []
        if table == 'log':
            # we can apply the filterstack here as well. we have columns and filtercolumns.
            # the only additional step is to enrich log lines with host/service-attributes
            # a timerange can be useful for a faster preselection of lines
            filter_clause, filter_values = sql_filter_stack()
            c = self.dbconn.cursor()
            try:
                #print "sql:", 'SELECT * FROM logs WHERE %s' % (filter_clause)
                c.execute('SELECT * FROM logs WHERE %s' % filter_clause, filter_values)
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]
            prefiltresult = []
            dbresult = c.fetchall()
            # make a generator: fill in the missing columns in the logline and filter it with filtercolumns
            prefiltresult = (y for y in (x.fill(self.hosts, self.services, self.hostname_lookup_table, self.servicename_lookup_table, set(columns + filtercolumns)) for x in dbresult) if filter_stack(self.create_output(y, [], filtercolumns)))
            # add output columns
            filtresult = [self.create_output(x, columns, filtercolumns) for x in prefiltresult]
            result = filtresult
            pass
            # CREATE TABLE IF NOT EXISTS logs(logobject INT, attempt INT, class INT, command_name VARCHAR(64), comment VARCHAR(256), contact_name VARCHAR(64), host_name VARCHAR(64), lineno INT, message VARCHAR(512), options INT, plugin_output VARCHAR(256), service_description VARCHAR(64), state INT, state_type VARCHAR(10), time INT, type VARCHAR(64))

        #print "result is", result
        return result


    def format_live_data(self, result, columns, outputformat, columnheaders, separators, aliases):
        output = ''
        lines = []
        if outputformat == 'csv':
            if len(result) > 0:
                if columnheaders != 'off' or len(columns) == 0:
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
                    lines.append(separators[1].join(separators[2].join(str(y) for y in x) if isinstance(x, list) else str(x) for x in [object[c] for c in columns]))
            else:
                if columnheaders == 'on':
                    if len(aliases) > 0:
                        lines.append(separators[1].join([aliases[col] for col in columns]))
                    else:
                        lines.append(separators[1].join(columns))
            return separators[0].join(lines)

        elif outputformat == 'json':
            if len(result) > 0:
                if columnheaders != 'off' or len(columns) == 0:
                    if len(aliases) > 0:
                        #This is for statements like "Stats: .... as alias_column
                        lines.append([str(aliases[col]) for col in columns])
                    else:
                        if (len(columns) == 0):
                            # Show all available columns
                            columns = sorted(result[0].keys())
                        lines.append(columns)
                for object in result:
                    lines.append([object[c] for c in columns])
            else:
                if columnheaders == 'on':
                    if len(aliases) > 0:
                        lines.append([aliases[col] for col in columns])
                    else:
                        lines.append(columns)
            return json.dumps(lines, separators=(',', ':'))


    def make_filter(self, operator, attribute, reference):
        #The filters are closures. 
        # Add parameter Class (Host, Service), lookup datatype (default string), convert reference
        def eq_filter(ref):
            return ref[attribute] == reference

        def eq_nocase_filter(ref):
            return ref[attribute].lower() == reference.lower()

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

        def match_filter(ref):
            p = re.compile(reference)
            return p.search(ref[attribute])

        def match_nocase_filter(ref):
            p = re.compile(reference, re.I)
            return p.search(ref[attribute])

        def ge_contains_filter(ref):
            if isinstance(ref[attribute], list):
                return reference in ref[attribute]
            else:
                return ref[attribute] >= reference

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
            return eq_filter
        elif operator == '!=':
            return ne_filter
        elif operator == '>':
            return gt_filter
        elif operator == '>=':
            return ge_contains_filter
        elif operator == '<':
            return gt_filter
        elif operator == '<=':
            return le_filter
        elif operator == '=~':
            return eq_nocase_filter
        elif operator == '~':
            return match_filter
        elif operator == '~~':
            return match_nocase_filter
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


    def make_sql_filter(self, operator, attribute, reference):
        #The filters are closures. 
        # Add parameter Class (Host, Service), lookup datatype (default string), convert reference
        def eq_filter():
            if reference == '':
                return ['%s IS NULL' % attribute, ()]
            else:
                return ['%s = ?' % attribute, (reference, )]
        def ne_filter():
            if reference == '':
                return ['%s IS NOT NULL' % attribute, ()]
            else:
                return ['%s != ?' % attribute, (reference, )]
        def ge_filter():
            return ['%s >= ?' % attribute, (reference, )]
        def le_filter():
            return ['%s <= ?' % attribute, (reference, )]
        def match_filter():
            return ['%s LIKE ?' % attribute, ('%'+reference+'%', )]
        if operator == '=':
            return eq_filter
        if operator == '>=':
            return ge_filter
        if operator == '<=':
            return le_filter
        if operator == '!=':
            return ne_filter
        if operator == '~':
            return match_filter


    def get_sql_filter_stack(self, filter_stack):
        if filter_stack.qsize() == 0:
            return ["1 = ?", 1]
        else:
            return filter_stack.get()
        pass


    def and_sql_filter_stack(self, num, filter_stack):
        filters = []
        for i in range(int(num)):
            filters.append(filter_stack.get())
        # Take from the stack:
        # List of functions returning [a where clause with ?, a tuple with the values for ?]
        # Combine the clauses with "and", merge the value tuples
        # Put a new function on the stack (returns anded clause and merged values)
        and_clause = '(' + (' AND ').join([ x()[0] for x in filters ]) + ')'
        and_values = reduce(lambda x, y: x+y, [ x()[1] for x in filters ])
        filter_stack.put(lambda : [and_clause, and_values])
        return filter_stack


    def or_sql_filter_stack(self, num, filter_stack):
        filters = []
        for i in range(int(num)):
            filters.append(filter_stack.get())
        and_clause = '(' + (' OR ').join([ x()[0] for x in filters ]) + ')'
        and_values = reduce(lambda x, y: x+y, [ x()[1] for x in filters ])
        filter_stack.put(lambda : [and_clause, and_values])
        return filter_stack


    def handle_request(self, data):
        title = ''
        content = ''
        response = ''
        columns = []
        filtercolumns = []
        responseheader = 'off'
        outputformat = 'csv'
        columnheaders = 'off'
        groupby = False
        aliases = []
        extcmd = False
        print "REQUEST", data
        # Set the default values for the separators
        separators = LiveStatus.separators
        # Initialize the stacks which are needed for the Filter: and Stats:
        # filter- and count-operations
        filter_stack = Queue.LifoQueue()
        sql_filter_stack = Queue.LifoQueue()
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
                if operator in ['=', '!=', '>', '>=', '<', '<=', '=~', '~', '~~']:
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    filtercolumns.append(attribute)
                    # reference is now datatype string. The referring object attribute on the other hand
                    # may be an integer. (current_attempt for example)
                    # So for the filter to work correctly (the two values compared must be
                    # of the same type), we need to convert the reference to the desired type
                    converter = self.find_converter(table, attribute)
                    if converter:
                        reference = converter(reference)
                    filter_stack.put(self.make_filter(operator, attribute, reference))
                    if table == 'log':
                        if attribute == 'time':
                            sql_filter_stack.put(self.make_sql_filter(operator, attribute, reference))
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
                    converter = self.find_converter(table, attribute)
                    if converter:
                        reference = converter(reference)
                    stats_filter_stack.put(self.make_filter(operator, attribute, reference))
                    stats_postprocess_stack.put(self.make_filter('count', attribute, groupby))
                elif operator in ['sum', 'min', 'max', 'avg', 'std']:
                    columns.append(attribute)
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
            elif line.find('COMMAND') != -1:
                cmd, extcmd = line.split(' ', 1)
            else:
                # This line is not valid or not implemented
                print "Received a line of input which i can't handle"
                print line
                pass
        #External command are send back to broker
        if extcmd:
            print "Managing an external command", extcmd
            e = ExternalCommand(extcmd)
            self.return_queue.put(e)
            #command_file = self.configs[0].command_file
            #if os.path.exists(command_file):
            #    try:
            #        fifo = os.open(command_file, os.O_NONBLOCK|os.O_WRONLY)
            #        os.write(fifo, extcmd)
            #        os.close(fifo)
            #    except:
            #        print "Unable to open/write the external command pipe"
            return '\n'
        else:
            # make filtercolumns unique
            filtercolumns = list(set(filtercolumns))
            if filter_stack.qsize() > 1:
                #If we have Filter: statements but no FilterAnd/Or statements
                #Make one big filter where the single filters are anded
                filter_stack = self.and_filter_stack(filter_stack.qsize(), filter_stack)
            try:
                #Get the function which implements the Filter: statements
                simplefilter_stack = self.get_filter_stack(filter_stack)
                if table == 'log':
                    if sql_filter_stack.qsize() > 1:
                        sql_filter_stack = self.and_sql_filter_stack(sql_filter_stack.qsize(), sql_filter_stack)
                    sql_simplefilter_stack = self.get_sql_filter_stack(sql_filter_stack)
                    result = self.get_live_data_log(table, columns, filtercolumns, simplefilter_stack, sql_simplefilter_stack)
                else:
                    #Get the function which implements the Stats: statements
                    stats = stats_filter_stack.qsize()
                    #Apply the filters on the broker's host/service/etc elements
                    result = self.get_live_data(table, columns, filtercolumns, simplefilter_stack, stats_filter_stack, stats_postprocess_stack)
                    if stats > 0:
                        columns = range(stats)
                        if len(aliases) == 0:
                            #If there were Stats: staments without "as", show no column headers at all
                            columnheaders = 'off'
                        else:
                            columnheaders = 'on'

                #Now bring the retrieved information to a form which can be sent back to the client
                response = self.format_live_data(result, columns, outputformat, columnheaders, separators, aliases) + "\n"
            except BaseException, e:
                import traceback
                print "REQUEST produces an exception", data
                print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                print e
                traceback.print_exc(32)
                print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    
    
            if responseheader == 'fixed16':
                statuscode = 200
                responselength = len(response) # no error
                response = '%3d %11d\n' % (statuscode, responselength) + response
    
            print "REQUEST", data
            print "RESPONSE\n%s\n" % response
            return response

    def row_factory(self, cursor, row):
        return Logline(cursor, row)
