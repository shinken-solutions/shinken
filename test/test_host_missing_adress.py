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
        self.setup_with_file('etc/shinken_host_missing_adress.cfg')

    def test_host_missing_adress(self):
        # The router got no adress. It should be set with the
        # host_name instead and should nto be an error
        now = time.time()
        router = self.sched.hosts.find_by_name("test_router_0")
        print "router adress:", router.address
        self.assertEqual('test_router_0', router.address)

if __name__ == '__main__':
    unittest.main()
