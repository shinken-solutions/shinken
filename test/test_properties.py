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
import shinken.property
from shinken.property import none_object


class PropertyTests:
    """Common tests for all property classes"""

    def test_no_default_value(self):
        p = self.prop_class()
        self.assertIs(p.default, none_object)
        self.assertFalse(p.has_default)
        self.assertTrue(p.required)

    def test_default_value(self):
        default_value = object()
        p = self.prop_class(default=default_value)
        self.assertIs(p.default, default_value)
        self.assertTrue(p.has_default)
        self.assertFalse(p.required)

    def test_fill_brok(self):
        p = self.prop_class()
        self.assertNotIn('full_status', p.fill_brok)
        p = self.prop_class(default='0', fill_brok=['full_status'])
        self.assertIn('full_status', p.fill_brok)

    def test_unused(self):
        p = self.prop_class()
        self.assertFalse(p.unused)


class TestBoolProp(unittest.TestCase, PropertyTests):
    """Test the BoolProp class"""

    prop_class = shinken.property.BoolProp

    def test_pythonize(self):
        p = self.prop_class()
        # allowed strings for `True`
        self.assertEqual(p.pythonize("1"), True)
        self.assertEqual(p.pythonize("yes"), True)
        self.assertEqual(p.pythonize("true"), True)
        self.assertEqual(p.pythonize("on"), True)
        # allowed strings for `False`
        self.assertEqual(p.pythonize("0"), False)
        self.assertEqual(p.pythonize("no"), False)
        self.assertEqual(p.pythonize("false"), False)
        self.assertEqual(p.pythonize("off"), False)


class TestStringProp(unittest.TestCase, PropertyTests):
    """Test the StringProp class"""

    prop_class = shinken.property.StringProp

    def test_pythonize(self):
        p = self.prop_class()
        self.assertEqual(p.pythonize("1"), "1")
        self.assertEqual(p.pythonize("yes"), "yes")
        self.assertEqual(p.pythonize("0"), "0")
        self.assertEqual(p.pythonize("no"), "no")



if __name__ == '__main__':
    unittest.main()
