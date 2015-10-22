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
# This file is used to test object properties overriding.
#

import re
from shinken_test import unittest, ShinkenTest


class TestPropertyOverride(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_property_override.cfg')

    def test_service_property_override(self):
        svc11 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv-svc1")
        svc12 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv-svc2")
        svc21 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv-svc1")
        svc22 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv-svc2")
        svc31 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv-svc1")
        svc32 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv-svc2")
        svc41 = self.sched.services.find_srv_by_name_and_hostname("test_host_04", "srv-svc1")
        svc42 = self.sched.services.find_srv_by_name_and_hostname("test_host_04", "srv-svc2")

        svc1proc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "proc proc1")
        svc1proc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "proc proc2")
        svc2proc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "proc proc1")
        svc2proc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "proc proc2")
        svc3proc1 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_03", "proc proc1")
        svc3proc2 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_03", "proc proc2")
        svc4proc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_04", "proc proc1")
        svc4proc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_04", "proc proc2")

        tp24x7 = self.sched.timeperiods.find_by_name("24x7")
        tptest = self.sched.timeperiods.find_by_name("testperiod")
        cgtest = self.sched.contactgroups.find_by_name("test_contact")
        cgadm = self.sched.contactgroups.find_by_name("admins")
        cmdsvc = self.sched.commands.find_by_name("check_service")
        cmdtest = self.sched.commands.find_by_name("dummy_command")

        # Checks we got the objects we need
        self.assertIsNot(svc11, None)
        self.assertIsNot(svc21, None)
        self.assertIsNot(svc1proc1, None)
        self.assertIsNot(svc1proc2, None)
        self.assertIsNot(svc2proc1, None)
        self.assertIsNot(svc2proc2, None)
        self.assertIsNot(tp24x7, None)
        self.assertIsNot(tptest, None)
        self.assertIsNot(cgtest, None)
        self.assertIsNot(cgadm, None)
        self.assertIsNot(cmdsvc, None)
        self.assertIsNot(cmdtest, None)
        self.assertIsNot(svc12, None)
        self.assertIsNot(svc22, None)

        # Check non overriden properies value
        for svc in (svc11, svc12, svc1proc1, svc1proc2,
                    svc21, svc2proc1, svc4proc1, svc4proc2):
            self.assertEqual(["test_contact"], svc.contact_groups)
            self.assertIs(tp24x7, svc.maintenance_period)
            self.assertEqual(1, svc.retry_interval)
            self.assertIs(cmdsvc, svc.check_command.command)
            self.assertEqual(["w","u","c","r","f","s"], svc.notification_options)
            self.assertIs(True, svc.notifications_enabled)

        # Check overriden properies value
        for svc in (svc22, svc2proc2, svc31, svc32, svc3proc1, svc3proc2,
                    svc41, svc42):
            self.assertEqual(["admins"], svc.contact_groups)
            self.assertIs(tptest, svc.maintenance_period)
            self.assertEqual(3, svc.retry_interval)
            self.assertIs(cmdtest, svc.check_command.command)
            self.assertEqual(["c","r"], svc.notification_options)
            self.assertIs(False, svc.notifications_enabled)


class TestConfigBroken(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_property_override_broken.cfg')

    def test_service_property_override_errors(self):
        self.assertFalse(self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']
        self.assertEqual(1, len([log for log in logs if re.search('Error: invalid service override syntax: fake', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search("Error: trying to override property 'retry_interval' on service identified by 'fakesrv' but it's unknown for this host", log)]) )
        self.assertEqual(1, len([log for log in logs if re.search("Error: trying to override 'host_name', a forbidden property for service 'proc proc2'", log)]) )


if __name__ == '__main__':
    unittest.main()
