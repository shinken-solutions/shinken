#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
        self.assertEqual('ramused', m.name)
        self.assertEqual(1009, m.value)
        self.assertEqual('MB', m.uom)
        self.assertEqual(None, m.warning)
        self.assertEqual(None, m.critical)
        self.assertEqual(0, m.min)
        self.assertEqual(1982, m.max)

        s = 'ramused=90%;85;95;;'
        m = Metric(s)
        self.assertEqual('ramused', m.name)
        self.assertEqual(90, m.value)
        self.assertEqual('%', m.uom)
        self.assertEqual(85, m.warning)
        self.assertEqual(95, m.critical)
        self.assertEqual(0, m.min)
        self.assertEqual(100, m.max)

        s = 'ramused=1009MB;;;0;1982 swapused=540MB;;;; memused=90%'
        p = PerfDatas(s)
        p.metrics
        m = p['swapused']
        self.assertEqual('swapused', m.name)
        self.assertEqual(540, m.value)
        self.assertEqual('MB', m.uom)
        self.assertEqual(None, m.warning)
        self.assertEqual(None, m.critical)
        self.assertEqual(None, m.min)
        self.assertEqual(None, m.max)

        m = p['memused']
        self.assertEqual('memused', m.name)
        self.assertEqual(90, m.value)
        self.assertEqual('%', m.uom)
        self.assertEqual(None, m.warning)
        self.assertEqual(None, m.critical)
        self.assertEqual(0, m.min)
        self.assertEqual(100, m.max)

        self.assertEqual(3, len(p))

        s = "'Physical Memory Used'=12085620736Bytes; 'Physical Memory Utilisation'=94%;80;90;"
        p = PerfDatas(s)
        p.metrics
        m = p['Physical Memory Used']
        self.assertEqual('Physical Memory Used', m.name)
        self.assertEqual(12085620736, m.value)
        self.assertEqual('Bytes', m.uom)
        self.assertIs(None, m.warning)
        self.assertIs(None, m.critical)
        self.assertIs(None, m.min)
        self.assertIs(None, m.max)

        m = p['Physical Memory Utilisation']
        self.assertEqual('Physical Memory Utilisation', m.name)
        self.assertEqual(94, m.value)
        self.assertEqual('%', m.uom)
        self.assertEqual(80, m.warning)
        self.assertEqual(90, m.critical)
        self.assertEqual(0, m.min)
        self.assertEqual(100, m.max)

        s = "'C: Space'=35.07GB; 'C: Utilisation'=87.7%;90;95;"
        p = PerfDatas(s)
        p.metrics
        m = p['C: Space']
        self.assertEqual('C: Space', m.name)
        self.assertEqual(35.07, m.value)
        self.assertEqual('GB', m.uom)
        self.assertIs(None, m.warning)
        self.assertIs(None, m.critical)
        self.assertIs(None, m.min)
        self.assertIs(None, m.max)

        m = p['C: Utilisation']
        self.assertEqual('C: Utilisation', m.name)
        self.assertEqual(87.7, m.value)
        self.assertEqual('%', m.uom)
        self.assertEqual(90, m.warning)
        self.assertEqual(95, m.critical)
        self.assertEqual(0, m.min)
        self.assertEqual(100, m.max)

        s = "time_offset-192.168.0.1=-7.22636468709e-05s;1;2;0;;"
        p = PerfDatas(s)
        m = p['time_offset-192.168.0.1']
        self.assertEqual('time_offset-192.168.0.1', m.name)
        self.assertEqual(-7.22636468709e-05, m.value)
        self.assertEqual('s', m.uom)
        self.assertEqual(1, m.warning)
        self.assertEqual(2, m.critical)
        self.assertEqual(0, m.min)
        self.assertIs(None, m.max)

        s = u"ééé-192.168.0.1=-7.22636468709e-05s;1;2;0;;"
        p = PerfDatas(s)
        m = p[u'ééé-192.168.0.1']
        self.assertEqual(m.name, u'ééé-192.168.0.1')
        self.assertEqual(m.value, -7.22636468709e-05)
        self.assertEqual(m.uom, 's')
        self.assertEqual(m.warning, 1)
        self.assertEqual(m.critical, 2)
        self.assertEqual(m.min, 0)
        self.assertEqual(m.max, None)

        #Test that creating a perfdata with nothing dosen't fail
        s = None
        p = PerfDatas(s)
        self.assertEqual(len(p), 0)

if __name__ == '__main__':
    unittest.main()

