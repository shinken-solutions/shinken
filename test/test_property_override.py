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
# This file is used to test object properties overriding.
#

import re
from shinken_test import unittest, ShinkenTest


class TestPropertyOverride(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_property_override.cfg')

    def test_service_property_override(self):
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv-svc")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv-svc")
        svc1proc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "proc proc1")
        svc1proc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "proc proc2")
        svc2proc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "proc proc1")
        svc2proc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "proc proc2")
        tp24x7 = self.sched.timeperiods.find_by_name("24x7")
        tptest = self.sched.timeperiods.find_by_name("testperiod")
        cgtest = self.sched.contactgroups.find_by_name("test_contact")
        cgadm = self.sched.contactgroups.find_by_name("admins")
        cmdsvc = self.sched.commands.find_by_name("check_service")
        cmdtest = self.sched.commands.find_by_name("dummy_command")
        svc12 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv-svc2")
        svc22 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv-svc2")

        # Checks we got the objects we need
        self.assert_(svc1 is not None)
        self.assert_(svc2 is not None)
        self.assert_(svc1proc1 is not None)
        self.assert_(svc1proc2 is not None)
        self.assert_(svc2proc1 is not None)
        self.assert_(svc2proc2 is not None)
        self.assert_(tp24x7 is not None)
        self.assert_(tptest is not None)
        self.assert_(cgtest is not None)
        self.assert_(cgadm is not None)
        self.assert_(cmdsvc is not None)
        self.assert_(cmdtest is not None)
        self.assert_(svc12 is not None)
        self.assert_(svc22 is not None)

        # Check non overriden properies value
        for svc in (svc1, svc1proc1, svc1proc2, svc2proc1, svc12):
            self.assert_(svc.contact_groups == "test_contact")
            self.assert_(svc.maintenance_period is tp24x7)
            self.assert_(svc.retry_interval == 1)
            self.assert_(svc.check_command.command is cmdsvc)
            self.assert_(svc.notification_options == ["w","u","c","r","f","s"])
            self.assert_(svc.notifications_enabled is True)

        # Check overriden properies value
        for svc in (svc2, svc2proc2, svc22):
            self.assert_(svc.contact_groups == "admins")
            self.assert_(svc.maintenance_period is tptest)
            self.assert_(svc.retry_interval == 3)
            self.assert_(svc.check_command.command is cmdtest)
            self.assert_(svc.notification_options == ["c","r"])
            self.assert_(svc.notifications_enabled is False)


class TestConfigBroken(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_property_override_broken.cfg')

    def test_service_property_override_errors(self):
        self.assert_(not self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        self.assert_(len([log for log in logs if re.search('Error: invalid service override syntax: fake', log)]) == 1)
        self.assert_(len([log for log in logs if re.search("Error: trying to override property 'retry_interval' on service 'fakesrv' but it's unknown for this host", log)]) == 1)
        self.assert_(len([log for log in logs if re.search("Error: trying to override 'host_name', a forbidden property for service 'proc proc2'", log)]) == 1)


if __name__ == '__main__':
    unittest.main()
