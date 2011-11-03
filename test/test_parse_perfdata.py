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
from shinken.misc.perfdata import Metric

class TestParsePerfdata(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
#    def setUp(self):
#        self.setup_with_file('etc/nagios_parse_perfdata.cfg')

    
    #Change ME :)
    def test_parsing_perfdata(self):
        s = 'ramused=1009MB;;;0;1982 swapused=540MB;;;0;3827 memused=1550MB;2973;3964;0;5810'
        s = 'ramused=1009MB;;;0;1982'
        m = Metric(s)
        self.assert_(m.name == 'ramused')
        self.assert_(m.value == 1009)
        self.assert_(m.uom == 'MB')
        self.assert_(m.warning == None)
        self.assert_(m.critical == None)
        self.assert_(m.min == 0)
        self.assert_(m.max == 1982)

        s = 'ramused=90%;85;95;;'
        m = Metric(s)
        self.assert_(m.name == 'ramused')
        self.assert_(m.value == 90)
        self.assert_(m.uom == '%')
        self.assert_(m.warning == 85)
        self.assert_(m.critical == 95)
        self.assert_(m.min == 0)
        self.assert_(m.max == 100)


if __name__ == '__main__':
    unittest.main()

