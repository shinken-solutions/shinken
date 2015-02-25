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


class TestNullInheritance(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_nullinheritance.cfg')

    # We search to see if null as value really delete the inheritance
    # of a property
    def test_null_inheritance(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        self.assertEqual('', svc.icon_image)


if __name__ == '__main__':
    unittest.main()
