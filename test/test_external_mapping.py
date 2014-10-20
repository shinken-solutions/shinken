#!/usr/bin/env python
#
# Copyright (C) 2012:
#    Hartmut Goebel <h.goebel@crazy-compilers.com>
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
Test libexec/external_mapping.py
"""

import os
import time
import subprocess
import unittest
from tempfile import NamedTemporaryFile
from shinken_test import *

try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error: you need the json or simplejson module"
        raise
                                                
external_mapping = os.path.join(os.path.dirname(__file__),
                                '..', 'libexec', 'external_mapping.py')


class TestExternalMapping(ShinkenTest):

    def setUp(self):
        time_hacker.set_real_time()

    def __setup(self, inputlines):
        """
        Create a temporary input file and a temporary output-file.
        """
        # create output file fist, so it is older
        outputfile = NamedTemporaryFile("w", suffix='.json', delete=False)
        outputfile.write('--- empty marker ---')
        outputfile.close()
        self.output_filename = outputfile.name

        time.sleep(1) # ensure a time-difference between files

        inputfile = NamedTemporaryFile("w", suffix='.txt', delete=False)
        for line in inputlines:
            inputfile.writelines((line, '\n'))
        inputfile.close()
        self.input_filename = inputfile.name

    def __cleanup(self):
        """
        Cleanup the temporary files.
        """
        os.remove(self.input_filename)
        os.remove(self.output_filename)

    def __run(self, lines):
        self.__setup(lines)
        subprocess.call([external_mapping,
                         '--input', self.input_filename,
                         '--output', self.output_filename])
        result = json.load(open(self.output_filename))
        self.__cleanup()
        return result


    def test_simple(self):
        lines = [
            'myhost:vm1',
            'yourhost:vm1',
            'theirhost:xen3',
            ]
        result = self.__run(lines)
        self.assertEqual(result,
                         [[["host", "myhost"], ["host", "vm1"]],
                          [["host", "yourhost"], ["host", "vm1"]],
                          [["host", "theirhost"], ["host", "xen3"]]])

    def test_empty(self):
        lines = []
        result = self.__run(lines)
        self.assertEqual(result, [])

    def test_spaces_around_names(self):
        lines = [
            '   myhost   :    vm1   ',
            'yourhost :vm1',
            'theirhost:  xen3   ',
            ]
        result = self.__run(lines)
        self.assertEqual(result,
                         [[["host", "myhost"], ["host", "vm1"]],
                          [["host", "yourhost"], ["host", "vm1"]],
                          [["host", "theirhost"], ["host", "xen3"]]])

    def test_comment_line(self):
        lines = [
            'myhost:vm1',
            '# this is a comment',
            'yourhost:vm1',
            ]
        result = self.__run(lines)
        self.assertEqual(result,
                         [[["host", "myhost"], ["host", "vm1"]],
                          [["host", "yourhost"], ["host", "vm1"]]])


if __name__ == '__main__':
    unittest.main()
