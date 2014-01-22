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
        self.setup_with_file('etc/shinken_contactgroups_plus_inheritance.cfg')

    def _dump(self, h):
        print "Dumping host", h.get_name()
        print h.contact_groups
        for c in h.contacts:
            print "->",c.get_name()
                        

    def test_contactgroups_plus_inheritance(self):
        host0 = self.sched.hosts.find_by_name("test_host_0")
        # HOST 1 should have 2 group of contacts
        # WARNING, it's a string, not the real objects!
        self._dump(host0)

        self.assert_("test_contact_1" in [c .get_name() for c in host0.contacts])
        self.assert_("test_contact_2" in [c .get_name() for c in host0.contacts])

        host2 = self.sched.hosts.find_by_name("test_host_2")
        self._dump(host2)
        self.assert_("test_contact_1" in [c .get_name() for c in host2.contacts])

        host3 = self.sched.hosts.find_by_name("test_host_3")
        self._dump(host3)
        self.assert_("test_contact_1" in [c .get_name() for c in host3.contacts])
        self.assert_("test_contact_2" in [c .get_name() for c in host3.contacts])

        host4 = self.sched.hosts.find_by_name("test_host_4")
        self._dump(host4)
        self.assert_("test_contact_1" in [c .get_name() for c in host4.contacts])

        host5 = self.sched.hosts.find_by_name("test_host_5")
        self._dump(host5)
        self.assert_("test_contact_1" in [c .get_name() for c in host5.contacts])
        self.assert_("test_contact_2" in [c .get_name() for c in host5.contacts])

        
        host6 = self.sched.hosts.find_by_name("test_host_6")
        self._dump(host6)
        self.assert_("test_contact_1" in [c .get_name() for c in host6.contacts])
        self.assert_("test_contact_2" in [c .get_name() for c in host6.contacts])


if __name__ == '__main__':
    unittest.main()
