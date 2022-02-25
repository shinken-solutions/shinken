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


class TestStringPerfdata(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/shinken_parse_perfdata.cfg')

    def test_string_all_four(self):
        self.assertEqual('ramused=1009MB;1;2;3;4', str(Metric('ramused=1009MB;1;2;3;4')))

    def test_string_drop_empty_from_end(self):
        self.assertEqual('ramused=1009MB', str(Metric('ramused=1009MB')))
        self.assertEqual('ramused=1009MB;1', str(Metric('ramused=1009MB;1')))
        self.assertEqual('ramused=1009MB;1;2', str(Metric('ramused=1009MB;1;2')))
        self.assertEqual('ramused=1009MB;1;2;3', str(Metric('ramused=1009MB;1;2;3')))
        self.assertEqual('ramused=1009MB;1;2;3;4', str(Metric('ramused=1009MB;1;2;3;4')))

    def test_string_empty_for_None(self):
        self.assertEqual('ramused=1009MB', str(Metric('ramused=1009MB;')))
        self.assertEqual('ramused=1009MB', str(Metric('ramused=1009MB;;')))
        self.assertEqual('ramused=1009MB', str(Metric('ramused=1009MB;;;')))
        self.assertEqual('ramused=1009MB', str(Metric('ramused=1009MB;;;;')))

        self.assertEqual('ramused=1009MB;;2', str(Metric('ramused=1009MB;;2')))
        self.assertEqual('ramused=1009MB;;;3', str(Metric('ramused=1009MB;;;3')))
        self.assertEqual('ramused=1009MB;;;;4', str(Metric('ramused=1009MB;;;;4')))

        self.assertEqual('ramused=1009MB;;2;;4', str(Metric('ramused=1009MB;;2;;4')))

    def test_string_zero_preserved(self):
        self.assertEqual('ramused=1009MB;0', str(Metric('ramused=1009MB;0')))
        self.assertEqual('ramused=1009MB;;0', str(Metric('ramused=1009MB;;0')))
        self.assertEqual('ramused=1009MB;;;0', str(Metric('ramused=1009MB;;;0')))
        self.assertEqual('ramused=1009MB;;;;0', str(Metric('ramused=1009MB;;;;0')))

    def test_string_percent_minmaxdefault_0_100(self):
        # If not specified, defaults of 0 and 100 for min/max should not come back
        self.assertEqual('utilization=80%;90;95', str(Metric('utilization=80%;90;95')))
        self.assertEqual('utilization=80%;90;95;;', str(Metric('utilization=80%;90;95')) + ";;")

    def test_string_percent_minmax_echo(self):
        # Defined values of min max should come back always, even if defaults
        self.assertEqual('utilization=80%;50;75;0;100', str(Metric('utilization=80%;50;75;0;100')))
        self.assertEqual('utilization=80%;50;75;0', str(Metric('utilization=80%;50;75;0')))
        self.assertEqual('utilization=80%;50;75;;100', str(Metric('utilization=80%;50;75;;100')))

        # Same tests with non-default values
        self.assertEqual('utilization=80%;50;75;85;95', str(Metric('utilization=80%;50;75;85;95')))
        self.assertEqual('utilization=80%;50;75;85', str(Metric('utilization=80%;50;75;85')))
        self.assertEqual('utilization=80%;50;75;;95', str(Metric('utilization=80%;50;75;;95')))

    def test_string_quoted_names(self):
        self.assertEqual("ram''used''=10", str(Metric("ram''used''=10")))
        self.assertEqual("ram''used=10", str(Metric("ram''used=10")))
        # Outer quotes present but not necessary should be stripped on format
        self.assertEqual("ram''used=10", str(Metric("'ram''used'=10")))
        # But not so if there is also a space
        self.assertEqual("'ram was ''used'=10", str(Metric("'ram was ''used'=10")))

        # String missing required outer quotes, should come back quoted
        # This is debatable as it basically is an invalid metric/perfdata
        self.assertEqual("'ram  ''used'''=10", str(Metric("ram  ''used''=10")))

if __name__ == '__main__':
    unittest.main()

