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

from shinken_test import *
from shinken.db_sqlite import DBSqlite


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def create_db(self):
        self.db = DBSqlite("/usr/local/shinken/var/merlindb.sqlite", table_prefix='')

    def test_connect_database(self):
        self.create_db()
        self.db.connect_database()

    def test_execute_query(self):
        self.create_db()
        self.db.connect_database()
        q = "DELETE FROM service WHERE instance_id = '0'"
        self.db.execute_query(q)



if __name__ == '__main__':
    unittest.main()
