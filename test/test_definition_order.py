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


class TestDefinitionOrder(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_definition_order.cfg')

    def test_definition_order(self):
        print "Get the hosts and services"
        now = time.time()
        svc_specific = self.sched.services.find_srv_by_name_and_hostname("test_host_specific", "ZE-SERVICE")
        svc_generic  = self.sched.services.find_srv_by_name_and_hostname("test_host_generic", "ZE-SERVICE")
        
        self.assert_(svc_specific is not None)
        self.assert_(svc_generic is not None)

        print svc_generic.check_command.command.command_name
        self.assert_(svc_generic.check_command.command.command_name == 'general')
        
        print svc_specific.check_command.command.command_name
        self.assert_(svc_specific.check_command.command.command_name == 'specific')
        
        

if __name__ == '__main__':
    unittest.main()
