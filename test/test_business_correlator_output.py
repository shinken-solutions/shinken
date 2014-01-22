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
# This file is used to test business rules output based on template expansion.
#

import time
from shinken_test import unittest, ShinkenTest


class TestBusinesscorrelOutput(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_business_correlator_output.cfg')

    def test_service_shorten_status(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "empty_bp_rule_output")
        self.assert_(svc_cor.status_to_short_status("OK") == "O")
        self.assert_(svc_cor.status_to_short_status("WARNING") == "W")
        self.assert_(svc_cor.status_to_short_status("CRITICAL") == "C")
        self.assert_(svc_cor.status_to_short_status("UNKNOWN") == "U")
        self.assert_(svc_cor.status_to_short_status("UP") == "U")
        self.assert_(svc_cor.status_to_short_status("DOWN") == "D")
        self.assert_(svc_cor.status_to_short_status("FAKE") == "FAKE")

    def test_bprule_empty_output(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "empty_bp_rule_output")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.get_business_rule_output() == "")

    def test_bprule_expand_template_macros(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "formatted_bp_rule_output")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv3")
        hst4 = self.sched.hosts.find_by_name("test_host_04")

        for i in range(2):
            self.scheduler_loop(1, [
                [svc1, 0, 'OK test_host_01/srv1'],
                [svc2, 1, 'WARNING test_host_02/srv2'],
                [svc3, 2, 'CRITICAL test_host_03/srv3'],
                [hst4, 2, 'DOWN test_host_04']])

        time.sleep(61)
        self.sched.manage_internal_checks()
        self.sched.consume_results()

        # Performs checks
        template = "$STATUS$,$SHORT_STATUS$,$HOST_NAME$,$SERVICE_DESCRIPTION$,$FULL_NAME$"
        output = svc_cor.expand_business_rule_item_macros(template, svc1)
        self.assert_(output == "OK,O,test_host_01,srv1,test_host_01/srv1")
        output = svc_cor.expand_business_rule_item_macros(template, svc2)
        self.assert_(output == "WARNING,W,test_host_02,srv2,test_host_02/srv2")
        output = svc_cor.expand_business_rule_item_macros(template, svc3)
        self.assert_(output == "CRITICAL,C,test_host_03,srv3,test_host_03/srv3")
        output = svc_cor.expand_business_rule_item_macros(template, hst4)
        self.assert_(output == "DOWN,D,test_host_04,,test_host_04")
        output = svc_cor.expand_business_rule_item_macros(template, svc_cor)
        self.assert_(output == "CRITICAL,C,dummy,formatted_bp_rule_output,dummy/formatted_bp_rule_output")

    def test_bprule_output(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "formatted_bp_rule_output")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.business_rule_output_template == "$STATUS$ $([$STATUS$: $FULL_NAME$] )$")

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv3")
        hst4 = self.sched.hosts.find_by_name("test_host_04")

        for i in range(2):
            self.scheduler_loop(1, [
                [svc1, 0, 'OK test_host_01/srv1'],
                [svc2, 1, 'WARNING test_host_02/srv2'],
                [svc3, 2, 'CRITICAL test_host_03/srv3'],
                [hst4, 2, 'DOWN test_host_04']])

        time.sleep(61)
        self.sched.manage_internal_checks()
        self.sched.consume_results()

        # Performs checks
        output = svc_cor.output
        self.assert_(output.find("[WARNING: test_host_02/srv2]") > 0)
        self.assert_(output.find("[CRITICAL: test_host_03/srv3]") > 0)
        self.assert_(output.find("[DOWN: test_host_04]") > 0)
        # Should not display OK state checks
        self.assert_(output.find("[OK: test_host_01/srv1]") == -1)
        self.assert_(output.startswith("CRITICAL"))

    def test_bprule_xof_one_critical_output(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "formatted_bp_rule_xof_output")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.business_rule_output_template == "$STATUS$ $([$STATUS$: $FULL_NAME$] )$")

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv3")
        hst4 = self.sched.hosts.find_by_name("test_host_04")

        for i in range(2):
            self.scheduler_loop(1, [
                [svc1, 0, 'OK test_host_01/srv1'],
                [svc2, 0, 'OK test_host_02/srv2'],
                [svc3, 2, 'CRITICAL test_host_03/srv3'],
                [hst4, 0, 'UP test_host_04']])

        time.sleep(61)
        self.sched.manage_internal_checks()
        self.sched.consume_results()

        # Performs checks
        self.assert_(svc_cor.business_rule.get_state() == 0)
        self.assert_(svc_cor.output == "OK [CRITICAL: test_host_03/srv3]")

    def test_bprule_xof_all_ok_output(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "formatted_bp_rule_xof_output")
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.business_rule_output_template == "$STATUS$ $([$STATUS$: $FULL_NAME$] )$")

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv3")
        hst4 = self.sched.hosts.find_by_name("test_host_04")

        for i in range(2):
            self.scheduler_loop(1, [
                [svc1, 0, 'OK test_host_01/srv1'],
                [svc2, 0, 'OK test_host_02/srv2'],
                [svc3, 0, 'OK test_host_03/srv3'],
                [hst4, 0, 'UP test_host_04']])

        time.sleep(61)
        self.sched.manage_internal_checks()
        self.sched.consume_results()

        # Performs checks
        self.assert_(svc_cor.business_rule.get_state() == 0)
        self.assert_(svc_cor.output == "OK all checks were successful.")


if __name__ == '__main__':
    unittest.main()
