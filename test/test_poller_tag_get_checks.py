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


class TestPollerTagGetchecks(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_poller_tag_get_checks.cfg')

    def test_good_checks_get_only_tags_with_specific_tags(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # schedule the host so it will have a check :)
        # and for ce the execution now
        host.schedule()
        self.assertEqual('mytestistrue', host.check_command.command.poller_tag)
        for a in host.actions:
            print "Tag", a.poller_tag
            a.t_to_go = 0
        svc.schedule()
        for a in svc.actions:
            print "Tag", a.poller_tag
            a.t_to_go = 0
        # the scheduler need to get this new checks in its own queues
        self.sched.get_new_actions()
        # Ask for untag checks only
        untaggued_checks = self.sched.get_to_run_checks(True, False, poller_tags=['None'])
        print "Got untaggued_checks", untaggued_checks
        self.assertGreater(len(untaggued_checks), 0)
        for c in untaggued_checks:
            # Should be the service one, but not the host one
            self.assertTrue(c.command.startswith('plugins/test_servicecheck.pl'))

        # Now get only tag ones
        taggued_checks = self.sched.get_to_run_checks(True, False, poller_tags=['mytestistrue'])
        self.assertGreater(len(taggued_checks), 0)
        for c in taggued_checks:
            # Should be the host one only
            self.assertTrue(c.command.startswith('plugins/test_hostcheck.pl'))

    def test_good_checks_get_only_tags_with_specific_module_types(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # schedule the host so it will have a check :)
        # and for ce the execution now
        host.schedule()
        self.assertEqual('mytestistrue', host.check_command.command.poller_tag)
        for a in host.actions:
            print "Tag", a.poller_tag
            a.t_to_go = 0
        svc.schedule()
        for a in svc.actions:
            print "Tag", a.poller_tag
            a.t_to_go = 0
        # the scheduler need to get this new checks in its own queues
        self.sched.get_new_actions()

        # Ask for badly named module type
        untaggued_checks = self.sched.get_to_run_checks(True, False, poller_tags=['None'], module_types=['fork'])
        print "Got untaggued_checks for forks", untaggued_checks
        self.assertGreater(len(untaggued_checks), 0)
        print "NB CHECKS", len(untaggued_checks)
        for c in untaggued_checks:
            print c.command
            # Should be the service one, but not the host one
            self.assertTrue(c.command.startswith('plugins/test_servicecheck.pl') or c.command.startswith('plugins/test_hostcheck.pl'))

        # Now get only tag ones and with a bad module type, so get NOTHING
        taggued_checks = self.sched.get_to_run_checks(True, False, poller_tags=['mytestistrue'], module_types=['myassischicken'])
        self.assertEqual(0, len(taggued_checks))

if __name__ == '__main__':
    unittest.main()
