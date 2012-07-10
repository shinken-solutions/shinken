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
from shinken.modules import redis_retention_scheduler
from shinken.modules.redis_retention_scheduler import get_instance

modconf = Module()
modconf.module_name = "RedisRetention"
modconf.module_type = redis_retention_scheduler.properties['type']
modconf.properties = redis_retention_scheduler.properties.copy()


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_redis_retention(self):
        print self.conf.modules
        # get our modules
        mod = redis_retention_scheduler.Redis_retention_scheduler(modconf, 'localhost')

        sl = get_instance(mod)
        print "Instance", sl
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()
        l = logger

        # update the hosts and service in the scheduler in the retention-file
        sl.hook_save_retention(self.sched)

        # Now we change thing
        svc = self.sched.hosts.find_by_name("test_host_0")
        self.assert_(svc.state == 'PENDING')
        print "State", svc.state
        svc.state = 'UP'  # was PENDING in the save time

        r = sl.hook_load_retention(self.sched)
        self.assert_(r == True)

        # search if the host is not changed by the loading thing
        svc2 = self.sched.hosts.find_by_name("test_host_0")
        self.assert_(svc == svc2)

        self.assert_(svc.state == 'PENDING')

        # Now make real loops with notifications
        self.scheduler_loop(10, [[svc, 2, 'CRITICAL | bibi=99%']])
        # update the hosts and service in the scheduler in the retention-file
        sl.hook_save_retention(self.sched)

        r = sl.hook_load_retention(self.sched)
        self.assert_(r == True)



if __name__ == '__main__':
    unittest.main()
