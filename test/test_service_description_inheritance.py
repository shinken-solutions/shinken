#!/usr/bin/env python
# Copyright (C) 2009-2014:
#    Sebastien Coavoux, s.coavoux@free.fr
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


class TestServiceDescriptionInheritance(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_service_description_inheritance.cfg')

    def test_service_description_inheritance(self):
        self.print_header()
        svc = self.sched.services.find_srv_by_name_and_hostname("MYHOST", "SSH")
        self.assertIsNotNone(svc)


    def test_service_description_inheritance_multihosts(self):
        self.print_header()
        for hname in ["MYHOST2", "MYHOST3"]:
            svc = self.sched.services.find_srv_by_name_and_hostname(hname, "SSH")
            self.assertIsNotNone(svc)

    def test_service_description_inheritance_with_defined_value(self):
	for hname in ["MYHOST4"]:
            svc = self.sched.services.find_srv_by_name_and_hostname(hname, "SUPER_SSH")
            self.assertIsNotNone(svc)
	for hname in ["MYHOST5"]:
            svc = self.sched.services.find_srv_by_name_and_hostname(hname, "GOOD_SSH")
            self.assertIsNotNone(svc)

    def test_service_description_inheritance_with_duplicate(self):
	for hname in ["MYHOST6"]:
            svc = self.sched.services.find_srv_by_name_and_hostname(hname, "sys: cpu1")
            self.assertIsNotNone(svc)
            svc1 = self.sched.services.find_srv_by_name_and_hostname(hname, "sys: /tmp")
            self.assertIsNotNone(svc1)

if __name__ == '__main__':
    unittest.main()
