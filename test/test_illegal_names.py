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
    # setUp is inherited from ShinkenTest

    def test_illegal_caracter_in_names(self):
        illegal_caracts = self.sched.conf.illegal_object_name_chars
        print "Illegal caracters: %s" % illegal_caracts
        host = self.sched.hosts.find_by_name("test_host_0")
        # should be correct
        self.assertTrue(host.is_correct())

        # Now change the name with incorrect caract
        for c in illegal_caracts:
            host.host_name = 'test_host_0' + c
            # and Now I want an incorrect here
            self.assertEqual(False, host.is_correct())

if __name__ == '__main__':
    unittest.main()
