#!/usr/bin/env python2.6
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *
from shinken.db import DB

class TestConfig(ShinkenTest):
    #setUp is in shinken_test


    def create_db(self):
        self.db = DB(table_prefix = 'test_')
    
    #Change ME :)
    def test_create_insert_query(self):
        self.create_db()
        data = {'id' : "1", "is_master" : True, 'plop' : "master of the universe"}
        q = self.db.create_insert_query('instances' , data)
        self.assert_(q == "INSERT INTO test_instances  (is_master , id , plop  ) VALUES ('1' , '1' , 'master of the universe'  )")

        
    def test_update_query(self):
        self.create_db()
        data = {'id' : "1", "is_master" : True, 'plop' : "master of the universe"}
        where = {'id' : "1", "is_master" : True}
        q = self.db.create_update_query('instances' , data, where)
        #beware of the last space
        self.assert_(q == "UPDATE test_instances set is_master='1' , id='1' , plop='master of the universe'  WHERE is_master='1' and id='1' ")
        


if __name__ == '__main__':
    unittest.main()

