#!/usr/bin/env python2.6
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


#
# This file is used to test host- and service-downtimes.
#

from shinken_test import *

sys.path.append("../shinken/modules/livestatus_broker")
from livestatus_broker import Livestatus_broker
sys.setcheckinterval(10000)

class TestConfig(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')
        self.livestatus_broker = Livestatus_broker('livestatus', '127.0.0.1', '50000', 'live', '/tmp/livelogs.db')
        self.livestatus_broker.properties = {
            'to_queue' : 0,
            'from_queue' : 0
            
            }
        self.livestatus_broker.init()
        self.sched.fill_initial_broks()


    def update_broker(self):
        for brok in self.sched.broks.values():
            self.livestatus_broker.manage_brok(brok)
        self.sched.broks = {}


    def test_fill_status(self):
        self.print_header()
        print "got initial broks"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker()
        #---------------------------------------------------------------
        # get the full hosts table
        #---------------------------------------------------------------
        data = 'GET hosts'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        #---------------------------------------------------------------
        # get only the host names and addresses
        #---------------------------------------------------------------
        data = 'GET hosts\nColumns: name address\nColumnHeaders: on'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        #---------------------------------------------------------------
        # query_1
        #---------------------------------------------------------------
        data = 'GET contacts'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_1_______________\n%s\n%s\n' % (data, response)

        #---------------------------------------------------------------
        # query_2
        #---------------------------------------------------------------
        data = 'GET contacts\nColumns: name alias'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_2_______________\n%s\n%s\n' % (data, response)

        #---------------------------------------------------------------
        # query_3
        #---------------------------------------------------------------
        #self.scheduler_loop(3, svc, 2, 'BAD')
        data = 'GET services\nColumns: host_name description state\nFilter: state = 2\nColumnHeaders: on'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_3_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == 'host_name;description;state\ntest_host_0;test_ok_0;2\n')
        data = 'GET services\nColumns: host_name description state\nFilter: state = 2'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_3_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == 'test_host_0;test_ok_0;2\n')
        data = 'GET services\nColumns: host_name description state\nFilter: state = 0'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_3_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == '\n')
        duration = 180
        now = time.time()
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;0;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        self.update_broker()
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.update_broker()
        self.scheduler_loop(3, [[svc, 2, 'BAD']])
        self.update_broker()
        data = 'GET services\nColumns: host_name description scheduled_downtime_depth\nFilter: state = 2\nFilter: scheduled_downtime_depth = 1'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_3_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == 'test_host_0;test_ok_0;1\n')

        #---------------------------------------------------------------
        # query_4
        #---------------------------------------------------------------      
        data = 'GET services\nColumns: host_name description state\nFilter: state = 2\nFilter: in_notification_period = 1\nAnd: 2\nFilter: state = 0\nOr: 2\nFilter: host_name = test_host_0\nFilter: description = test_ok_0\nAnd: 3\nFilter: contacts >= harri\nFilter: contacts >= test_contact\nOr: 3'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_4_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == 'test_host_0;test_ok_0;2\n')

        #---------------------------------------------------------------
        # query_6
        #---------------------------------------------------------------      
        data = 'GET services\nStats: state = 0\nStats: state = 1\nStats: state = 2\nStats: state = 3'        
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_6_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == '0;0;1;0\n')

        #---------------------------------------------------------------
        # query_7
        #---------------------------------------------------------------      
        data = 'GET services\nStats: state = 0\nStats: state = 1\nStats: state = 2\nStats: state = 3\nFilter: contacts >= test_contact'        
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'query_6_______________\n%s\n%s\n' % (data, response)
        self.assert_(response == '0;0;1;0\n')


    def test_json(self):
        self.print_header()
        print "got initial broks"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker()
        data = 'GET services\nColumns: host_name description state\nOutputFormat: json'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'json wo headers__________\n%s\n%s\n' % (data, response)
        self.assert_(response == '[["test_host_0","test_ok_0",2]]\n')
        data = 'GET services\nColumns: host_name description state\nOutputFormat: json\nColumnHeaders: on'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print 'json with headers__________\n%s\n%s\n' % (data, response)
        self.assert_(response == '[["host_name","description","state"],["test_host_0","test_ok_0",2]]\n')
        #100% mklivesttaus: self.assert_(response == '[["host_name","description","state"],\n["test_host_0","test_ok_0",2]]\n')


    def test_thruk(self):
        self.print_header()
        print "got initial broks"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker()
        #---------------------------------------------------------------
        # get the full hosts table
        #---------------------------------------------------------------
        data = 'GET status\nColumns: livestatus_version program_version accept_passive_host_checks accept_passive_service_checks check_external_commands check_host_freshness check_service_freshness enable_event_handlers enable_flap_detection enable_notifications execute_host_checks execute_service_checks last_command_check last_log_rotation nagios_pid obsess_over_hosts obsess_over_services process_performance_data program_start interval_length'
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        data = """GET hosts
Stats: name != 
Stats: check_type = 0
Stats: check_type = 1
Stats: has_been_checked = 1
Stats: state = 0
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 1
StatsAnd: 2
Stats: has_been_checked = 1
Stats: state = 2
StatsAnd: 2
Stats: has_been_checked = 0
Stats: has_been_checked = 0
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: has_been_checked = 0
Stats: scheduled_downtime_depth > 0
StatsAnd: 2
Stats: state = 0
Stats: has_been_checked = 1
Stats: active_checks_enabled = 0
StatsAnd: 3
Stats: state = 0
Stats: has_been_checked = 1
Stats: scheduled_downtime_depth > 0
StatsAnd: 3
Stats: state = 1
Stats: has_been_checked = 1
Stats: acknowledged = 1
StatsAnd: 3
Stats: state = 1
Stats: scheduled_downtime_depth > 0
Stats: has_been_checked = 1
StatsAnd: 3
Stats: state = 1
Stats: active_checks_enabled = 0
Stats: has_been_checked = 1
StatsAnd: 3
Stats: state = 1
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
Stats: has_been_checked = 1
StatsAnd: 5
Stats: state = 2
Stats: acknowledged = 1
Stats: has_been_checked = 1
StatsAnd: 3
Stats: state = 2
Stats: scheduled_downtime_depth > 0
Stats: has_been_checked = 1
StatsAnd: 3
Stats: state = 2
Stats: active_checks_enabled = 0
StatsAnd: 2
Stats: state = 2
Stats: active_checks_enabled = 1
Stats: acknowledged = 0
Stats: scheduled_downtime_depth = 0
Stats: has_been_checked = 1
StatsAnd: 5
Stats: is_flapping = 1
Stats: flap_detection_enabled = 0
Stats: notifications_enabled = 0
Stats: event_handler_enabled = 0
Stats: active_checks_enabled = 0
Stats: accept_passive_checks = 0
Stats: state = 1
Stats: childs !=
StatsAnd: 2
Separators: 10 59 44 124
ResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        data = """GET comments
Columns: host_name source type author comment entry_time entry_type expire_time
Filter: service_description ="""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        data = """GET hosts
Columns: comments has_been_checked state name address acknowledged notifications_enabled active_checks_enabled is_flapping scheduled_downtime_depth is_executing notes_url_expanded action_url_expanded icon_image_expanded icon_image_alt last_check last_state_change plugin_output next_check long_plugin_output
Separators: 10 59 44 124
ResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        duration = 180
        now = time.time()
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_001;test_warning_00;%d;%d;0;0;%d;lausser;blablubsvc" % (now, now, now + duration, duration)
        print cmd
        self.sched.run_external_command(cmd)
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_001;%d;%d;0;0;%d;lausser;blablubhost" % (now, now, now + duration, duration)
        print cmd
        self.sched.run_external_command(cmd)
        self.update_broker()
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.update_broker()
        self.scheduler_loop(3, [[svc, 2, 'BAD']])
        self.update_broker()
        data = """GET downtimes
Filter: service_description = 
Columns: author comment end_time entry_time fixed host_name id start_time
Separators: 10 59 44 124
ResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        data = """GET comments
Filter: service_description = 
Columns: author comment
Separators: 10 59 44 124
ResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        data = """GET services
Filter: has_been_checked = 1
Filter: check_type = 0
Stats: sum has_been_checked
Stats: sum latency
Separators: 10 59 44 124
ResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        data = """GET services
Filter: has_been_checked = 1
Filter: check_type = 0
Stats: sum has_been_checked
Stats: sum latency
Stats: sum execution_time
Stats: min latency
Stats: min execution_time
Stats: max latency
Stats: max execution_time
Separators: 10 59 44 124
ResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        data = """GET services\nFilter: has_been_checked = 1\nFilter: check_type = 0\nStats: sum has_been_checked as has_been_checked\nStats: sum latency as latency_sum\nStats: sum execution_time as execution_time_sum\nStats: min latency as latency_min\nStats: min execution_time as execution_time_min\nStats: max latency as latency_max\nStats: max execution_time as execution_time_max\n\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        data = """GET hostgroups\nColumnHeaders: on\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        data = """GET hosts\nColumns: name groups\nColumnHeaders: on\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        
        data = """GET hostgroups\nColumns: name num_services num_services_ok\nColumnHeaders: on\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        data = """GET hostgroups\nColumns: name num_services_pending num_services_ok num_services_warning num_services_critical num_services_unknown worst_service_state worst_service_hard_state\nColumnHeaders: on\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']])
        self.update_broker()
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 1, 'WARNING']])
        self.update_broker()
        
        print "WARNING SOFT;1"
        # worst_service_state 1, worst_service_hard_state 0
        data = """GET hostgroups\nColumns: name num_services_pending num_services_ok num_services_warn num_services_crit num_services_unknown worst_service_state worst_service_hard_state\nColumnHeaders: on\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 1, 'WARNING']])
        self.update_broker()
        print "WARNING HARD;3"
        # worst_service_state 1, worst_service_hard_state 1
        data = """GET hostgroups\nColumns: name num_services_pending num_services_ok num_services_warn num_services_crit num_services_unknown worst_service_state worst_service_hard_state\nColumnHeaders: on\nResponseHeader: fixed16"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        for s in self.livestatus_broker.livestatus.services.values():
            print "%s %d %s;%d" % (s.state, s.state_id, s.state_type, s.attempt)


    def test_thruk_comments(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)

        print "downtime was scheduled. check its activity and the comment"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)
        self.assert_(svc.comments[0] in self.sched.comments.values())
        self.assert_(svc.downtimes[0].comment_id == svc.comments[0].id)

        now = time.time()
        cmd = "[%lu] ADD_SVC_COMMENT;test_host_0;test_ok_0;1;lausser;comment" % now
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.assert_(len(self.sched.comments) == 2)
        self.assert_(len(svc.comments) == 2)

        self.update_broker()

        data = """GET comments\nColumns: host_name service_description id source type author comment entry_time entry_type persistent expire_time expires\nFilter: service_description !=\nResponseHeader: fixed16\nOutputFormat: json\n"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response


    def test_thruk_logs(self):
        self.print_header()
        start = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 1, 'WARNING']])
        self.update_broker()
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        now = time.time()
        cmd = "[%lu] ADD_SVC_COMMENT;test_host_0;test_ok_0;1;lausser;comment" % now
        self.sched.run_external_command(cmd)
        time.sleep(1)
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 2, 'DOWN'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        end = time.time()

        # show history for service
        data = """GET log
Columns: time type options state
Filter: time >= """ + str(int(start)) + """
Filter: time <= """ + str(int(end)) + """
Filter: type = SERVICE ALERT
Filter: type = HOST ALERT
Filter: type = SERVICE FLAPPING ALERT
Filter: type = HOST FLAPPING ALERT
Filter: type = SERVICE DOWNTIME ALERT
Filter: type = HOST DOWNTIME ALERT
Or: 6
Filter: host_name = test_host_0
Filter: service_description = test_ok_0
And: 3
Filter: type ~ starting...
Filter: type ~ shutting down...
Or: 3
Filter: current_service_description != 

Filter: service_description = 
Filter: host_name != 
And: 2
Filter: service_description = 
Filter: host_name = 
And: 2
Or: 3"""

        response = self.livestatus_broker.livestatus.handle_request(data)
        print response

    def test_thruk_logs_alerts_summary(self):
        self.print_header()
        start = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 1, 'WARNING']])
        self.update_broker()
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        now = time.time()
        cmd = "[%lu] ADD_SVC_COMMENT;test_host_0;test_ok_0;1;lausser;comment" % now
        self.sched.run_external_command(cmd)
        time.sleep(1)
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 2, 'DOWN'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        end = time.time()

        # is this an error in thruk?

        data = """GET log
Filter: options ~ ;HARD;
Filter: type = HOST ALERT
Filter: time >= 1284056080
Filter: time <= 1284660880
Filter: current_service_description != 
Filter: service_description = 
Filter: host_name != 
And: 2
Filter: service_description = 
Filter: host_name = 
And: 2
Or: 3
Columns: time state state_type host_name service_description current_host_groups current_service_groups plugin_output"""

        response = self.livestatus_broker.livestatus.handle_request(data)
        print response


    def test_thruk_logs_current(self):
        self.print_header()
        start = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 1, 'WARNING']])
        self.update_broker()
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        now = time.time()
        cmd = "[%lu] ADD_SVC_COMMENT;test_host_0;test_ok_0;1;lausser;comment" % now
        self.sched.run_external_command(cmd)
        time.sleep(1)
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 2, 'DOWN'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 0, 'UUP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
#        time.sleep(1)
#        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 2, 'DOWN'], [svc, 0, 'OK']], do_sleep=False)
#        self.update_broker()
        end = time.time()
        
        # show history for service
        data = """GET log
Columns: time type options state current_host_name
Filter: time >= """ + str(int(start)) + """
Filter: time <= """ + str(int(end)) + """
Filter: type = SERVICE ALERT
Filter: type = HOST ALERT
Filter: type = SERVICE FLAPPING ALERT
Filter: type = HOST FLAPPING ALERT
Filter: type = SERVICE DOWNTIME ALERT
Filter: type = HOST DOWNTIME ALERT
Or: 6
Filter: current_host_name = test_host_0
Filter: current_service_description = test_ok_0
And: 2"""
        data = """GET log
Columns: time type options state current_host_name
Filter: time >= """ + str(int(start)) + """
Filter: time <= """ + str(int(end)) + """
Filter: current_host_name = test_host_0
Filter: current_service_description = test_ok_0
And: 2"""

        response = self.livestatus_broker.livestatus.handle_request(data)
        print response


    def test_thruk_tac_svc(self):
        self.print_header()
        start = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 1, 'WARNING']])
        self.update_broker()
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        now = time.time()
        cmd = "[%lu] ADD_SVC_COMMENT;test_host_0;test_ok_0;1;lausser;comment" % now
        self.sched.run_external_command(cmd)
        time.sleep(1)
        self.scheduler_loop(1, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 2, 'DOWN'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
        time.sleep(1)
        self.scheduler_loop(3, [[host, 0, 'UUP'], [router, 0, 'UP'], [svc, 0, 'OK']], do_sleep=False)
        self.update_broker()
#        time.sleep(1)
#        self.scheduler_loop(3, [[host, 0, 'UP'], [router, 2, 'DOWN'], [svc, 0, 'OK']], do_sleep=False)
#        self.update_broker()
        end = time.time()
        
        # show history for service
        data = """GET services
Filter: has_been_checked = 1
Filter: check_type = 0
Stats: sum has_been_checked
Stats: sum latency
Stats: sum execution_time
Stats: min latency
Stats: min execution_time
Stats: max latency
Stats: max execution_time"""

        response = self.livestatus_broker.livestatus.handle_request(data)
        print response


    def test_columns(self):
        self.print_header()
        self.update_broker()
        #---------------------------------------------------------------
        # get the columns meta-table
        #---------------------------------------------------------------
        data = """GET columns"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response


    def test_scheduler_table(self):
        self.print_header()
        creation_tab = {'scheduler_name' : 'scheduler-1', 'address' : 'localhost', 'spare' : '0'}
        sched = SchedulerLink(creation_tab)
        sched.pythonize()
        sched.alive = True
        b = sched.get_initial_status_brok()
        self.sched.add(b)
        creation_tab = {'scheduler_name' : 'scheduler-2', 'address' : 'othernode', 'spare' : '1'}
        sched = SchedulerLink(creation_tab)
        sched.pythonize()
        sched.alive = True
        b2 = sched.get_initial_status_brok()
        self.sched.add(b2)

        self.update_broker()
        #---------------------------------------------------------------
        # get the columns meta-table
        #---------------------------------------------------------------
        data = """GET schedulers"""
        response = self.livestatus_broker.livestatus.handle_request(data)
        print response
        good_response = """address;alive;name;port;spare;weight
localhost;1;scheduler-1;7768;0;1
othernode;1;scheduler-2;7768;1;1
"""
        print response == good_response
        self.assert_(response == good_response)


if __name__ == '__main__':
    import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="Thruk.profile" )

