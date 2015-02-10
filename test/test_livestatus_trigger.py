#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#
# This file is used to test host- and service-downtimes.
#


import sys
import time


from shinken_test import (
    unittest,
    original_time_sleep,
    original_time_time,
)

from mock_livestatus import mock_livestatus_handle_request
from test_livestatus import LiveStatus_Template


sys.setcheckinterval(10000)

# we have an external process, so we must un-fake time functions
time.time = original_time_time
time.sleep = original_time_sleep


@mock_livestatus_handle_request
class TestConfigSmall(LiveStatus_Template):

    _setup_config_file = 'etc/nagios_1r_1h_1s.cfg'

    def test_host_wait(self):
        self.print_header()
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker(True)
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."
        print "i updated the broker at", time.time()
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."

        #---------------------------------------------------------------
        # get only the host names and addresses
        #---------------------------------------------------------------
        request = """
GET hosts
Columns: name state address
ColumnHeaders: on
Filter: host_name = test_host_0
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        good_response = """name;state;address
test_host_0;0;127.0.0.1
"""
        self.assert_(isinstance(response, str))
        self.assert_(self.lines_equal(response, good_response))

        request = """
GET hosts
Columns: name state address last_check
ColumnHeaders: on
Filter: host_name = test_host_0
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response

        time.sleep(1)
        now = time.time()
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."
        print "i query with trigger at", now
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."

        request = """
COMMAND [%d] SCHEDULE_FORCED_HOST_CHECK;test_host_0;%d

GET hosts
WaitObject: test_host_0
WaitCondition: last_check >= %d
WaitTimeout: 10000
WaitTrigger: check
Columns: last_check state plugin_output
Filter: host_name = test_host_0
Localtime: %d
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
ColumnHeaders: off
""" % (now, now, now, now)

        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "response is", response
        self.assert_(isinstance(response, list))
        self.assert_('wait' in [q.my_type for q in response])
        self.assert_('query' in [q.my_type for q in response])

        # launch the query, which must return an empty result
        query = [q for q in response if q.my_type == "query"][0]
        wait = [q for q in response if q.my_type == "wait"][0]
        result = wait.condition_fulfilled()
        # not yet...the plugin must run first
        self.assert_(not result)
        # result = query.launch_query()
        # response = query.response
        # response.format_live_data(result, query.columns, query.aliases)
        # output, keepalive = response.respond()
        # print "output is", output

        time.sleep(1)
        result = wait.condition_fulfilled()
        # not yet...the plugin must run first
        print "must be empty", result
        self.assert_(not result)

        # update the broker
        # wait....launch the wait
        # launch the query again, which must return a result
        self.scheduler_loop(3, [[host, 2, 'DOWN']])
        self.update_broker(True)

        time.sleep(1)
        result = wait.condition_fulfilled()
        # the plugin has run
        print "must not be empty", result
        self.assert_(result)

        result = query.launch_query()
        response = query.response
        response.columnheaders = "on"
        print response
        response.format_live_data(result, query.columns, query.aliases)
        output, keepalive = response.respond()
        output = ''.join(output) # response.respond() now return a LiveStatusListResponse instance..
        self.assert_(output.strip())

    def test_multiple_externals(self):
        self.print_header()
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker(True)
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."
        print "i updated the broker at", time.time()
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."

        #---------------------------------------------------------------
        # get only the host names and addresses
        #---------------------------------------------------------------
        request = """COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        good_response = ""
        self.assert_(isinstance(response, str))
        self.assert_(self.lines_equal(response, good_response))





if __name__ == '__main__':
    # import cProfile
    command = """unittest.main()"""
    unittest.main()
    # cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )
