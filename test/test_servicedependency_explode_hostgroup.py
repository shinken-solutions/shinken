#!/usr/bin/env python2.6
#Copyright (C) 2009-2014:
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
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class TestServiceDepAndGroups(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/shinken_servicedependency_explode_hostgroup.cfg')


    #Change ME :)
    def test_explodehostgroup(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        svc = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "SNMP")
        self.assertEqual(len(svc.act_depend_of_me), 2)

        service_dependencies = []
        service_dependency_postfix = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "POSTFIX")
        service_dependency_cpu = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "CPU")
        service_dependencies.append(service_dependency_postfix)
        service_dependencies.append(service_dependency_cpu)

        # Is service correctly depend of first one
        all_services = []
        for services in svc.act_depend_of_me:
            all_services.extend(services)
        self.assertIn(service_dependency_postfix, all_services)
        self.assertIn(service_dependency_cpu, all_services)

if __name__ == '__main__':
    unittest.main()

