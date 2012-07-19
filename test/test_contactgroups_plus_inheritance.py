#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
# This file is used to test attribute inheritance and the right order
#

from shinken_test import *


class TestPlusInInheritance(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_contactgroups_plus_inheritance.cfg')

    def test_contactgroups_plus_inheritance(self):
        host1 = self.sched.hosts.find_by_name("test_host_0")
        # HOST 1 should have 2 group of contacts
        # WARNING, it's a string, not the real objects!
        print host1.contact_groups

        for c in host1.contacts:
            print c.get_name()

        self.assert_("test_contact_1" in [c .get_name() for c in host1.contacts])
        self.assert_("test_contact_2" in [c .get_name() for c in host1.contacts])


if __name__ == '__main__':
    unittest.main()
