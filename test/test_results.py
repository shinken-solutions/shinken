#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
Test sending and logging of results done be shinken.logging.send_result
"""

import sys
import os
import time
import cPickle
from cStringIO import StringIO

import unittest
from tempfile import NamedTemporaryFile

import __import_shinken
from shinken.log import Log, send_result
import shinken.log as logging
from shinken.brok import Brok


class Collector:
    """Helper class for collecting broks"""
    def __init__(self):
        self.list = []

    def add(self, o):
        self.list.append(o)


class LogCollectMixin:

    def _get_brok_log_messages(self, collector):
        """
        Return the log messages stored as Broks into the collector.

        This also tests whether all objects collected by the collector
        are log entries.
        """
        for obj in collector.list:
            self.assertIsInstance(obj, Brok)
            self.assertEqual(obj.type, 'log')
            data = cPickle.loads(obj.data)
            self.assertEqual(data.keys(), ['log'])
            yield data['log']

    def setUp(self):
        self._orig_logger = logging.logger
        self._stdout = sys.stdout
        sys.stdout = StringIO()

        self._collector = Collector()
        self.logger = Log('shinken')
        self.logger.load_obj(self._collector)
        # need to patch `logging.logger` since `logging.send_result`
        # accesses it
        logging.logger = self.logger

    def tearDown(self):
        sys.stdout = self._stdout
        logging.logger = self._orig_logger

    def _get_logging_output(self):
        msgs = list(self._get_brok_log_messages(self._collector))
        lines = sys.stdout.getvalue().splitlines()
        return msgs, lines

    def _send_result(self, result, *args):
        send_result(result, *args)
        return self._get_logging_output()
    

class TestStandardLogging(LogCollectMixin, unittest.TestCase):

    def test_send_result_if_log_level_is_info(self):
        self.logger.setLevel(logging.INFO)
        msgs, lines = self._send_result('Some result')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Some result\n$')


    def test_send_result_if_log_level_is_debug(self):
        self.logger.setLevel(logging.DEBUG)
        msgs, lines = self._send_result('Some result')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Some result\n$')


class TestWithLocalLogging(TestStandardLogging):

    def setUp(self):
        super(TestWithLocalLogging, self).setUp()
        logfile = NamedTemporaryFile("w", delete=False)
        logfile.close()
        self.logfile_name = logfile.name
        # set up a temporary file for logging
        self.logger.register_local_log(self.logfile_name)

    def tearDown(self):
        os.remove(self.logfile_name)
        super(TestWithLocalLogging, self).tearDown()

    def _get_logging_output(self):
        msgs, lines = super(TestWithLocalLogging, self)._get_logging_output()
        local_lines = list(open(self.logfile_name).readlines())
        return msgs, lines, local_lines


    def test_send_result_if_log_level_is_info(self):
        self.logger.setLevel(logging.INFO)
        msgs, lines, local_lines = self._send_result('Some result')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Some result\n$')


    def test_send_result_if_log_level_is_debug(self):
        self.logger.setLevel(logging.DEBUG)
        msgs, lines, local_lines = self._send_result('Some result')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Some result\n$')
        self.assertRegexpMatches(local_lines[0],
                                 r'^\[\d+\] DEBUG:\s+Some result\n$')


if __name__ == '__main__':
    unittest.main()
