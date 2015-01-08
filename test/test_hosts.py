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


class TestHost(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def get_hst(self):
        return self.sched.hosts.find_by_name("test_host_0")

    # Look if get_*_name return the good result
    def test_get_name(self):
        hst = self.get_hst()
        print hst.get_dbg_name()
        self.assertEqual('test_host_0', hst.get_name())
        self.assertEqual('test_host_0', hst.get_dbg_name())


    # getstate should be with all properties in dict class + id
    # check also the setstate
    def test___getstate__(self):
        hst = self.get_hst()
        cls = hst.__class__
        # We get the state
        state = hst.__getstate__()
        # Check it's the good length
        self.assertEqual(len(cls.properties) + len(cls.running_properties) + 1, len(state))
        # we copy the service
        hst_copy = copy.copy(hst)
        # reset the state in the original service
        hst.__setstate__(state)
        # And it should be the same:then before :)
        for p in cls.properties:
            ## print getattr(hst_copy, p)
            ## print getattr(hst, p)
            self.assertEqual(getattr(hst, p), getattr(hst_copy, p) )


    # Look if it can detect all incorrect cases
    def test_is_correct(self):
        hst = self.get_hst()

        # first it's ok
        self.assertEqual(True, hst.is_correct())

        # Now try to delete a required property
        max_check_attempts = hst.max_check_attempts
        del hst.max_check_attempts
        self.assertEqual(True, hst.is_correct())
        hst.max_check_attempts = max_check_attempts

        ###
        ### Now special cases
        ###

        # no check command
        check_command = hst.check_command
        del hst.check_command
        self.assertEqual(False, hst.is_correct())
        hst.check_command = check_command
        self.assertEqual(True, hst.is_correct())

        # no notification_interval
        notification_interval = hst.notification_interval
        del hst.notification_interval
        self.assertEqual(False, hst.is_correct())
        hst.notification_interval = notification_interval
        self.assertEqual(True, hst.is_correct())


    # Look for set/unset impacted states (unknown)
    def test_impact_state(self):
        hst = self.get_hst()
        ori_state = hst.state
        ori_state_id = hst.state_id
        hst.set_impact_state()
        self.assertEqual('UNREACHABLE', hst.state)
        self.assertEqual(2, hst.state_id)
        hst.unset_impact_state()
        self.assertEqual(ori_state, hst.state)
        self.assertEqual(ori_state_id, hst.state_id)


    def test_states_from_exit_status(self):
        hst = self.get_hst()

        # First OK
        self.scheduler_loop(1, [[hst, 0, 'OK']])
        self.assertEqual('UP', hst.state)
        self.assertEqual(0, hst.state_id)
        self.assertEqual(True, hst.is_state('UP'))
        self.assertEqual(True, hst.is_state('o'))

        # Then warning
        self.scheduler_loop(1, [[hst, 1, 'WARNING']])
        self.assertEqual('UP', hst.state)
        self.assertEqual(0, hst.state_id)
        self.assertEqual(True, hst.is_state('UP'))
        self.assertEqual(True, hst.is_state('o'))

        # Then Critical
        self.scheduler_loop(1, [[hst, 2, 'CRITICAL']])
        self.assertEqual('DOWN', hst.state)
        self.assertEqual(1, hst.state_id)
        self.assertEqual(True, hst.is_state('DOWN'))
        self.assertEqual(True, hst.is_state('d'))

        # And unknown
        self.scheduler_loop(1, [[hst, 3, 'UNKNOWN']])
        self.assertEqual('DOWN', hst.state)
        self.assertEqual(1, hst.state_id)
        self.assertEqual(True, hst.is_state('DOWN'))
        self.assertEqual(True, hst.is_state('d'))

        # And something else :)
        self.scheduler_loop(1, [[hst, 99, 'WTF THE PLUGIN DEV DID? :)']])
        self.assertEqual('DOWN', hst.state)
        self.assertEqual(1, hst.state_id)
        self.assertEqual(True, hst.is_state('DOWN'))
        self.assertEqual(True, hst.is_state('d'))

        # And a special case: use_aggressive_host_checking
        hst.__class__.use_aggressive_host_checking = True
        self.scheduler_loop(1, [[hst, 1, 'WARNING SHOULD GO DOWN']])
        self.assertEqual('DOWN', hst.state)
        self.assertEqual(1, hst.state_id)
        self.assertEqual(True, hst.is_state('DOWN'))
        self.assertEqual(True, hst.is_state('d'))


    def test_hostgroup(self):
        hg = self.conf.hostgroups.find_by_name("hostgroup_01")
        self.assertIsNot(hg, None)
        h = self.conf.hosts.find_by_name('test_host_0')
        self.assertIn(h, hg.members)
        self.assertIn(hg.get_name(), [hg.get_name() for hg in h.hostgroups])


    def test_childs(self):
        h = self.sched.hosts.find_by_name('test_host_0')
        r = self.sched.hosts.find_by_name('test_router_0')

        # Search if h is in r.childs
        self.assertIn(h, r.childs)
        # and the reverse
        self.assertIn(r, h.parents)
        print "r.childs", r.childs
        print "h.childs", h.childs

        # And also in the parent/childs dep list
        self.assertIn(h, r.child_dependencies)
        # and the reverse
        self.assertIn(r, h.parent_dependencies)


if __name__ == '__main__':
    unittest.main()
