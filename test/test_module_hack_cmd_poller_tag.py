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
from shinken.modules.hack_commands_poller_tag_arbiter import module as hack_commands_poller_tag_arbiter
from shinken.modules.hack_commands_poller_tag_arbiter.module import get_instance


class TestHackCmdPollerTag(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_module_hack_cmd_poller_tag.cfg')

    def test_hack_cmd_poller_tag(self):
        modconf = self.conf.modules.find_by_name('HackCommandsPollerTag')

        # get our modules
        mod = hack_commands_poller_tag_arbiter.Hack_cmds_pt(modconf)
        # Look if we really change our commands

        # Calls the mod with our config
        mod.hook_late_configuration(self)

        cmd1 = self.sched.commands.find_by_name('should_change')
        self.assert_(cmd1 is not None)
        cmd2 = self.sched.commands.find_by_name('should_not_change')
        self.assert_(cmd2 is not None)

        # cmd1 should have been updated, but not cmd2
        print "CMD1", cmd1.__dict__
        print "P", cmd1.poller_tag
        self.assert_(cmd1.poller_tag == 'other')
        print "CMD2", cmd2.__dict__
        print "P", cmd1.poller_tag
        self.assert_(cmd2.poller_tag == 'alreadydefined')

        # look for a objects that use it
        h1 = self.sched.hosts.find_by_name("test_host_0")
        self.assert_(h1 is not None)
        h2 = self.sched.hosts.find_by_name("test_router_0")
        self.assert_(h2 is not None)

        # Ok, host1 call cmd2, and host2 cmd1...
        # sorry for the crossing:p
        print "H1", h1.check_command
        print h1.check_command.command
        self.assert_(h1.check_command.poller_tag == 'alreadydefined')
        print "H2", h2.check_command
        print h2.check_command.command
        self.assert_(h2.check_command.poller_tag == 'other')

    def test_underscore_commands_module_type_recognition(self):
        cmd_tag = self.sched.commands.find_by_name('will_tag')
        self.assert_(cmd_tag is not None)
        self.assert_(cmd_tag.module_type == 'nrpe_poller')
        cmd_not_tag = self.sched.commands.find_by_name('will_not_tag')
        self.assert_(cmd_not_tag is not None)
        self.assert_(cmd_not_tag.module_type == 'isetwhatiwant')




if __name__ == '__main__':
    unittest.main()
