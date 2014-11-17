#!/usr/bin/env python
# Copyright (C) 2009-2014:
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


class TestConfig(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_resultmodulation.cfg')

    def get_svc(self):
        return self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

    def get_host(self):
        return self.sched.hosts.find_by_name("test_host_0")

    def get_router(self):
        return self.sched.hosts.find_by_name("test_router_0")

    def test_service_resultmodulation(self):
        svc = self.get_svc()
        host = self.get_host()
        router = self.get_router()

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [svc, 2, 'BAD | value1=0 value2=0'],])
        self.assertEqual('UP', host.state)
        self.assertEqual('HARD', host.state_type)

        # This service got a result modulation. So Criticals are in fact
        # Warnings. So even with some CRITICAL (2), it must be warning
        self.assertEqual('WARNING', svc.state)

        # If we remove the resultmodulations, we should have theclassic behavior
        svc.resultmodulations = []
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.assertEqual('CRITICAL', svc.state)

        # Now look for the inheritaed thing
        # resultmodulation is a inplicit inherited parameter
        # and router define it, but not test_router_0/test_ok_0. So this service should also be impacted
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_ok_0")
        self.assertEqual(router.resultmodulations, svc2.resultmodulations)

        self.scheduler_loop(2, [[svc2, 2, 'BAD | value1=0 value2=0']])
        self.assertEqual('WARNING', svc2.state)


if __name__ == '__main__':
    unittest.main()
