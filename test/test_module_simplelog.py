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

from shinken.brok import Brok
from shinken.modules.simplelog_broker.module import get_instance


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_simplelog(self):
        print self.conf.modules
        # get our modules
        mod = None
        for m in self.conf.modules:
            if m.module_type == 'simple_log':
                mod = m
        self.assert_(mod is not None)
        self.assert_(mod.path == 'tmp/nagios.log')
        self.assert_(mod.module_name == 'Simple-log')

        try:
            os.unlink(mod.path)
        except:
            pass

        sl = get_instance(mod)
        print sl
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()
        b = Brok('log', {'log': "look at my ass.\n"})
        b.prepare()
        sl.manage_brok(b)
        b = Brok('log', {'log': "look at my ass again.\n"})
        b.prepare()
        sl.manage_brok(b)
        sl.file.close()
        fd = open(mod.path)
        buf = fd.readline()
        self.assert_(buf == "look at my ass.\n")
        buf = fd.readline()
        self.assert_(buf == "look at my ass again.\n")
        fd.close()
        os.unlink(mod.path)


if __name__ == '__main__':
    unittest.main()
