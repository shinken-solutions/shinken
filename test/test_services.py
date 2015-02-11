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

import copy
from shinken_test import *


class TestService(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def get_svc(self):
        return self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")


    # Look if get_*_name return the good result
    def test_get_name(self):
        svc = self.get_svc()
        print svc.get_dbg_name()
        self.assertEqual('test_ok_0', svc.get_name())
        self.assertEqual('test_host_0/test_ok_0', svc.get_dbg_name())


    # getstate should be with all properties in dict class + id
    # check also the setstate
    def test___getstate__(self):
        svc = self.get_svc()
        cls = svc.__class__
        # We get the state
        state = svc.__getstate__()
        # Check it's the good length
        self.assertEqual(len(cls.properties) + len(cls.running_properties) + 1, len(state))
        # we copy the service
        svc_copy = copy.copy(svc)
        # reset the state in the original service
        svc.__setstate__(state)
        # And it should be the same:then before :)
        for p in cls.properties:
            ## print getattr(svc_copy, p)
            ## print getattr(svc, p)
            self.assertEqual(getattr(svc, p), getattr(svc_copy, p) )


    # Look if it can detect all incorrect cases
    def test_is_correct(self):
        svc = self.get_svc()

        # first it's ok
        self.assertEqual(True, svc.is_correct())

        # Now try to delete a required property
        max_check_attempts = svc.max_check_attempts
        del svc.max_check_attempts
        self.assertEqual(True, svc.is_correct())
        svc.max_check_attempts = max_check_attempts

        ###
        ### Now special cases
        ###

        # no check command
        check_command = svc.check_command
        del svc.check_command
        self.assertEqual(False, svc.is_correct())
        svc.check_command = check_command
        self.assertEqual(True, svc.is_correct())

        # no notification_interval
        notification_interval = svc.notification_interval
        del svc.notification_interval
        self.assertEqual(False, svc.is_correct())
        svc.notification_interval = notification_interval
        self.assertEqual(True, svc.is_correct())


    # Look for set/unset impacted states (unknown)
    def test_impact_state(self):
        svc = self.get_svc()
        ori_state = svc.state
        ori_state_id = svc.state_id
        svc.set_impact_state()
        self.assertEqual('UNKNOWN', svc.state)
        self.assertEqual(3, svc.state_id)
        svc.unset_impact_state()
        self.assertEqual(ori_state, svc.state)
        self.assertEqual(ori_state_id, svc.state_id)

    # Look for display name setting
    def test_display_name(self):
        svc = self.get_svc()
        print 'Display name', svc.display_name, 'toto'
        print 'Full name', svc.get_full_name()
        self.assertEqual(u'test_ok_0', svc.display_name)

    def test_states_from_exit_status(self):
        svc = self.get_svc()

        # First OK
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual('OK', svc.state)
        self.assertEqual(0, svc.state_id)
        self.assertEqual(True, svc.is_state('OK'))
        self.assertEqual(True, svc.is_state('o'))

        # Then warning
        self.scheduler_loop(1, [[svc, 1, 'WARNING']])
        self.assertEqual('WARNING', svc.state)
        self.assertEqual(1, svc.state_id)
        self.assertEqual(True, svc.is_state('WARNING'))
        self.assertEqual(True, svc.is_state('w'))
        # Then Critical
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL']])
        self.assertEqual('CRITICAL', svc.state)
        self.assertEqual(2, svc.state_id)
        self.assertEqual(True, svc.is_state('CRITICAL'))
        self.assertEqual(True, svc.is_state('c'))

        # And unknown
        self.scheduler_loop(1, [[svc, 3, 'UNKNOWN']])
        self.assertEqual('UNKNOWN', svc.state)
        self.assertEqual(3, svc.state_id)
        self.assertEqual(True, svc.is_state('UNKNOWN'))
        self.assertEqual(True, svc.is_state('u'))

        # And something else :)
        self.scheduler_loop(1, [[svc, 99, 'WTF return :)']])
        self.assertEqual('CRITICAL', svc.state)
        self.assertEqual(2, svc.state_id)
        self.assertEqual(True, svc.is_state('CRITICAL'))
        self.assertEqual(True, svc.is_state('c'))


    def test_business_impact_value(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        # This service inherit the improtance value from his father, 5
        self.assertEqual(5, svc.business_impact)


    # Look if the service is in the servicegroup
    def test_servicegroup(self):
        sg = self.sched.servicegroups.find_by_name("servicegroup_01")
        self.assertIsNot(sg, None)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        self.assertIn(svc, sg.members)
        self.assertIn(sg.get_name(), [sg.get_name() for sg in svc.servicegroups])

    # Look at the good of the last_hard_state_change
    def test_service_last_hard_state(self):
        self.print_header()
        # We want an eventhandelr (the perfdata command) to be put in the actions dict
        # after we got a service check
        now = time.time()
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        # We do not want to be just a string but a real command
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "FUCK", svc.last_hard_state_change
        orig = svc.last_hard_state_change
        self.assertEqual('OK', svc.last_hard_state)

        # now still ok
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        self.assertEqual(orig, svc.last_hard_state_change)
        self.assertEqual('OK', svc.last_hard_state)

        # now error but still SOFT
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | bibi=99%']])
        print "FUCK", svc.state_type
        self.assertEqual(orig, svc.last_hard_state_change)
        self.assertEqual('OK', svc.last_hard_state)

        # now go hard!
        time.sleep(2)
        now = int(time.time())
        self.assertLess(svc.last_hard_state_change, now)
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | bibi=99%']])
        print "FUCK", svc.state_type
        self.assertGreaterEqual(svc.last_hard_state_change, now)
        self.assertEqual('CRITICAL', svc.last_hard_state)
        print "Last hard state id", svc.last_hard_state_id
        self.assertEqual(2, svc.last_hard_state_id)

    # Check if the autoslots are fill like it should
    def test_autoslots(self):
        svc = self.get_svc()
        self.assertNotIn("check_period", svc.__dict__)

    # Check if the parent/childs dependencies are fill like it should
    def test_parent_child_dep_list(self):
        svc = self.get_svc()
        # Look if our host is a parent
        self.assertIn(svc.host, svc.parent_dependencies)
        # and if we are a child of it
        self.assertIn(svc, svc.host.child_dependencies)


if __name__ == '__main__':
    unittest.main()
