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
Test pickle retention broker.
"""

import os
import copy

from shinken_test import unittest, ShinkenTest

from shinken.daemons.brokerdaemon import Broker
from shinken.objects.module import Module

from shinken.modulesctx import modulesctx
pickle_retention_file_generic = modulesctx.get_module('pickle_retention_file_generic')
get_instance = pickle_retention_file_generic.get_instance

modconf = Module()
modconf.module_name = "PickleRetentionGeneric"
modconf.module_type = pickle_retention_file_generic.properties['type']
modconf.properties = pickle_retention_file_generic.properties.copy()


class TestPickleRetentionBroker(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_pickle_retention(self):
        # get our modules
        mod = pickle_retention_file_generic.Pickle_retention_generic(
            modconf, 'tmp/retention-test.dat')
        try:
            os.unlink(mod.path)
        except:
            pass

        sl = get_instance(mod)
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()

        svc = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_0", "test_ok_0")
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0']])

        self.sched.get_new_broks()

        # Saving the broks we got
        old_broks = copy.copy(self.sched.broks)

        # Now get a real broker object
        broker = Broker('', False, False, False, None)

        broker.broks = self.sched.broks.values()
        sl.hook_save_retention(broker) #, l)
        # update the hosts and service in the scheduler in the retention-file

        # Now we clean the source, like if we restart
        broker.broks = []

        self.assertEqual(len(broker.broks), 0)

        r = sl.hook_load_retention(broker)

        # We check we load them :)
        for b in old_broks.values():
            found = False
            for b2 in broker.broks:
                if b2.id == b.id:
                    found = True
            self.assertTrue(found)

        # Ok, we can delete the retention file
        os.unlink(mod.path)



if __name__ == '__main__':
    unittest.main()
