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


class TestCustomsonservicehosgroups(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_customs_on_service_hosgroups.cfg')

    # We look for 3 services: on defined as direct on 1 hosts, on other
    # on 2 hsots, and a last one on a hostgroup
    def test_check_for_custom_copy_on_serice_hostgroups(self):
        # The one host service
        svc_one_host = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_on_1_host")
        self.assertIsNot(svc_one_host, None)
        # The 2 hosts service(s)
        svc_two_hosts_1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_on_2_hosts")
        self.assertIsNot(svc_two_hosts_1, None)
        svc_two_hosts_2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_on_2_hosts")
        self.assertIsNot(svc_two_hosts_2, None)
        # Then the one defined on a hostgroup
        svc_on_group = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_on_group")
        self.assertIsNot(svc_on_group, None)

        # Each one should have customs
        self.assertEqual('custvalue', svc_one_host.customs['_CUSTNAME'])
        self.assertEqual('custvalue', svc_two_hosts_1.customs['_CUSTNAME'])
        self.assertEqual('custvalue', svc_two_hosts_2.customs['_CUSTNAME'])
        self.assertEqual('custvalue', svc_on_group.customs['_CUSTNAME'])






if __name__ == '__main__':
    unittest.main()
