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
ip_tag_arbiter = modulesctx.get_module('ip_tag')
get_instance   = ip_tag_arbiter.get_instance


class TestIpTag(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_module_ip_tag.cfg')

    def test_hack_cmd_poller_tag(self):
        modconf = self.conf.modules.find_by_name('IpTag')

        # look for a objects that use it
        h1 = self.sched.hosts.find_by_name("test_host_0")
        h2 = self.sched.hosts.find_by_name("test_router_0")

        # get our modules
        mod = get_instance(modconf)
        # Look if we really change our commands

        # Ok we lie a bit, in the early phase, we should NOT
        # already got poller_tag properties. Must lie here
        # and find a better way to manage this in tests
        del h2.poller_tag

        # Calls the mod with our config
        mod.hook_early_configuration(self)

        print "H1", h1.poller_tag
        self.assert_(h1.poller_tag == 'None')

        print"H2", h2.poller_tag
        self.assert_(h2.poller_tag == 'DMZ')
        # We can't check the check_command, becausewe fake the early conf in a late time
        # so we can't have tagged it.
        #self.assert_(h2.check_command.poller_tag == 'DMZ')

    def test_hack_cmd_grp(self):
        modconf = self.conf.modules.find_by_name('IpTagAppend')

        # look for a objects that use it
        h1 = self.sched.hosts.find_by_name("test_host_0")
        h2 = self.sched.hosts.find_by_name("test_router_0")
        h3 = self.sched.hosts.find_by_name("127.0.0.1")

        # get our modules
        mod = get_instance(modconf)
        # Look if we really change our commands

        # Ok we lie a bit, in the early phase, we should NOT
        # already got poller_tag properties. Must lie here
        # and find a better way to manage this in tests
        h1.hostgroups = 'linux,windows'
        h2.hostgroups = 'linux,windows'
        h3.hostgroups = 'linux,windows'

        # Calls the mod with our config
        mod.hook_early_configuration(self)

        print "H1", h1.hostgroups
        self.assert_('newgroup' not in h1.hostgroups)

        print "H2", h2.hostgroups
        self.assert_('newgroup' in h2.hostgroups)

        print "H3", h3.hostgroups
        self.assert_('newgroup' in h3.hostgroups)



if __name__ == '__main__':
    unittest.main()
