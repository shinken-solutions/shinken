#!/usr/bin/env python2
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


class TestCheckModulations(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_checkmodulations.cfg')

    def test_dummy(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("host_modulated")
        self.assertIsNot(host, None)
        print host.checkmodulations

        mod = self.sched.checkmodulations.find_by_name("MODULATION")
        self.assertIsNot(mod, None)

        self.assertIn(mod, host.checkmodulations)

        c = None
        for c in host.checks_in_progress:
            print c.command
            self.assertEqual('plugins/nothing VALUE', c.command)


if __name__ == '__main__':
    unittest.main()
