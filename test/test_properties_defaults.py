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

from shinken_test import *


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
            if hasattr(item.properties[name], 'default'):
                if item.properties[name].default != value:
                    print "%s, %s: %s, %s" % (name, value, item.properties[name].default, value)
                self.assertEqual(item.properties[name].default, value)

    def test_all_props_are_tested(self):
        item = self.item # shortcut
        prop_names = set(list(self.properties.keys()) + self.unused_props + self.without_default)

        for name in item.properties:
            if name.startswith('$') and name.endswith('$'):
                continue
            self.assertIn(name, prop_names,
                          msg='unknown property %r found' % name)

class TestConfig(PropertiesTester, ShinkenTest, unittest.TestCase):

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
        ('workdir', '/var/run/shinken/'),
        ('config_base_dir', ''),
        ('modules_dir', '/var/lib/shinken/modules'),
        ('use_local_log', '1'),
        ('log_level', 'WARNING'),
        ('local_log', '/var/log/shinken/arbiterd.log'),
        ('resource_file', '/tmp/resources.txt'),
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
        ('lock_file', '/var/run/shinken/arbiterd.pid'),
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
        ('daemon_enabled', '1'),

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
        ('server_key', 'etc/certs/server.key'),
        ('ca_cert', 'etc/certs/ca.pem'),
        ('server_cert', 'etc/certs/server.cert'),
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

        ('use_multiprocesses_serializer', '0'),
        ('daemon_thread_pool_size', '8'),
        ('enable_environment_macros', '1'),
        ('timeout_exit_status', '2'),
        ])

    def setUp(self):
        from shinken.objects.config import Config
        self.item = Config()


class TestCommand(PropertiesTester, ShinkenTest, unittest.TestCase):

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
        ('enable_environment_macros', 0),
        ])

    def setUp(self):
        from shinken.objects.command import Command
        self.item = Command()


class TestContactgroup(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['members', 'contactgroup_name', 'alias']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('unknown_members', []),
        ('id', 0),
        ])

    def setUp(self):
        from shinken.objects.contactgroup import Contactgroup
        self.item = Contactgroup()


class TestContact(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = [
        'contact_name',
        'host_notification_period', 'service_notification_period',
        'host_notification_options', 'service_notification_options',
        'host_notification_commands', 'service_notification_commands'
        ]

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('alias', 'none'),
        ('contactgroups', ''),
        ('host_notifications_enabled', '1'),
        ('service_notifications_enabled', '1'),
        ('min_business_impact', '0'),
        ('email', 'none'),
        ('pager', 'none'),
        ('address1', 'none'),
        ('address2', 'none'),
        ('address3', 'none'),
        ('address4', 'none'),
        ('address5', 'none'),
        ('address6', 'none'),
        ('can_submit_commands', '0'),
        ('is_admin', '0'),
        ('retain_status_information', '1'),
        ('notificationways', ''),
        ('password', 'NOPASSWORDSET'),
        ])

    def setUp(self):
        from shinken.objects.contact import Contact
        self.item = Contact()


class TestDiscoveryrule(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['discoveryrule_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('creation_type', 'service'),
        ('discoveryrule_order', '0'),
        ])

    def setUp(self):
        from shinken.objects.discoveryrule import Discoveryrule
        self.item = Discoveryrule()


class TestDiscoveryrun(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['discoveryrun_name', 'discoveryrun_command']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ])

    def setUp(self):
        from shinken.objects.discoveryrun import Discoveryrun
        self.item = Discoveryrun()


class TestEscalation(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['escalation_name', 'first_notification', 'last_notification', 'first_notification_time', 'last_notification_time', 'contacts', 'contact_groups']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('notification_interval', '-1'),
        ('escalation_period', ''),
        ('escalation_options', 'd,u,r,w,c'),
        ])

    def setUp(self):
        from shinken.objects.escalation import Escalation
        self.item = Escalation()


class TestHostdependency(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['dependent_host_name', 'host_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('dependent_hostgroup_name', ''),
        ('hostgroup_name', ''),
        ('inherits_parent', '0'),
        ('execution_failure_criteria', 'n'),
        ('notification_failure_criteria', 'n'),
        ('dependency_period', ''),
        ])

    def setUp(self):
        from shinken.objects.hostdependency import Hostdependency
        self.item = Hostdependency()


class TestHostescalation(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = [
        'host_name', 'hostgroup_name',
        'first_notification', 'last_notification',
        'contacts', 'contact_groups'
        ]

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('notification_interval', '30'),
        ('escalation_period', ''),
        ('escalation_options', 'd,u,r,w,c'),
        ])

    def setUp(self):
        from shinken.objects.hostescalation import Hostescalation
        self.item = Hostescalation()


class TestHostextinfo(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['host_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('notes', ''),
        ('notes_url', ''),
        ('icon_image', ''),
        ('icon_image_alt', ''),
        ('vrml_image', ''),
        ('statusmap_image', ''),
        ('2d_coords', ''),
        ('3d_coords', ''),
        ])

    def setUp(self):
        from shinken.objects.hostextinfo import HostExtInfo
        self.item = HostExtInfo()


class TestHostgroup(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['members', 'hostgroup_name', 'alias']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('unknown_members', []),
        ('id', 0),
        ('notes', ''),
        ('notes_url', ''),
        ('action_url', ''),
        ('realm', ''),
        ])

    def setUp(self):
        from shinken.objects.hostgroup import Hostgroup
        self.item = Hostgroup()


class TestHost(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = [
        'host_name', 'alias', 'address',
        'check_period', 'notification_period']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('display_name', ''),
        ('parents', ''),
        ('hostgroups', ''),
        ('check_command', '_internal_host_up'),
        ('initial_state', 'u'),
        ('check_interval', '0'),
        ('max_check_attempts', '1'),
        ('retry_interval', '0'),
        ('active_checks_enabled', '1'),
        ('passive_checks_enabled', '1'),
        ('obsess_over_host', '0'),
        ('check_freshness', '0'),
        ('freshness_threshold', '0'),
        ('event_handler', ''),
        ('event_handler_enabled', '0'),
        ('low_flap_threshold', '25'),
        ('high_flap_threshold', '50'),
        ('flap_detection_enabled', '1'),
        ('flap_detection_options', 'o,d,u'),
        ('process_perf_data', '1'),
        ('retain_status_information', '1'),
        ('retain_nonstatus_information', '1'),
        ('contacts', ''),
        ('contact_groups', ''),
        ('notification_interval', '60'),
        ('first_notification_delay', '0'),
        ('notification_options', 'd,u,r,f'),
        ('notifications_enabled', '1'),
        ('stalking_options', ''),
        ('notes', ''),
        ('notes_url', ''),
        ('action_url', ''),
        ('icon_image', ''),
        ('icon_image_alt', ''),
        ('icon_set', ''),
        ('vrml_image', ''),
        ('statusmap_image', ''),
        ('2d_coords', ''),
        ('3d_coords', ''),
        ('failure_prediction_enabled', '0'),
        ('realm', None),
        ('poller_tag', 'None'),
        ('reactionner_tag', 'None'),
        ('resultmodulations', ''),
        ('business_impact_modulations', ''),
        ('escalations', ''),
        ('maintenance_period', ''),
        ('business_impact', '2'),
        ('trigger', ''),
        ('trigger_name', ''),
        ('time_to_orphanage', '300'),
        ('trending_policies', ''),
        ('checkmodulations', ''),
        ('macromodulations', ''),
        ('custom_views', ''),
        ('service_overrides', ''),
        ('business_rule_output_template', ''),
        ('business_rule_smart_notifications', '0'),
        ('business_rule_downtime_as_ack', '0'),
        ('labels', ''),
        ('business_rule_host_notification_options', ''),
        ('business_rule_service_notification_options', ''),
        ])

    def setUp(self):
        from shinken.objects.host import Host
        self.item = Host()


class TestModule(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['module_name', 'module_type']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('modules', ''),
        ])

    def setUp(self):
        from shinken.objects.module import Module
        self.item = Module()


class TestNotificationway(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = [
        'notificationway_name',
        'host_notification_period', 'service_notification_period',
        'host_notification_options', 'service_notification_options',
        'host_notification_commands', 'service_notification_commands']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('host_notifications_enabled', '1'),
        ('service_notifications_enabled', '1'),
        ('min_business_impact', '0'),
        ])

    def setUp(self):
        from shinken.objects.notificationway import NotificationWay
        self.item = NotificationWay()


class TestPack(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['pack_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ])

    def setUp(self):
        from shinken.objects.pack import Pack
        self.item = Pack()


class TestRealm(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['members', 'realm_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('unknown_members', []),
        ('id', 0),
        ('realm_members', ''),
        ('higher_realms', ''),
        ('default', '0'),
        ('broker_complete_links', '0'),
        ])

    def setUp(self):
        from shinken.objects.realm import Realm
        self.item = Realm()


class TestResultmodulation(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['resultmodulation_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('exit_codes_match', ''),
        ('exit_code_modulation', None),
        ('modulation_period', None),
        ])

    def setUp(self):
        from shinken.objects.resultmodulation import Resultmodulation
        self.item = Resultmodulation()


class TestServicedependency(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['dependent_host_name', 'dependent_service_description', 'host_name', 'service_description']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('dependent_hostgroup_name', ''),
        ('hostgroup_name', ''),
        ('inherits_parent', '0'),
        ('execution_failure_criteria', 'n'),
        ('notification_failure_criteria', 'n'),
        ('dependency_period', ''),
        ('explode_hostgroup', '0'),
        ])

    def setUp(self):
        from shinken.objects.servicedependency import Servicedependency
        self.item = Servicedependency()


class TestServiceescalation(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = [
        'host_name', 'hostgroup_name',
        'service_description',
        'first_notification', 'last_notification',
        'contacts', 'contact_groups']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('notification_interval', '30'),
        ('escalation_period', ''),
        ('escalation_options', 'd,u,r,w,c'),
        ])

    def setUp(self):
        from shinken.objects.serviceescalation import Serviceescalation
        self.item = Serviceescalation()


class TestServiceextinfo(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['host_name', 'service_description']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('notes', ''),
        ('notes_url', ''),
        ('icon_image', ''),
        ('icon_image_alt', ''),
        ])

    def setUp(self):
        from shinken.objects.serviceextinfo import ServiceExtInfo
        self.item = ServiceExtInfo()


class TestServicegroup(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['members', 'servicegroup_name', 'alias']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('unknown_members', []),
        ('id', 0),
        ('notes', ''),
        ('notes_url', ''),
        ('action_url', ''),
        ])

    def setUp(self):
        from shinken.objects.servicegroup import Servicegroup
        self.item = Servicegroup()


class TestService(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = [
        'host_name', 'service_description',
        'check_command', 'check_interval',
        'retry_interval', 'check_period', 'notification_period']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('max_check_attempts', '1'),
        ('hostgroup_name', ''),
        ('display_name', ''),
        ('servicegroups', ''),
        ('is_volatile', '0'),
        ('initial_state', 'o'),
        ('active_checks_enabled', '1'),
        ('passive_checks_enabled', '1'),
        ('obsess_over_service', '0'),
        ('check_freshness', '0'),
        ('freshness_threshold', '0'),
        ('event_handler', ''),
        ('event_handler_enabled', '0'),
        ('low_flap_threshold', '-1'),
        ('high_flap_threshold', '-1'),
        ('flap_detection_enabled', '1'),
        ('flap_detection_options', 'o,w,c,u'),
        ('process_perf_data', '1'),
        ('retain_status_information', '1'),
        ('retain_nonstatus_information', '1'),
        ('notification_interval', '60'),
        ('first_notification_delay', '0'),
        ('notification_options', 'w,u,c,r,f,s'),
        ('notifications_enabled', '1'),
        ('contacts', ''),
        ('contact_groups', ''),
        ('stalking_options', ''),
        ('notes', ''),
        ('notes_url', ''),
        ('action_url', ''),
        ('icon_image', ''),
        ('icon_image_alt', ''),
        ('icon_set', ''),
        ('failure_prediction_enabled', '0'),
        ('parallelize_check', '1'),
        ('poller_tag', 'None'),
        ('reactionner_tag', 'None'),
        ('resultmodulations', ''),
        ('business_impact_modulations', ''),
        ('escalations', ''),
        ('maintenance_period', ''),
        ('duplicate_foreach', ''),
        ('default_value', ''),
        ('business_impact', '2'),
        ('trigger', ''),
        ('trigger_name', ''),
        ('time_to_orphanage', '300'),
        ('trending_policies', ''),
        ('checkmodulations', ''),
        ('macromodulations', ''),
        ('aggregation', ''),
        ('service_dependencies', ''),
        ('custom_views', ''),
        ('merge_host_contacts', '0'),
        ('business_rule_output_template', ''),
        ('business_rule_smart_notifications', '0'),
        ('business_rule_downtime_as_ack', '0'),
        ('labels', ''),
        ('business_rule_host_notification_options', ''),
        ('business_rule_service_notification_options', ''),
        ])

    def setUp(self):
        from shinken.objects.service import Service
        self.item = Service()


class TestTimeperiod(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['timeperiod_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('alias', ''),
        ('use', ''),
        ('register', '1'),
        ('dateranges', []),
        ('exclude', []),
        ('is_active', '0'),
        ])

    def setUp(self):
        from shinken.objects.timeperiod import Timeperiod
        self.item = Timeperiod()


class TestTrigger(PropertiesTester, ShinkenTest, unittest.TestCase):

    unused_props = []

    without_default = ['trigger_name']

    properties = dict([
        ('imported_from', 'unknown'),
        ('use', ''),
        ('name', ''),
        ('code_src', ''),
        ])

    def setUp(self):
        from shinken.objects.trigger import Trigger
        self.item = Trigger()


if __name__ == '__main__':
    unittest.main()
