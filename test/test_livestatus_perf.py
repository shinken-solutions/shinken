#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


from shinken_test import *
import os
import re
import subprocess
import shutil
import time
import random
import copy

from shinken.brok import Brok
from shinken.objects.timeperiod import Timeperiod
from shinken.objects.module import Module
from shinken.comment import Comment

sys.setcheckinterval(10000)

def isprime(startnumber):
    startnumber*=1.0
    for divisor in range(2,int(startnumber**0.5)+1):
        if startnumber/divisor==int(startnumber/divisor):
            return False
    return True


class TestConfigCrazy(ShinkenTest):
    def setUp(self):
        print "comment me for performance tests"
        self.setup_with_file('etc/nagios_10r_1000h_20000s.cfg')
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()

        self.sched.conf.skip_initial_broks = False
        self.sched.fill_initial_broks()
        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_0000")
        host.__class__.use_aggressive_host_checking = 1


    def tearDown(self):
        print "comment me for performance tests";
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs+"-journal"):
            os.remove(self.livelogs+"-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        self.livestatus_broker = None

    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        super(TestConfigCrazy, self).scheduler_loop(count, reflist, do_sleep, sleep_time)


    def update_broker(self, dodeepcopy=False):
        #The brok should be manage in the good order
        ids = self.sched.broks.keys()
        ids.sort()
        for brok_id in ids:
            brok = self.sched.broks[brok_id]
            #print "Managing a brok type", brok.type, "of id", brok_id
            #if brok.type == 'update_service_status':
            #    print "Problem?", brok.data['is_problem']
            if dodeepcopy:
                brok = copy.deepcopy(brok)
            self.livestatus_broker.manage_brok(brok)
        self.sched.broks = {}


    def test_perf(self):
        print "comment me for performance tests";
        self.print_header()
        now = time.time()
        objlist = []
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 0, 'OK'])
        self.scheduler_loop(1, objlist)
        primes = [num for num in xrange(0, 999) if isprime(num)]
        down_hosts = [self.sched.hosts.find_by_name("test_host_%04d" % num) for num in xrange(0, 1000) if num in primes]
        crit_services = []
        warn_services = []
        for num in [x for x in xrange(100, 200) if x in primes]:
            crit_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_01"))
            crit_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_05"))
            crit_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_11"))
        for num in [x for x in xrange(100, 200) if x in primes]:
            warn_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_19"))

        for num in [x for x in xrange(201, 999) if x in primes]:
            warn_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_03"))
            warn_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_07"))
            crit_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_13"))
            crit_services.append(self.sched.services.find_srv_by_name_and_hostname("test_host_%04d" % num, "test_ok_17"))
        print "%d services are in a warning state" % len(warn_services)
        print "%d services are in a critical state" % len(crit_services)
        nonok = []
        nonok.extend([[w, 1, "W"] for w in warn_services])
        nonok.extend([[c, 2, "C"] for c in crit_services])
        nonok.extend([[h, 2, "D"] for h in down_hosts])
        self.scheduler_loop(1, nonok)
        nonok = []
        nonok.extend([[w, 1, "W"] for w in warn_services if warn_services.index(w) in primes])
        lenw = len(nonok)
        nonok.extend([[c, 2, "C"] for c in crit_services if crit_services.index(c) in primes])
        lenc = len(nonok) - lenw
        nonok.extend([[h, 2, "D"] for h in down_hosts if down_hosts.index(h) in primes])
        lenh = len(nonok) -lenc - lenw
        print "%d hosts are hard/down" % lenh
        print "%d services are in a hard/warning state" % lenw
        print "%d services are in a hard/critical state" % lenc
        self.scheduler_loop(3, nonok)
        self.update_broker()
        pages = {
            'multisite_tac': ("""
GET status
Columns: livestatus_version program_version program_start
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
ColumnHeaders: off
""", """
GET hosts
Stats: state >= 0
Stats: state > 0
Stats: scheduled_downtime_depth = 0
StatsAnd: 2
Stats: state > 0
Stats: scheduled_downtime_depth = 0
Stats: acknowledged = 0
StatsAnd: 3
Filter: custom_variable_names < _REALNAME
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET hosts
Columns: name state has_been_checked worst_service_state scheduled_downtime_depth
Filter: custom_variable_names < _REALNAME
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET services
Stats: state >= 0
Stats: state > 0
Stats: scheduled_downtime_depth = 0
Stats: host_scheduled_downtime_depth = 0
Stats: host_state = 0
StatsAnd: 4
Stats: state > 0
Stats: scheduled_downtime_depth = 0
Stats: host_scheduled_downtime_depth = 0
Stats: acknowledged = 0
Stats: host_state = 0
StatsAnd: 5
Filter: host_custom_variable_names < _REALNAME
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET status
Columns: service_checks_rate host_checks_rate external_commands_rate connections_rate forks_rate log_messages_rate cached_log_messages
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET hosts
Columns: name state worst_service_state
Filter: custom_variable_names >= _REALNAME
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET hosts
Columns: name state worst_service_state
Filter: custom_variable_names < _REALNAME
Filter: state > 0
Filter: worst_service_state > 0
Or: 2
Localtime: 1326899941
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
"""),
            'multisite_all_hosts': ("""
GET hosts
Columns: host_scheduled_downtime_depth host_num_services_pending host_pnpgraph_present host_comments_with_info host_num_services_crit host_icon_image host_in_notification_period host_custom_variable_values host_modified_attributes_list host_downtimes host_acknowledged host_custom_variable_names host_state host_accept_passive_checks host_has_been_checked host_check_command host_num_services_ok host_num_services_unknown host_notifications_enabled host_active_checks_enabled host_is_flapping host_action_url_expanded host_name host_num_services_warn host_notes_url_expanded
Filter: host_custom_variable_names < _REALNAME
Limit: 1001
Localtime: 1326900125
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET hosts
Columns: name custom_variable_names custom_variable_values services
Localtime: 1326900125
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
"""),
            'multisite_host_detail': ("""
GET services
Columns: service_in_notification_period service_last_check service_action_url_expanded service_comments_with_info service_icon_image service_notifications_enabled service_check_command service_custom_variable_names service_perf_data service_scheduled_downtime_depth service_accept_passive_checks host_state service_has_been_checked service_notes_url_expanded service_downtimes service_modified_attributes_list service_custom_variable_values service_acknowledged service_plugin_output host_has_been_checked service_last_state_change service_description service_active_checks_enabled service_pnpgraph_present host_name service_is_flapping service_state
Filter: host_name = omd-live
Limit: 1001
Localtime: 1326900173
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET hosts
Columns: name custom_variable_names custom_variable_values services
Localtime: 1326900173
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
"""),
            'multisite_all_services': ("""
GET services
Columns: service_in_notification_period service_last_check service_action_url_expanded service_comments_with_info service_icon_image service_notifications_enabled service_check_command service_custom_variable_names service_perf_data service_scheduled_downtime_depth service_accept_passive_checks host_state service_has_been_checked service_notes_url_expanded service_downtimes service_modified_attributes_list service_custom_variable_values service_acknowledged service_plugin_output host_has_been_checked service_last_state_change service_description service_active_checks_enabled service_pnpgraph_present host_name service_is_flapping service_state
Filter: host_custom_variable_names < _REALNAME
Filter: host_custom_variable_names < _REALNAME
Limit: 1001
Localtime: 1326900225
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""", """
GET hosts
Columns: name custom_variable_names custom_variable_values services
Localtime: 1326900225
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
"""),
            'multisite_service_detail': ("""
GET services
Columns: service_in_notification_period service_last_check service_action_url_expanded service_long_plugin_output service_last_notification service_latency service_comments_with_info service_has_been_checked service_notifications_enabled service_contact_groups service_next_check service_check_command service_custom_variable_names service_perf_data service_max_check_attempts service_groups service_scheduled_downtime_depth service_accept_passive_checks service_icon_image service_execution_time service_notes_url_expanded service_next_notification service_downtimes service_modified_attributes_list service_custom_variable_values service_acknowledged service_plugin_output service_last_state_change service_description service_current_attempt host_address service_active_checks_enabled service_check_type service_pnpgraph_present service_contacts service_notification_period host_name service_is_flapping service_state host_has_been_checked host_state
Filter: service_description = Dummy Service
Filter: host_name = omd-live
Limit: 1001
Localtime: 1326900364
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""",),
            'multisite_alert_statistics': ("""
GET log
Columns: log_lineno host_name service_description
Filter: log_time >= 1324308478
Filter: class = 1
Stats: state = 0
Stats: state = 1
Stats: state = 2
Stats: state = 3
Stats: state != 0
Limit: 1001
Localtime: 1326900478
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""",),
            'multisite_events': ("""
GET log
Columns: log_state_type log_plugin_output log_state log_lineno host_name service_description log_time log_type
Filter: log_time >= 1326295843
Filter: class = 1
Filter: class = 3
Or: 2
Limit: 1001
Localtime: 1326900643
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""",),
            'multisite_servicegroups_grid': ("""
GET servicegroups
Columns: servicegroup_members_with_state servicegroup_alias servicegroup_name
Limit: 1001
Localtime: 1326900707
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""",),
            'multisite_servicegroups_summary': ("""
GET servicegroups
Columns: servicegroup_alias servicegroup_num_services_warn servicegroup_name servicegroup_num_services_crit servicegroup_num_services_ok servicegroup_num_services_unknown servicegroup_num_services_pending
Limit: 1001
Localtime: 1326900726
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""",),
            'multisite_services_by_group': ("""
GET services
Stats: state >= 0
Stats: state > 0
Stats: scheduled_downtime_depth = 0
Stats: host_scheduled_downtime_depth = 0
Stats: host_state = 0
StatsAnd: 4
Stats: state > 0
Stats: scheduled_downtime_depth = 0
Stats: host_scheduled_downtime_depth = 0
Stats: acknowledged = 0
Stats: host_state = 0
StatsAnd: 5
Filter: host_custom_variable_names < _REALNAME
Localtime: 1326900741
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
""",),
            'thruk_tac': ("""
GET status
Columns: accept_passive_host_checks accept_passive_service_checks check_external_commands check_host_freshness check_service_freshness enable_event_handlers enable_flap_detection enable_notifications execute_host_checks execute_service_checks last_command_check last_log_rotation livestatus_version nagios_pid obsess_over_hosts obsess_over_services process_performance_data program_start program_version interval_length
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Stats: check_type = 0
StatsAnd: 1
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326901529
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326901289
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326900689
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326897989
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326899498
StatsAnd: 3
Stats: check_type = 1
StatsAnd: 1
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326901529
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326901289
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326900689
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326897989
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326899498
StatsAnd: 3
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Filter: has_been_checked = 1
Filter: check_type = 0
Stats: sum execution_time
Stats: sum latency
Stats: sum percent_state_change
Stats: min execution_time
Stats: min latency
Stats: min percent_state_change
Stats: max execution_time
Stats: max latency
Stats: max percent_state_change
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Filter: has_been_checked = 1
Filter: check_type = 1
Stats: sum percent_state_change
Stats: min percent_state_change
Stats: max percent_state_change
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Stats: check_type = 0
StatsAnd: 1
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326901529
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326901289
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326900689
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326897989
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: last_check >= 1326899498
StatsAnd: 3
Stats: check_type = 1
StatsAnd: 1
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326901529
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326901289
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326900689
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326897989
StatsAnd: 3
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: last_check >= 1326899498
StatsAnd: 3
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Filter: has_been_checked = 1
Filter: check_type = 0
Stats: sum execution_time
Stats: sum latency
Stats: sum percent_state_change
Stats: min execution_time
Stats: min latency
Stats: min percent_state_change
Stats: max execution_time
Stats: max latency
Stats: max percent_state_change
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Filter: has_been_checked = 1
Filter: check_type = 1
Stats: sum percent_state_change
Stats: min percent_state_change
Stats: max percent_state_change
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Stats: name !=
StatsAnd: 1
Stats: check_type = 0
StatsAnd: 1
Stats: check_type = 1
StatsAnd: 1
Stats: has_been_checked = 0
StatsAnd: 1
Stats: has_been_checked = 0
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: has_been_checked = 0
Stats: scheduled_downtime_depth > 0
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 0
StatsAnd: 2
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 0
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 0
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 0
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 1
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 1
Stats: acknowledged = 1
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 1
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 1
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 1
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 1
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
StatsAnd: 5
Stats: has_been_checked = 1
Stats: state = 2
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 2
Stats: acknowledged = 1
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 2
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 2
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 2
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 2
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
StatsAnd: 5
Stats: is_flapping = 1
StatsAnd: 1
Stats: flap_detection_enabled = 0
StatsAnd: 1
Stats: notifications_enabled = 0
StatsAnd: 1
Stats: event_handler_enabled = 0
StatsAnd: 1
Stats: check_type = 0
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: check_type = 1
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: accept_passive_checks = 0
StatsAnd: 1
Stats: state = 1
Stats: childs !=
StatsAnd: 2
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Stats: description !=
StatsAnd: 1
Stats: check_type = 0
StatsAnd: 1
Stats: check_type = 1
StatsAnd: 1
Stats: has_been_checked = 0
StatsAnd: 1
Stats: has_been_checked = 0
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: has_been_checked = 0
Stats: scheduled_downtime_depth > 0
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 0
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 0
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 0
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 0
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 1
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 1
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 1
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 1
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 1
Stats: acknowledged = 1
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 1
Stats: host_state != 0
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 1
Stats: host_state = 0
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
StatsAnd: 6
Stats: has_been_checked = 1
Stats: state = 2
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 2
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 2
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 2
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 2
Stats: acknowledged = 1
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 2
Stats: host_state != 0
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 2
Stats: host_state = 0
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
StatsAnd: 6
Stats: has_been_checked = 1
Stats: state = 3
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 3
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: check_type = 0
Stats: has_been_checked = 1
Stats: state = 3
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 3
Stats: active_checks_enabled = 0
StatsAnd: 4
Stats: has_been_checked = 1
Stats: state = 3
Stats: acknowledged = 1
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 3
Stats: host_state != 0
StatsAnd: 3
Stats: has_been_checked = 1
Stats: state = 3
Stats: host_state = 0
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
StatsAnd: 6
Stats: is_flapping = 1
StatsAnd: 1
Stats: flap_detection_enabled = 0
StatsAnd: 1
Stats: notifications_enabled = 0
StatsAnd: 1
Stats: event_handler_enabled = 0
StatsAnd: 1
Stats: check_type = 0
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: check_type = 1
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: accept_passive_checks = 0
StatsAnd: 1
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_all_hosts': ("""
GET comments
Columns: author comment entry_time entry_type expires expire_time host_name id persistent service_description source type
Filter: service_description !=
Filter: service_description =
Or: 2
OutputFormat: json
ResponseHeader: fixed16
""", """
GET downtimes
Columns: author comment end_time entry_time fixed host_name id start_time service_description triggered_by
Filter: service_description !=
Filter: service_description =
Or: 2
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Stats: name !=
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled address alias check_command check_freshness check_interval check_options check_period check_type checks_enabled childs comments current_attempt current_notification_number event_handler_enabled execution_time custom_variable_names custom_variable_values first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts name next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled num_services_crit num_services_ok num_services_pending num_services_unknown num_services_warn num_services obsess_over_host parents percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
Limit: 150
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_host_detail': ("""
GET hosts
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled address alias check_command check_freshness check_interval check_options check_period check_type checks_enabled childs comments current_attempt current_notification_number event_handler_enabled execution_time custom_variable_names custom_variable_values first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts name next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled num_services_crit num_services_ok num_services_pending num_services_unknown num_services_warn num_services obsess_over_host parents percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
Filter: name = omd-live
OutputFormat: json
ResponseHeader: fixed16
""", """
GET comments
Columns: author comment entry_time entry_type expires expire_time host_name id persistent service_description source type
Filter: service_description !=
Filter: service_description =
Or: 2
Filter: host_name = omd-live
Filter: service_description =
OutputFormat: json
ResponseHeader: fixed16
""", """
GET downtimes
Columns: author comment end_time entry_time fixed host_name id start_time service_description triggered_by
Filter: service_description !=
Filter: service_description =
Or: 2
Filter: host_name = omd-live
Filter: service_description =
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_host_status_detail': ("""
GET services
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled check_command check_interval check_options check_period check_type checks_enabled comments current_attempt current_notification_number description event_handler event_handler_enabled custom_variable_names custom_variable_values execution_time first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold host_acknowledged host_action_url_expanded host_active_checks_enabled host_address host_alias host_checks_enabled host_check_type host_comments host_groups host_has_been_checked host_icon_image_expanded host_icon_image_alt host_is_executing host_is_flapping host_name host_notes_url_expanded host_notifications_enabled host_scheduled_downtime_depth host_state host_accept_passive_checks icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled obsess_over_service percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
Filter: host_name = omd-live
Limit: 150
OutputFormat: json
ResponseHeader: fixed16
""",),
            'thruk_all_services': ("""
GET services
Stats: description !=
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled check_command check_interval check_options check_period check_type checks_enabled comments current_attempt current_notification_number description event_handler event_handler_enabled custom_variable_names custom_variable_values execution_time first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold host_acknowledged host_action_url_expanded host_active_checks_enabled host_address host_alias host_checks_enabled host_check_type host_comments host_groups host_has_been_checked host_icon_image_expanded host_icon_image_alt host_is_executing host_is_flapping host_name host_notes_url_expanded host_notifications_enabled host_scheduled_downtime_depth host_state host_accept_passive_checks icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled obsess_over_service percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
Limit: 150
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_service_detail': ("""
GET services
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled check_command check_interval check_options check_period check_type checks_enabled comments current_attempt current_notification_number description event_handler event_handler_enabled custom_variable_names custom_variable_values execution_time first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold host_acknowledged host_action_url_expanded host_active_checks_enabled host_address host_alias host_checks_enabled host_check_type host_comments host_groups host_has_been_checked host_icon_image_expanded host_icon_image_alt host_is_executing host_is_flapping host_name host_notes_url_expanded host_notifications_enabled host_scheduled_downtime_depth host_state host_accept_passive_checks icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled obsess_over_service percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
Filter: host_name = omd-live
Filter: description = Dummy Service
OutputFormat: json
ResponseHeader: fixed16
""", """
GET comments
Columns: author comment entry_time entry_type expires expire_time host_name id persistent service_description source type
Filter: service_description !=
Filter: service_description =
Or: 2
Filter: host_name = omd-live
Filter: service_description = Dummy Service
OutputFormat: json
ResponseHeader: fixed16
""", """
GET downtimes
Columns: author comment end_time entry_time fixed host_name id start_time service_description triggered_by
Filter: service_description !=
Filter: service_description =
Or: 2
Filter: host_name = omd-live
Filter: service_description = Dummy Service
OutputFormat: json
ResponseHeader: fixed16
""", """
GET hosts
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled address alias check_command check_freshness check_interval check_options check_period check_type checks_enabled childs comments current_attempt current_notification_number event_handler_enabled execution_time custom_variable_names custom_variable_values first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts name next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled num_services_crit num_services_ok num_services_pending num_services_unknown num_services_warn num_services obsess_over_host parents percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
Filter: name = omd-live
OutputFormat: json
ResponseHeader: fixed16
""", """
GET commands
Columns: name line
Filter: name = omd-dummy
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_alert_history': ("""
GET log
Columns: class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups
Filter: type = HOST ALERT
Filter: time >= 1324224038
Filter: time <= 1326902438
And: 2
OutputFormat: json
ResponseHeader: fixed16
""", """
GET log
Columns: class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups
Filter: type = SERVICE ALERT
Filter: time >= 1324224038
Filter: time <= 1326902438
And: 2
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_servicegroups_grid': ("""
GET hosts
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled address alias check_command check_freshness check_interval check_options check_period check_type checks_enabled childs comments current_attempt current_notification_number event_handler_enabled execution_time custom_variable_names custom_variable_values first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts name next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled num_services_crit num_services_ok num_services_pending num_services_unknown num_services_warn num_services obsess_over_host parents percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled check_command check_interval check_options check_period check_type checks_enabled comments current_attempt current_notification_number description event_handler event_handler_enabled custom_variable_names custom_variable_values execution_time first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold host_acknowledged host_action_url_expanded host_active_checks_enabled host_address host_alias host_checks_enabled host_check_type host_comments host_groups host_has_been_checked host_icon_image_expanded host_icon_image_alt host_is_executing host_is_flapping host_name host_notes_url_expanded host_notifications_enabled host_scheduled_downtime_depth host_state host_accept_passive_checks icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled obsess_over_service percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
OutputFormat: json
ResponseHeader: fixed16
""", """
GET servicegroups
Columns: name alias members action_url notes notes_url
OutputFormat: json
ResponseHeader: fixed16
"""),
            'thruk_servicegroups_summary': ("""
GET servicegroups
Columns: name alias members action_url notes notes_url
OutputFormat: json
ResponseHeader: fixed16
""", """
GET services
Columns: accept_passive_checks acknowledged action_url action_url_expanded active_checks_enabled check_command check_interval check_options check_period check_type checks_enabled comments current_attempt current_notification_number description event_handler event_handler_enabled custom_variable_names custom_variable_values execution_time first_notification_delay flap_detection_enabled groups has_been_checked high_flap_threshold host_acknowledged host_action_url_expanded host_active_checks_enabled host_address host_alias host_checks_enabled host_check_type host_comments host_groups host_has_been_checked host_icon_image_expanded host_icon_image_alt host_is_executing host_is_flapping host_name host_notes_url_expanded host_notifications_enabled host_scheduled_downtime_depth host_state host_accept_passive_checks icon_image icon_image_alt icon_image_expanded is_executing is_flapping last_check last_notification last_state_change latency long_plugin_output low_flap_threshold max_check_attempts next_check notes notes_expanded notes_url notes_url_expanded notification_interval notification_period notifications_enabled obsess_over_service percent_state_change perf_data plugin_output process_performance_data retry_interval scheduled_downtime_depth state state_type modified_attributes_list
OutputFormat: json
ResponseHeader: fixed16
"""),
        }
        last_host = reduce(lambda x,y:y,self.livestatus_broker.datamgr.rg.hosts) 
        #last_service = reduce(lambda x,y:y,self.livestatus_broker.datamgr.rg.services) 

        elapsed = {}
        requestelapsed = {}
        for page in pages:
            print "oage is", page
            elapsed[page] = 0
            requestelapsed[page] = []
            for request in pages[page]:
                print "+--------------------------\n%s\n--------------------------\n" % request
                # 
                request = request.replace('omd-live',last_host.host_name)
                request = request.replace('Dummy Service', 'test_ok_19')
                print "---------------------------\n%s\n--------------------------\n" % request
                tic = time.time()
                response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
                tac = time.time()
                elapsed[page] += (tac - tic)
                requestelapsed[page].append(tac - tic)
        for page in pages:
            print "%-40s %-10.4f  %s" % (page, elapsed[page], ["%.3f" % f for f in requestelapsed[page]])


if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig)
    #unittest.TextTestRunner(verbosity=2).run(allsuite)

