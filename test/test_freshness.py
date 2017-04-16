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

from __future__ import with_statement

import mock
from shinken.util import format_t_into_dhms_format

from shinken_test import *

import shinken.objects.host
from shinken.objects.host import Host


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

    def test_scheduler_check_freshness(self):
        now = time.time()
        sched = self.sched

        # we need a host to act on :
        host = sched.hosts.find_by_name('test_host_0')

        # prepare it :
        # some cleaning:
        del host.actions[:]
        del host.checks_in_progress[:]
        host.update_in_checking()  # and update_in_checking()
        # so that host.in_checking == False

        host.last_state_update = now - 60*60*12
        host.freshness_threshold = 60*60 * 24  # 24 hour
        host.passive_checks_enabled = True
        host.active_checks_enabled = False
        host.check_period = None
        host.freshness_threshold = 15
        host.check_freshness = True

        Host.global_check_freshness = True  # we also need to enable this

        # that's what we should get after calling check_freshness():
        expected_host_next_chk = host.next_chk
        expected_brok_id = Brok.id

        with mock.patch('shinken.objects.host.logger') as log_mock:
            with mock.patch('time.time', return_value=now):

                # pre-asserts :
                self.assertFalse(host.actions)
                self.assertFalse(host.checks_in_progress)
                self.assertFalse(sched.broks)
                self.assertFalse(sched.checks)

                # now call the scheduler.check_freshness() :
                self.sched.check_freshness()

        # and here comes the post-asserts :
        self.assertEqual(1, len(host.actions),
                         '1 action should have been created for the host.')
        chk = host.actions[0]

        self.assertEqual(host.actions, host.checks_in_progress,
                         'the host should have got 1 check in progress.')

        self.assertEqual(1, len(sched.checks),
                         '1 check should have been created in the scheduler checks dict.')

        # now assert that the scheduler has also got the new check:

        # in its checks:
        self.assertIn(chk.id, sched.checks)
        self.assertIs(chk, sched.checks[chk.id])

        log_mock.warning.assert_called_once_with(
            "The results of host '%s' are stale by %s "
            "(threshold=%s).  I'm forcing an immediate check "
            "of the host.",
            host.get_name(),
            format_t_into_dhms_format(int(now - host.last_state_update)),
            format_t_into_dhms_format(int(now - host.freshness_threshold)),
        )

        # finally assert the there had a new host_next_scheduler brok:
        self.assertEqual(1, len(sched.broks),
                         '1 brok should have been created in the scheduler broks.')
        self.assertIn(expected_brok_id, sched.broks,
                      'We should have got this brok_id in the scheduler broks.')
        brok = sched.broks[expected_brok_id]
        self.assertEqual(brok.type, 'host_next_schedule')

        brok.prepare()
        self.assertEqual(host.host_name, brok.data['host_name'])
        self.assertTrue(brok.data['in_checking'])
        # verify the host next_chk attribute is good:
        self.assertLess(now, brok.data['next_chk'])
        interval = host.check_interval * host.interval_length
        interval = min(interval, host.max_check_spread * host.interval_length)
        max_next_chk = now + min(interval, host.max_check_spread * host.interval_length)
        self.assertGreater(max_next_chk, brok.data['next_chk'])
        # actually it should not have been updated, so the one we recorded
        # before calling check_freshness() should be exactly equals,
        # but NB: this could highly depend on the condition applied to the
        # host used in this test case !!
        self.assertEqual(expected_host_next_chk, brok.data['next_chk'])


if __name__ == '__main__':
    unittest.main()
