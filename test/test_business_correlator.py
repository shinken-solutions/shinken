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
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('|', bp_rule.operand)

        # We check for good parent/childs links
        # So svc_cor should be a son of svc_bd1 and svc_bd2
        # and bd1 and bd2 should be parents of svc_cor
        self.assertIn(svc_cor, svc_bd1.child_dependencies)
        self.assertIn(svc_cor, svc_bd2.child_dependencies)
        self.assertIn(svc_bd1, svc_cor.parent_dependencies)
        self.assertIn(svc_bd2, svc_cor.parent_dependencies)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        self.assertEqual('service', sons[0].operand)
        self.assertEqual(svc_bd1, sons[0].sons[0])
        self.assertEqual('service', sons[1].operand)
        self.assertEqual(svc_bd2, sons[1].sons[0])

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(2, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(1, svc_bd2.last_hard_state_id)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assertEqual(1, state)




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
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_And")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('&', bp_rule.operand)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        self.assertEqual('service', sons[0].operand)
        self.assertEqual(svc_bd1, sons[0].sons[0])
        self.assertEqual('service', sons[1].operand)
        self.assertEqual(svc_bd2, sons[1].sons[0])

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule must go CRITICAL
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # Now we also set bd2 as WARNING/HARD...
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(1, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And If we set one WARNING too?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(1, svc_bd1.last_hard_state_id)

        # Must be WARNING (worse no 0 value for both)
        state = bp_rule.get_state()
        self.assertEqual(1, state)

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
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
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
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('of:', bp_rule.operand)
        # Simple 1of: so in fact a triple ('1','2','2') (1of and MAX,MAX
        if with_pct is True:
            if with_neg is True:
                self.assertEqual(('-50%', '2', '2'), bp_rule.of_values)
            else:
                self.assertEqual(('50%', '2', '2'), bp_rule.of_values)
        else:
            if with_neg is True:
                self.assertEqual(('-1', '2', '2'), bp_rule.of_values)
            else:
                self.assertEqual(('1', '2', '2'), bp_rule.of_values)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        self.assertEqual('service', sons[0].operand)
        self.assertEqual(svc_bd1, sons[0].sons[0])
        self.assertEqual('service', sons[1].operand)
        self.assertEqual(svc_bd2, sons[1].sons[0])

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule still be OK
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we also set bd2 as CRITICAL/HARD...
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(2, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2 now
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And If we set one WARNING now?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(1, svc_bd1.last_hard_state_id)

        # Must be WARNING (worse no 0 value for both, like for AND rule)
        state = bp_rule.get_state()
        self.assertEqual(1, state)

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
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('of:', bp_rule.operand)
        # Simple 1of: so in fact a triple ('1','2','2') (1of and MAX,MAX
        if with_pct is True:
            if with_neg is True:
                self.assertEqual(('-50%', '2', '2'), bp_rule.of_values)
            else:
                self.assertEqual(('50%', '2', '2'), bp_rule.of_values)
        else:
            if with_neg is True:
                self.assertEqual(('-1', '2', '2'), bp_rule.of_values)
            else:
                self.assertEqual(('1', '2', '2'), bp_rule.of_values)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        self.assertEqual('host', sons[0].operand)
        self.assertEqual(host, sons[0].sons[0])
        self.assertEqual('host', sons[1].operand)
        self.assertEqual(router, sons[1].sons[0])

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
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('|', bp_rule.operand)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        self.assertEqual('service', sons[0].operand)
        self.assertEqual(svc_bd1, sons[0].sons[0])
        self.assertEqual('service', sons[1].operand)
        self.assertEqual(svc_bd2, sons[1].sons[0])

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        state = bp_rule.get_state()
        self.assertEqual(0, state)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(2, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And now we must be CRITICAL/SOFT!
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('CRITICAL', svc_cor.state)
        self.assertEqual('SOFT', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # OK, re recheck again, GO HARD!
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('CRITICAL', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(2, svc_cor.last_hard_state_id)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(1, svc_bd2.last_hard_state_id)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assertEqual(1, state)

        # And in a HARD
        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('WARNING', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(1, svc_cor.last_hard_state_id)

        print "All elements", bp_rule.list_all_elements()

        print "IMPACT:", svc_bd2.impacts
        for i in svc_bd2.impacts:
            print i.get_name()

        # Assert that Simple_Or Is an impact of the problem bd2
        self.assertIn(svc_cor, svc_bd2.impacts)
        # and bd1 too
        self.assertIn(svc_cor, svc_bd1.impacts)

    def test_dep_node_list_elements(self):
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('|', bp_rule.operand)

        print "All elements", bp_rule.list_all_elements()
        all_elt = bp_rule.list_all_elements()

        self.assertIn(svc_bd2, all_elt)
        self.assertIn(svc_bd1, all_elt)

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
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_web1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "web1")
        self.assertEqual(False, svc_web1.got_business_rule)
        self.assertIs(None, svc_web1.business_rule)
        svc_web2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "web2")
        self.assertEqual(False, svc_web2.got_business_rule)
        self.assertIs(None, svc_web2.business_rule)
        svc_lvs1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs1")
        self.assertEqual(False, svc_lvs1.got_business_rule)
        self.assertIs(None, svc_lvs1.business_rule)
        svc_lvs2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs2")
        self.assertEqual(False, svc_lvs2.got_business_rule)
        self.assertIs(None, svc_lvs2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "ERP")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('&', bp_rule.operand)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 3 sons, each 3 rules
        self.assertEqual(3, len(sons))
        bd_node = sons[0]
        self.assertEqual('|', bd_node.operand)
        self.assertEqual(svc_bd1, bd_node.sons[0].sons[0])
        self.assertEqual(svc_bd2, bd_node.sons[1].sons[0])

        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        state = bp_rule.get_state()
        self.assertEqual(0, state)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        print "Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(2, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And now we must be CRITICAL/SOFT!
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('CRITICAL', svc_cor.state)
        self.assertEqual('SOFT', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # OK, re recheck again, GO HARD!
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('CRITICAL', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(2, svc_cor.last_hard_state_id)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(1, svc_bd2.last_hard_state_id)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assertEqual(1, state)

        # And in a HARD
        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('WARNING', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(1, svc_cor.last_hard_state_id)

        print "All elements", bp_rule.list_all_elements()

        print "IMPACT:", svc_bd2.impacts
        for i in svc_bd2.impacts:
            print i.get_name()

        # Assert that Simple_Or Is an impact of the problem bd2
        self.assertIn(svc_cor, svc_bd2.impacts)
        # and bd1 too
        self.assertIn(svc_cor, svc_bd1.impacts)

        # And now all is green :)
        self.scheduler_loop(2, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | value1=1 value2=2']])

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

        # And no more in impact
        self.assertNotIn(svc_cor, svc_bd2.impacts)
        self.assertNotIn(svc_cor, svc_bd1.impacts)

        # And what if we set 2 service from distant rule CRITICAL?
        # ERP should be still OK
        # And now all is green :)
        self.scheduler_loop(2, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2'], [svc_web1, 2, 'CRITICAL | value1=1 value2=2']])

        print "ERP: Launch internal check"
        svc_cor.launch_check(now-1)
        c = svc_cor.actions[0]
        self.assertEqual(True, c.internal)
        self.assertTrue(c.is_launchable(now))

        # ask the scheduler to launch this check
        # and ask 2 loops: one for launch the check
        # and another to integer the result
        self.scheduler_loop(2, [])

        # We should have no more the check
        self.assertEqual(0, len(svc_cor.actions))

        print "ERP: Look at svc_cor state", svc_cor.state
        # What is the svc_cor state now?
        self.assertEqual('OK', svc_cor.state)
        self.assertEqual('HARD', svc_cor.state_type)
        self.assertEqual(0, svc_cor.last_hard_state_id)

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
        self.assertEqual(False, A.got_business_rule)
        self.assertIs(None, A.business_rule)
        B = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "B")
        self.assertEqual(False, B.got_business_rule)
        self.assertIs(None, B.business_rule)
        C = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "C")
        self.assertEqual(False, C.got_business_rule)
        self.assertIs(None, C.business_rule)
        D = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "D")
        self.assertEqual(False, D.got_business_rule)
        self.assertIs(None, D.business_rule)
        E = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "E")
        self.assertEqual(False, E.got_business_rule)
        self.assertIs(None, E.business_rule)

        if with_pct == False:
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Complex_ABCOf")
        else:
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Complex_ABCOf_pct")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('of:', bp_rule.operand)
        if with_pct == False:
            self.assertEqual(('5', '1', '1'), bp_rule.of_values)
        else:
            self.assertEqual(('100%', '20%', '20%'), bp_rule.of_values)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(5, len(sons))
        self.assertEqual('service', sons[0].operand)
        self.assertEqual(A, sons[0].sons[0])
        self.assertEqual('service', sons[1].operand)
        self.assertEqual(B, sons[1].sons[0])
        self.assertEqual('service', sons[2].operand)
        self.assertEqual(C, sons[2].sons[0])
        self.assertEqual('service', sons[3].operand)
        self.assertEqual(D, sons[3].sons[0])
        self.assertEqual('service', sons[4].operand)
        self.assertEqual(E, sons[4].sons[0])

        # Now state working on the states
        self.scheduler_loop(1, [[A, 0, 'OK'], [B, 0, 'OK'], [C, 0, 'OK'], [D, 0, 'OK'], [E, 0, 'OK']])
        self.assertEqual('OK', A.state)
        self.assertEqual('HARD', A.state_type)
        self.assertEqual('OK', B.state)
        self.assertEqual('HARD', B.state_type)
        self.assertEqual('OK', C.state)
        self.assertEqual('HARD', C.state_type)
        self.assertEqual('OK', D.state)
        self.assertEqual('HARD', D.state_type)
        self.assertEqual('OK', E.state)
        self.assertEqual('HARD', E.state_type)

        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we set the A as soft/CRITICAL
        self.scheduler_loop(1, [[A, 2, 'CRITICAL']])
        self.assertEqual('CRITICAL', A.state)
        self.assertEqual('SOFT', A.state_type)
        self.assertEqual(0, A.last_hard_state_id)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get A CRITICAL/HARD
        self.scheduler_loop(1, [[A, 2, 'CRITICAL']])
        self.assertEqual('CRITICAL', A.state)
        self.assertEqual('HARD', A.state_type)
        self.assertEqual(2, A.last_hard_state_id)

        # The rule still be OK
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # Now we also set B as CRITICAL/HARD...
        self.scheduler_loop(2, [[B, 2, 'CRITICAL']])
        self.assertEqual('CRITICAL', B.state)
        self.assertEqual('HARD', B.state_type)
        self.assertEqual(2, B.last_hard_state_id)

        # And now the state of the rule must be 2 now
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And If we set A dn B WARNING now?
        self.scheduler_loop(2, [[A, 1, 'WARNING'], [B, 1, 'WARNING']])
        self.assertEqual('WARNING', A.state)
        self.assertEqual('HARD', A.state_type)
        self.assertEqual(1, A.last_hard_state_id)
        self.assertEqual('WARNING', B.state)
        self.assertEqual('HARD', B.state_type)
        self.assertEqual(1, B.last_hard_state_id)

        # Must be WARNING (worse no 0 value for both, like for AND rule)
        state = bp_rule.get_state()
        print "state", state
        self.assertEqual(1, state)

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
        self.assertEqual(0, bp_rule.get_state())
        # 5,1,1
        if with_pct == False:
            bp_rule.of_values = ('5', '1', '1')
        else:
            bp_rule.of_values = ('100%', '20%', '20%')
        bp_rule.is_of_mul = True
        self.assertEqual(1, bp_rule.get_state())
        # 5,2,1
        if with_pct == False:
            bp_rule.of_values = ('5', '2', '1')
        else:
            bp_rule.of_values = ('100%', '40%', '20%')
        bp_rule.is_of_mul = True
        self.assertEqual(0, bp_rule.get_state())

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
        self.assertEqual(2, bp_rule.get_state())
        # 4,1,1
        if with_pct == False:
            bp_rule.of_values = ('4', '1', '1')
        else:
            bp_rule.of_values = ('40%', '20%', '20%')
        bp_rule.is_of_mul = True
        self.assertEqual(2, bp_rule.get_state())

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
        self.assertEqual(0, bp_rule.get_state())
        # * 4,1,1
        if with_pct == False:
            bp_rule.of_values = ('4', '1', '1')
        else:
            bp_rule.of_values = ('80%', '20%', '20%')
        bp_rule.is_of_mul = True
        self.assertEqual(2, bp_rule.get_state())
        # * 4,1,3
        if with_pct == False:
            bp_rule.of_values = ('4', '1', '3')
        else:
            bp_rule.of_values = ('80%', '20%', '60%')
        bp_rule.is_of_mul = True
        self.assertEqual(1, bp_rule.get_state())

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
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_And_not")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('&', bp_rule.operand)

        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        self.assertEqual('service', sons[0].operand)
        self.assertEqual(svc_bd1, sons[0].sons[0])
        self.assertEqual('service', sons[1].operand)
        self.assertEqual(svc_bd2, sons[1].sons[0])

        # Now state working on the states
        self.scheduler_loop(2, [[svc_bd1, 0, 'OK | value1=1 value2=2'], [svc_bd2, 2, 'CRITICAL | rtt=10']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('CRITICAL', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        # We are a NOT, so should be OK here
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        # becase we want HARD states
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule must go CRITICAL
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # Now we also set bd2 as WARNING/HARD...
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(1, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And If we set one WARNING too?
        self.scheduler_loop(2, [[svc_bd1, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(1, svc_bd1.last_hard_state_id)

        # Must be WARNING (worse no 0 value for both)
        state = bp_rule.get_state()
        self.assertEqual(1, state)

        # Now try to get ok in both place, should be bad :)
        self.scheduler_loop(2, [[svc_bd1, 0, 'OK | value1=1 value2=2'], [svc_bd2, 0, 'OK | value1=1 value2=2']])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(0, svc_bd2.last_hard_state_id)

        # Must be CRITICAL (ok and not ok IS no OK :) )
        state = bp_rule.get_state()
        self.assertEqual(2, state)






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
        self.assertIsNot(svc_lvs1, None)
        svc_lvs2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "lvs2")
        self.assertIsNot(svc_lvs2, None)

        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assertEqual(False, svc_bd1.got_business_rule)
        self.assertIs(None, svc_bd1.business_rule)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assertEqual(False, svc_bd2.got_business_rule)
        self.assertIs(None, svc_bd2.business_rule)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Multi_levels")
        self.assertEqual(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        bp_rule = svc_cor.business_rule
        self.assertEqual('&', bp_rule.operand)

        # We check for good parent/childs links
        # So svc_cor should be a son of svc_bd1 and svc_bd2
        # and bd1 and bd2 should be parents of svc_cor
        self.assertIn(svc_cor, svc_bd1.child_dependencies)
        self.assertIn(svc_cor, svc_bd2.child_dependencies)
        self.assertIn(svc_cor, router.child_dependencies)
        self.assertIn(svc_bd1, svc_cor.parent_dependencies)
        self.assertIn(svc_bd2, svc_cor.parent_dependencies)
        self.assertIn(router, svc_cor.parent_dependencies)


        sons = bp_rule.sons
        print "Sons,", sons
        # We've got 2 sons, 2 services nodes
        self.assertEqual(2, len(sons))
        # Son0 is (test_host_0,db1| (test_host_0,db2 & (test_host_0,lvs1|test_host_0,lvs2) ) )
        son0 = sons[0]
        self.assertEqual('|', son0.operand)
        # Son1 is test_router_0
        self.assertEqual('host', sons[1].operand)
        self.assertEqual(router, sons[1].sons[0])

        # Son0_0 is test_host_0,db1
        # Son0_1 is test_host_0,db2 & (test_host_0,lvs1|test_host_0,lvs2)
        son0_0 = son0.sons[0]
        son0_1 = son0.sons[1]
        self.assertEqual('service', son0_0.operand)
        self.assertEqual(svc_bd1, son0_0.sons[0])
        self.assertEqual('&', son0_1.operand)

        # Son0_1_0 is test_host_0,db2
        # Son0_1_1 is test_host_0,lvs1|test_host_0,lvs2
        son0_1_0 = son0_1.sons[0]
        son0_1_1 = son0_1.sons[1]
        self.assertEqual('service', son0_1_0.operand)
        self.assertEqual(svc_bd2, son0_1_0.sons[0])
        self.assertEqual('|', son0_1_1.operand)

        # Son0_1_1_0 is test_host_0,lvs1
        # Son0_1_1_1 is test_host_0,lvs2
        son0_1_1_0 = son0_1_1.sons[0]
        son0_1_1_1 = son0_1_1.sons[1]


        self.assertEqual('service', son0_1_1_0.operand)
        self.assertEqual(svc_lvs1, son0_1_1_0.sons[0])
        self.assertEqual('service', son0_1_1_1.operand)
        self.assertEqual(svc_lvs2, son0_1_1_1.sons[0])


        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10'],
                                [svc_lvs1, 0, 'OK'], [svc_lvs2, 0, 'OK'], [router, 0, 'UP'] ])
        self.assertEqual('OK', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual('OK', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)

        # All is green, the rule should be green too
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we set the bd1 as soft/CRITICAL
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('SOFT', svc_bd1.state_type)
        self.assertEqual(0, svc_bd1.last_hard_state_id)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get bd1 CRITICAL/HARD
        self.scheduler_loop(1, [[svc_bd1, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd1.state)
        self.assertEqual('HARD', svc_bd1.state_type)
        self.assertEqual(2, svc_bd1.last_hard_state_id)

        # The rule must still be a 0 (or inside)
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we also set bd2 as CRITICAL/HARD... byebye 0 :)
        self.scheduler_loop(2, [[svc_bd2, 2, 'CRITICAL | value1=1 value2=2']])
        self.assertEqual('CRITICAL', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(2, svc_bd2.last_hard_state_id)

        # And now the state of the rule must be 2
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # And If we set one WARNING?
        self.scheduler_loop(2, [[svc_bd2, 1, 'WARNING | value1=1 value2=2']])
        self.assertEqual('WARNING', svc_bd2.state)
        self.assertEqual('HARD', svc_bd2.state_type)
        self.assertEqual(1, svc_bd2.last_hard_state_id)

        # Must be WARNING (better no 0 value)
        state = bp_rule.get_state()
        self.assertEqual(1, state)

        # We should got now svc_bd2 and svc_bd1 as root problems
        print "Root problems"
        for p in svc_cor.source_problems:
            print p.get_full_name()
        self.assertIn(svc_bd1, svc_cor.source_problems)
        self.assertIn(svc_bd2, svc_cor.source_problems)



        # What about now with the router in DOWN?
        self.scheduler_loop(5, [[router, 2, 'DOWN']])
        self.assertEqual('DOWN', router.state)
        self.assertEqual('HARD', router.state_type)
        self.assertEqual(1, router.last_hard_state_id)

        # Must be CRITICAL (CRITICAL VERSUS DOWN -> DOWN)
        state = bp_rule.get_state()
        self.assertEqual(2, state)

        # Now our root problem is router
        print "Root problems"
        for p in svc_cor.source_problems:
            print p.get_full_name()
        self.assertIn(router, svc_cor.source_problems)












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

        self.assertEqual(True, host.got_business_rule)
        self.assertIsNot(host.business_rule, None)
        bp_rule = host.business_rule
        self.assertEqual('|', bp_rule.operand)

        # Now state working on the states
        self.scheduler_loop(3, [[host, 0, 'UP'], [A, 0, 'UP'], [B, 0, 'UP'] ] )
        self.assertEqual('UP', host.state)
        self.assertEqual('HARD', host.state_type)
        self.assertEqual('UP', A.state)
        self.assertEqual('HARD', A.state_type)

        state = bp_rule.get_state()
        print "WTF0", state
        self.assertEqual(0, state)

        # Now we set the A as soft/DOWN
        self.scheduler_loop(1, [[A, 2, 'DOWN']])
        self.assertEqual('DOWN', A.state)
        self.assertEqual('SOFT', A.state_type)
        self.assertEqual(0, A.last_hard_state_id)

        # The business rule must still be 0
        state = bp_rule.get_state()
        self.assertEqual(0, state)

        # Now we get A DOWN/HARD
        self.scheduler_loop(3, [[A, 2, 'DOWN']])
        self.assertEqual('DOWN', A.state)
        self.assertEqual('HARD', A.state_type)
        self.assertEqual(1, A.last_hard_state_id)

        # The rule must still be a 2 (or inside)
        state = bp_rule.get_state()
        print "WFT", state
        self.assertEqual(2, state)

        # Now we also set B as DOWN/HARD, should get back to 0!
        self.scheduler_loop(3, [[B, 2, 'DOWN']])
        self.assertEqual('DOWN', B.state)
        self.assertEqual('HARD', B.state_type)
        self.assertEqual(1, B.last_hard_state_id)

        # And now the state of the rule must be 0 again! (strange rule isn't it?)
        state = bp_rule.get_state()
        self.assertEqual(0, state)





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
        self.assertFalse(self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        # Info: Simple_1Of_1unk_svc: my business rule is invalid
        # Info: Simple_1Of_1unk_svc: Business rule uses unknown service test_host_0/db3
        # Error: [items] In Simple_1Of_1unk_svc is incorrect ; from etc/business_correlator_broken/services.cfg
        self.assertEqual(3, len([log for log in logs if re.search('Simple_1Of_1unk_svc', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('service test_host_0/db3', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('Simple_1Of_1unk_svc.+from etc.+business_correlator_broken.+services.cfg', log)]) )
        # Info: ERP_unk_svc: my business rule is invalid
        # Info: ERP_unk_svc: Business rule uses unknown service test_host_0/web100
        # Info: ERP_unk_svc: Business rule uses unknown service test_host_0/lvs100
        # Error: [items] In ERP_unk_svc is incorrect ; from etc/business_correlator_broken/services.cfg
        self.assertEqual(4, len([log for log in logs if re.search('ERP_unk_svc', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('service test_host_0/web100', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('service test_host_0/lvs100', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('ERP_unk_svc.+from etc.+business_correlator_broken.+services.cfg', log)]) )
        # Info: Simple_1Of_1unk_host: my business rule is invalid
        # Info: Simple_1Of_1unk_host: Business rule uses unknown host test_host_9
        # Error: [items] In Simple_1Of_1unk_host is incorrect ; from etc/business_correlator_broken/services.cfg
        self.assertEqual(3, len([log for log in logs if re.search('Simple_1Of_1unk_host', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('host test_host_9', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('Simple_1Of_1unk_host.+from etc.+business_correlator_broken.+services.cfg', log)]) )

        # Now the number of all failed business rules.
        self.assertEqual(3, len([log for log in logs if re.search('my business rule is invalid', log)]) )



if __name__ == '__main__':
    unittest.main()
