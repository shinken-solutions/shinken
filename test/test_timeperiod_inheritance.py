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
        self.setup_with_file('etc/shinken_timeperiod_inheritance.cfg')

    def test_dummy(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the Timeperiods"
        now = time.time()
        tp = self.sched.timeperiods.find_by_name("24x7")
        print "TP", tp.__dict__

        # sunday should be inherited from templates
        print "Check for sunday in the timeperiod"
        got_sunday = False
        for dr in tp.dateranges:
            print dr.__dict__
            if hasattr(dr, 'day') and dr.day == 'sunday':
                got_sunday = True
        self.assertEqual(True, got_sunday)


if __name__ == '__main__':
    unittest.main()
