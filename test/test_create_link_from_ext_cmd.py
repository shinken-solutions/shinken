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


class TestCreateLinkFromExtCmd(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/shinken_1r_1h_1s.cfg')

    def test_simple_host_link(self):
        now = int(time.time())
        h = self.sched.hosts.find_by_name('test_host_0')
        self.assert_(h is not None)
        h.act_depend_of = []
        r = self.sched.hosts.find_by_name('test_router_0')
        self.assert_(r is not None)
        r.act_depend_of = []
        e = ExternalCommandManager(self.conf, 'dispatcher')
        cmd = "[%lu] ADD_SIMPLE_HOST_DEPENDENCY;test_host_0;test_router_0" % now
        self.sched.run_external_command(cmd)
        self.assert_(h.is_linked_with_host(r))

        # Now we remove this link
        cmd = "[%lu] DEL_HOST_DEPENDENCY;test_host_0;test_router_0" % now
        self.sched.run_external_command(cmd)
        self.assert_(not h.is_linked_with_host(r))



if __name__ == '__main__':
    unittest.main()
