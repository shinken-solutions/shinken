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


class TestBusinesscorrelExpand(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_business_correlator_expand_expression.cfg')

    # Tries to expand hostgroup based expression, and compare it with its
    # manually written counterpart.
    def test_hostgroup_expansion(self):
        for ruleid in range(1, 10):
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_%s0" % ruleid)
            bp_rule0 = svc_cor.business_rule
            svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_%s1" % ruleid)
            bp_rule1 = svc_cor.business_rule
            self.assert_(str(bp_rule0) == str(bp_rule1))

    def test_hostgroup_expansion_bprule_simple_host_srv(self):
        for name in ("bprule_00", "bprule_50"):
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
        for name in ("bprule_10", "bprule_60"):
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
        for name in ("bprule_20", "bprule_70"):
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
        for name in ("bprule_30", "bprule_80"):
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
        for name in ("bprule_40", "bprule_90"):
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

    def test_macro_expansion_bprule_macro_expand(self):
        # Tests macro expansion
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bprule_macro_expand")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == 'of:')
        self.assert_(bp_rule.of_values == ('1', '2', '2'))

    def test_macro_expansion_bprule_macro_modulated(self):
        # Tests macro modulation
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy_modulated", "bprule_macro_modulated")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
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

        self.assert_(svc_cor.business_rule is not bp_rule)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.get_state() == 2)
        self.assert_(svc_cor.last_hard_state_id == 2)

        # Tests modulated value
        mod = self.sched.macromodulations.find_by_name("xof_modulation")
        mod.customs['_XOF'] = '1'

        # Forces business rule evaluation.
        self.scheduler_loop(2, [[svc_cor, None, None]], do_sleep=True)

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

        self.assert_(svc_cor.business_rule is bp_rule)
        self.assert_(svc_cor.last_hard_state_id == 3)
        self.assert_(svc_cor.output.startswith("Error while re-evaluating business rule"))


class TestConfigBroken(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_business_correlator_expand_expression_broken.cfg')

    def test_hostgroup_expansion_errors(self):
        self.assert_(not self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        self.assert_(len([log for log in logs if re.search('Business rule uses unknown or empty hostgroup', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('Business rule uses invalid regex', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('Business rule uses regex that no host_name matches', log)]) == 1)
        self.assert_(len([log for log in logs if re.search('Business rule uses unknown service', log)]) == 2)
        # With permissive flag set, there should only be warnings regarding
        # unknown services.
        self.assert_(len([log for log in logs if re.search('Business rule got an unknown service for.*Ignored', log)]) == 2)


if __name__ == '__main__':
    unittest.main()
