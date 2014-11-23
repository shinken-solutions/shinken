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


class TestReactionnerTagGetNotifs(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_reactionner_tag_get_notif.cfg')

    # For a service, we generate a notification and a event handler.
    # Each one got a specific reactionner_tag that we will look for.
    def test_good_checks_get_only_tags_with_specific_tags(self):
        now = int(time.time())
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'BAD | value1=0 value2=0']])

        print "Go bad now"
        self.scheduler_loop(2, [[svc, 2, 'BAD | value1=0 value2=0']])

        to_del = []
        for a in self.sched.actions.values():
            print "\n\nA?", a, "\nZZZ%sZZZ" % a.command
            # Set them go NOW
            a.t_to_go = now
            # In fact they are already launched, so we-reenabled them :)
            print "AHAH?", a.status, a.__class__.my_type
            if a.__class__.my_type == 'notification' and (a.status == 'zombie' or a.status == ' scheduled'):
                to_del.append(a.id)

            a.status = 'scheduled'
            # And look for good tagging
            if a.command.startswith('plugins/notifier.pl'):
                print 'TAG:%s' % a.reactionner_tag
                self.assertEqual('runonwindows', a.reactionner_tag)
            if a.command.startswith('plugins/sms.pl'):
                print 'TAG:%s' % a.reactionner_tag
                self.assertEqual('sms', a.reactionner_tag)
            if a.command.startswith('plugins/test_eventhandler.pl'):
                print 'TAG: %s' % a.reactionner_tag
                self.assertEqual('eventtag', a.reactionner_tag)

        print "\n\n"
        for _i in to_del:
            print "DELETING", self.sched.actions[_i]
            del self.sched.actions[_i]

        print "NOW ACTION!"*20,'\n\n'

        # Ok the tags are defined as it should, now try to get them as a reactionner :)
        # Now get only tag ones
        taggued_runonwindows_checks = self.sched.get_to_run_checks(False, True, reactionner_tags=['runonwindows'])
        self.assertGreater(len(taggued_runonwindows_checks), 0)
        for c in taggued_runonwindows_checks:
            # Should be the host one only
            self.assertTrue(c.command.startswith('plugins/notifier.pl'))


        # Ok the tags are defined as it should, now try to get them as a reactionner :)
        # Now get only tag ones
        taggued_sms_checks = self.sched.get_to_run_checks(False, True, reactionner_tags=['sms'])
        self.assertGreater(len(taggued_sms_checks), 0)
        for c in taggued_sms_checks:
            # Should be the host one only
            self.assertTrue(c.command.startswith('plugins/sms.pl'))


        taggued_eventtag_checks = self.sched.get_to_run_checks(False, True, reactionner_tags=['eventtag'])
        self.assertGreater(len(taggued_eventtag_checks), 0)
        for c in taggued_eventtag_checks:
            # Should be the host one only
            self.assertTrue(c.command.startswith('plugins/test_eventhandler.pl'))


    # Same that upper, but with modules types
    def test_good_checks_get_only_tags_with_specific_tags_andmodule_types(self):
        now = int(time.time())
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'BAD | value1=0 value2=0']])

        print "Go bad now"
        self.scheduler_loop(2, [[svc, 2, 'BAD | value1=0 value2=0']])

        for a in self.sched.actions.values():
            # Set them go NOW
            a.t_to_go = now
            # In fact they are already launched, so we-reenabled them :)
            a.status = 'scheduled'
            # And look for good tagging
            if a.command.startswith('plugins/notifier.pl'):
                print a.__dict__
                print a.reactionner_tag
                self.assertEqual('runonwindows', a.reactionner_tag)
            if a.command.startswith('plugins/test_eventhandler.pl'):
                print a.__dict__
                print a.reactionner_tag
                self.assertEqual('eventtag', a.reactionner_tag)

        # Ok the tags are defined as it should, now try to get them as a reactionner :)
        # Now get only tag ones
        taggued_runonwindows_checks = self.sched.get_to_run_checks(False, True, reactionner_tags=['runonwindows'], module_types=['fork'])
        self.assertGreater(len(taggued_runonwindows_checks), 0)
        for c in taggued_runonwindows_checks:
            # Should be the host one only
            self.assertTrue(c.command.startswith('plugins/notifier.pl'))

        taggued_eventtag_checks = self.sched.get_to_run_checks(False, True, reactionner_tags=['eventtag'], module_types=['myassischicken'])
        self.assertEqual(0, len(taggued_eventtag_checks))



if __name__ == '__main__':
    unittest.main()
