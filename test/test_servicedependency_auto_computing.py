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

from shinken_test import ShinkenTest, unittest


class TestServiceDependencyAutoComputing(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_servicedependency_auto_computing.cfg')
        if hasattr(self, 'sched'):
            # There are no common host between svc0 and svc3 therefore
            # no servicedependency can be created and shinken should
            # print the error msg :
            # "[Shinken] [items] Service svc3 not found for host
            #  [Shinken] [items] Service svc0 not found for host
            #  [Shinken] 	servicedependencies conf incorrect!!"
            self.fail("The configuration should not be correct")

    def test_matching_svc(self):
        services = self.conf.services
        svcs = []
        svcs.append(services.find_srv_by_name_and_hostname('h0', 'svc0'))
        svcs.append(services.find_srv_by_name_and_hostname('h1', 'svc0'))
        svcs.append(services.find_srv_by_name_and_hostname('h2', 'svc0'))
        for svc in svcs:
            self.assertIsNotNone(svc)
            dep_svcs = [info_dep[0] for info_dep in svc.act_depend_of_me]
            self.assertNotEqual(dep_svcs, [])
            for dep_svc in dep_svcs:
                self.assertEqual(dep_svc.host_name, svc.host_name)
                self.assertEqual(dep_svc.service_description, 'svc2')

    def test_multiple_srv_description(self):
        services = self.conf.services
        expected_dep_svc = {'h1': ['svc2'], 'h2': ['svc2'],\
                            'h3': ['svc2', 'svc3'], 'h4': ['svc2', 'svc3']}
        svcs = []
        svcs.append(services.find_srv_by_name_and_hostname('h1', 'svc1'))
        svcs.append(services.find_srv_by_name_and_hostname('h2', 'svc1'))
        svcs.append(services.find_srv_by_name_and_hostname('h3', 'svc1'))
        svcs.append(services.find_srv_by_name_and_hostname('h4', 'svc1'))
        for svc in svcs:
            self.assertIsNotNone(svc)
            dep_svcs = [info_dep[0] for info_dep in svc.act_depend_of_me]
            description = expected_dep_svc[svc.host_name]
            for dep_svc in dep_svcs:
                self.assertTrue(dep_svc.service_description in description)
                description.remove(dep_svc.service_description)
            self.assertEqual(description, [])


if __name__ == '__main__':
    unittest.main()
