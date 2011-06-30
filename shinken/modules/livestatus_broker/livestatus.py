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
import re
import copy
import os
import time
try:
    import json
except ImportError:
    import simplejson as json
try:
    import sqlite3
except ImportError:
    try:
        import pysqlite2.dbapi2 as sqlite3
    except ImportError:
        import sqlite as sqlite3

from shinken.bin import VERSION
from shinken.external_command import ExternalCommand
from shinken.macroresolver import MacroResolver
from shinken.util import from_bool_to_int, from_float_to_int, to_int, to_split, get_customs_keys, get_customs_values

from livestatus_stack import LiveStatusStack

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


def get_livestatus_full_name(prop, ref, request):
    """Returns a host's or a service's name in livestatus notation.
    
    This function takes either a host or service object as it's first argument. 
    The third argument is a livestatus request object. The important information
    in the request object is the separators array. It contains the character
    that separates host_name and service_description which is used for services'
    names with the csv output format. If the output format is json, services' names
    are lists composed of host_name and service_description. 
    """
    cls_name = prop.__class__.my_type
    if request.response.outputformat == 'csv':
        if cls_name == 'service':
            return prop.host_name + request.response.separators[3] + prop.service_description
        else:
            return prop.host_name
    elif request.response.outputformat == 'json' or request.response.outputformat == 'python':
        if cls_name == 'service':
            return [prop.host_name, prop.service_description]
        else:
            return prop.host_name
        pass


def join_with_separators(prop, ref, request, *args):
    if request.response.outputformat == 'csv':
        return request.response.separators[3].join([str(arg) for arg in args])
    elif request.response.outputformat == 'json' or request.response.outputformat == 'python':
        return args
    else:
        return None
    pass


def from_svc_hst_distinct_lists(dct):
    """Transform a dict with keys hosts and services to a list."""
    t = []
    for h in dct['hosts']:
        t.append(h)
    for s in dct['services']:
        t.append(s)
    return t


def worst_host_state(state_1, state_2):
    """Return the worst of two host states."""
    #lambda x: reduce(lambda g, c: c if g == 0 else (c if c == 1 else g), (y.state_id for y in x), 0),
    if state_2 == 0:
        return state_1
    if state_1 == 1:
        return state_1
    return state_2


def worst_service_state(state_1, state_2):
    """Return the worst of two service states."""
    #reduce(lambda g, c: c if g == 0 else (c if c == 2 else (c if (c == 3 and g != 2) else g)), (z.state_id for y in x for z in y.services if z.state_type_id == 1), 0),
    if state_2 == 0:
        return state_1
    if state_1 == 2:
        return state_1
    if state_1 == 3 and state_2 != 2:
        return state_1
    return state_2


def find_pnp_perfdata_xml(name, ref, request):
    """Check if a pnp xml file exists for a given host or service name."""
    if request.pnp_path_readable:
        if '/' in name:
            # It is a service
            if os.access(request.pnp_path + '/' + name + '.xml', os.R_OK):
                return 1
        else:
            # It is a host
            if os.access(request.pnp_path + '/' + name + '/_HOST_.xml', os.R_OK):
                return 1
    # If in doubt, there is no pnp file
    return 0


class Problem:
    def __init__(self, source, impacts):
        self.source = source
        self.impacts = impacts



class Logline(dict):
    """A class which represents a line from the logfile
    
    Public functions:
    fill -- Attach host and/or service objects to a Logline object
    
    """
    
    def __init__(self, cursor, row):
        for idx, col in enumerate(cursor.description):
            setattr(self, col[0], row[idx])


    def fill(self, hosts, services, columns):
        """Attach host and/or service objects to a Logline object
        
        Lines describing host or service events only contain host_name
        and/or service_description. This method finds the corresponding
        objects and adds them to the line as attributes log_host
        and/or log_service
        
        """
        if self.logobject == LOGOBJECT_HOST:
            try:
                setattr(self, 'log_host', hosts[self.host_name])
            except:
                pass
        elif self.logobject == LOGOBJECT_SERVICE:
            try:
                setattr(self, 'log_host', hosts[self.host_name])
                setattr(self, 'log_service', services[self.host_name + self.service_description])
            except:
                pass
        return self




class LiveStatus(object):
    """A class that represents the status of all objects in the broker
    
    """
    # description (optional): no need to explain this
    # prop (optional): the property of the object. If this is missing, the key is the property
    # type (mandatory): int, float, string, list
    # depythonize : use it if the property needs to be post-processed. 
    # fulldepythonize : the same, but the postprocessor takes three arguments. property, object, request
    # delegate : get the property of a different object
    # as : use it together with delegate, if the property of the other object has another name
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The same as action_url, but with the most important macros expanded',
                'prop' : 'action_url',
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
                'description' : 'A list of all direct childs of the host',
                'type' : 'list',
            },
            'comments' : {
                'default' : '',
                'depythonize' : 'id',
                'description' : 'A list of the ids of all comments of this host',
                'type' : 'list',
            },
            'comments_with_info' : {
                'default' : '',
                'fulldepythonize' : lambda p, e, r: join_with_separators(p, e, r, str(p.id), p.author, p.comment),
                'description' : 'A list of the ids of all comments of this host with id, author and comment',
                'prop' : 'comments',
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
                'prop' : 'customs',
                'description' : 'A list of the names of all custom variables',
                'type' : 'list',
                'depythonize' : get_customs_keys,
            },
            'custom_variable_values' : {
                'prop' : 'customs',
                'description' : 'A list of the values of the custom variables',
                'type' : 'list',
                'depythonize' : get_customs_values,
            },
            'display_name' : {
                'description' : 'Optional display name of the host - not used by Nagios\' web interface',
                'prop' : 'host_name',
                'type' : 'string',
            },
            'downtimes' : {
                'depythonize' : 'id',
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
            'got_business_rule' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is an business rule based host or not (0/1)',
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'prop' : 'icon_image',
                'type' : 'string',
            },
            'in_check_period' : {
                'fulldepythonize' : lambda p, e, r: from_bool_to_int((p is None and [False] or [p.is_time_valid(r.tic)])[0]),
                'description' : 'Wether this host is currently in its check period (0/1)',
                'prop' : 'check_period',
                'type' : 'int',
            },
            'in_notification_period' : {
                'fulldepythonize' : lambda p, e, r: from_bool_to_int((p is None and [False] or [p.is_time_valid(r.tic)])[0]),
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'prop' : 'notification_period',
                'type' : 'int',
            },
            'initial_state' : {
                'description' : 'Initial host state',
                'type' : 'int',
            },
            'is_executing' : {
                'default' : 0, # value in scheduler is not real-time
                'description' : 'is there a host check currently running... (0/1)',
                #'prop' : 'in_checking',
                'type' : 'int',
            },
            'is_flapping' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is flapping (0/1)',
                'type' : 'int',
            },
            'is_impact' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is an impact or not (0/1)',
                'type' : 'int',
            },
            'is_problem' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is a problem or not (0/1)',
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The same as notes, but with the most important macros expanded',
                'prop' : 'notes',
                'type' : 'string',
            },
            'notes_url' : {
                'description' : 'An optional URL with further information about the host',
                'type' : 'string',
            },
            'notes_url_expanded' : {
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'prop' : 'notes_url',
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
            'pnpgraph_present' : {
                'fulldepythonize' : find_pnp_perfdata_xml,
                'description' : 'Whether there is a PNP4Nagios graph present for this host (0/1)',
                'prop' : 'host_name',
                'type' : 'int',
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
            'criticity' : {
                'converter' : int,
                'description' : 'The importance we gave to this host between hte minimum 0 and the maximum 5',
                'type' : 'int',
            },
            'source_problems' : {
                'description' : 'The name of the source problems (host or service)',
                'prop' : 'source_problems',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
            },
            'impacts' : {
                'description' : 'List of what the source impact (list of hosts and services)',
                'prop' : 'impacts',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
            },
            'parent_dependencies' : {
                'description' : 'List of the dependencies (logical, network or business one) of this host.',
                'prop' : 'parent_dependencies',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
            },
            'child_dependencies' : {
                'description' : 'List of the host/service that depend on this host (logical, network or business one).',
                'prop' : 'child_dependencies',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The action_url with (the most important) macros expanded',
                'prop' : 'action_url',
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
            'comments_with_info' : {
                'default' : '',
                'fulldepythonize' : lambda p, e, r: join_with_separators(p, e, r, str(p.id), p.author, p.comment),
                'description' : 'A list of the ids of all comments of this service with id, author and comment',
                'prop' : 'comments',
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
                'prop' : 'customs',
                'description' : 'A list of the names of all custom variables of the service',
                'type' : 'list',
                'depythonize' : get_customs_keys,
            },
            'custom_variable_values' : {
                'prop' : 'customs',
                'description' : 'A list of the values of all custom variable of the service',
                'type' : 'list',
                'depythonize' : get_customs_values,
            },
            'description' : {
                'description' : 'Description of the service (also used as key)',
                'prop' : 'service_description',
                'type' : 'string',
            },
            'display_name' : {
                'description' : 'An optional display name (not used by Nagios standard web pages)',
                'prop' : 'service_description',
                'type' : 'string',
            },
            'downtimes' : {
                'depythonize' : lambda x: x.id,
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
            'got_business_rule' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the service state is an business rule based host or not (0/1)',
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The same as action_url, but with the most important macros expanded',
                'prop' : 'host',
                'type' : 'string',
            },
            'host_active_checks_enabled' : {
                'description' : 'Wether active checks are enabled for the host (0/1)',
                'type' : 'int',
            },
            'host_address' : {
                'depythonize' : lambda x: x.address,
                'description' : 'IP address',
                'prop' : 'host',
                'type' : 'string',
            },
            'host_alias' : {
                'depythonize' : lambda x: x.alias,
                'description' : 'An alias name for the host',
                'prop' : 'host',
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
                #'default' : '',
                #'depythonize' : lambda h: ([c.id for c in h.comments]),
                'description' : 'A list of the ids of all comments of this host',
                #'prop' : 'host',
                'type' : 'list',
            },
            'host_comments_with_info' : {
                #'default' : '',
                #'depythonize' : lambda h: ([c.id for c in h.comments]),
                'description' : 'A list of the ids of all comments of this host',
                #'prop' : 'host',
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
                'depythonize' : lambda h: get_customs_keys(h.customs),
                'prop' : 'host',
                'type' : 'list',
            },
            'host_custom_variable_values' : {
                'description' : 'A list of the values of the custom variables',
                'depythonize' : lambda h: get_customs_values(h.customs),
                'prop' : 'host',
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The same as icon_image, but with the most important macros expanded',
                'prop' : 'host',
                'type' : 'string',
            },
            'host_in_check_period' : {
                'depythonize' : lambda h: from_bool_to_int((h.check_period is None and [False] or [h.check_period.is_time_valid(time.time())])[0]),
                'description' : 'Wether this host is currently in its check period (0/1)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_in_notification_period' : {
                'depythonize' : lambda h: from_bool_to_int((h.notification_period is None and [False] or [h.notification_period.is_time_valid(time.time())])[0]),
                'description' : 'Wether this host is currently in its notification period (0/1)',
                'prop' : 'host',
                'type' : 'int',
            },
            'host_initial_state' : {
                'description' : 'Initial host state',
                'type' : 'int',
            },
            'host_is_executing' : {
                'default' : 0, # value in scheduler is not real-time
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The same as notes, but with the most important macros expanded',
                'prop' : 'host',
                'type' : 'string',
            },
            'host_notes_url' : {
                'description' : 'An optional URL with further information about the host',
                'type' : 'string',
            },
            'host_notes_url_expanded' : {
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'Same es notes_url, but with the most important macros expanded',
                'prop' : 'host',
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The icon_image with (the most important) macros expanded',
                'prop' : 'icon_image',
                'type' : 'string',
            },
            'in_check_period' : {
                'depythonize' : lambda tp: from_bool_to_int((tp is None and [False] or [tp.is_time_valid(time.time())])[0]),
                'description' : 'Wether the service is currently in its check period (0/1)',
                'prop' : 'check_period',
                'type' : 'int',
            },
            'in_notification_period' : {
                'depythonize' : lambda tp: from_bool_to_int((tp is None and [False] or [tp.is_time_valid(time.time())])[0]),
                'description' : 'Wether the service is currently in its notification period (0/1)',
                'prop' : 'notification_period',
                'type' : 'int',
            },
            'initial_state' : {
                'description' : 'The initial state of the service',
                'type' : 'int',
            },
            'is_executing' : {
                'default' : 0, # value in scheduler is not real-time
                'description' : 'is there a service check currently running... (0/1)',
                'type' : 'int',
            },
            'is_flapping' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the service is flapping (0/1)',
                'type' : 'int',
            },
            'is_impact' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is an impact or not (0/1)',
                'type' : 'int',
            },
            'is_problem' : {
                'depythonize' : from_bool_to_int,
                'description' : 'Wether the host state is a problem or not (0/1)',
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
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The notes with (the most important) macros expanded',
                'prop' : 'notes',
                'type' : 'string',
            },
            'notes_url' : {
                'description' : 'An optional URL for additional notes about the service',
                'type' : 'string',
            },
            'notes_url_expanded' : {
                'fulldepythonize' : lambda p, e, r: MacroResolver().resolve_simple_macros_in_string(p, e.get_data_for_checks()),
                'description' : 'The notes_url with (the most important) macros expanded',
                'prop' : 'notes_url',
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
            'pnpgraph_present' : {
                'fulldepythonize' : find_pnp_perfdata_xml,
                'description' : 'Whether there is a PNP4Nagios graph present for this service (0/1)',
                'prop' : 'get_dbg_name',
                'type' : 'int',
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
            'criticity' : {
                'converter' : int,
                'description' : 'The importance we gave to this service between hte minimum 0 and the maximum 5',
                'type' : 'int',
            },
            'source_problems' : {
                'description' : 'The name of the source problems (host or service)',
                'prop' : 'source_problems',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
            },
            'impacts' : {
                'description' : 'List of what the source impact (list of hosts and services)',
                'prop' : 'impacts',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
            },
            'parent_dependencies' : {
                'description' : 'List of the dependencies (logical, network or business one) of this service.',
                'prop' : 'parent_dependencies',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
            },
            'child_dependencies' : {
                'description' : 'List of the host/service that depend on this service (logical, network or business one).',
                'prop' : 'child_dependencies',
                'type' : 'list',
                'depythonize' : from_svc_hst_distinct_lists,
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
                'depythonize' : lambda x: sum((len(y.services) for y in x)),
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
                'depythonize' : lambda x: reduce(worst_host_state, (y.state_id for y in x), 0),
                'description' : 'The worst state of all of the groups\' hosts (UP <= UNREACHABLE <= DOWN)',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'worst_service_hard_state' : {
                'depythonize' : lambda x: reduce(worst_service_state, (z.state_id for y in x for z in y.services if z.state_type_id == 1), 0),
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : 'get_hosts',
                'type' : 'list',
            },
            'worst_service_state' : {
                'depythonize' : lambda x: reduce(worst_service_state, (z.state_id for y in x for z in y.services), 0),
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
                'fulldepythonize' : get_livestatus_full_name,
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
                'depythonize' : lambda x: reduce(worst_service_state, (y.state_id for y in x), 0),
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
                'prop' : 'contact_name',
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



        #Pollers
        'PollerLink' : {
            'name' : {
                'description' : 'The name of the poller',
                'prop' : 'poller_name',
                'type' : 'string',
            },
            'address' : {
                'description' : 'The ip or dns adress of the poller',
                'prop' : 'address',
                'type' : 'string',
            },
            'port' : {
                'description' : 'The TCP port of the poller',
                'prop' : 'port',
                'type' : 'int',
            },
            'spare' : {
                'description' : 'If the poller is a spare or not',
                'depythonize' : from_bool_to_int,
                'prop' : 'spare',
                'type' : 'int',
            },
            'alive' : {
                'description' : 'If the poller is alive or not',
                'prop' : 'alive',
                'depythonize' : from_bool_to_int,
                'type' : 'int',
            },
        },


        #Reactionners
        'ReactionnerLink' : {
            'name' : {
                'description' : 'The name of the reactionner',
                'prop' : 'reactionner_name',
                'type' : 'string',
            },
            'address' : {
                'description' : 'The ip or dns adress of the reactionner',
                'prop' : 'address',
                'type' : 'string',
            },
            'port' : {
                'description' : 'The TCP port of the reactionner',
                'prop' : 'port',
                'type' : 'int',
            },
            'spare' : {
                'description' : 'If the reactionner is a spare or not',
                'depythonize' : from_bool_to_int,
                'prop' : 'spare',
                'type' : 'int',
            },
            'alive' : {
                'description' : 'If the reactionner is alive or not',
                'prop' : 'alive',
                'depythonize' : from_bool_to_int,
                'type' : 'int',
            },
        },


        #Brokers
        'BrokerLink' : {
            'name' : {
                'description' : 'The name of the broker',
                'prop' : 'broker_name',
                'type' : 'string',
            },
            'address' : {
                'description' : 'The ip or dns adress of the broker',
                'prop' : 'address',
                'type' : 'string',
            },
            'port' : {
                'description' : 'The TCP port of the broker',
                'prop' : 'port',
                'type' : 'int',
            },
            'spare' : {
                'description' : 'If the broker is a spare or not',
                'depythonize' : from_bool_to_int,
                'prop' : 'spare',
                'type' : 'int',
            },
            'alive' : {
                'description' : 'If the broker is alive or not',
                'prop' : 'alive',
                'depythonize' : from_bool_to_int,
                'type' : 'int',
            },
        },


        #Problem
        'Problem' : {
            'source' : {
                'description' : 'The source name of the problem (host or service)',
                'prop' : 'source',
                'type' : 'string',
                'fulldepythonize' : get_livestatus_full_name
            },
            'impacts' : {
                'description' : 'List of what the source impact (list of hosts and services)',
                'prop' : 'impacts',
                'type' : 'string',
                'depythonize' : from_svc_hst_distinct_lists,
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
                'default' : 0, # value in scheduler is not real-time
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
                # automatic delegation does not work here, because it would
                # ref always to be a host
                'delegate' : 'ref',
                'as' : 'host_name',
                'description' : 'Host name',
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
                'default' : 0, # value in scheduler is not real-time
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
                'default' : 0, # value in scheduler is not real-time
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
                'delegate' : 'ref',
                'as' : 'host_name',
                'description' : 'Host name',
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
                'default' : 0, # value in scheduler is not real-time
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

        # loop over hostgroups then over members
        'Hostsbygroup' : {
            'hostgroup_action_url' : {
                'description' : 'An optional URL to custom actions or information about the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'string',
            },
            'hostgroup_alias' : {
                'depythonize' : lambda x: getattr(x, 'hostgroup_alias', ''),
                'description' : 'An alias of the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'string',
            },
            'hostgroup_members' : {
                'description' : 'A list of all host names that are members of the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'list',
            },
            'hostgroup_members_with_state' : {
                'description' : 'A list of all host names that are members of the hostgroup together with state and has_been_checked',
                'prop' : 'hostgroup',
                'type' : 'list',
            },
            'hostgroup_name' : {
                'depythonize' : lambda x: getattr(x, 'hostgroup_name', ''),
                'description' : 'Name of the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'string',
            },
            'hostgroup_notes' : {
                'description' : 'Optional notes to the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'string',
            },
            'hostgroup_notes_url' : {
                'description' : 'An optional URL with further information about the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'string',
            },
            'hostgroup_num_hosts' : {
                'description' : 'The total number of hosts in the group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_hosts_down' : {
                'description' : 'The number of hosts in the group that are down',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_hosts_pending' : {
                'description' : 'The number of hosts in the group that are pending',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_hosts_unreach' : {
                'description' : 'The number of hosts in the group that are unreachable',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_hosts_up' : {
                'description' : 'The number of hosts in the group that are up',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services' : {
                'description' : 'The total number of services of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_crit' : {
                'description' : 'The total number of services with the state CRIT of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_crit' : {
                'description' : 'The total number of services with the state CRIT of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_ok' : {
                'description' : 'The total number of services with the state OK of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_unknown' : {
                'description' : 'The total number of services with the state UNKNOWN of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_warn' : {
                'description' : 'The total number of services with the state WARN of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_ok' : {
                'description' : 'The total number of services with the state OK of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_pending' : {
                'description' : 'The total number of services with the state Pending of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_unknown' : {
                'description' : 'The total number of services with the state UNKNOWN of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_num_services_warn' : {
                'description' : 'The total number of services with the state WARN of hosts in this group',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_worst_host_state' : {
                'description' : 'The worst state of all of the groups\' hosts (UP <= UNREACHABLE <= DOWN)',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_worst_service_hard_state' : {
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
            'hostgroup_worst_service_state' : {
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
                'prop' : 'hostgroup',
                'type' : 'int',
            },
        },

        'Servicesbygroup' : {
            'servicegroup_action_url' : {
                'description' : 'An optional URL to custom notes or actions on the service group',
                'type' : 'string',
            },
            'servicegroup_alias' : {
                'description' : 'An alias of the service group',
                'type' : 'string',
            },
            'servicegroup_members' : {
                'description' : 'A list of all members of the service group as host/service pairs',
                'type' : 'list',
            },
            'servicegroup_members_with_state' : {
                'description' : 'A list of all members of the service group with state and has_been_checked',
                'type' : 'list',
            },
            'servicegroup_name' : {
                'description' : 'The name of the service group',
                'type' : 'string',
            },
            'servicegroup_notes' : {
                'description' : 'Optional additional notes about the service group',
                'type' : 'string',
            },
            'servicegroup_notes_url' : {
                'description' : 'An optional URL to further notes on the service group',
                'type' : 'string',
            },
            'servicegroup_num_services' : {
                'description' : 'The total number of services in the group',
                'type' : 'int',
            },
            'servicegroup_num_services_crit' : {
                'description' : 'The number of services in the group that are CRIT',
                'type' : 'int',
            },
            'servicegroup_num_services_hard_crit' : {
                'description' : 'The number of services in the group that are CRIT',
                'type' : 'int',
            },
            'servicegroup_num_services_hard_ok' : {
                'description' : 'The number of services in the group that are OK',
                'type' : 'int',
            },
            'servicegroup_num_services_hard_unknown' : {
                'description' : 'The number of services in the group that are UNKNOWN',
                'type' : 'int',
            },
            'servicegroup_num_services_hard_warn' : {
                'description' : 'The number of services in the group that are WARN',
                'type' : 'int',
            },
            'servicegroup_num_services_ok' : {
                'description' : 'The number of services in the group that are OK',
                'type' : 'int',
            },
            'servicegroup_num_services_pending' : {
                'description' : 'The number of services in the group that are PENDING',
                'type' : 'int',
            },
            'servicegroup_num_services_unknown' : {
                'description' : 'The number of services in the group that are UNKNOWN',
                'type' : 'int',
            },
            'servicegroup_num_services_warn' : {
                'description' : 'The number of services in the group that are WARN',
                'type' : 'int',
            },
            'servicegroup_worst_service_state' : {
                'description' : 'The worst soft state of all of the groups services (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'int',
            },
        },

        'Servicesbyhostgroup' : {
            'hostgroup_action_url' : {
                'description' : 'An optional URL to custom actions or information about the hostgroup',
                'type' : 'string',
            },
            'hostgroup_alias' : {
                'description' : 'An alias of the hostgroup',
                'type' : 'string',
            },
            'hostgroup_members' : {
                'description' : 'A list of all host names that are members of the hostgroup',
                'type' : 'list',
            },
            'hostgroup_members_with_state' : {
                'description' : 'A list of all host names that are members of the hostgroup together with state and has_been_checked',
                'type' : 'list',
            },
            'hostgroup_name' : {
                'depythonize' : lambda x: getattr(x, 'hostgroup_name', ''),
                'description' : 'Name of the hostgroup',
                'prop' : 'hostgroup',
                'type' : 'string',
            },
            'hostgroup_notes' : {
                'description' : 'Optional notes to the hostgroup',
                'type' : 'string',
            },
            'hostgroup_notes_url' : {
                'description' : 'An optional URL with further information about the hostgroup',
                'type' : 'string',
            },
            'hostgroup_num_hosts' : {
                'description' : 'The total number of hosts in the group',
                'type' : 'int',
            },
            'hostgroup_num_hosts_down' : {
                'description' : 'The number of hosts in the group that are down',
                'type' : 'int',
            },
            'hostgroup_num_hosts_pending' : {
                'description' : 'The number of hosts in the group that are pending',
                'type' : 'int',
            },
            'hostgroup_num_hosts_unreach' : {
                'description' : 'The number of hosts in the group that are unreachable',
                'type' : 'int',
            },
            'hostgroup_num_hosts_up' : {
                'description' : 'The number of hosts in the group that are up',
                'type' : 'int',
            },
            'hostgroup_num_services' : {
                'description' : 'The total number of services of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_crit' : {
                'description' : 'The total number of services with the state CRIT of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_crit' : {
                'description' : 'The total number of services with the state CRIT of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_ok' : {
                'description' : 'The total number of services with the state OK of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_unknown' : {
                'description' : 'The total number of services with the state UNKNOWN of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_hard_warn' : {
                'description' : 'The total number of services with the state WARN of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_ok' : {
                'description' : 'The total number of services with the state OK of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_pending' : {
                'description' : 'The total number of services with the state Pending of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_unknown' : {
                'description' : 'The total number of services with the state UNKNOWN of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_num_services_warn' : {
                'description' : 'The total number of services with the state WARN of hosts in this group',
                'type' : 'int',
            },
            'hostgroup_worst_host_state' : {
                'description' : 'The worst state of all of the groups\' hosts (UP <= UNREACHABLE <= DOWN)',
                'type' : 'int',
            },
            'hostgroup_worst_service_hard_state' : {
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
                'type' : 'int',
            },
            'hostgroup_worst_service_state' : {
                'description' : 'The worst state of all services that belong to a host of this group (OK <= WARN <= UNKNOWN <= CRIT)',
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
                'default' : 0,
                'description' : 'The current number of log messages MK Livestatus keeps in memory',
                'prop' : None,
                'type' : 'int',
            },
            'cached_log_messages_rate' : {
                'default' : 0,
                'description' : 'The current number of log messages MK Livestatus keeps in memory',
                'prop' : None,
                'type' : 'float',
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
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("connections"),
                'description' : 'The number of client connections to Livestatus since program start',
                'prop' : 'is_running',
                'type' : 'int',
            },
            'connections_rate' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("connections_rate"),
                'description' : 'The averaged number of new client connections to Livestatus per second',
                'prop' : 'is_running',
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
            'external_commands_rate' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("external_commands_rate"),
                'description' : 'The averaged number of external commands per second',
                'prop' : 'is_running',
                'type' : 'float',
            },
            'external_command_buffer_max' : {
                'default' : 0,
                'description' : 'The maximum number of slots used in the external command buffer',
                'prop' : None,
                'type' : 'int',
            },
            'external_command_buffer_slots' : {
                'default' : 0,
                'description' : 'The size of the buffer for the external commands',
                'prop' : None,
                'type' : 'int',
            },
            'external_command_buffer_usage' : {
                'default' : 0,
                'description' : 'The number of slots in use of the external command buffer',
                'prop' : None,
                'type' : 'int',
            },
            'forks' : {
                'default' : '0',
                'fulldepythonize' : lambda p, e, r: r.counters.count("forks"),
                'description' : 'The number of process creations since program start',
                'prop' : 'is_running',
                'type' : 'float',
            },
            'forks_rate' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("forks_rate"),
                'description' : 'The averaged number of forks per second',
                'prop' : 'is_running',
                'type' : 'float',
            },
            'host_checks' : {
                'default' : '0',
                'fulldepythonize' : lambda p, e, r: r.counters.count("host_checks"),
                'description' : 'The number of host checks since program start',
                'prop' : 'is_running',
                'type' : 'int',
            },
            'host_checks_rate' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("host_checks_rate"),
                'description' : 'the averaged number of host checks per second',
                'prop' : 'is_running',
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
                'default' : '1.1.3-shinken',
                'description' : 'The version of the MK Livestatus module',
                'prop' : None,
                'type' : 'string',
            },
            'log_messages' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("log_messages"),
                'description' : 'The number of new log messages since program start',
                'prop' : 'is_running',
                'type' : 'float',
            },
            'log_messages_rate' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("log_messages_rate"),
                'description' : 'The averaged number of log messages per second',
                'prop' : 'is_running',
                'type' : 'float',
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
                'default' : VERSION,
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
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("service_checks"),
                'description' : 'The number of completed service checks since program start',
                'prop' : 'is_running',
                'type' : 'int',
            },
            'service_checks_rate' : {
                'default' : 0,
                'fulldepythonize' : lambda p, e, r: r.counters.count("service_checks_rate"),
                'description' : 'The averaged number of service checks per second',
                'prop' : 'is_running',
                'type' : 'float',
            },
        },

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
                'default' : 0, # value in scheduler is not real-time
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
                'default' : 0, # value in scheduler is not real-time
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

    separators = map(lambda x: chr(int(x)), [10, 59, 44, 124])


    def __init__(self, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, pollers, reactionners, brokers, dbconn, pnp_path, return_queue):
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.schedulers = schedulers
        self.pollers = pollers
        self.reactionners = reactionners
        self.brokers = brokers
        self.dbconn = dbconn
        LiveStatus.pnp_path = pnp_path
        self.debuglevel = 2
        self.dbconn.row_factory = self.row_factory 
        self.return_queue = return_queue

        self.create_out_map_delegates()
        self.create_out_map_hooks()

        # add Host attributes to Hostsbygroup etc.
        for attribute in LiveStatus.out_map['Host']:
            LiveStatus.out_map['Hostsbygroup'][attribute] = LiveStatus.out_map['Host'][attribute]
        for attribute in self.out_map['Service']:
            LiveStatus.out_map['Servicesbygroup'][attribute] = LiveStatus.out_map['Service'][attribute]
        for attribute in self.out_map['Service']:
            LiveStatus.out_map['Servicesbyhostgroup'][attribute] = LiveStatus.out_map['Service'][attribute]

        self.counters = LiveStatusCounters()


    def row_factory(self, cursor, row):
        """Handler for the sqlite fetch method."""
        return Logline(cursor, row)


    def handle_request(self, data):
        """Execute the livestatus request.
        
        This function creates a LiveStatusRequest method, calls the parser,
        handles the execution of the request and formatting of the result.
        
        """
        request = LiveStatusRequest(data, self.configs, self.hosts, self.services, 
            self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, 
            self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.return_queue, self.counters)
        request.parse_input(data)
        #print "REQUEST\n%s\n" % data
        to_del = []
        if sorted([q.my_type for q in request.queries]) == ['command', 'query', 'wait']:
            # The Multisite way
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
            output = [q for q in request.queries if q.my_type == 'wait'] + [q for q in request.queries if q.my_type == 'query']
        elif sorted([q.my_type for q in request.queries]) == ['query', 'wait']:
            # The Thruk way
            output = [q for q in request.queries if q.my_type == 'wait'] + [q for q in request.queries if q.my_type == 'query']
            keepalive = True
        elif sorted([q.my_type for q in request.queries]) == ['command', 'query']:
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
            for query in [q for q in request.queries if q.my_type == 'query']:
                # This was a simple query, respond immediately
                result = query.launch_query()
                # Now bring the retrieved information to a form which can be sent back to the client
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()

        elif sorted([q.my_type for q in request.queries]) == ['query']:
            for query in [q for q in request.queries if q.my_type == 'query']:
                # This was a simple query, respond immediately
                result = query.launch_query()
                # Now bring the retrieved information to a form which can be sent back to the client
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
        elif sorted([q.my_type for q in request.queries]) == ['command']:
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
        elif [q.my_type for q in request.queries if q.my_type != 'command'] == []:
            # Only external commands. Thruk uses it when it sends multiple
            # objects into a downtime.
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
        else:
            # We currently do not handle this kind of composed request
            output = ""
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "We currently do not handle this kind of composed request"
            print sorted([q.my_type for q in request.queries])

        #print "RESPONSE\n%s\n" % output
        print "DURATION %.4fs" % (time.time() - request.tic)
        return output, keepalive


    def make_hook(self, hook, prop, default, func, as_prop):

        def hook_get_prop(elt):
            return getattr(elt, prop, default)


        def hook_get_prop_depythonize(elt):
            try:
                attr = getattr(elt, prop)
                if callable(attr):
                    attr = attr()
                return func(attr)
            except Exception, e:
                print "i am an exception in hook_get_prop_depythonize for managing an object '%s' with the property '%s' and the value '%s'" % (type(elt), prop, getattr(elt, prop, '')), e
                return default


        def hook_get_prop_depythonize_notcallable(elt):
            if hasattr(elt, prop):
                value = getattr(elt, prop)
                if value is None or value == 'none':
                    return default
                elif isinstance(value, list):
                    # Example: Service['comments'] = { type : 'list', depythonize : 'id' }
                    # 
                    value = [getattr(item, func)() for item in value if callable(getattr(item, func)) ] \
                        + [getattr(item, func) for item in value if not callable(getattr(item, func)) ]
                    return value
                else:
                    f = getattr(value, func)
                    if callable(f):
                        return f()
                    else:
                        return f
            else:
                return default


        def hook_get_prop_full_depythonize(elt):
            try:
                value = getattr(elt, prop)
                if callable(value):
                    value = value()
                if value is None or value == 'none':
                    raise
                elif isinstance(value, list):
                    return [func(item, elt, self) for item in value]
                else:
                    return func(value, elt, self)
            except Exception, e:
                print "i am an exception", e
                return default


        def hook_get_prop_delegate(elt):
            if not as_prop:
                new_prop = prop
            else:
                new_prop = as_prop
            if hasattr(elt, func):
                attr = getattr(elt, func)
                if callable(attr):
                    attr = attr()
                new_hook = self.out_map[attr.__class__.__name__][new_prop]['hook']
                if 'fulldepythonize' in self.out_map[attr.__class__.__name__][new_prop]:
                    return new_hook(attr, self)
                return new_hook(attr)
            else:
                return default


        if hook == 'get_prop':
            return hook_get_prop
        elif hook == 'get_prop_depythonize':
            return hook_get_prop_depythonize
        elif hook == 'get_prop_depythonize_notcallable':
            return hook_get_prop_depythonize_notcallable
        elif hook == 'get_prop_full_depythonize':
            return hook_get_prop_full_depythonize
        elif hook == 'get_prop_delegate':
            return hook_get_prop_delegate


    def create_out_map_hooks(self):
        """Add hooks to the elements of the LiveStatus.out_map.
        
        This function analyzes the elements of the out_map.
        Depending on the existence of several keys like
        default, prop, depythonize, etc. it creates a function which
        resolves an attribute as fast as possible and adds this function
        as a new key called hook.
        
        """
        for objtype in LiveStatus.out_map:
            for attribute in LiveStatus.out_map[objtype]:
                entry =  LiveStatus.out_map[objtype][attribute]
                if 'prop' not in entry or entry['prop'] is None:
                    prop = attribute
                else:
                    prop = entry['prop']
                if 'default' in entry:
                    default = entry['default']
                else:
                    try:
                        if entry['type'] == 'int' or entry['type'] == 'float':
                            default = 0
                        elif entry['type'] == 'list':
                            default = []
                        else:
                            raise
                    except:
                        default = ''
                if 'delegate' in entry: 
                    entry['hook'] = self.make_hook('get_prop_delegate', prop, default, entry['delegate'], entry.setdefault('as', None))
                else:
                    if 'depythonize' in entry:
                        func = entry['depythonize']
                        if callable(func):
                            entry['hook'] = self.make_hook('get_prop_depythonize', prop, default, func, None)
                        else:
                            entry['hook'] = self.make_hook('get_prop_depythonize_notcallable', prop, default, func, None)
                    elif 'fulldepythonize' in entry:
                        func = entry['fulldepythonize']
                        entry['hook'] = self.make_hook('get_prop_full_depythonize', prop, default, func, None)
                        entry['hooktype'] = 'depythonize'
                    else:
                        entry['hook'] = self.make_hook('get_prop', prop, default, None, None)
            # This hack is ugly, i should be beaten up for it. But whithout it
            # mapping of Downtime.host_name would not work if it's a
            # host downtime. It cannot automatically be delegated to ref,
            # because autom. delegation assumes ref is a Host then, so
            # service_description would not work.
            # So the request will be delegated to a host, but with the full
            # property "host_name" which is only possible with the 
            # following code.
            if objtype == 'Host':
                attributes = LiveStatus.out_map[objtype].keys()
                for attribute in attributes:
                    LiveStatus.out_map[objtype]['host_' + attribute] =  LiveStatus.out_map[objtype][attribute]
                    

    def create_out_map_delegates(self):
        """Add delegate keys for certain attributes.
        
        Some attributes are not directly reachable via prop or
        need a complicated depythonize function.
        Example: Logline (the objects created for a "GET log" request
        have the column current_host_state. The Logline object does
        not have an attribute of this name, but a log_host attribute.
        The Host object represented by log_host has an attribute state
        which is the desired current_host_state. Because it's the same
        for all columns starting with current_host, a rule can
        be applied that automatically redirects the resolving to the
        corresponding object. Instead of creating a complicated
        depythonize handler which gets log_host and then state, two new
        keys for Logline/current_host_state are added:
        delegate = log_host
        as = state
        This instructs the hook function to first get attribute state of
        the object represented by log_host.
        
        """
        delegate_map = {
            'Logline' : {
                'current_service_' : 'log_service',
                'current_host_' : 'log_host',
            },
            'Service' : {
                'host_' : 'host',
            },
            'Comment' : {
                'service_' : 'ref',
                'host_' : 'ref',
            },
            'Downtime' : {
                'service_' : 'ref',
                'host_' : 'ref',
            }
        }
        for objtype in LiveStatus.out_map:
            for attribute in LiveStatus.out_map[objtype]:
                entry =  LiveStatus.out_map[objtype][attribute]
                if objtype in delegate_map:
                    for prefix in delegate_map[objtype]:
                        if attribute.startswith(prefix):
                            if 'delegate' not in entry:
                                entry['delegate'] = delegate_map[objtype][prefix]
                                entry['as'] = attribute.replace(prefix, '')




    def count_event(self, counter):
        self.counters.increment(counter)



class LiveStatusResponse:
    
    """A class which represents the response to a livestatus request.
    
    Public functions:
    respond -- Add a header to the response text
    format_live_data -- Take the raw output and format it according to
    the desired output format (csv or json)
    
    """
    
    def __init__(self, responseheader = 'off', outputformat = 'csv', keepalive = 'off', columnheaders = 'off', separators = LiveStatus.separators):
        self.responseheader = responseheader
        self.outputformat = outputformat
        self.keepalive = keepalive
        self.columnheaders = columnheaders
        self.separators = separators
        self.output = ''
        pass


    def __str__(self):
        output = "LiveStatusResponse:\n"
        for attr in ["responseheader", "outputformat", "keepalive", "columnheaders", "separators"]:
            output += "response %s: %s\n" % (attr, getattr(self, attr))
        return output


    def respond(self):
        self.output += '\n'
        if self.responseheader == 'fixed16':
            statuscode = 200 
            responselength = len(self.output)
            self.output = '%3d %11d\n' % (statuscode, responselength) + self.output

        return self.output, self.keepalive


    def format_live_data(self, result, columns, aliases):
        lines = []
        header = ''
        showheader = False
        #print "my result is", result
        print "outputformat", self.outputformat
        if len(result) > 0:
            if self.columnheaders != 'off' or len(columns) == 0:
                if len(aliases) > 0:
                    showheader = True
                else:
                    showheader = True
                    if len(columns) == 0:
                        # Show all available columns
                        columns = sorted(result[0].keys())
        elif self.columnheaders == 'on':
            showheader = True
        if self.outputformat == 'csv':
            for object in result:
                # Construct one line of output for each object found
                l = []
                for x in [object[c] for c in columns]:
                    if isinstance(x, list):
                        l.append(self.separators[2].join(str(y) for y in x))
                    else:
                        l.append(str(x))
                lines.append(self.separators[1].join(l))
            if showheader:
                if len(aliases) > 0:
                    # This is for statements like "Stats: .... as alias_column
                    lines.insert(0, self.separators[1].join([aliases[col] for col in columns]))
                else:
                    lines.insert(0, self.separators[1].join(columns))
            self.output = self.separators[0].join(lines)
        elif self.outputformat == 'json' or self.outputformat == 'python':
            for object in result:
                lines.append([object[c] for c in columns])
            if self.columnheaders == 'on':
                if len(aliases) > 0:
                    lines.insert(0, [str(aliases[col]) for col in columns])
                else:
                    lines.insert(0, columns)
            if self.outputformat == 'json':
                self.output = json.dumps(lines, separators=(',', ':'))
            else:
                print "type is ", type(self)
                self.output = str(json.loads(json.dumps(lines, separators=(',', ':'))))


class LiveStatusConstraints:
    """ Represent the constraints applied on a livestatus request """
    def __init__(self, filter_func, out_map, filter_map, output_map, without_filter):
        self.filter_func = filter_func
        self.out_map = out_map
        self.filter_map = filter_map
        self.output_map = output_map
        self.without_filter = without_filter


class LiveStatusRequest(LiveStatus):    
   
    """A class describing a livestatus request."""
    
    def __init__(self, data, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, pollers, reactionners, brokers, dbconn, pnp_path, return_queue, counters):
        self.data = data
        # Runtime data form the global LiveStatus object
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.schedulers = schedulers
        self.pollers = pollers
        self.reactionners = reactionners
        self.brokers = brokers
        self.dbconn = dbconn
        self.pnp_path = pnp_path
        self.return_queue = return_queue
        self.counters = counters

        self.queries = []
        # Set a timestamp for this specific request
        self.tic = time.time()


    def parse_input(self, data):
        """Parse the lines of a livestatus request.
        
        This function looks for keywords in input lines and
        sets the attributes of the request object
        
        """
        external_cmds = []
        query_cmds = []
        wait_cmds = []
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space folowing the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if len(line) == 0:
                pass
            elif keyword in ('GET'):
                query_cmds.append(line)
                wait_cmds.append(line)
            elif keyword in ('WaitObject', 'WaitCondition', 'WaitConditionOr', 'WaitConditionAnd', 'WaitTrigger', 'WaitTimeout'):
                wait_cmds.append(line)
            elif keyword in ('COMMAND'):
                external_cmds.append(line)
            else:
                query_cmds.append(line)
        if len(external_cmds) > 0:
            for external_cmd in external_cmds:
                query = LiveStatusCommandQuery(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.return_queue, self.counters)
                query.parse_input(external_cmd)
                self.queries.append(query)
        if len(wait_cmds) > 1:
            query = LiveStatusWaitQuery(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.return_queue, self.counters)
            query.parse_input('\n'.join(wait_cmds))
            self.queries.append(query)
        if len(query_cmds) > 0:
            query = LiveStatusQuery(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.return_queue, self.counters)
            query.parse_input('\n'.join(query_cmds))
            self.queries.append(query)


class LiveStatusQuery(LiveStatus):

    my_type = 'query'

    def __init__(self, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, pollers, reactionners, brokers, dbconn, pnp_path, return_queue, counters):
        # Runtime data form the global LiveStatus object
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.schedulers = schedulers
        self.pollers = pollers
        self.reactionners = reactionners
        self.brokers = brokers
        self.dbconn = dbconn
        self.pnp_path = pnp_path
        self.return_queue = return_queue
        self.counters = counters

        # Private attributes for this specific request
        self.response = LiveStatusResponse(responseheader = 'off', outputformat = 'csv', keepalive = 'off', columnheaders = 'undef', separators = LiveStatus.separators)
        self.table = None
        self.columns = []
        self.filtercolumns = []
        self.prefiltercolumns = []
        self.stats_group_by = []
        self.stats_columns = []
        self.aliases = []
        self.limit = None
        self.extcmd = False
        self.out_map = self.copy_out_map_hooks()

        # Initialize the stacks which are needed for the Filter: and Stats:
        # filter- and count-operations
        self.filter_stack = LiveStatusStack()
        self.sql_filter_stack = LiveStatusStack()
        self.sql_filter_stack.type = 'sql'
        self.stats_filter_stack = LiveStatusStack()
        self.stats_postprocess_stack = LiveStatusStack()
        self.stats_request = False

        # When was this query launched?
        self.tic = time.time()
        # Clients can also send their local time with the request
        self.client_localtime = self.tic


    def find_converter(self, attribute):
        """Return a function that converts textual numbers
        in the request to the correct data type"""
        out_map = LiveStatus.out_map[self.out_map_name]
        if attribute in out_map and 'type' in out_map[attribute]:
            if out_map[attribute]['type'] == 'int':
                return int
            elif out_map[attribute]['type'] == 'float':
                return float
        return None


    def set_default_out_map_name(self):
        """Translate the table name to the corresponding out_map key."""
        try:
            self.out_map_name = {
                'hosts' : 'Host',
                'services' : 'Service',
                'hostgroups' : 'Hostgroup',
                'servicegroups' : 'Servicegroup',
                'contacts' : 'Contact',
                'contactgroups' : 'Contactgroup',
                'comments' : 'Comment',
                'downtimes' : 'Downtime',
                'commands' : 'Command',
                'timeperiods' : 'Timeperiod',
                'hostsbygroup' : 'Hostsbygroup',
                'servicesbygroup' : 'Servicesbygroup',
                'servicesbyhostgroup' : 'Servicesbyhostgroup',
                'status' : 'Config',
                'log' : 'Logline',
                'schedulers' : 'SchedulerLink',
                'pollers' : 'PollerLink',
                'reactionners' : 'ReactionnerLink',
                'brokers' : 'BrokerLink',
                'problems' : 'Problem',
                'columns' : 'Config', # just a dummy
            }[self.table]
        except:
            self.out_map_name = 'hosts'


    def copy_out_map_hooks(self):
        """Update the hooks for some out_map entries.
        
        Livestatus columns which have a fulldepythonize postprocessor
        need an updated argument list. The third argument needs to
        be the request object. (When the out_map is first supplied
        with hooks, the third argument is the Livestatus object.)
        
        """
        new_map = {}
        for objtype in LiveStatus.out_map:
            new_map[objtype] = {}
            for attribute in LiveStatus.out_map[objtype]:
                new_map[objtype][attribute] = {}
                entry =  LiveStatus.out_map[objtype][attribute]
                if 'hooktype' in entry:
                    if 'prop' not in entry or entry['prop'] is None:
                        prop = attribute
                    else:
                        prop = entry['prop']
                    if 'default' in entry:
                        default = entry['default']
                    else:
                        if entry['type'] == 'int' or entry['type'] == 'float':
                            default = 0
                        else:
                            default = ''
                    func = entry['fulldepythonize']
                    new_map[objtype][attribute]['hook'] = self.make_hook('get_prop_full_depythonize', prop, default, func, None)
                else:
                    new_map[objtype][attribute]['hook'] = entry['hook']
        return new_map


    def __str__(self):
        output = "LiveStatusRequest:\n"
        for attr in ["table", "columns", "filtercolumns", "prefiltercolumns", "aliases", "stats_group_by", "stats_request"]:
            output += "request %s: %s\n" % (attr, getattr(self, attr))
        return output
  

    def split_command(self, line, splits=1):
        """Create a list from the words of a line"""
        return line.split(' ', splits)


    def split_option(self, line, splits=1):
        """Like split_commands, but converts numbers to int data type"""
        #x = [int(i) if i.isdigit() else i for i in [token.strip() for token in re.split(r"[\s]+", line, splits)]]
        x = map (lambda i: (i.isdigit() and int(i)) or i, [token.strip() for token in re.split(r"[\s]+", line, splits)])
        return x


    def split_option_with_columns(self, line):
        """Split a line in a command and a list of words"""
        cmd, columns = self.split_option(line)
        return cmd, [self.strip_table_from_column(c) for c in re.compile(r'\s+').split(columns)]


    def strip_table_from_column(self, column):
        """Cut off the table name, because it is possible 
        to say service_state instead of state"""
        bygroupmatch = re.compile('(\w+)by.*group').search(self.table)
        if bygroupmatch:
            return re.sub(re.sub('s$', '', bygroupmatch.group(1)) + '_', '', column, 1)
        else:
            return re.sub(re.sub('s$', '', self.table) + '_', '', column, 1)


    def parse_input(self, data):
        """Parse the lines of a livestatus request.
        
        This function looks for keywords in input lines and
        sets the attributes of the request object
        
        """
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space folowing the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET': # Get the name of the base table
                cmd, self.table = self.split_command(line)
                self.set_default_out_map_name()
            elif keyword == 'Columns': # Get the names of the desired columns
                cmd, self.columns = self.split_option_with_columns(line)
                self.response.columnheaders = 'off'
            elif keyword == 'ResponseHeader':
                cmd, responseheader = self.split_option(line)
                self.response.responseheader = responseheader
            elif keyword == 'OutputFormat':
                cmd, outputformat = self.split_option(line)
                self.response.outputformat = outputformat
            elif keyword == 'KeepAlive':
                cmd, keepalive = self.split_option(line)
                self.response.keepalive = keepalive
            elif keyword == 'ColumnHeaders':
                cmd, columnheaders = self.split_option(line)
                self.response.columnheaders = columnheaders
            elif keyword == 'Limit':
                cmd, self.limit = self.split_option(line)
            elif keyword == 'Filter':
                try:
                    cmd, attribute, operator, reference = self.split_option(line, 3)
                except:
                    cmd, attribute, operator, reference = self.split_option(line, 2) + ['']
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    # Cut off the table name
                    attribute = self.strip_table_from_column(attribute)
                    # Some operators can simply be negated
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = { '!>' : '<=', '!>=' : '<', '!<' : '>=', '!<=' : '>' }[operator]
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    self.filtercolumns.append(attribute)
                    self.prefiltercolumns.append(attribute)
                    self.filter_stack.put(self.make_filter(operator, attribute, reference))
                    if self.table == 'log':
                        if attribute == 'time':
                            self.sql_filter_stack.put(self.make_sql_filter(operator, attribute, reference))
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif keyword == 'And':
                cmd, andnum = self.split_option(line)
                # Take the last andnum functions from the stack
                # Construct a new function which makes a logical and
                # Put the function back onto the stack
                self.filter_stack.and_elements(andnum)
            elif keyword == 'Or':
                cmd, ornum = self.split_option(line)
                # Take the last ornum functions from the stack
                # Construct a new function which makes a logical or
                # Put the function back onto the stack
                self.filter_stack.or_elements(ornum)
            elif keyword == 'StatsGroupBy':
                cmd, stats_group_by = self.split_option_with_columns(line)
                self.filtercolumns.extend(stats_group_by)
                self.stats_group_by.extend(stats_group_by)
                # Deprecated. If your query contains at least one Stats:-header
                # then Columns: has the meaning of the old StatsGroupBy: header
            elif keyword == 'Stats':
                self.stats_request = True
                try:
                    cmd, attribute, operator, reference = self.split_option(line, 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference.find('as ', 3) != -1:
                        attribute, operator = operator, attribute
                        asas, alias = reference.split(' ')
                        self.aliases.append(alias)
                    elif attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference == '=':
                        # Workaround for thruk-cmds like: Stats: sum latency =
                        attribute, operator = operator, attribute
                        reference = ''
                except:
                    cmd, attribute, operator = self.split_option(line, 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std']:
                        attribute, operator = operator, attribute
                    reference = ''
                attribute = self.strip_table_from_column(attribute)
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = { '!>' : '<=', '!>=' : '<', '!<' : '>=', '!<=' : '>' }[operator]
                    self.filtercolumns.append(attribute)
                    self.stats_columns.append(attribute)
                    self.stats_filter_stack.put(self.make_filter(operator, attribute, reference))
                    self.stats_postprocess_stack.put(self.make_filter('count', attribute, None))
                elif operator in ['sum', 'min', 'max', 'avg', 'std']:
                    self.stats_columns.append(attribute)
                    self.stats_filter_stack.put(self.make_filter('dummy', attribute, None))
                    self.stats_postprocess_stack.put(self.make_filter(operator, attribute, None))
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif keyword == 'StatsAnd':
                cmd, andnum = self.split_option(line)
                self.stats_filter_stack.and_elements(andnum)
            elif keyword == 'StatsOr':
                cmd, ornum = self.split_option(line)
                self.stats_filter_stack.or_elements(ornum)
            elif keyword == 'Separators':
                cmd, sep1, sep2, sep3, sep4 = line.split(' ', 5)
                self.response.separators = map(lambda x: chr(int(x)), [sep1, sep2, sep3, sep4])
            elif keyword == 'Localtime':
                cmd, self.client_localtime = self.split_option(line)
            elif keyword == 'COMMAND':
                cmd, self.extcmd = line.split(' ', 1)
            else:
                # This line is not valid or not implemented
                print "Received a line of input which i can't handle : '%s'" % line
                pass


    def launch_query(self):
        """ Prepare the request object's filter stacks """
        
        # A minimal integrity check
        if not self.table:
            return []

        # Make columns unique
        self.filtercolumns = list(set(self.filtercolumns))
        self.prefiltercolumns = list(set(self.prefiltercolumns))
        self.stats_columns = list(set(self.stats_columns))

        if self.stats_request:
            if len(self.columns) > 0:
                # StatsGroupBy is deprecated. Columns: can be used instead
                self.stats_group_by = self.columns
            elif len(self.stats_group_by) > 0:
                self.columns = self.stats_group_by + self.stats_columns
            #if len(self.stats_columns) > 0 and len(self.columns) == 0:
            if len(self.stats_columns) > 0:
                self.columns = self.stats_columns + self.columns

        # Make one big filter where the single filters are anded
        self.filter_stack.and_elements(self.filter_stack.qsize())
        try:
            # Remember the number of stats filters. We need these numbers as columns later.
            # But we need to ask now, because get_live_data() will empty the stack
            num_stats_filters = self.stats_filter_stack.qsize()
            if self.table == 'log':
                self.sql_filter_stack.and_elements(self.sql_filter_stack.qsize())
                result = self.get_live_data_log()
            else:
                # If the pnpgraph_present column is involved, then check
                # with each request if the pnp perfdata path exists
                if 'pnpgraph_present' in self.columns + self.filtercolumns + self.prefiltercolumns and self.pnp_path and os.access(self.pnp_path, os.R_OK):
                    self.pnp_path_readable = True
                else:
                    self.pnp_path_readable = False
                # Apply the filters on the broker's host/service/etc elements
          
                result = self.get_live_data()
                
            if self.stats_request:
                self.columns = range(num_stats_filters)
                if self.stats_group_by:
                    self.columns = tuple(list(self.stats_group_by) + list(self.columns))
                if len(self.aliases) == 0:
                    #If there were Stats: staments without "as", show no column headers at all
                    self.response.columnheaders = 'off'
                else:
                    self.response.columnheaders = 'on'

        except Exception, e:
            import traceback
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print e
            traceback.print_exc(32) 
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            result = []
        
        return result

    
    def get_hosts_or_services_livedata(self, cs):
        objects = getattr(self, self.table)
        if cs.without_filter and not self.limit:
            # Simply format the output
            return [self.create_output(cs.output_map, x) for x in objects.itervalues()]
        elif cs.without_filter and self.limit:
            # Simply format the output of a subset of the objects
            return [self.create_output(cs.output_map, x) for x in objects.values()[:self.limit]]
        else:
            # Filter the objects and format the output. At least hosts
            # and services are already sorted by name.
            return [
                self.create_output(cs.output_map, y) for y in (
                    x for x in objects.itervalues() 
                    if cs.without_filter or cs.filter_func(self.create_output(cs.filter_map, x)))
            ]

    
    def get_hosts_livedata(self, cs):
        return self.get_hosts_or_services_livedata(cs)
    

    def get_services_livedata(self, cs):
        return self.get_hosts_or_services_livedata(cs)


    def get_simple_livedata(self, cs):
        objects = getattr(self, self.table)
        return [ self.create_output(cs.output_map, obj) for obj in objects.values() ]


    def get_filtered_livedata(self, cs):
        objects = getattr(self, self.table).values()
        if cs.without_filter:
            return [ y for y in [ self.create_output(cs.output_map, x) for x in objects ] if cs.filter_func(y) ]
        res = [ x for x in objects if cs.filter_func(self.create_output(cs.filter_map, x)) ]
        return [ self.create_output(cs.output_map, x) for x in res ]


    def get_list_livedata(self, cs):
        t = self.table
        if cs.without_filter:
            res = [ self.create_output(cs.output_map, y) for y in 
                        reduce(list.__add__
                            , [ getattr(x, t) for x in self.services.values() + self.hosts.values()
                                    if len(getattr(x, t)) > 0 ]
                            , [])
            ]
        else:
            res = [ c for c in reduce(list.__add__
                        , [ getattr(x, t) for x in self.services.values() + self.hosts.values() 
                                if len(getattr(x, t)) > 0]
                        , []
                        )
                    if cs.filter_func(self.create_output(cs.filter_map, c)) ]
            res = [ self.create_output(cs.output_map, x) for x in res ]
        return res
    
    
    def get_group_livedata(self, cs, objs, an, group_key, member_key):
        """ return a list of elements from a "group" of 'objs'. group can be a hostgroup or a servicegroup.
objs: the objects to get elements from.
an: the attribute name to set on result.
group_key: the key to be used to sort the group members.
member_key: the key to be used to sort each resulting element of a group member. """
        return [ self.create_output(cs.output_map, x) for x in (
                    svc for svc in (
                        setattr(og[0], an, og[1]) or og[0] for og in (
                            ( copy.copy(item0), inner_list0[1]) for inner_list0 in (
                                (sorted(sg1.members, key = member_key), sg1) for sg1 in
                                    sorted([sg0 for sg0 in objs if sg0.members], key = group_key)
                                ) for item0 in inner_list0[0]
                            )
                        ) if (cs.without_filter or cs.filter_func(self.create_output(cs.filter_map, svc))))
        ]


    def get_hostbygroups_livedata(self, cs):
        member_key = lambda k: k.host_name
        group_key = lambda k: k.hostgroup_name
        return self.get_group_livedata(cs, self.hostgroups.values(), 'hostgroup', group_key, member_key)        


    def get_servicebygroups_livedata(self, cs):
        member_key = lambda k: k.get_name()
        group_key = lambda k: k.servicegroup_name
        return self.get_group_livedata(cs, self.servicegroups.values(), 'servicegroup', group_key, member_key)
    

    def get_problem_livedata(self, cs):
        # We will crate a problems list first with all problems and source in it
        # TODO : create with filter
        problems = []
        for h in self.hosts.values():
            if h.is_problem:
                pb = Problem(h, h.impacts)
                problems.append(pb)
        for s in self.services.values():
            if s.is_problem:
                pb = Problem(s, s.impacts)
                problems.append(pb)
        # Then return
        return [ self.create_output(cs.output_map, pb) for pb in problems ]


    def get_status_livedata(self, cs):
        cs.out_map = self.out_map['Config']
        return [ self.create_output(cs.output_map, c) for c in self.configs.values() ]


    def get_columns_livedata(self, cs):
        result = []
        result.append({
            'description' : 'A description of the column' , 'name' : 'description' , 'table' : 'columns' , 'type' : 'string' })
        result.append({
            'description' : 'The name of the column within the table' , 'name' : 'name' , 'table' : 'columns' , 'type' : 'string' })
        result.append({
            'description' : 'The name of the table' , 'name' : 'table' , 'table' : 'columns' , 'type' : 'string' })
        result.append({
            'description' : 'The data type of the column (int, float, string, list)' , 'name' : 'type' , 'table' : 'columns' , 'type' : 'string' })
        tablenames = { 'Host' : 'hosts', 'Service' : 'services', 'Hostgroup' : 'hostgroups', 'Servicegroup' : 'servicegroups', 'Contact' : 'contacts', 'Contactgroup' : 'contactgroups', 'Command' : 'commands', 'Downtime' : 'downtimes', 'Comment' : 'comments', 'Timeperiod' : 'timeperiods', 'Config' : 'status', 'Logline' : 'log', 'Statsbygroup' : 'statsgroupby', 'Hostsbygroup' : 'hostsbygroup', 'Servicesbygroup' : 'servicesbygroup', 'Servicesbyhostgroup' : 'servicesbyhostgroup' }
        for obj in sorted(LiveStatus.out_map, key=lambda x: x):
            if obj in tablenames:
                for attr in LiveStatus.out_map[obj]:
                    if 'description' in LiveStatus.out_map[obj][attr] and LiveStatus.out_map[obj][attr]['description']:
                        result.append({ 'description' : LiveStatus.out_map[obj][attr]['description'], 'name' : attr, 'table' : tablenames[obj], 'type' : LiveStatus.out_map[obj][attr]['type'] })
                    else:
                        result.append({'description' : 'to_do_desc', 'name' : attr, 'table' : tablenames[obj], 'type' : LiveStatus.out_map[obj][attr]['type'] })
        return result


    def get_servicebyhostgroups_livedata(self, cs):
        # to test..
        res = [ self.create_output(cs.output_map, x) for x in (
                svc for svc in (
                    setattr(svchgrp[0], 'hostgroup', svchgrp[1]) or svchgrp[0] for svchgrp in (
                        # (service, hostgroup), (service, hostgroup), (service, hostgroup), ...  service objects are individuals
                        (copy.copy(item1), inner_list1[1]) for inner_list1 in (
                            # ([service, service, ...], hostgroup), ([service, ...], hostgroup), ...  flattened by host. only if a host has services. sorted by service_description
                            (sorted(item0.services, key = lambda k: k.service_description), inner_list0[1]) for inner_list0 in (
                                # ([host, host, ...], hostgroup), ([host, host, host, ...], hostgroup), ...  sorted by host_name
                                (sorted(hg1.members, key = lambda k: k.host_name), hg1) for hg1 in   # ([host, host], hg), ([host], hg),... hostgroup.members->explode->sort
                                    # hostgroups, sorted by hostgroup_name
                                    sorted([hg0 for hg0 in self.hostgroups.values() if hg0.members], key = lambda k: k.hostgroup_name)
                            ) for item0 in inner_list0[0] if item0.services
                        ) for item1 in inner_list1[0]
                    )
                ) if (cs.without_filter or cs.filter_func(self.create_output(cs.filter_map, svc)))
            )]
        return res

    objects_get_handlers = {
        'hosts':                get_hosts_livedata,
        'services':             get_services_livedata,
        'commands':             get_filtered_livedata,
        'schedulers':           get_simple_livedata,
        'brokers':              get_simple_livedata,
        'pollers':              get_simple_livedata,
        'reactionners':         get_simple_livedata,
        'contacts':             get_filtered_livedata,
        'contactgroups':        get_filtered_livedata,
        'hostgroups':           get_filtered_livedata,
        'servicegroups':        get_filtered_livedata,
        'timeperiods':          get_filtered_livedata,
        'downtimes':            get_list_livedata,
        'comments':             get_list_livedata,
        'hostsbygroup':         get_hostbygroups_livedata,
        'servicesbygroup':      get_servicebygroups_livedata,
        'problems':             get_problem_livedata,
        'status':               get_status_livedata,
        'columns':              get_columns_livedata,
        'servicesbyhostgroup':  get_servicebyhostgroups_livedata
    }


    def get_live_data(self):
        """Find the objects which match the request.
        
        This function scans a list of objects (hosts, services, etc.) and
        applies the filter functions first. The remaining objects are
        converted to simple dicts which have only the keys that were
        requested through Column: attributes. """
        # We will use prefiltercolumns here for some serious speedup.
        # For example, if nagvis wants Filter: host_groups >= hgxy
        # we don't have to use the while list of hostgroups in
        # the innermost loop
        # Filter: host_groups >= linux-servers
        # host_groups is a service attribute
        # We can get all services of all hosts of all hostgroups and filter at the end
        # But it would save a lot of time to already filter the hostgroups. This means host_groups must be hard-coded
        # Also host_name, but then we must filter the second step.
        # And a mixture host_groups/host_name with FilterAnd/Or? Must have several filter functions
        
        handler = self.objects_get_handlers.get(self.table, None)
        if not handler:
            print("Got unhandled table: %s" % (self.table))
            return []
        
        # Get the function which implements the Filter: statements
        filter_func     = self.filter_stack.get_stack()
        out_map         = self.out_map[self.out_map_name]
        filter_map      = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map      = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter  = len(self.filtercolumns) == 0
    
        cs = LiveStatusConstraints(filter_func, out_map, filter_map, output_map, without_filter)
        res = handler(self, cs)

        if self.limit:
            res = res[:self.limit]
            
        if self.stats_request:
            res = self.statsify_result(res)
        
        return res


    def get_live_data_log(self):
        """Like get_live_data, but for log objects"""
        filter_func = self.filter_stack.get_stack()
        sql_filter_func = self.sql_filter_stack.get_stack()
        out_map = self.out_map[self.out_map_name]
        filter_map = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter = len(self.filtercolumns) == 0
        result = []
        if self.table == 'log':
            out_map = self.out_map['Logline']
            # We can apply the filterstack here as well. we have columns and filtercolumns.
            # the only additional step is to enrich log lines with host/service-attributes
            # A timerange can be useful for a faster preselection of lines
            filter_clause, filter_values = sql_filter_func()
            c = self.dbconn.cursor()
            try:
                if sqlite3.paramstyle == 'pyformat':
                    matchcount = 0
                    for m in re.finditer(r"\?", filter_clause):
                        filter_clause = re.sub('\\?', '%(' + str(matchcount) + ')s', filter_clause, 1)
                        matchcount += 1
                    filter_values = dict(zip([str(x) for x in xrange(len(filter_values))], filter_values))
                c.execute('SELECT * FROM logs WHERE %s' % filter_clause, filter_values)
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]
            dbresult = c.fetchall()
            if sqlite3.paramstyle == 'pyformat':
                dbresult = [self.row_factory(c, d) for d in dbresult]

            prefiltresult = [y for y in (x.fill(self.hosts, self.services, set(self.columns + self.filtercolumns)) for x in dbresult) if (without_filter or filter_func(self.create_output(filter_map, y)))]
            filtresult = [self.create_output(output_map, x) for x in prefiltresult]
            if self.stats_request:
                result = self.statsify_result(filtresult)
            else:
                # Results are host/service/etc dicts with the requested attributes
                # Columns: = keys of the dicts
                result = filtresult

        #print "result is", result
        return result


    def create_output(self, out_map, elt):
        """Convert an object to a dict with selected keys.""" 
        output = {} 
        display_attributes = out_map.keys()
        for display in display_attributes:
            try:
                hook = out_map[display]['hook']
                value = hook(elt)
            except:
                value = ''
            output[display] = value
        return output


    def statsify_result(self, filtresult):
        """Applies the stats filter functions to the result.
        
        Explanation:
        stats_group_by is ["service_description", "host_name"]
        filtresult is a list of elements which have, among others, service_description and host_name attributes

        Step 1:
        groupedresult is a dict where the keys are unique combinations of the stats_group_by attributes
                                where the values are arrays of elements which have those attributes in common
        Example:
            groupedresult[("host1","svc1")] = { host_name : "host1", service_description : "svc1", state : 2, in_downtime : 0 }
            groupedresult[("host1","svc2")] = { host_name : "host1", service_description : "svc2", state : 0, in_downtime : 0 }
            groupedresult[("host1","svc2")] = { host_name : "host1", service_description : "svc2", state : 1, in_downtime : 1 }

        resultdict is a dict where the keys are unique combinations of the stats_group_by attributes
                            where the values are dicts
        resultdict values are dicts where the keys are attribute names from stats_group_by
                                   where the values are attribute values
        Example:
            resultdict[("host1","svc1")] = { host_name : "host1", service_description : "svc1" }
            resultdict[("host1","svc2")] = { host_name : "host1", service_description : "svc2" }
        These attributes are later used as output columns

        Step 2:
        Run the filters (1 filter for each Stats: statement) and the postprocessors (default: len)
        The filters are numbered. After each run, add the result to resultdictay as <filterno> : <result>
        Example for Stats: state = 0\nStats: state = 1\nStats: state = 2\nStats: state = 3\n
            resultdict[("host1","svc1")] = { host_name : "host1", service_description : "svc1", 0 : 0, 1 : 0, 2 : 1, 3 : 0 }
            resultdict[("host1","svc2")] = { host_name : "host1", service_description : "svc2", 0 : 1, 1 : 1, 2 : 0, 3 : 0 }

        Step 3:
        Create the final result array from resultdict
        
        """
        result = []
        resultdict = {}
        if self.stats_group_by:
            # stats_group_by is a list in newer implementations
            if isinstance(self.stats_group_by, list):
                self.stats_group_by = tuple(self.stats_group_by)
            else:
                self.stats_group_by = tuple([self.stats_group_by])
            # Break up filtresult and prepare resultdict
            # rseultarr is not a simple array (for a single result line)
            # It is a dict with the statsgroupyby: as key
            groupedresult = {}
            for elem in filtresult:
                # Make a tuple consisting of the stats_group_by values
                stats_group_by_values = tuple([elem[c] for c in self.stats_group_by])
                if not stats_group_by_values in groupedresult:
                    groupedresult[stats_group_by_values] = []
                groupedresult[stats_group_by_values].append(elem)
            for group in groupedresult:
                # All possible combinations of stats_group_by values. group is a tuple
                resultdict[group] = dict(zip(self.stats_group_by, group))

        #The number of Stats: statements
        #For each statement there is one function on the stack
        maxidx = self.stats_filter_stack.qsize()
        for i in range(maxidx):
            # Stats:-statements were put on a Lifo, so we need to reverse the number
            #stats_number = str(maxidx - i - 1)
            stats_number = maxidx - i - 1
            # First, get a filter for the attributes mentioned in Stats: statements
            filtfunc = self.stats_filter_stack.get()
            # Then, postprocess (sum, max, min,...) the results
            postprocess = self.stats_postprocess_stack.get()
            if self.stats_group_by:
                # Calc statistics over _all_ elements of groups
                # which share the same stats_filter_by
                for group in groupedresult:
                    resultdict[group][stats_number] = postprocess(filter(filtfunc, groupedresult[group]))
            else:
                # Calc statistics over _all_ elements of filtresult
                resultdict[stats_number] = postprocess(filter(filtfunc, filtresult))
        if self.stats_group_by:
            for group in resultdict:
                result.append(resultdict[group])
        else:
            # Without StatsGroupBy: we have only one line
            result = [resultdict]
        return result


    def make_filter(self, operator, attribute, reference):
        if reference is not None:
            # Reference is now datatype string. The referring object attribute on the other hand
            # may be an integer. (current_attempt for example)
            # So for the filter to work correctly (the two values compared must be
            # of the same type), we need to convert the reference to the desired type
            converter = self.find_converter(attribute)
            if converter:
                reference = converter(reference)

        # The filters are closures.
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
            if ref != []:
                return max(float(obj[attribute]) for obj in ref)
            return 0

        def min_postproc(ref):
            if ref != []:
                return min(float(obj[attribute]) for obj in ref)
            return 0

        def avg_postproc(ref):
            if ref != []:
                return sum(float(obj[attribute]) for obj in ref) / len(ref)
            return 0

        def std_postproc(ref):
            return 0

        if operator == '=':
            return eq_filter
        elif operator == '!=':
            return ne_filter
        elif operator == '>':
            return gt_filter
        elif operator == '>=':
            return ge_contains_filter
        elif operator == '<':
            return lt_filter
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


    def make_sql_filter(self, operator, attribute, reference):
        # The filters are text fragments which are put together to form a sql where-condition finally.
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
        def gt_filter():
            return ['%s > ?' % attribute, (reference, )]
        def ge_filter(): 
            return ['%s >= ?' % attribute, (reference, )]
        def lt_filter():
            return ['%s < ?' % attribute, (reference, )]
        def le_filter():
            return ['%s <= ?' % attribute, (reference, )]
        def match_filter():
            return ['%s LIKE ?' % attribute, ('%'+reference+'%', )]
        if operator == '=':
            return eq_filter
        if operator == '>':
            return gt_filter
        if operator == '>=':
            return ge_filter
        if operator == '<':
            return lt_filter
        if operator == '<=':
            return le_filter
        if operator == '!=':
            return ne_filter
        if operator == '~':
            return match_filter


class LiveStatusWaitQuery(LiveStatusQuery):

    my_type = 'wait'

    def __init__(self, *args, **kwargs):
        super(LiveStatusWaitQuery, self).__init__(*args, **kwargs)
        self.response = LiveStatusResponse(responseheader = 'off', outputformat = 'csv', keepalive = 'off', columnheaders = 'off', separators = LiveStatus.separators)
        self.wait_start = time.time()
        self.wait_timeout = 0
        self.wait_trigger = 'all'


    def parse_input(self, data):
        """Parse the lines of a livestatus request.
        
        This function looks for keywords in input lines and
        sets the attributes of the request object
        
        """
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space folowing the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET': # Get the name of the base table
                cmd, self.table = self.split_command(line)
                self.set_default_out_map_name()
            elif keyword == 'WaitObject': # Pick a specific object by name
                cmd, object = self.split_option(line)
                # It's like Filter: name = %s
                # Only for services it's host<blank>servicedesc
                if self.table == 'services':
                    host_name, service_description = object.split(' ', 1)
                    self.filtercolumns.append('host_name')
                    self.prefiltercolumns.append('host_name')
                    self.filter_stack.put(self.make_filter('=', 'host_name', host_name))
                    self.filtercolumns.append('description')
                    self.prefiltercolumns.append('description')
                    self.filter_stack.put(self.make_filter('=', 'description', service_description))
                    try:
                        # A WaitQuery works like an ordinary Query. But if
                        # we already know which object we're watching for
                        # changes, instead of scanning the entire list and
                        # applying a Filter:, we simply reduce the list
                        # so it has just one element.
                        self.services = { host_name + service_description : self.services[host_name + service_description] }
                    except:
                        pass
                elif self.table == 'hosts':
                    attribute = self.strip_table_from_column('name')
                    self.filtercolumns.append('name')
                    self.prefiltercolumns.append('name')
                    self.filter_stack.put(self.make_filter('=', 'name', object))
                    try:
                        self.hosts = { host_name : self.hosts[host_name] }
                    except:
                        pass
                else:
                    attribute = self.strip_table_from_column('name')
                    self.filtercolumns.append('name')
                    self.prefiltercolumns.append('name')
                    self.filter_stack.put(self.make_filter('=', 'name', object))
                    # For the other tables this works like an ordinary query.
                    # In the future there might be more lookup-tables
            elif keyword == 'WaitTrigger':
                cmd, self.wait_trigger = self.split_option(line)
                if self.wait_trigger not in ['check', 'state', 'log', 'downtime', 'comment', 'command']:
                    self.wait_trigger = 'all'
            elif keyword == 'WaitCondition':
                try:
                    cmd, attribute, operator, reference = self.split_option(line, 3)
                except:
                    cmd, attribute, operator, reference = self.split_option(line, 2) + ['']
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    # We need to set columns, if not columnheaders will be set to "on"
                    self.columns.append(attribute)
                    # Cut off the table name
                    attribute = self.strip_table_from_column(attribute)
                    # Some operators can simply be negated
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = { '!>' : '<=', '!>=' : '<', '!<' : '>=', '!<=' : '>' }[operator]
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    self.filtercolumns.append(attribute)
                    self.prefiltercolumns.append(attribute)
                    self.filter_stack.put(self.make_filter(operator, attribute, reference))
                    if self.table == 'log':
                        if attribute == 'time':
                            self.sql_filter_stack.put(self.make_sql_filter(operator, attribute, reference))
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif keyword == 'WaitConditionAnd':
                cmd, andnum = self.split_option(line)
                # Take the last andnum functions from the stack
                # Construct a new function which makes a logical and
                # Put the function back onto the stack
                self.filter_stack.and_elements(andnum)
            elif keyword == 'WaitConditionOr':
                cmd, ornum = self.split_option(line)
                # Take the last ornum functions from the stack
                # Construct a new function which makes a logical or
                # Put the function back onto the stack
                self.filter_stack.or_elements(ornum)
            elif keyword == 'WaitTimeout':
                cmd, self.wait_timeout = self.split_option(line)
                self.wait_timeout = int(self.wait_timeout) / 1000
            else:
                # This line is not valid or not implemented
                print "Received a line of input which i can't handle : '%s'" % line
                pass
        # Make columns unique
        self.filtercolumns = list(set(self.filtercolumns))
        self.prefiltercolumns = list(set(self.prefiltercolumns))

        # Make one big filter where the single filters are anded
        self.filter_stack.and_elements(self.filter_stack.qsize())

        if self.table == 'log':
            self.sql_filter_stack.and_elements(self.sql_filter_stack.qsize())


    def launch_query(self):
        """ Prepare the request object's filter stacks """
        
        print "."
        # A minimal integrity check
        if not self.table:
            return []

        try:
            # Remember the number of stats filters. We need these numbers as columns later.
            # But we need to ask now, because get_live_data() will empty the stack
            if self.table == 'log':
                result = self.get_live_data_log()
            else:
                # If the pnpgraph_present column is involved, then check
                # with each request if the pnp perfdata path exists
                if 'pnpgraph_present' in self.columns + self.filtercolumns + self.prefiltercolumns and self.pnp_path and os.access(self.pnp_path, os.R_OK):
                    self.pnp_path_readable = True
                else:
                    self.pnp_path_readable = False
                # Apply the filters on the broker's host/service/etc elements
          
                result = self.get_live_data()
                
        except Exception, e:
            import traceback
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print e
            traceback.print_exc(32) 
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            result = []
        
        return result


    def get_live_data(self):
        """Find the objects which match the request.
        
        This function scans a list of objects (hosts, services, etc.) and
        applies the filter functions first. The remaining objects are
        converted to simple dicts which have only the keys that were
        requested through Column: attributes. """
        # We will use prefiltercolumns here for some serious speedup.
        # For example, if nagvis wants Filter: host_groups >= hgxy
        # we don't have to use the while list of hostgroups in
        # the innermost loop
        # Filter: host_groups >= linux-servers
        # host_groups is a service attribute
        # We can get all services of all hosts of all hostgroups and filter at the end
        # But it would save a lot of time to already filter the hostgroups. This means host_groups must be hard-coded
        # Also host_name, but then we must filter the second step.
        # And a mixture host_groups/host_name with FilterAnd/Or? Must have several filter functions

        handler = self.objects_get_handlers.get(self.table, None)
        if not handler:
            print("Got unhandled table: %s" % (self.table))
            return []

        # Get the function which implements the Filter: statements
        filter_func     = self.filter_stack.get_stack()
        out_map         = self.out_map[self.out_map_name]
        filter_map      = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map      = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter  = len(self.filtercolumns) == 0

        cs = LiveStatusConstraints(filter_func, out_map, filter_map, output_map, without_filter)
        res = handler(self, cs)

        # A LiveStatusWaitQuery is launched several times, so we need to
        # put back the big filter function
        self.filter_stack.put_stack(filter_func)
        return res


    def get_live_data_log(self):
        """Like get_live_data, but for log objects"""
        filter_func = self.filter_stack.get_stack()
        sql_filter_func = self.sql_filter_stack.get_stack()
        out_map = self.out_map[self.out_map_name]
        filter_map = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter = len(self.filtercolumns) == 0
        result = []
        if self.table == 'log':
            out_map = self.out_map['Logline']
            # We can apply the filterstack here as well. we have columns and filtercolumns.
            # the only additional step is to enrich log lines with host/service-attributes
            # A timerange can be useful for a faster preselection of lines
            filter_clause, filter_values = sql_filter_func()
            c = self.dbconn.cursor()
            try:
                if sqlite3.paramstyle == 'pyformat':
                    matchcount = 0
                    for m in re.finditer(r"\?", filter_clause):
                        filter_clause = re.sub('\\?', '%(' + str(matchcount) + ')s', filter_clause, 1)
                        matchcount += 1
                    filter_values = dict(zip([str(x) for x in xrange(len(filter_values))], filter_values))
                c.execute('SELECT * FROM logs WHERE %s' % filter_clause, filter_values)
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]
            dbresult = c.fetchall()
            if sqlite3.paramstyle == 'pyformat':
                dbresult = [self.row_factory(c, d) for d in dbresult]

            prefiltresult = [y for y in (x.fill(self.hosts, self.services, set(self.columns + self.filtercolumns)) for x in dbresult) if (without_filter or filter_func(self.create_output(filter_map, y)))]
            filtresult = [self.create_output(output_map, x) for x in prefiltresult]
            result = filtresult

        self.filter_stack.put_stack(filter_func)
        self.sql_filter_stack.put_stack(sql_filter_func)
        #print "result is", result
        return result


    def condition_fulfilled(self):
         result = self.launch_query()
         response = self.response
         response.format_live_data(result, self.columns, self.aliases)
         output, keepalive = response.respond()
         return output.strip()



class LiveStatusCommandQuery(LiveStatusQuery):

    my_type = 'command'

    def parse_input(self, data):
        """Parse the lines of a livestatus request.
        
        This function looks for keywords in input lines and
        sets the attributes of the request object
        
        """
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space folowing the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'COMMAND':
                cmd, self.extcmd = line.split(' ', 1)
            else:
                # This line is not valid or not implemented
                print "Received a line of input which i can't handle : '%s'" % line
                pass


    def launch_query(self):
        """ Prepare the request object's filter stacks """
        if self.extcmd:
            # External command are send back to broker
            self.extcmd = self.extcmd.decode('utf8', 'replace')
            e = ExternalCommand(self.extcmd)
            self.return_queue.put(e)
            return []



class LiveStatusCounters(LiveStatus):    
    def __init__(self):
        self.counters = {
            'neb_callbacks' : 0,
            'connections' : 0,
            'service_checks' : 0,
            'host_checks' : 0,
            'forks' : 0,
            'log_message' : 0,
            'external_commands' : 0
        }
        self.last_counters = {
            'neb_callbacks' : 0,
            'connections' : 0,
            'service_checks' : 0,
            'host_checks' : 0,
            'forks' : 0,
            'log_message' : 0,
            'external_commands' : 0
        }
        self.rate = {
            'neb_callbacks' : 0.0,
            'connections' : 0.0,
            'service_checks' : 0.0,
            'host_checks' : 0.0,
            'forks' : 0.0,
            'log_message' : 0.0,
            'external_commands' : 0.0
        }
        self.last_update = 0
        self.interval = 10
        self.rating_weight = 0.25

    def increment(self, counter):
        if counter in self.counters:
            self.counters[counter] += 1
   

    def calc_rate(self):
        elapsed = time.time() - self.last_update
        if elapsed > self.interval:
            self.last_update = time.time()
            for counter in self.counters:
                delta = self.counters[counter] - self.last_counters[counter]
                new_rate = delta / elapsed
                if self.rate[counter] == 0:
                    avg_rate = new_rate
                else:
                    avg_rate = self.rate[counter] * (1 - self.rating_weight) + new_rate * self.rating_weight
                self.rate[counter] = avg_rate
                self.last_counters[counter] = self.counters[counter]


    def count(self, counter):
        if counter in self.counters:
            return self.counters[counter]
        elif counter.endswith('_rate'):
            if counter[0:-5] in self.rate:
                return self.rate[counter[0:-5]]
            else:
                return 0.0
        else:
            return 0
