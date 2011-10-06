#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
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
from shinken.log import logger

class TestConfig(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')

    
    # Try to raise an utf8 log message
    def test_utf8log(self):
        sutf = 'héhé'
        logger.log(sutf)
        sutf8 = u'I love myself $Â£Â¤'
        logger.log(sutf8)
        s = unichr(40960) + u'abcd' + unichr(1972)
        logger.log(s)

        

if __name__ == '__main__':
    unittest.main()

