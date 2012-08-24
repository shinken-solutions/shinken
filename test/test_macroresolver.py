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

from shinken_test import *
from shinken.macroresolver import MacroResolver
from shinken.commandcall import CommandCall
from shinken.objects import Command


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def get_mr(self):
        mr = MacroResolver()
        mr.init(self.conf)
        return mr

    def get_hst_svc(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        hst = self.sched.hosts.find_by_name("test_host_0")
        return (svc, hst)

    def test_resolv_simple(self):
        mr = self.get_mr()
        (svc, hst) = self.get_hst_svc()
        data = svc.get_data_for_checks()
        com = mr.resolve_command(svc.check_command, data)
        print com
        self.assert_(com == "plugins/test_servicecheck.pl --type=ok --failchance=5% --previous-state=PENDING --state-duration=0 --total-critical-on-host=0 --total-warning-on-host=0 --hostname test_host_0 --servicedesc test_ok_0 --custom custvalue")

    # Here call with a special macro TOTALHOSTSUP
    # but call it as arg. So will need 2 pass in macro resolver
    # at last to resolv it.
    def test_special_macros(self):
        mr = self.get_mr()
        (svc, hst) = self.get_hst_svc()
        data = svc.get_data_for_checks()
        hst.state = 'UP'
        dummy_call = "special_macro!$TOTALHOSTSUP$"
        cc = CommandCall(self.conf.commands, dummy_call)
        com = mr.resolve_command(cc, data)
        print com
        self.assert_(com == 'plugins/nothing 1')



    # Here call with a special macro HOSTREALM
    def test_special_macros_realm(self):
        mr = self.get_mr()
        (svc, hst) = self.get_hst_svc()
        data = svc.get_data_for_checks()
        hst.state = 'UP'
        dummy_call = "special_macro!$HOSTREALM$"
        cc = CommandCall(self.conf.commands, dummy_call)
        com = mr.resolve_command(cc, data)
        print com
        self.assert_(com == 'plugins/nothing Default')


    # For output macro we want to delete all illegal macro caracter
    def test_illegal_macro_output_chars(self):
        "$HOSTOUTPUT$, $HOSTPERFDATA$, $HOSTACKAUTHOR$, $HOSTACKCOMMENT$, $SERVICEOUTPUT$, $SERVICEPERFDATA$, $SERVICEACKAUTHOR$, and $SERVICEACKCOMMENT$ "
        mr = self.get_mr()
        (svc, hst) = self.get_hst_svc()
        data = svc.get_data_for_checks()
        illegal_macro_output_chars = self.sched.conf.illegal_macro_output_chars
        print "Illegal macros caracters:", illegal_macro_output_chars
        hst.output = 'monculcestdupoulet'
        dummy_call = "special_macro!$HOSTOUTPUT$"

        for c in illegal_macro_output_chars:
            hst.output = 'monculcestdupoulet' + c
            cc = CommandCall(self.conf.commands, dummy_call)
            com = mr.resolve_command(cc, data)
            print com
            self.assert_(com == 'plugins/nothing monculcestdupoulet')

    def test_env_macros(self):
        mr = self.get_mr()
        (svc, hst) = self.get_hst_svc()
        data = svc.get_data_for_checks()
        data.append(self.conf)

        env = mr.get_env_macros(data)
        print "Env:", env        
        self.assert_(env != {})
        self.assert_(env['NAGIOS_HOSTNAME'] == 'test_host_0')
        self.assert_(env['NAGIOS_SERVICEPERCENTCHANGE'] == '0.0')
        self.assert_(env['NAGIOS__SERVICECUSTNAME'] == 'custvalue')
        self.assert_(env['NAGIOS__HOSTOSTYPE'] == 'gnulinux')
        self.assert_('NAGIOS_USER1' not in env)


    def test_resource_file(self):
        mr = self.get_mr()
        (svc, hst) = self.get_hst_svc()
        data = svc.get_data_for_checks()
        dummy_call = "special_macro!$USER1$"
        cc = CommandCall(self.conf.commands, dummy_call)
        com = mr.resolve_command(cc, data)
        self.assert_(com == 'plugins/nothing plugins')

        dummy_call = "special_macro!$INTERESTINGVARIABLE$"
        cc = CommandCall(self.conf.commands, dummy_call)
        com = mr.resolve_command(cc, data)
        print "CUCU", com
        self.assert_(com == 'plugins/nothing interestingvalue')

        # Look for multiple = in lines, should split the first
        # and keep others in the macro value
        dummy_call = "special_macro!$ANOTHERVALUE$"
        cc = CommandCall(self.conf.commands, dummy_call)
        com = mr.resolve_command(cc, data)
        print "CUCU", com
        self.assert_(com == 'plugins/nothing blabla=toto')




if __name__ == '__main__':
    unittest.main()
