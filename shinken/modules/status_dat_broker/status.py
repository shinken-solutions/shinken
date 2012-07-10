#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


# File for create the status.dat file
import time
import os
import tempfile

from shinken.util import from_bool_to_string


class StatusFile:
    out_map = {
        'Host': {
            'host_name': {}, # 'host_name',
            'modified_attributes': {'prop': None, 'default': '0'},
            'check_command': {'depythonize': 'get_name'},
            'check_period': {'prop': 'check_period', 'depythonize': 'get_name'},
            'notification_period': {'prop': 'notification_period', 'depythonize': 'get_name'},
            'check_interval': {},
            'retry_interval': {},
            'event_handler': {'depythonize': 'get_name', 'default': ''},
            'has_been_checked': {'prop': None, 'default': '0'},
            'should_be_scheduled': {'prop': None, 'default': '0'},
            'check_execution_time': {'prop': 'execution_time', 'default': '0'},
            'check_latency': {'prop': 'latency'},
            'check_type': {'prop': None, 'default': '0'},
            'current_state': {'prop': 'state_id'},
            'last_hard_state': {'prop': None, 'default': '0'},
            'last_event_id': {'prop': None, 'default': '0'},
            'current_event_id': {'prop': None, 'default': '0'},
            'current_problem_id': {'prop': None, 'default': '0'},
            'last_problem_id': {'prop': None, 'default': '0'},
            'plugin_output': {'prop': 'output'},
            'long_plugin_output': {'prop': 'long_output'},
            'performance_data': {'prop': None, 'default': '0'},
            'last_check': {'prop': 'last_chk'},
            'next_check': {'prop': 'next_chk'},
            'check_options': {'prop': None, 'default': '0'},
            'current_attempt': {'prop': 'attempt'},
            'max_attempts': {'prop': 'max_check_attempts'},
            'current_event_id': {'prop': None, 'default': '0'},
            'last_event_id': {'prop': None, 'default': '0'},
            'state_type': {'prop': 'state_type_id', 'default': '0'},
            'last_state_change': {'prop': None, 'default': '0'},
            'last_hard_state_change': {'prop': None, 'default': '0'},
            'last_time_up': {'prop': None, 'default': '0'},
            'last_time_down': {'prop': None, 'default': '0'},
            'last_time_unreachable': {'prop': None, 'default': '0'},
            'last_notification': {'prop': None, 'default': '0'},
            'next_notification': {'prop': None, 'default': '0'},
            'no_more_notifications': {'prop': None, 'default': '0'},
            'current_notification_number': {'prop': None, 'default': '0'},
            'current_notification_id': {'prop': None, 'default': '0'},
            'notifications_enabled': {'depythonize': from_bool_to_string},
            'problem_has_been_acknowledged': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'acknowledgement_type': {'prop': None, 'default': '0'},
            'active_checks_enabled': {'depythonize': from_bool_to_string},
            'passive_checks_enabled': {'depythonize': from_bool_to_string},
            'event_handler_enabled': {'depythonize': from_bool_to_string},
            'flap_detection_enabled': {'depythonize': from_bool_to_string},
            'failure_prediction_enabled': {'depythonize': from_bool_to_string},
            'process_performance_data': {'depythonize': from_bool_to_string},
            'obsess_over_host': {'depythonize': from_bool_to_string},
            'last_update': {'prop': None, 'default': '0'},
            'is_flapping': {'depythonize': from_bool_to_string},
            'percent_state_change': {},
            'scheduled_downtime_depth': {'prop': None, 'default': '0'}
            },
        'Service': {
            'host_name': {},
            'service_description': {},
            'modified_attributes': {'prop': None, 'default': '0'},
            'check_command': {'depythonize': 'get_name'},
            'check_period': {'depythonize': 'get_name'},
            'notification_period': {'depythonize': 'get_name'},
            'check_interval': {},
            'retry_interval': {},
            'event_handler': {'depythonize': 'get_name', 'default': ''},
            'has_been_checked': {'prop': None, 'default': '0'},
            'should_be_scheduled': {'prop': None, 'default': '0'},
            'check_execution_time': {'prop': 'execution_time', 'default': '0'},
            'check_latency': {'prop': 'latency'},
            'check_type': {'prop': None, 'default': '0'},
            'current_state': {'prop': 'state_id'},
            'last_hard_state': {'prop': None, 'default': '0'},
            'last_event_id': {'prop': None, 'default': '0'},
            'current_event_id': {'prop': None, 'default': '0'},
            'current_problem_id': {'prop': None, 'default': '0'},
            'last_problem_id': {'prop': None, 'default': '0'},
            'current_attempt': {'prop': 'attempt'},
            'max_attempts': {'prop': 'max_check_attempts'},
            'current_event_id': {'prop': None, 'default': '0'},
            'last_event_id': {'prop': None, 'default': '0'},
            'state_type': {'prop': 'state_type_id', 'default': '0'},
            'last_state_change': {'prop': None, 'default': '0'},
            'last_hard_state_change': {'prop': None, 'default': '0'},
            'last_time_ok': {'prop': None, 'default': '0'},
            'last_time_warning': {'prop': None, 'default': '0'},
            'last_time_unknown': {'prop': None, 'default': '0'},
            'last_time_critical': {'prop': None, 'default': '0'},
            'plugin_output': {'prop': 'output'},
            'long_plugin_output': {'prop': 'long_output'},
            'performance_data': {'prop': None, 'default': ''},
            'last_check': {'prop': 'last_chk'},
            'next_check': {'prop': 'next_chk'},
            'check_options': {'prop': None, 'default': '0'},
            'current_notification_number': {'prop': None, 'default': '0'},
            'current_notification_id': {'prop': None, 'default': '0'},
            'last_notification': {'prop': None, 'default': '0'},
            'next_notification': {'prop': None, 'default': '0'},
            'no_more_notifications': {'prop': None, 'default': '0'},
            'notifications_enabled': {'depythonize': from_bool_to_string},
            'active_checks_enabled': {'depythonize': from_bool_to_string},
            'passive_checks_enabled': {'depythonize': from_bool_to_string},
            'event_handler_enabled': {'depythonize': from_bool_to_string},
            'problem_has_been_acknowledged': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'acknowledgement_type': {'prop': None, 'default': '0'},
            'flap_detection_enabled': {'depythonize': from_bool_to_string},
            'failure_prediction_enabled': {'depythonize': from_bool_to_string},
            'process_performance_data': {'depythonize': from_bool_to_string},
            'obsess_over_service': {'depythonize': from_bool_to_string},
            'last_update': {'prop': None, 'default': '0'},
            'is_flapping': {'depythonize': from_bool_to_string},
            'percent_state_change': {},
            'scheduled_downtime_depth': {'prop': None, 'default': '0'}
            },
        'Contact': {
            'contact_name': {},
            'modified_attributes': {'prop': None, 'default': '0'},
            'modified_host_attributes': {'prop': None, 'default': '0'},
            'modified_service_attributes': {'prop': None, 'default': '0'},
            'host_notification_period': {},
            'service_notification_period': {},
            'last_host_notification': {'prop': None, 'default': '0'},
            'last_service_notification': {'prop': None, 'default': '0'},
            'host_notifications_enabled': {'depythonize': from_bool_to_string},
            'service_notifications_enabled': {'depythonize': from_bool_to_string}
            },
        'Config': {
            'modified_host_attributes': {'prop': None, 'default': '0'},
            'modified_service_attributes': {'prop': None, 'default': '0'},
            'nagios_pid': {'prop': 'pid', 'default': '0'},
            'daemon_mode': {'prop': None, 'default': '0'},
            'program_start': {'prop': None, 'default': '0'},
            'last_command_check': {'prop': None, 'default': '0'},
            'last_log_rotation': {'prop': None, 'default': '0'},
            'enable_notifications': {'prop': None, 'default': '0'},
            'active_service_checks_enabled': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'passive_service_checks_enabled': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'active_host_checks_enabled': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'passive_host_checks_enabled': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'enable_event_handlers': {'prop': 'event_handlers_enabled', 'default': '0', 'depythonize': from_bool_to_string},
            'obsess_over_services': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'obsess_over_hosts': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'check_service_freshness': {'prop': None, 'default': '0'},
            'check_host_freshness': {'prop': None, 'default': '0'},
            'enable_flap_detection': {'prop': None, 'default': '0'},
            'enable_failure_prediction': {'prop': None, 'default': '0'},
            'process_performance_data': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'global_host_event_handler': {'prop': None, 'default': '0'},
            'global_service_event_handler': {'prop': None, 'default': '0'},
            'next_comment_id': {'prop': None, 'default': '0'},
            'next_downtime_id': {'prop': None, 'default': '0'},
            'next_event_id': {'prop': None, 'default': '0'},
            'next_problem_id': {'prop': None, 'default': '0'},
            'next_notification_id': {'prop': None, 'default': '0'},
            'total_external_command_buffer_slots': {'prop': None, 'default': '0'},
            'used_external_command_buffer_slots': {'prop': None, 'default': '0'},
            'high_external_command_buffer_slots': {'prop': None, 'default': '0'},
            'active_scheduled_host_check_stats': {'prop': None, 'default': '0,0,0'},
            'active_ondemand_host_check_stats': {'prop': None, 'default': '0,0,0'},
            'passive_host_check_stats': {'prop': None, 'default': '0,0,0'},
            'active_scheduled_service_check_stats': {'prop': None, 'default': '0,0,0'},
            'active_ondemand_service_check_stats': {'prop': None, 'default': '0,0,0'},
            'passive_service_check_stats': {'prop': None, 'default': '0,0,0'},
            'cached_host_check_stats': {'prop': None, 'default': '0,0,0'},
            'cached_service_check_stats': {'prop': None, 'default': '0,0,0'},
            'external_command_stats': {'prop': None, 'default': '0,0,0'},
            'parallel_host_check_stats': {'prop': None, 'default': '0,0,0'},
            'serial_host_check_stats': {'prop': None, 'default': '0,0,0'}
            },
        'Downtime': {
            'host_name': {},
            'service_description': {},
            'downtime_id': {'prop': 'id', 'default': '0'},
            'entry_time': {'prop': None, 'default': '0'},
            'start_time': {'prop': None, 'default': '0'},
            'end_time': {'prop': None, 'default': '0'},
            'triggered_by': {'prop': 'trigger_id', 'default': '0'},
            'fixed': {'prop': None, 'default': '0', 'depythonize': from_bool_to_string},
            'duration': {'prop': None, 'default': '0'},
            'author': {'prop': None, 'default': '0'},
            'comment': {'prop': None, 'default': '0'},
        },
        'Comment': {
            'host_name': {},
            'service_description': {},
            'comment_id': {'prop': 'id', 'default': '0'},
            'source': {'prop': None, 'default': '0'},
            'comment_type': {'prop': None, 'default': '0'},
            'entry_type': {'prop': None, 'default': '0'},
            'entry_time': {'prop': None, 'default': '0'},
            'persistent': {'prop': None, 'depythonize': from_bool_to_string},
            'expires': {'prop': None, 'depythonize': from_bool_to_string},
            'expire_time': {'prop': None, 'default': '0'},
            'author': {'prop': None},
            'comment_data': {'prop': 'comment'},
        },
    }

    def __init__(self, path, configs, hosts, services, contacts):
        #self.conf = scheduler.conf
        #self.scheduler = scheduler
        self.path = path
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts

    def create_output(self, elt):
        output = ''
        if elt.__class__.__name__ in StatusFile.out_map:
            type_map = StatusFile.out_map[elt.__class__.__name__]
            for display in type_map:
                value = None
                if 'prop' not in type_map[display] or type_map[display]['prop'] is None:
                    prop = display
                else:
                    prop = type_map[display]['prop']

                if prop is not None and hasattr(elt, prop):
                    value = getattr(elt, prop)

                    # Maybe it's not a value, but a function link
                    if callable(value):
                        value = value()

                    if 'depythonize' in type_map[display]:
                        f = type_map[display]['depythonize']
                        if callable(f):
                            value = f(value)
                        else:
                            #print "Elt: ", elt, "prop", prop
                            # ok not a direct function, maybe a functin provided by value...
                            if value is not None:
                                f = getattr(value, f)
                                value = f()

                if value is None:
                    try:
                        value = type_map[display]['default']
                    except KeyError:  # Fuck!
                        value = ''
                output += '\t' + display + '=' + unicode(value) + '\n'

        return output

    def create_or_update(self):

        output = '''########################################
#          SHINKEN STATUS FILE
#
# THIS FILE IS AUTOMATICALLY GENERATED
# BY SHINKEN.  DO NOT MODIFY THIS FILE!
########################################

'''
        now = time.time()
        output += 'info {\n' + '\tcreated=' + str(now) + '\n' + '\tversion=3.0.2\n\t}\n\n'

        for c in self.configs.values():
            tmp = self.create_output(c)
            output += 'programstatus {\n' + tmp + '\t}\n\n'

        for h in self.hosts.values():
            tmp = self.create_output(h)
            output += 'hoststatus {\n' + tmp + '\t}\n\n'

        for s in self.services.values():
            tmp = self.create_output(s)
            output += 'servicestatus {\n' + tmp + '\t}\n\n'

        for c in self.contacts.values():
            tmp = self.create_output(c)
            output += 'contactstatus {\n' + tmp + '\t}\n\n'

        for h in self.hosts.values():
            for c in h.comments:
                c.host_name = c.ref.host_name
                tmp = self.create_output(c)
                output += c.ref.my_type + 'comment {\n' + tmp + '\t}\n\n'

        for s in self.services.values():
            for c in s.comments:
                # this is just a workaround until a data-driven solution is found
                c.host_name = c.ref.host_name
                if (hasattr(c.ref, 'service_description')):
                    c.service_description = c.ref.service_description
                tmp = self.create_output(c)
                output += c.ref.my_type + 'comment {\n' + tmp + '\t}\n\n'

        for h in self.hosts.values():
            for dt in h.downtimes:
                dt.host_name = dt.ref.host_name
                tmp = self.create_output(dt)
                output += dt.ref.my_type + 'downtime {\n' + tmp + '\t}\n\n'

        for s in self.services.values():
            for dt in s.downtimes:
                # this is just a workaround until a data-driven solution is found
                dt.host_name = dt.ref.host_name
                if (hasattr(dt.ref, 'service_description')):
                    dt.service_description = dt.ref.service_description
                tmp = self.create_output(dt)
                output += dt.ref.my_type + 'downtime {\n' + tmp + '\t}\n\n'

        #print "Create output:", output
        try:
            temp_fh, temp_status_file = tempfile.mkstemp(dir=os.path.dirname(self.path))
            os.write(temp_fh, output.encode('ascii', 'ignore'))
            os.close(temp_fh)
            os.chmod(temp_status_file, 0640)
            os.rename(temp_status_file, self.path)
        except OSError, exp:
            return exp
