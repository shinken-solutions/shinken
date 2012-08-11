#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012:
#    Hartmut Goebel <h.goebel@crazy-compilers.com>
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

"""
Test default values for item types.
"""

import unittest

import __import_shinken
from shinken.property import UnusedProp, none_object
import shinken.daemon


class PropertiesTester(object):

    def test_unused_properties(self):
        item = self.item # shortcut
        for name in self.unused_props:
            self.assertIn(name, item.properties,
                          msg='property %r not found in %s' % (name, self.item.my_type))
            self.assertIsInstance(item.properties[name], UnusedProp)

    def test_properties_without_default(self):
        item = self.item # shortcut
        for name in self.without_default:
            self.assertIn(name, item.properties,
                          msg='property %r not found in %s' % (name, self.item.my_type))
            self.assertIs(item.properties[name].default, none_object,
                          msg='property %r is not `none_object` but %r' % (name, item.properties[name]))
            self.assertTrue(item.properties[name].required)

    def test_default_values(self):
        item = self.item # shortcut
        for name, value in self.properties.iteritems():
            self.assertIn(name, item.properties,
                          msg='property %r not found in %s' % (name, self.item.my_type))
            self.assertEqual(item.properties[name].default, value)

    def test_all_props_are_tested(self):
        item = self.item # shortcut
        prop_names = set(list(self.properties.keys()) + self.unused_props + self.without_default)

        for name in item.properties:
            if name.startswith('$') and name.endswith('$'):
                continue
            self.assertIn(name, prop_names,
                          msg='unknown property %r found' % name)


class TestConfig(unittest.TestCase, PropertiesTester):

    unused_props = [
        'log_file', 'object_cache_file', 'precached_object_file',
        'temp_file', 'status_file', 'status_update_interval',
        'command_check_interval', 'external_command_buffer_slots',
        'check_for_updates', 'bare_update_checks',
        'retain_state_information', 'use_retained_program_state',
        'use_retained_scheduling_info',
        'retained_host_attribute_mask',
        'retained_service_attribute_mask',
        'retained_process_host_attribute_mask',
        'retained_process_service_attribute_mask',
        'retained_contact_host_attribute_mask',
        'retained_contact_service_attribute_mask', 'sleep_time',
        'service_inter_check_delay_method',
        'service_interleave_factor', 'max_concurrent_checks',
        'check_result_reaper_frequency',
        'max_check_result_reaper_time', 'check_result_path',
        'max_check_result_file_age', 'host_inter_check_delay_method',
        'free_child_process_memory', 'child_processes_fork_twice',
        'admin_email', 'admin_pager', 'event_broker_options',
        'debug_file', 'debug_level', 'debug_verbosity',
        'max_debug_file_size']

    without_default = []

    properties = dict([
        ('prefix', '/usr/local/shinken/'),
        ('workdir', ''),
        ('config_base_dir', ''),
        ('use_local_log', '1'),
        ('log_level', 20),
        ('local_log', 'arbiterd.log'),
        ('resource_file', '/tmp/ressources.txt'),
        ('shinken_user', shinken.daemon.get_cur_user()),
        ('shinken_group', shinken.daemon.get_cur_group()),
        ('enable_notifications', '1'),
        ('execute_service_checks', '1'),
        ('accept_passive_service_checks', '1'),
        ('execute_host_checks', '1'),
        ('accept_passive_host_checks', '1'),
        ('enable_event_handlers', '1'),
        ('log_rotation_method', 'd'),
        ('log_archive_path', '/usr/local/shinken/var/archives'),
        ('check_external_commands', '1'),
        ('command_file', ''),
        ('lock_file', 'arbiterd.pid'),
        ('state_retention_file', ''),
        ('retention_update_interval', '60'),
        ('use_syslog', '0'),
        ('log_notifications', '1'),
        ('log_service_retries', '1'),
        ('log_host_retries', '1'),
        ('log_event_handlers', '1'),
        ('log_initial_states', '1'),
        ('log_external_commands', '1'),
        ('log_passive_checks', '1'),
        ('global_host_event_handler', ''),
        ('global_service_event_handler', ''),
        ('max_service_check_spread', '30'),
        ('max_host_check_spread', '30'),
        ('interval_length', '60'),
        ('auto_reschedule_checks', '1'),
        ('auto_rescheduling_interval', '1'),
        ('auto_rescheduling_window', '180'),
        ('use_aggressive_host_checking', '0'),
        ('translate_passive_host_checks', '1'),
        ('passive_host_checks_are_soft', '1'),
        ('enable_predictive_host_dependency_checks', '1'),
        ('enable_predictive_service_dependency_checks', '1'),
        ('cached_host_check_horizon', '0'),
        ('cached_service_check_horizon', '0'),
        ('use_large_installation_tweaks', '0'),
        ('enable_environment_macros', '1'),
        ('enable_flap_detection', '1'),
        ('low_service_flap_threshold', '20'),
        ('high_service_flap_threshold', '30'),
        ('low_host_flap_threshold', '20'),
        ('high_host_flap_threshold', '30'),
        ('soft_state_dependencies', '0'),
        ('service_check_timeout', '60'),
        ('host_check_timeout', '30'),
        ('event_handler_timeout', '30'),
        ('notification_timeout', '30'),
        ('ocsp_timeout', '15'),
        ('ochp_timeout', '15'),
        ('perfdata_timeout', '5'),
        ('obsess_over_services', '0'),
        ('ocsp_command', ''),
        ('obsess_over_hosts', '0'),
        ('ochp_command', ''),
        ('process_performance_data', '1'),
        ('host_perfdata_command', ''),
        ('service_perfdata_command', ''),
        ('host_perfdata_file', ''),
        ('service_perfdata_file', ''),
        ('host_perfdata_file_template', '/tmp/host.perf'),
        ('service_perfdata_file_template', '/tmp/host.perf'),
        ('host_perfdata_file_mode', 'a'),
        ('service_perfdata_file_mode', 'a'),
        ('host_perfdata_file_processing_interval', '15'),
        ('service_perfdata_file_processing_interval', '15'),
        ('host_perfdata_file_processing_command', ''),
        ('service_perfdata_file_processing_command', None),
        ('check_for_orphaned_services', '1'),
        ('check_for_orphaned_hosts', '1'),
        ('check_service_freshness', '1'),
        ('service_freshness_check_interval', '60'),
        ('check_host_freshness', '1'),
        ('host_freshness_check_interval', '60'),
        ('additional_freshness_latency', '15'),
        ('enable_embedded_perl', '1'),
        ('use_embedded_perl_implicitly', '0'),
        ('date_format', None),
        ('use_timezone', ''),
        ('illegal_object_name_chars', '`~!$%^&*"|\'<>?,()='),
        ('illegal_macro_output_chars', ''),
        ('use_regexp_matching', '0'),
        ('use_true_regexp_matching', None),
        ('broker_module', ''),
        ('modified_attributes', 0L),

        # Shinken specific
        ('idontcareaboutsecurity', '0'),
        ('flap_history', '20'),
        ('max_plugins_output_length', '8192'),
        ('no_event_handlers_during_downtimes', '0'),
        ('cleaning_queues_interval', '900'),
        ('disable_old_nagios_parameters_whining', '0'),
        ('enable_problem_impacts_states_change', '0'),
        ('resource_macros_names', []),

        # SSL part
        ('use_ssl', '0'),
        ('certs_dir', 'etc/certs'),
        ('ca_cert', 'etc/certs/ca.pem'),
        ('server_cert', 'etc/certs/server.pem'),
        ('hard_ssl_name_check', '0'),

        ('human_timestamp_log', '0'),

        # Discovery part
        ('strip_idname_fqdn', '1'),
        ('runners_timeout', '3600'),
        ('pack_distribution_file', 'pack_distribution.dat'),

        # WebUI part
        ('webui_lock_file', 'webui.pid'),
        ('webui_port', '8080'),
        ('webui_host', '0.0.0.0'),
        ])

    def setUp(self):
        from shinken.objects.config import Config
        self.item = Config()


class TestCommand(unittest.TestCase, PropertiesTester):

    unused_props = []

    without_default = ['command_name', 'command_line']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('poller_tag', 'None'),
        ('reactionner_tag', 'None'),
        ('module_type', None),
        ('timeout', '-1'),
        ])

    def setUp(self):
        from shinken.objects.command import Command
        self.item = Command()

if __name__ == '__main__':
    unittest.main()
