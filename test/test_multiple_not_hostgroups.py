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


class TestMultipleNotHG(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_multiple_not_hostgroups.cfg')

    def test_dummy(self):

        for s in self.sched.services:
            print "SERVICES", s.get_full_name()
        
        svc = self.sched.services.find_srv_by_name_and_hostname("hst_in_BIG", "THE_SERVICE")
        self.assertIsNot(svc, None)

        svc = self.sched.services.find_srv_by_name_and_hostname("hst_in_IncludeLast", "THE_SERVICE")
        self.assertIsNot(svc, None)

        svc = self.sched.services.find_srv_by_name_and_hostname("hst_in_NotOne", "THE_SERVICE")
        self.assertIs(None, svc)

        svc = self.sched.services.find_srv_by_name_and_hostname("hst_in_NotTwo", "THE_SERVICE")
        self.assertIs(None, svc)


if __name__ == '__main__':
    unittest.main()
