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
# This file is used to test hostgroups and regex expressions expansion in
# business rules.
#

import re
from shinken_test import unittest, ShinkenTest

# Set this variable False to disable profiling test
PROFILE_BP_RULE_RE_PROCESSING = False


class TestBusinesscorrelExpand(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_business_correlator_expand_expression.cfg')

    def test_hostgroup_expansion_bprule_simple_host_srv(self):
        for name in ("bprule_00", "bprule_01", "bprule_02", "bprule_03", "bprule_04", "bprule_05", "bprule_06"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == '&')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('2', '2', '2'))

            srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
            srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv1")

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)
            self.assert_(sons[0].operand == 'service')
            self.assert_(sons[1].operand == 'service')

            self.assert_(srv1 in (sons[0].sons[0], sons[1].sons[0]))
            self.assert_(srv2 in (sons[0].sons[0], sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_simple_xof_host_srv(self):
        for name in ("bprule_10", "bprule_11", "bprule_12", "bprule_13", "bprule_14", "bprule_15", "bprule_16"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == 'of:')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('1', '2', '2'))

            srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
            srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv1")

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)
            self.assert_(sons[0].operand == 'service')
            self.assert_(sons[1].operand == 'service')

            self.assert_(srv1 in (sons[0].sons[0], sons[1].sons[0]))
            self.assert_(srv2 in (sons[0].sons[0], sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_combined_and(self):
        for name in ("bprule_20", "bprule_21", "bprule_22", "bprule_23", "bprule_24", "bprule_25", "bprule_26"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == '&')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('2', '2', '2'))

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)

            for son in sons:
                self.assert_(son.operand == '&')
                self.assert_(son.not_value is False)
                self.assert_(son.of_values == ('2', '2', '2'))
                self.assert_(len(son.sons) == 2)
                self.assert_(son.sons[0].operand == 'service')
                self.assert_(son.sons[1].operand == 'service')

            hst1_srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
            hst2_srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv1")
            hst1_srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv2")
            hst2_srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

            self.assert_(hst1_srv1 in (sons[0].sons[0].sons[0], sons[0].sons[1].sons[0]))
            self.assert_(hst2_srv1 in (sons[0].sons[0].sons[0], sons[0].sons[1].sons[0]))
            self.assert_(hst1_srv2 in (sons[1].sons[0].sons[0], sons[1].sons[1].sons[0]))
            self.assert_(hst2_srv2 in (sons[1].sons[0].sons[0], sons[1].sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_combined_or(self):
        for name in ("bprule_30", "bprule_31", "bprule_32", "bprule_33", "bprule_34", "bprule_35", "bprule_36"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == '|')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('2', '2', '2'))

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)

            for son in sons:
                self.assert_(son.operand == '&')
                self.assert_(son.not_value is False)
                self.assert_(son.of_values == ('2', '2', '2'))
                self.assert_(len(son.sons) == 2)
                self.assert_(son.sons[0].operand == 'service')
                self.assert_(son.sons[1].operand == 'service')

            hst1_srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
            hst2_srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv1")
            hst1_srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv2")
            hst2_srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

            self.assert_(hst1_srv1 in (sons[0].sons[0].sons[0], sons[0].sons[1].sons[0]))
            self.assert_(hst2_srv1 in (sons[0].sons[0].sons[0], sons[0].sons[1].sons[0]))
            self.assert_(hst1_srv2 in (sons[1].sons[0].sons[0], sons[1].sons[1].sons[0]))
            self.assert_(hst2_srv2 in (sons[1].sons[0].sons[0], sons[1].sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_simple_hosts(self):
        for name in ("bprule_40", "bprule_41", "bprule_42", "bprule_43"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == '&')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('2', '2', '2'))

            hst1 = self.sched.hosts.find_by_name("test_host_01")
            hst2 = self.sched.hosts.find_by_name("test_host_02")

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)
            self.assert_(sons[0].operand == 'host')
            self.assert_(sons[1].operand == 'host')

            self.assert_(hst1 in (sons[0].sons[0], sons[1].sons[0]))
            self.assert_(hst2 in (sons[0].sons[0], sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_xof_hosts(self):
        for name in ("bprule_50", "bprule_51", "bprule_52", "bprule_53"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == 'of:')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('1', '2', '2'))

            hst1 = self.sched.hosts.find_by_name("test_host_01")
            hst2 = self.sched.hosts.find_by_name("test_host_02")

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)
            self.assert_(sons[0].operand == 'host')
            self.assert_(sons[1].operand == 'host')

            self.assert_(hst1 in (sons[0].sons[0], sons[1].sons[0]))
            self.assert_(hst2 in (sons[0].sons[0], sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_same_host_srv(self):
        for name in ("bprule_60", "bprule_61"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_01", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == '&')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('2', '2', '2'))

            srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
            srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv2")

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)
            self.assert_(sons[0].operand == 'service')
            self.assert_(sons[1].operand == 'service')

            self.assert_(srv1 in (sons[0].sons[0], sons[1].sons[0]))
            self.assert_(srv2 in (sons[0].sons[0], sons[1].sons[0]))

    def test_hostgroup_expansion_bprule_xof_same_host_srv(self):
        for name in ("bprule_70", "bprule_71"):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_01", name)
            self.assert_(svc_cor.got_business_rule is True)
            self.assert_(svc_cor.business_rule is not None)
            bp_rule = svc_cor.business_rule
            self.assert_(bp_rule.operand == 'of:')
            self.assert_(bp_rule.not_value is False)
            self.assert_(bp_rule.of_values == ('1', '2', '2'))

            srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
            srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv2")

            sons = bp_rule.sons
            self.assert_(len(sons) == 2)
            self.assert_(sons[0].operand == 'service')
            self.assert_(sons[1].operand == 'service')

            self.assert_(srv1 in (sons[0].sons[0], sons[1].sons[0]))
            self.assert_(srv2 in (sons[0].sons[0], sons[1].sons[0]))

    def test_macro_expansion_bprule_no_macro(self):
        # Tests macro expansion
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_no_macro")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.processed_business_rule == "1 of: test_host_01,srv1 & test_host_02,srv2")
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        self.assert_(bp_rule.of_values == ('1', '2', '2'))

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        # Setting dependent services status
        self.scheduler_loop(1, [
            [svc1, 0, 'UP | value1=1 value2=2'],
            [svc2, 0, 'UP | value1=1 value2=2']])

        self.assert_(svc1.state == 'OK')
        self.assert_(svc1.state_type == 'HARD')
        self.assert_(svc2.state == 'OK')
        self.assert_(svc2.state_type == 'HARD')

        self.scheduler_loop(1, [[svc1, 2, 'CRITICAL | value1=1 value2=2']])

        self.assert_(svc1.state == 'CRITICAL')
        self.assert_(svc1.state_type == 'HARD')

        # Forces business rule evaluation.
        self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True)

        # Business rule should not have been re-evaluated (no macro in the
        # bp_rule)
        self.assert_(svc_cor.business_rule is bp_rule)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.get_state() == 0)
        self.assert_(svc_cor.last_hard_state_id == 0)

    def test_macro_expansion_bprule_macro_expand(self):
        # Tests macro expansion
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_macro_expand")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.processed_business_rule == "1 of: test_host_01,srv1 & test_host_02,srv2")
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        self.assert_(bp_rule.of_values == ('1', '2', '2'))

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        # Setting dependent services status
        self.scheduler_loop(1, [
            [svc1, 0, 'UP | value1=1 value2=2'],
            [svc2, 0, 'UP | value1=1 value2=2']])

        self.assert_(svc1.state == 'OK')
        self.assert_(svc1.state_type == 'HARD')
        self.assert_(svc2.state == 'OK')
        self.assert_(svc2.state_type == 'HARD')

        self.scheduler_loop(1, [[svc1, 2, 'CRITICAL | value1=1 value2=2']])

        self.assert_(svc1.state == 'CRITICAL')
        self.assert_(svc1.state_type == 'HARD')

        # Forces business rule evaluation.
        self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True)

        # Business rule should not have been re-evaluated (macro did not change
        # value)
        self.assert_(svc_cor.business_rule is bp_rule)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.get_state() == 0)
        self.assert_(svc_cor.last_hard_state_id == 0)

    def test_macro_expansion_bprule_macro_modulated(self):
        # Tests macro modulation
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy_modulated", "bprule_macro_modulated")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.processed_business_rule == "2 of: test_host_01,srv1 & test_host_02,srv2")
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        self.assert_(bp_rule.of_values == ('2', '2', '2'))

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        # Setting dependent services status
        self.scheduler_loop(1, [
            [svc1, 0, 'UP | value1=1 value2=2'],
            [svc2, 0, 'UP | value1=1 value2=2']])

        self.assert_(svc1.state == 'OK')
        self.assert_(svc1.state_type == 'HARD')
        self.assert_(svc2.state == 'OK')
        self.assert_(svc2.state_type == 'HARD')

        self.scheduler_loop(1, [[svc1, 2, 'CRITICAL | value1=1 value2=2']])

        self.assert_(svc1.state == 'CRITICAL')
        self.assert_(svc1.state_type == 'HARD')

        # Forces business rule evaluation.
        self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True)

        # Business rule should not have been re-evaluated (macro did not change
        # value)
        self.assert_(svc_cor.business_rule is bp_rule)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.get_state() == 2)
        self.assert_(svc_cor.last_hard_state_id == 2)

        # Tests modulated value
        mod = self.sched.macromodulations.find_by_name("xof_modulation")
        mod.customs['_XOF'] = '1'

        # Forces business rule evaluation.
        self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True)

        self.assert_(svc_cor.processed_business_rule == "1 of: test_host_01,srv1 & test_host_02,srv2")
        self.assert_(svc_cor.business_rule is not bp_rule)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        self.assert_(bp_rule.of_values == ('1', '2', '2'))
        self.assert_(bp_rule.get_state() == 0)
        self.assert_(svc_cor.last_hard_state_id == 0)

        # Tests wrongly written macro modulation (inserts invalid string)
        mod.customs['_XOF'] = 'fake'

        # Forces business rule evaluation.
        self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True)

        # Business rule should have been re-evaluated (macro was modulated)
        self.assert_(svc_cor.business_rule is bp_rule)
        self.assert_(svc_cor.last_hard_state_id == 3)
        self.assert_(svc_cor.output.startswith("Error while re-evaluating business rule"))

    def test_macro_expansion_bprule_macro_profile(self):
        if PROFILE_BP_RULE_RE_PROCESSING is False:
            return

        import cProfile as profile

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        # Setting dependent services status
        self.scheduler_loop(1, [
            [svc1, 0, 'UP | value1=1 value2=2'],
            [svc2, 0, 'UP | value1=1 value2=2']], verbose=False)

        self.assert_(svc1.state == 'OK')
        self.assert_(svc1.state_type == 'HARD')
        self.assert_(svc2.state == 'OK')
        self.assert_(svc2.state_type == 'HARD')

        self.scheduler_loop(1, [[svc1, 2, 'CRITICAL | value1=1 value2=2']], verbose=False)

        self.assert_(svc1.state == 'CRITICAL')
        self.assert_(svc1.state_type == 'HARD')

        print "Profiling without macro"

        def profile_bp_rule_without_macro():
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_no_macro")
            for i in range(1000):
                self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True, verbose=False)

        profile.runctx('profile_bp_rule_without_macro()', globals(), locals())

        print "Profiling with macro"

        def profile_bp_rule_macro_expand():
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_macro_expand")
            for i in range(1000):
                self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True, verbose=False)

        profile.runctx('profile_bp_rule_macro_expand()', globals(), locals())

        print "Profiling with macro modulation"

        def profile_bp_rule_macro_modulated():
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy_modulated", "bprule_macro_modulated")
            for i in range(1000):
                self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True, verbose=False)

        profile.runctx('profile_bp_rule_macro_modulated()', globals(), locals())


class TestConfigBroken(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_business_correlator_expand_expression_broken.cfg')

    def test_hostgroup_expansion_errors(self):
        self.assert_(not self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        self.assert_(len([log for log in logs if re.search('Business rule uses invalid regex', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('Business rule got an empty result', log)]) == 3)


if __name__ == '__main__':
    unittest.main()
