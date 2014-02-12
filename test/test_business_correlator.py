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

import re
from shinken_test import *


class TestBusinesscorrel(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_business_correlator.cfg')

    # We will try a simple bd1 OR db2
    def test_simple_or_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        # We check for good parent/childs links
        # So svc_cor should be a son of svc_bd1 and svc_bd2
        # and bd1 and bd2 should be parents of svc_cor
        self.assert_(svc_cor in svc_bd1.child_dependencies)
        self.assert_(svc_cor in svc_bd2.child_dependencies)
        self.assert_(svc_bd1 in svc_cor.parent_dependencies)
        self.assert_(svc_bd2 in svc_cor.parent_dependencies)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')

        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)




    # We will try a simple bd1 AND db2
    def test_simple_and_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_And")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '&')

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')

        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule must go CRITICAL
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # Now we also set bd2 as WARNING/HARD...
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING too?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'WARNING')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 1)

        # Must be WARNING (worse no 0 value for both)
        state = bp_rule.get_state()
        self.assert_(state == 1)

    # We will try a simple 1of: bd1 OR/AND db2
    def test_simple_1of_business_correlator(self):
        self.run_simple_1of_business_correlator()

    # We will try a simple -1of: bd1 OR/AND db2
    def test_simple_1of_neg_business_correlator(self):
        self.run_simple_1of_business_correlator(with_neg=True)

    # We will try a simple 50%of: bd1 OR/AND db2
    def test_simple_1of_pct_business_correlator(self):
        self.run_simple_1of_business_correlator(with_pct=True)

    # We will try a simple -50%of: bd1 OR/AND db2
    def test_simple_1of_pct_neg_business_correlator(self):
        self.run_simple_1of_business_correlator(with_pct=True, with_neg=True)


    def run_simple_1of_business_correlator(self, with_pct=False, with_neg=False):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        if with_pct is True:
            if with_neg is True:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_pct_neg")
            else:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_pct")
        else:
            if with_neg is True:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_neg")
            else:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        # Simple 1of: so in fact a triple ('1','2','2') (1of and MAX,MAX
        if with_pct is True:
            if with_neg is True:
                self.assert_(bp_rule.of_values == ('-50%', '2', '2'))
            else:
                self.assert_(bp_rule.of_values == ('50%', '2', '2'))
        else:
            if with_neg is True:
                self.assert_(bp_rule.of_values == ('-1', '2', '2'))
            else:
                self.assert_(bp_rule.of_values == ('1', '2', '2'))

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')

        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule still be OK
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we also set bd2 as CRITICAL/HARD...
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)

        # And now the state of the rule must be 2 now
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING now?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'WARNING')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 1)

        # Must be WARNING (worse no 0 value for both, like for AND rule)
        state = bp_rule.get_state()
        self.assert_(state == 1)

    # We will try a simple 1of: test_router_0 OR/AND test_host_0
    def test_simple_1of_business_correlator_with_hosts(self):
        self.run_simple_1of_business_correlator_with_hosts()

    # We will try a simple -1of: test_router_0 OR/AND test_host_0
    def test_simple_1of_neg_business_correlator_with_hosts(self):
        self.run_simple_1of_business_correlator_with_hosts(with_neg=True)

    # We will try a simple 50%of: test_router_0 OR/AND test_host_0
    def test_simple_1of_pct_business_correlator_with_hosts(self):
        self.run_simple_1of_business_correlator_with_hosts(with_pct=True)

    # We will try a simple -50%of: test_router_0 OR/AND test_host_0
    def test_simple_1of_pct_neg_business_correlator_with_hosts(self):
        self.run_simple_1of_business_correlator_with_hosts(with_pct=True, with_neg=True)

    def run_simple_1of_business_correlator_with_hosts(self, with_pct=False, with_neg=False):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        if with_pct is True:
            if with_neg is True:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_with_host_pct_neg")
            else:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_with_host_pct")
        else:
            if with_neg is True:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_with_host_neg")
            else:
                svc_cor = self.sched.services.find_srv_by_name_and_hostname(
                        "test_host_0", "Simple_1Of_with_host")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        # Simple 1of: so in fact a triple ('1','2','2') (1of and MAX,MAX
        if with_pct is True:
            if with_neg is True:
                self.assert_(bp_rule.of_values == ('-50%', '2', '2'))
            else:
                self.assert_(bp_rule.of_values == ('50%', '2', '2'))
        else:
            if with_neg is True:
                self.assert_(bp_rule.of_values == ('-1', '2', '2'))
            else:
                self.assert_(bp_rule.of_values == ('1', '2', '2'))

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'host')
        self.assert_(sons[0].sons[0] == host)
        self.assert_(sons[1].operand == 'host')
        self.assert_(sons[1].sons[0] == router)

    # We will try a simple bd1 OR db2, but this time we will
    # schedule a real check and see if it's good
    def test_simple_or_business_correlator_with_schedule(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')

        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And now we must be CRITICAL/SOFT!
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'SOFT')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # OK, re recheck again, GO HARD!
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 2)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)

        # And in a HARD
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'WARNING')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 1)

        print "All elements", bp_rule.list_all_elements()

        print "IMPACT:", svc_bd2.impacts
        for i in svc_bd2.impacts:
            print i.get_name()

        # Assert that Simple_Or Is an impact of the problem bd2
        self.assert_(svc_cor in svc_bd2.impacts)
        # and bd1 too
        self.assert_(svc_cor in svc_bd1.impacts)

    def test_dep_node_list_elements(self):
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        print "All elements", bp_rule.list_all_elements()
        all_elt = bp_rule.list_all_elements()

        self.assert_(svc_bd2 in all_elt)
        self.assert_(svc_bd1 in all_elt)

        print "DBG: bd2 depend_on_me", svc_bd2.act_depend_of_me

    # We will try a full ERP rule and
    # schedule a real check and see if it's good
    def test_full_erp_rule_with_schedule(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_web1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "web1")
        self.assert_(svc_web1.got_business_rule == False)
        self.assert_(svc_web1.business_rule is None)
        svc_web2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "web2")
        self.assert_(svc_web2.got_business_rule == False)
        self.assert_(svc_web2.business_rule is None)
        svc_lvs1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs1")
        self.assert_(svc_lvs1.got_business_rule == False)
        self.assert_(svc_lvs1.business_rule is None)
        svc_lvs2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs2")
        self.assert_(svc_lvs2.got_business_rule == False)
        self.assert_(svc_lvs2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "ERP")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '&')

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 3 sons, each 3 rules
        self.assert_(len(sons) == 3)
        bd_node = sons[0]
        self.assert_(bd_node.operand == '|')
        self.assert_(bd_node.sons[0].sons[0] == svc_bd1)
        self.assert_(bd_node.sons[1].sons[0] == svc_bd2)

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')

        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And now we must be CRITICAL/SOFT!
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'SOFT')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # OK, re recheck again, GO HARD!
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'CRITICAL')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 2)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)

        # And in a HARD
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'WARNING')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 1)

        print "All elements", bp_rule.list_all_elements()

        print "IMPACT:", svc_bd2.impacts
        for i in svc_bd2.impacts:
            print i.get_name()

        # Assert that Simple_Or Is an impact of the problem bd2
        self.assert_(svc_cor in svc_bd2.impacts)
        # and bd1 too
        self.assert_(svc_cor in svc_bd1.impacts)

        # And now all is green :)
        self.scheduler_loop(2, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | value1=1 value2=2']])

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

        # And no more in impact
        self.assert_(svc_cor not in svc_bd2.impacts)
        self.assert_(svc_cor not in svc_bd1.impacts)

        # And what if we set 2 service from distant rule CRITICAL?
        # ERP should be still OK
        # And now all is green :)
        self.scheduler_loop(2, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2'], [svc_web1, 2, 'CRITICAL | value1=1 value2=2']])

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assert_(c.internal == True)
        self.assert_(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assert_(len(svc_cor.actions) == 0)

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assert_(svc_cor.state == 'OK')
        self.assert_(svc_cor.state_type == 'HARD')
        self.assert_(svc_cor.last_hard_state_id == 0)

    # We will try a simple 1of: bd1 OR/AND db2
    def test_complex_ABCof_business_correlator(self):
        self.run_complex_ABCof_business_correlator(with_pct=False)

    # We will try a simple 1of: bd1 OR/AND db2
    def test_complex_ABCof_pct_business_correlator(self):
        self.run_complex_ABCof_business_correlator(with_pct=True)

    def run_complex_ABCof_business_correlator(self, with_pct=False):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        A = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "A")
        self.assert_(A.got_business_rule == False)
        self.assert_(A.business_rule is None)
        B = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "B")
        self.assert_(B.got_business_rule == False)
        self.assert_(B.business_rule is None)
        C = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "C")
        self.assert_(C.got_business_rule == False)
        self.assert_(C.business_rule is None)
        D = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "D")
        self.assert_(D.got_business_rule == False)
        self.assert_(D.business_rule is None)
        E = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "E")
        self.assert_(E.got_business_rule == False)
        self.assert_(E.business_rule is None)

        if with_pct == False:
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Complex_ABCOf")
        else:
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Complex_ABCOf_pct")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        if with_pct == False:
            self.assert_(bp_rule.of_values == ('5', '1', '1'))
        else:
            self.assert_(bp_rule.of_values == ('100%', '20%', '20%'))

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 5)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == A)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == B)
        self.assert_(sons[2].operand == 'service')
        self.assert_(sons[2].sons[0] == C)
        self.assert_(sons[3].operand == 'service')
        self.assert_(sons[3].sons[0] == D)
        self.assert_(sons[4].operand == 'service')
        self.assert_(sons[4].sons[0] == E)

        # Now state working on the states
        self.scheduler_loop(1, [[A, 0, 'OK'], [B, 0, 'OK'], [C, 0, 'OK'], [D, 0, 'OK'], [E, 0, 'OK']])
        self.assert_(A.state == 'OK')
        self.assert_(A.state_type == 'HARD')
        self.assert_(B.state == 'OK')
        self.assert_(B.state_type == 'HARD')
        self.assert_(C.state == 'OK')
        self.assert_(C.state_type == 'HARD')
        self.assert_(D.state == 'OK')
        self.assert_(D.state_type == 'HARD')
        self.assert_(E.state == 'OK')
        self.assert_(E.state_type == 'HARD')

        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we set the A as soft/CRITICAL
        self.scheduler_loop(1, [[A, 2, 'CRITICAL']])
        self.assert_(A.state == 'CRITICAL')
        self.assert_(A.state_type == 'SOFT')
        self.assert_(A.last_hard_state_id == 0)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get A CRITICAL/HARD
        self.scheduler_loop(1, [[A, 2, 'CRITICAL']])
        self.assert_(A.state == 'CRITICAL')
        self.assert_(A.state_type == 'HARD')
        self.assert_(A.last_hard_state_id == 2)

        # The rule still be OK
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # Now we also set B as CRITICAL/HARD...
        self.scheduler_loop(2, [[B, 2, 'CRITICAL']])
        self.assert_(B.state == 'CRITICAL')
        self.assert_(B.state_type == 'HARD')
        self.assert_(B.last_hard_state_id == 2)

        # And now the state of the rule must be 2 now
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set A dn B WARNING now?
        self.scheduler_loop(2, [[A, 1, 'WARNING'], [B, 1, 'WARNING']])
        self.assert_(A.state == 'WARNING')
        self.assert_(A.state_type == 'HARD')
        self.assert_(A.last_hard_state_id == 1)
        self.assert_(B.state == 'WARNING')
        self.assert_(B.state_type == 'HARD')
        self.assert_(B.last_hard_state_id == 1)

        # Must be WARNING (worse no 0 value for both, like for AND rule)
        state = bp_rule.get_state()
        print "state", state
        self.assert_(state == 1)

        # Ok now more fun, with changing of_values and states

        ### W O O O O
        # 4 of: -> Ok (we got 4 OK, and not 4 warn or crit, so it's OK)
        # 5,1,1 -> Warning (at least one warning, and no crit -> warning)
        # 5,2,1 -> OK (we want warning only if we got 2 bad states, so not here)
        self.scheduler_loop(2, [[A, 1, 'WARNING'], [B, 0, 'OK']])
        # 4 of: -> 4,5,5
        if with_pct == False:
            bp_rule.of_values = ('4', '5', '5')
        else:
            bp_rule.of_values = ('80%', '100%', '100%')
        bp_rule.is_of_mul = False
        self.assert_(bp_rule.get_state() == 0)
        # 5,1,1
        if with_pct == False:
            bp_rule.of_values = ('5', '1', '1')
        else:
            bp_rule.of_values = ('100%', '20%', '20%')
        bp_rule.is_of_mul = True
        self.assert_(bp_rule.get_state() == 1)
        # 5,2,1
        if with_pct == False:
            bp_rule.of_values = ('5', '2', '1')
        else:
            bp_rule.of_values = ('100%', '40%', '20%')
        bp_rule.is_of_mul = True
        self.assert_(bp_rule.get_state() == 0)

        ###* W C O O O
        # 4 of: -> Crtitical (not 4 ok, so we take the worse state, the critical)
        # 4,1,1 -> Critical (2 states raise the waring, but on raise critical, so worse state is critical)
        self.scheduler_loop(2, [[A, 1, 'WARNING'], [B, 2, 'Crit']])
        # 4 of: -> 4,5,5
        if with_pct == False:
            bp_rule.of_values = ('4', '5', '5')
        else:
            bp_rule.of_values = ('80%', '100%', '100%')
        bp_rule.is_of_mul = False
        self.assert_(bp_rule.get_state() == 2)
        # 4,1,1
        if with_pct == False:
            bp_rule.of_values = ('4', '1', '1')
        else:
            bp_rule.of_values = ('40%', '20%', '20%')
        bp_rule.is_of_mul = True
        self.assert_(bp_rule.get_state() == 2)

        ##* W C C O O
        # * 2 of: OK
        # * 4,1,1 -> Critical (same as before)
        # * 4,1,3 -> warning (the warning rule is raised, but the critical is not)
        self.scheduler_loop(2, [[A, 1, 'WARNING'], [B, 2, 'Crit'], [C, 2, 'Crit']])
        # * 2 of: 2,5,5
        if with_pct == False:
            bp_rule.of_values = ('2', '5', '5')
        else:
            bp_rule.of_values = ('40%', '100%', '100%')
        bp_rule.is_of_mul = False
        self.assert_(bp_rule.get_state() == 0)
        # * 4,1,1
        if with_pct == False:
            bp_rule.of_values = ('4', '1', '1')
        else:
            bp_rule.of_values = ('80%', '20%', '20%')
        bp_rule.is_of_mul = True
        self.assert_(bp_rule.get_state() == 2)
        # * 4,1,3
        if with_pct == False:
            bp_rule.of_values = ('4', '1', '3')
        else:
            bp_rule.of_values = ('80%', '20%', '60%')
        bp_rule.is_of_mul = True
        self.assert_(bp_rule.get_state() == 1)

    # We will try a simple bd1 AND NOT db2
    def test_simple_and_not_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_And_not")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '&')

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)

        # Now state working on the states
        self.scheduler_loop(2, [[svc_bd1, 0, 'OK | value1=1 value2=2'], [svc_bd2, 2, 'CRITICAL | rtt=10']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')

        # We are a NOT, so should be OK here
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule must go CRITICAL
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # Now we also set bd2 as WARNING/HARD...
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING too?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'WARNING')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 1)

        # Must be WARNING (worse no 0 value for both)
        state = bp_rule.get_state()
        self.assert_(state == 1)

        # Now try to get ok in both place, should be bad :)
        self.scheduler_loop(2, [[svc_bd1, 0, 'OK | value1=1 value2=2'], [svc_bd2, 0, 'OK | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 0)
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 0)

        # Must be CRITICAL (ok and not ok IS no OK :) )
        state = bp_rule.get_state()
        self.assert_(state == 2)






    # We will try a simple bd1 OR db2
    def test_multi_layers(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # THE RULE IS (test_host_0,db1| (test_host_0,db2 & (test_host_0,lvs1|test_host_0,lvs2) ) ) & test_router_0
        svc_lvs1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs1")
        self.assert_(svc_lvs1 is not None)
        svc_lvs2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs2")
        self.assert_(svc_lvs2 is not None)

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule is None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule is None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Multi_levels")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '&')

        # We check for good parent/childs links
        # So svc_cor should be a son of svc_bd1 and svc_bd2
        # and bd1 and bd2 should be parents of svc_cor
        self.assert_(svc_cor in svc_bd1.child_dependencies)
        self.assert_(svc_cor in svc_bd2.child_dependencies)
        self.assert_(svc_cor in router.child_dependencies)
        self.assert_(svc_bd1 in svc_cor.parent_dependencies)
        self.assert_(svc_bd2 in svc_cor.parent_dependencies)
        self.assert_(router in svc_cor.parent_dependencies)


        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        # Son0 is (test_host_0,db1| (test_host_0,db2 & (test_host_0,lvs1|test_host_0,lvs2) ) )
        son0 = sons[0]
        self.assert_(son0.operand == '|')
        # Son1 is test_router_0
        self.assert_(sons[1].operand == 'host')
        self.assert_(sons[1].sons[0] == router)

        # Son0_0 is test_host_0,db1
        # Son0_1 is test_host_0,db2 & (test_host_0,lvs1|test_host_0,lvs2)
        son0_0 = son0.sons[0]
        son0_1 = son0.sons[1]
        self.assert_(son0_0.operand == 'service')
        self.assert_(son0_0.sons[0] == svc_bd1)
        self.assert_(son0_1.operand == '&')

        # Son0_1_0 is test_host_0,db2
        # Son0_1_1 is test_host_0,lvs1|test_host_0,lvs2
        son0_1_0 = son0_1.sons[0]
        son0_1_1 = son0_1.sons[1]
        self.assert_(son0_1_0.operand == 'service')
        self.assert_(son0_1_0.sons[0] == svc_bd2)
        self.assert_(son0_1_1.operand == '|')

        # Son0_1_1_0 is test_host_0,lvs1
        # Son0_1_1_1 is test_host_0,lvs2
        son0_1_1_0 = son0_1_1.sons[0]
        son0_1_1_1 = son0_1_1.sons[1]


        self.assert_(son0_1_1_0.operand == 'service')
        self.assert_(son0_1_1_0.sons[0] == svc_lvs1)
        self.assert_(son0_1_1_1.operand == 'service')
        self.assert_(son0_1_1_1.sons[0] == svc_lvs2)


        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10'],
                                [svc_lvs1, 0, 'OK'], [svc_lvs2, 0, 'OK'], [router, 0, 'UP'] ])
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')

        # All is green, the rule should be green too
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'SOFT')
        self.assert_(svc_bd1.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd1.state == 'CRITICAL')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd1.last_hard_state_id == 2)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'CRITICAL')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 2)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assert_(svc_bd2.state == 'WARNING')
        self.assert_(svc_bd2.state_type == 'HARD')
        self.assert_(svc_bd2.last_hard_state_id == 1)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assert_(state == 1)

        # We should got now svc_bd2 and svc_bd1 as root problems
        print "Root problems"
        for p in svc_cor.source_problems:
            print p.get_full_name()
        self.assert_(svc_bd1 in svc_cor.source_problems)
        self.assert_(svc_bd2 in svc_cor.source_problems)



        # What about now with the router in DOWN?
        self.scheduler_loop(5, [[router, 2, 'DOWN']])
        self.assert_(router.state == 'DOWN')
        self.assert_(router.state_type == 'HARD')
        self.assert_(router.last_hard_state_id == 1)

        # Must be CRITICAL (CRITICAL VERSUS DOWN -> DOWN)
        state = bp_rule.get_state()
        self.assert_(state == 2)

        # Now our root problem is router
        print "Root problems"
        for p in svc_cor.source_problems:
            print p.get_full_name()
        self.assert_(router in svc_cor.source_problems)












    # We will try a strange rule that ask UP&UP -> DOWN&DONW-> OK
    def test_darthelmet_rule(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_darthelmet")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        A = self.sched.hosts.find_by_name("test_darthelmet_A")
        B = self.sched.hosts.find_by_name("test_darthelmet_B")

        self.assert_(host.got_business_rule == True)
        self.assert_(host.business_rule is not None)
        bp_rule = host.business_rule
        self.assert_(bp_rule.operand == '|')

        # Now state working on the states
        self.scheduler_loop(3, [[host, 0, 'UP'], [A, 0, 'UP'], [B, 0, 'UP'] ] )
        self.assert_(host.state == 'UP')
        self.assert_(host.state_type == 'HARD')
        self.assert_(A.state == 'UP')
        self.assert_(A.state_type == 'HARD')

        state = bp_rule.get_state()
        print "WTF0", state
        self.assert_(state == 0)

        # Now we set the A as soft/DOWN
        self.scheduler_loop(1, [[A, 2, 'DOWN']])
        self.assert_(A.state == 'DOWN')
        self.assert_(A.state_type == 'SOFT')
        self.assert_(A.last_hard_state_id == 0)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assert_(state == 0)

        # Now we get A DOWN/HARD
        self.scheduler_loop(3, [[A, 2, 'DOWN']])
        self.assert_(A.state == 'DOWN')
        self.assert_(A.state_type == 'HARD')
        self.assert_(A.last_hard_state_id == 1)

        # The rule must still be a 2 (or inside)
        state = bp_rule.get_state()
        print "WFT", state
        self.assert_(state == 2)

        # Now we also set B as DOWN/HARD, should get back to 0!
        self.scheduler_loop(3, [[B, 2, 'DOWN']])
        self.assert_(B.state == 'DOWN')
        self.assert_(B.state_type == 'HARD')
        self.assert_(B.last_hard_state_id == 1)

        # And now the state of the rule must be 0 again! (strange rule isn't it?)
        state = bp_rule.get_state()
        self.assert_(state == 0)





class TestConfigBroken(ShinkenTest):
    """A class with a broken configuration, where business rules reference unknown hosts/services"""

    def setUp(self):
        self.setup_with_file('etc/shinken_business_correlator_broken.cfg')


    def test_conf_is_correct(self):
        #
        # Business rules use services which don't exist. We want
        # the arbiter to output an error message and exit
        # in a controlled manner.
        #
        print "conf_is_correct", self.conf.conf_is_correct
        self.assert_(not self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        # Info: Simple_1Of_1unk_svc: my business rule is invalid
        # Info: Simple_1Of_1unk_svc: Business rule uses unknown service test_host_0/db3
        # Error: [items] In Simple_1Of_1unk_svc is incorrect ; from etc/business_correlator_broken/services.cfg
        self.assert_(len([log for log in logs if re.search('Simple_1Of_1unk_svc', log)]) == 3)
        self.assert_(len([log for log in logs if re.search('service test_host_0/db3', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('Simple_1Of_1unk_svc.+from etc.+business_correlator_broken.+services.cfg', log)]) == 1)
        # Info: ERP_unk_svc: my business rule is invalid
        # Info: ERP_unk_svc: Business rule uses unknown service test_host_0/web100
        # Info: ERP_unk_svc: Business rule uses unknown service test_host_0/lvs100
        # Error: [items] In ERP_unk_svc is incorrect ; from etc/business_correlator_broken/services.cfg
        self.assert_(len([log for log in logs if re.search('ERP_unk_svc', log)]) == 4)
        self.assert_(len([log for log in logs if re.search('service test_host_0/web100', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('service test_host_0/lvs100', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('ERP_unk_svc.+from etc.+business_correlator_broken.+services.cfg', log)]) == 1)
        # Info: Simple_1Of_1unk_host: my business rule is invalid
        # Info: Simple_1Of_1unk_host: Business rule uses unknown host test_host_9
        # Error: [items] In Simple_1Of_1unk_host is incorrect ; from etc/business_correlator_broken/services.cfg
        self.assert_(len([log for log in logs if re.search('Simple_1Of_1unk_host', log)]) == 3)
        self.assert_(len([log for log in logs if re.search('host test_host_9', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('Simple_1Of_1unk_host.+from etc.+business_correlator_broken.+services.cfg', log)]) == 1)

        # Now the number of all failed business rules.
        self.assert_(len([log for log in logs if re.search('my business rule is invalid', log)]) == 3)



if __name__ == '__main__':
    unittest.main()
