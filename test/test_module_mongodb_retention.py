#!/usr/bin/env python
#
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

"""
Test Mongodb retention.
"""

from shinken_test import unittest, ShinkenTest

from shinken.objects.module import Module
from shinken.modules import mongodb_retention
from shinken.modules.mongodb_retention import get_instance

modconf = Module()
modconf.module_name = "MongodbRetention"
modconf.uri = 'mongodb://127.0.0.1:27017'
modconf.database = 'test'
modconf.module_type = mongodb_retention.properties['type']
modconf.properties = mongodb_retention.properties.copy()


class TestMongodbRetention(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_mongodb_retention(self):
        # get our modules
        sl = mongodb_retention.Mongodb_retention_scheduler(
            modconf, 'localhost', 'test')

        # sl = get_instance(mod)
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()

        # update the hosts and service in the scheduler in the retention-file
        sl.hook_save_retention(self.sched)

        # Now we change thing
        svc = self.sched.hosts.find_by_name("test_host_0")
        self.assertEqual(svc.state, 'PENDING')

        svc.state = 'UP'  # was PENDING in the save time
        r = sl.hook_load_retention(self.sched)
        self.assertTrue(r)

        # search if the host is not changed by the loading thing
        svc2 = self.sched.hosts.find_by_name("test_host_0")
        self.assertEqual(svc, svc2)
        self.assertEqual(svc.state, 'PENDING')

        # Now make real loops with notifications
        self.scheduler_loop(10, [[svc, 2, 'CRITICAL | bibi=99%']])
        # update the hosts and service in the scheduler in the retention-file
        sl.hook_save_retention(self.sched)

        r = sl.hook_load_retention(self.sched)
        self.assertTrue(r)


if __name__ == '__main__':
    unittest.main()
