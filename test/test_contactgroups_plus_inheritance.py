#!/usr/bin/env python
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

#
# This file is used to test attribute inheritance and the right order
#

from shinken_test import *

class TestConfig(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_contactgroups_plus_inheritance.cfg')
    
    #Change ME :)
    def test_action_url(self):
        host1 = self.sched.hosts.find_by_name("test_host_0")
        #HOST 1 should have 2 group of contacts
        for cg in host1.contact_groups:
            print cg
        self.assert_("test_contact_1" in host1.contact_groups)
        self.assert_("test_contact_2" in host1.contact_groups)

if __name__ == '__main__':
    unittest.main()


