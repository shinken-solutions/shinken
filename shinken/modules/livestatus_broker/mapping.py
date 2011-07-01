

import os

from shinken.bin import VERSION
from shinken.macroresolver import MacroResolver
from shinken.util import from_bool_to_int, from_float_to_int, to_int, to_split, get_customs_keys, get_customs_values



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


def from_svc_hst_distinct_lists(dct):
    """Transform a dict with keys hosts and services to a list."""
    t = []
    for h in dct['hosts']:
        t.append(h)
    for s in dct['services']:
        t.append(s)
    return t



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
