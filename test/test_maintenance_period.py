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
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class TestConfig(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/nagios_maintenance_period.cfg')

    #Change ME :)
    def test_check_defined_maintenance_period(self):
        a_24_7 = self.sched.timeperiods.find_by_name("24x7")
        print "Get the hosts and services"
        test_router_0 = self.sched.hosts.find_by_name("test_router_0")
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_nobody = self.sched.hosts.find_by_name("test_nobody")

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_ok_0")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_nobody", "test_ok_0")

        #Standard links
        self.assert_(test_router_0.maintenance_period == a_24_7)
        self.assert_(test_host_0.maintenance_period == None)
        self.assert_(test_nobody.maintenance_period == None)

        #Now inplicit inheritance
        #This one is defined in the service conf
        self.assert_(svc1.maintenance_period == a_24_7)
        #This one is empty, because maintenance_period are not inherited from the
        #host like check/notification_periods
        self.assert_(svc2.maintenance_period == None)
        #This one got nothing :)
        self.assert_(svc3.maintenance_period == None)


if __name__ == '__main__':
    unittest.main()

