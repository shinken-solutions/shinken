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


class TestComplexHostgroups(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_complex_hostgroups.cfg')

    def get_svc(self):
        return self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

    def find_service(self, name, desc):
        return self.sched.services.find_srv_by_name_and_hostname(name, desc)

    def find_host(self, name):
        return self.sched.hosts.find_by_name(name)

    def find_servicegroup(self, name):
        return self.sched.servicegroups.find_by_name(name)

    def dump_hosts(self, svc):
        for h in svc.host_name:
            print h

    def test_complex_hostgroups(self):
        # find example service
        svc = self.get_svc()
        # find two servicegroups, make sure they exist
        sg1 = self.find_servicegroup("servicegroup_01")
        self.assert_(sg1 is not None)
        sg2 = self.find_servicegroup("ok")
        self.assert_(sg2 is not None)
        # test if svc is a member of sg1 AND sg2
        self.assert_(svc in sg1.members)
        self.assert_(svc in sg2.members)
        # test if services "servicegroup" attribute contains sg1 and sg2
        self.assert_(sg1 in svc.servicegroups)
        self.assert_(sg2 in svc.servicegroups)


if __name__ == '__main__':
    unittest.main()
