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
from shinken.misc.perfdata import Metric, PerfDatas


class TestParsePerfdata(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/shinken_parse_perfdata.cfg')

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

        s = 'ramused=1009MB;;;0;1982 swapused=540MB;;;; memused=90%'
        p = PerfDatas(s)
        p.metrics
        m = p['swapused']
        self.assert_(m.name == 'swapused')
        self.assert_(m.value == 540)
        self.assert_(m.uom == 'MB')
        self.assert_(m.warning == None)
        self.assert_(m.critical == None)
        self.assert_(m.min == None)
        self.assert_(m.max == None)

        m = p['memused']
        self.assert_(m.name == 'memused')
        self.assert_(m.value == 90)
        self.assert_(m.uom == '%')
        self.assert_(m.warning == None)
        self.assert_(m.critical == None)
        self.assert_(m.min == 0)
        self.assert_(m.max == 100)

        self.assert_(len(p) == 3)

        s = "'Physical Memory Used'=12085620736Bytes; 'Physical Memory Utilisation'=94%;80;90;"
        p = PerfDatas(s)
        p.metrics
        m = p['Physical Memory Used']
        self.assert_(m.name == 'Physical Memory Used')
        self.assert_(m.value == 12085620736)
        self.assert_(m.uom == 'Bytes')
        self.assert_(m.warning is None)
        self.assert_(m.critical is None)
        self.assert_(m.min is None)
        self.assert_(m.max is None)

        m = p['Physical Memory Utilisation']
        self.assert_(m.name == 'Physical Memory Utilisation')
        self.assert_(m.value == 94)
        self.assert_(m.uom == '%')
        self.assert_(m.warning == 80)
        self.assert_(m.critical == 90)
        self.assert_(m.min == 0)
        self.assert_(m.max == 100)

        s = "'C: Space'=35.07GB; 'C: Utilisation'=87.7%;90;95;"
        p = PerfDatas(s)
        p.metrics
        m = p['C: Space']
        self.assert_(m.name == 'C: Space')
        self.assert_(m.value == 35.07)
        self.assert_(m.uom == 'GB')
        self.assert_(m.warning is None)
        self.assert_(m.critical is None)
        self.assert_(m.min is None)
        self.assert_(m.max is None)

        m = p['C: Utilisation']
        self.assert_(m.name == 'C: Utilisation')
        self.assert_(m.value == 87.7)
        self.assert_(m.uom == '%')
        self.assert_(m.warning == 90)
        self.assert_(m.critical == 95)
        self.assert_(m.min == 0)
        self.assert_(m.max == 100)

        s = "time_offset-192.168.0.1=-7.22636468709e-05s;1;2;0;;"
        p = PerfDatas(s)
        m = p['time_offset-192.168.0.1']
        self.assert_(m.name == 'time_offset-192.168.0.1')
        self.assert_(m.value == -7.22636468709e-05)
        self.assert_(m.uom == 's')
        self.assert_(m.warning == 1)
        self.assert_(m.critical == 2)
        self.assert_(m.min == 0)
        self.assert_(m.max is None)


if __name__ == '__main__':
    unittest.main()

