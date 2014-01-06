#!/usr/bin/env python
# Copyright (C) 2009-2010:
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


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def get_hst(self):
        return self.sched.hosts.find_by_name("test_host_0")

    # Look if get_*_name return the good result
    def test_get_name(self):
        hst = self.get_hst()
        print hst.get_dbg_name()
        self.assert_(hst.get_name() == 'test_host_0')
        self.assert_(hst.get_dbg_name() == 'test_host_0')

    # getstate should be with all properties in dict class + id
    # check also the setstate
    def test___getstate__(self):
        hst = self.get_hst()
        cls = hst.__class__
        # We get the state
        state = hst.__getstate__()
        # Check it's the good length
        self.assert_(len(state) == len(cls.properties) + len(cls.running_properties) + 1)
        # we copy the service
        hst_copy = copy.copy(hst)
        # reset the state in the original service
        hst.__setstate__(state)
        # And it should be the same:then before :)
        for p in cls.properties:
            ## print getattr(hst_copy, p)
            ## print getattr(hst, p)
            self.assert_(getattr(hst_copy, p) == getattr(hst, p))

    # Look if it can detect all incorrect cases
    def test_is_correct(self):
        hst = self.get_hst()

        # first it's ok
        self.assert_(hst.is_correct() == True)

        # Now try to delete a required property
        max_check_attempts = hst.max_check_attempts
        del hst.max_check_attempts
        self.assert_(hst.is_correct() == True)
        hst.max_check_attempts = max_check_attempts

        ###
        ### Now special cases
        ###

        # no check command
        check_command = hst.check_command
        del hst.check_command
        self.assert_(hst.is_correct() == False)
        hst.check_command = check_command
        self.assert_(hst.is_correct() == True)

        # no notification_interval
        notification_interval = hst.notification_interval
        del hst.notification_interval
        self.assert_(hst.is_correct() == False)
        hst.notification_interval = notification_interval
        self.assert_(hst.is_correct() == True)

    # Look for set/unset impacted states (unknown)
    def test_impact_state(self):
        hst = self.get_hst()
        ori_state = hst.state
        ori_state_id = hst.state_id
        hst.set_impact_state()
        self.assert_(hst.state == 'UNREACHABLE')
        self.assert_(hst.state_id == 2)
        hst.unset_impact_state()
        self.assert_(hst.state == ori_state)
        self.assert_(hst.state_id == ori_state_id)

    def test_set_state_from_exit_status(self):
        hst = self.get_hst()
        # First OK
        hst.set_state_from_exit_status(0)
        self.assert_(hst.state == 'UP')
        self.assert_(hst.state_id == 0)
        self.assert_(hst.is_state('UP') == True)
        self.assert_(hst.is_state('o') == True)
        # Then warning
        hst.set_state_from_exit_status(1)
        self.assert_(hst.state == 'UP')
        self.assert_(hst.state_id == 0)
        self.assert_(hst.is_state('UP') == True)
        self.assert_(hst.is_state('o') == True)
        # Then Critical
        hst.set_state_from_exit_status(2)
        self.assert_(hst.state == 'DOWN')
        self.assert_(hst.state_id == 1)
        self.assert_(hst.is_state('DOWN') == True)
        self.assert_(hst.is_state('d') == True)
        # And unknown
        hst.set_state_from_exit_status(3)
        self.assert_(hst.state == 'DOWN')
        self.assert_(hst.state_id == 1)
        self.assert_(hst.is_state('DOWN') == True)
        self.assert_(hst.is_state('d') == True)

        # And something else :)
        hst.set_state_from_exit_status(99)
        self.assert_(hst.state == 'DOWN')
        self.assert_(hst.state_id == 1)
        self.assert_(hst.is_state('DOWN') == True)
        self.assert_(hst.is_state('d') == True)

        # And a special case: use_aggressive_host_checking
        hst.__class__.use_aggressive_host_checking = 1
        hst.set_state_from_exit_status(1)
        self.assert_(hst.state == 'DOWN')
        self.assert_(hst.state_id == 1)
        self.assert_(hst.is_state('DOWN') == True)
        self.assert_(hst.is_state('d') == True)

    def test_hostgroup(self):
        hg = self.sched.hostgroups.find_by_name("hostgroup_01")
        self.assert_(hg is not None)
        h = self.sched.hosts.find_by_name('test_host_0')
        self.assert_(h in hg.members)
        self.assert_(hg in h.hostgroups)

    def test_childs(self):
        h = self.sched.hosts.find_by_name('test_host_0')
        r = self.sched.hosts.find_by_name('test_router_0')

        # Search if h is in r.childs
        self.assert_(h in r.childs)
        # and the reverse
        self.assert_(r in h.parents)
        print "r.childs", r.childs
        print "h.childs", h.childs

        # And also in the parent/childs dep list
        self.assert_(h in r.child_dependencies)
        # and the reverse
        self.assert_(r in h.parent_dependencies)


if __name__ == '__main__':
    unittest.main()
