#!/usr/bin/env python
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
# This file is used to test reading and processing of config files
#

from shinken_test import *


class TestSnapshot(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_snapshot.cfg')

    def test_dummy(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("GotSNAP")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("GotSNAP", "SRV")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(5, [[host, 2, 'DOWN'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.assertEqual('DOWN', host.state)
        self.assertEqual('HARD', host.state_type)
        
        self.assert_any_log_match('HOST SNAPSHOT.*')
        self.assert_log_match(2, 'HOST SNAPSHOT.*')

        self.assert_any_log_match('SERVICE SNAPSHOT.*')
        self.assert_log_match(4, 'SERVICE SNAPSHOT.*')

        self.show_and_clear_logs()
        
        broks = self.sched.broks.values()
        [b.prepare() for b in broks]
        types = set([b.type for b in broks])
        print types
        self.assertIn('service_snapshot', types)
        self.assertIn('host_snapshot', types)

if __name__ == '__main__':
    unittest.main()
