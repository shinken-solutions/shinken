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


class TestServiceDepAndGroups(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_servicedependency_implicit_hostgroup.cfg')

    def test_implicithostgroups(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc_postfix = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "POSTFIX")
        self.assertIsNot(svc_postfix, None)

        svc_snmp = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "SNMP")
        self.assertIsNot(svc_snmp, None)

        svc_cpu = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "CPU")
        self.assertIsNot(svc_cpu, None)

        svc_snmp2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "SNMP")
        self.assertIsNot(svc_snmp2, None)

        svc_postfix_fathers = [c[0].get_full_name() for c in svc_postfix.act_depend_of]
        print svc_postfix_fathers
        # Should be [u'test_router_0/SNMP', u'test_host_0/SNMP', u'test_host_0']
        self.assertIn('test_router_0/SNMP', svc_postfix_fathers)
        self.assertIn('test_host_0/SNMP', svc_postfix_fathers)

        # Now look for the routers services
        svc_cpu_fathers = [c[0].get_full_name() for c in svc_cpu.act_depend_of]
        print svc_cpu_fathers
        # Should be [u'test_router_0/SNMP', u'test_host_0/SNMP', u'test_host_0']
        self.assertIn('test_router_0/SNMP', svc_cpu_fathers)
        self.assertIn('test_host_0/SNMP', svc_cpu_fathers)

        svc.act_depend_of = []  # no hostchecks on critical checkresults

    def test_implicithostnames(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        svc_postfix = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "POSTFIX_BYSSH")
        self.assertIsNot(svc_postfix, None)

        svc_ssh = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "SSH")
        self.assertIsNot(svc_ssh, None)

        svc_cpu = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "CPU_BYSSH")
        self.assertIsNot(svc_cpu, None)

        svc_postfix_fathers = [c[0].get_full_name() for c in svc_postfix.act_depend_of]
        print svc_postfix_fathers
        # Should be [u'test_router_0/SNMP', u'test_host_0/SNMP', u'test_host_0']
        self.assertIn('test_host_0/SSH', svc_postfix_fathers)

        # Now look for the routers services
        svc_cpu_fathers = [c[0].get_full_name() for c in svc_cpu.act_depend_of]
        print svc_cpu_fathers
        # Should be [u'test_router_0/SNMP', u'test_host_0/SNMP', u'test_host_0']
        self.assertIn('test_host_0/SSH', svc_cpu_fathers)



if __name__ == '__main__':
    unittest.main()
