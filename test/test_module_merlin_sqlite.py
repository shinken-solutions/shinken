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
import tempfile

from shinken_test import unittest, ShinkenTest

from shinken.brok import Brok
from shinken.modules.merlindb_broker import get_instance


curpath = os.path.abspath(os.path.dirname(__file__))


skipit = True

@unittest.skipIf(skipit, "Skipping for now.. please investigate")
class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest


    def setUp(self):
        super(TestConfig, self).setUp()
        self.my_temppath = tempfile.mkdtemp()

    def tearDown(self):
        super(TestConfig, self).tearDown()
        os.system('rm -rf %r' % self.my_temppath)

    def test_simplelog(self):
        print self.conf.modules
        # get our modules
        mod = None
        for m in self.conf.modules:
            if m.module_name == 'ToMerlindb_Sqlite':
                mod = m
        self.assert_(mod is not None)
        # bad to use absolute path:
        #self.assert_(mod.database_path == '/usr/local/shinken/var/merlindb.sqlite')
        mod.database_path = os.path.join(self.my_temppath, 'merlindb.sqlite')
        self.assert_(mod.module_type == 'merlindb')
        self.assert_(mod.backend == 'sqlite')

        md = get_instance(mod)
        print "TOTO", md.db_backend.__dict__

        md.init()
        b = Brok('clean_all_my_instance_id', {'instance_id': 0})
        md.manage_brok(b)
        r = md.db_backend.db_cursor.execute("SELECT count(*) from timeperiod WHERE instance_id = '0'")
        self.assert_(r.fetchall() == [(0,)])





if __name__ == '__main__':
    unittest.main()
