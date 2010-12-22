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
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_realms.cfg')

    
    # We check for each host, if they are in the good realm
    def test_realm_assigntion(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        realm1 = self.conf.realms.find_by_name('realm1')
        self.assert_(realm1 != None)
        realm2 = self.conf.realms.find_by_name('realm2')
        self.assert_(realm2 != None)
        test_host_realm1 = self.sched.hosts.find_by_name("test_host_realm1")
        self.assert_(test_host_realm1 != None)
        self.assert_(test_host_realm1.realm == realm1)
        test_host_realm2 = self.sched.hosts.find_by_name("test_host_realm2")
        self.assert_(test_host_realm2 != None)
        self.assert_(test_host_realm2.realm == realm2)



if __name__ == '__main__':
    unittest.main()

