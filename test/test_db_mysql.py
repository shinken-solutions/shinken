#!/usr/bin/env python
# Copyright (C) 2009-2014:
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
try:
    from shinken.db_mysql import DBMysql
except ImportError:
    # Oups this server do not have mysql installed, skip this test
    DBMysql = None


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def create_db(self):
        self.db = DBMysql(host='localhost', user='root', password='root', database='merlin', character_set='utf8')

    def test_connect_database(self):
        if not DBMysql:
            return
        self.create_db()
        try:
            self.db.connect_database()
        except Exception:  # arg, no database here? sic!
            pass

    def test_execute_query(self):
        if not DBMysql:
            return
        self.create_db()
        try:
            self.db.connect_database()
            q = "DELETE FROM service WHERE instance_id = '0'"
            self.db.execute_query(q)
        except Exception:
            pass



if __name__ == '__main__':
    unittest.main()
