#!/usr/bin/env python
# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

"""
Test shinken.property
"""

import unittest

import __import_shinken
from shinken.property import UnusedProp, BoolProp, IntegerProp, FloatProp, CharProp, StringProp


class TestBoolProp(unittest.TestCase):
    """Test the BoolProp class"""

    def test_pythonize(self):
        p = BoolProp()
        self.assertEqual(p.pythonize("1"), True)
        self.assertEqual(p.pythonize("0"), False)

    def test_fill_brok(self):
        p = BoolProp()
        self.assertNotIn('full_status', p.fill_brok)
        p = BoolProp(default='0', fill_brok=['full_status'])
        self.assertIn('full_status', p.fill_brok)


if __name__ == '__main__':
    unittest.main()
