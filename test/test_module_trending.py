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
from shinken_test import *
from shinken.brok import Brok

from shinken.modules.trending_broker import module as trending_broker
from shinken.modules.trending_broker.module import get_instance

modconf = Module()
modconf.module_name = "Trending"
modconf.module_type = trending_broker.properties['type']
modconf.properties = trending_broker.properties.copy()


class TestTrendingModule(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_trending_module(self):
        
        mod = trending_broker.Trending_broker(modconf)

        mod.uri = 'IDONOTEXIST'
        
        sl = trending_broker.get_instance(mod)
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        try:
            sl.init()
        except Exception, exp:
            print exp

        svc = self.sched.hosts.find_by_name("test_host_0")
        t = int(time.time())
        print "T", t
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0']])
        # manage all host check result broks
        for b in self.sched.broks.values():
            if b.type == 'host_check_result':
                sl.manage_brok(b)

        values = sl.get_metric_and_value('value1=1;2;3 value2=4;5;6')
        print values
        


if __name__ == '__main__':
    unittest.main()
