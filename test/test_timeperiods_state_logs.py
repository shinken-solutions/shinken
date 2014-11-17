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


class TestTPStateLog(ShinkenTest):

    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/shinken_timeperiods_state_logs.cfg')


    # A timeperiod state change should raise a log, and only when change.
    def test_tp_state_log(self):
        now = time.time()
        tp = self.sched.timeperiods.find_by_name('24x7')

        self.assertIsNot(tp, None)
        tp.check_and_log_activation_change()
        self.assert_any_log_match("TIMEPERIOD TRANSITION: 24x7;-1;1")
        self.show_and_clear_logs()

        # Now make this tp unable to be active again by removing al it's daterange:p
        dr = tp.dateranges
        tp.dateranges = []
        tp.check_and_log_activation_change()
        self.assert_any_log_match("TIMEPERIOD TRANSITION: 24x7;1;0")
        self.show_and_clear_logs()

        # Ok, let get back to work :)
        tp.dateranges = dr
        tp.check_and_log_activation_change()
        self.assert_any_log_match("TIMEPERIOD TRANSITION: 24x7;0;1")
        self.show_and_clear_logs()



if __name__ == '__main__':
    unittest.main()
