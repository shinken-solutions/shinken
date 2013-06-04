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

import os

from shinken_test import unittest, ShinkenTest

from shinken.log import logger
from shinken.objects.module import Module

from shinken.modulesctx import modulesctx
hack_poller_tag_by_macros = modulesctx.get_module('hack_poller_tag_by_macros')
get_instance = hack_poller_tag_by_macros.get_instance



class TestHackPollerTagByMacors(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_module_hack_poller_tag_by_macros.cfg')

    def test_hack_cmd_poller_tag(self):
        modconf = self.conf.modules.find_by_name('HackCommandsPollerTag')

        # get our modules
        mod = hack_poller_tag_by_macros.Hack_pt_by_macros(modconf)
        # Look if we really change our commands

        # Calls the mod with our config
        mod.hook_late_configuration(self)

        # look for a objects that use it
        h1 = self.sched.hosts.find_by_name("test_host_0")
        print h1.poller_tag
        self.assert_(h1.poller_tag == 'None')
        h2 = self.sched.hosts.find_by_name("test_router_0")
        self.assert_(h2.poller_tag == 'DMZ')
        self.assert_(h2.check_command.poller_tag == 'DMZ')

        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_ok_0")

        print svc.poller_tag
        self.assert_(svc.poller_tag == 'None')
        print svc2.poller_tag, svc2.check_command.poller_tag

        self.assert_(svc2.poller_tag == 'DMZ2')
        self.assert_(svc2.check_command.poller_tag == 'DMZ2')

        # In tests we schedule before applying hook_late_conf, so we must reschedule it
        h2.checks_in_progress = []
        h2.in_checking = False
        h2.schedule()
        t = h2.checks_in_progress.pop().poller_tag
        self.assert_(t == 'DMZ')

        svc2.checks_in_progress = []
        svc2.in_checking = False
        svc2.schedule()
        t = svc2.checks_in_progress.pop().poller_tag
        self.assert_(t == 'DMZ2')


if __name__ == '__main__':
    unittest.main()
