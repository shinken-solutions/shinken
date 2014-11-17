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


class TestFreshness(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_freshness.cfg')

    # Check if the check_freshnes is doing it's job
    def test_check_freshness(self):
        self.print_header()
        # We want an eventhandelr (the perfdata command) to be put in the actions dict
        # after we got a service check
        now = time.time()
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc.active_checks_enabled = False
        self.assertEqual(True, svc.check_freshness)
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        # We do not want to be just a string but a real command
        print "Additonal freshness latency", svc.__class__.additional_freshness_latency
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "Addi:", svc.last_state_update, svc.freshness_threshold, svc.check_freshness
        # By default check fresh ness is set at false, so no new checks
        self.assertEqual(0, len(svc.actions))
        svc.do_check_freshness()
        self.assertEqual(0, len(svc.actions))

        # We make it 10s less than it was
        svc.last_state_update = svc.last_state_update - 10

        #svc.check_freshness = True
        # Now we active it, with a too small value (now - 10s is still higer than now - (1 - 15, the addition time)
        # So still no check
        svc.freshness_threshold = 1
        print "Addi:", svc.last_state_update, svc.freshness_threshold, svc.check_freshness
        svc.do_check_freshness()
        self.assertEqual(0, len(svc.actions))

        # Now active globaly the check freshness
        cmd = "[%lu] ENABLE_SERVICE_FRESHNESS_CHECKS" % now
        self.sched.run_external_command(cmd)

        # Ok, now, we remove again 10s. Here we will saw the new entry
        svc.last_state_update = svc.last_state_update - 10
        svc.do_check_freshness()
        self.assertEqual(1, len(svc.actions))
        # And we check for the message in the log too
        self.assert_any_log_match('The results of service.*')


if __name__ == '__main__':
    unittest.main()
