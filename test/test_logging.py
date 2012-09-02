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
Test shinken.logging
"""

import sys
import os
import time
import cPickle
from cStringIO import StringIO

import unittest
from tempfile import NamedTemporaryFile

import __import_shinken
from shinken.log import Log
import shinken.log as logging
from shinken.brok import Brok

# The logging module requires some object for collecting broks
class Dummy:
    """Dummy class for collecting broks"""
    def add(self, o):
        pass

class Collector:
    """Dummy class for collecting broks"""
    def __init__(self):
        self.list = []

    def add(self, o):
        self.list.append(o)


class TestLevels(unittest.TestCase):

    def test_getLevelName(self):
        for name , level in (
            ('NOTSET',   logging.NOTSET),
            ('DEBUG',    logging.DEBUG),
            ('INFO',     logging.INFO),
            ('WARNING',  logging.WARNING),
            ('ERROR',    logging.ERROR),
            ('CRITICAL', logging.CRITICAL),
            ):
            self.assertEqual(logging.getLevelName(level), name)

    def test_default_level(self):
        logger = Log('shinken')
        self.assertEqual(logger.level, logging.NOTSET)

    def test_setLevel(self):
        logger = Log('shinken')
        logger.setLevel(logging.WARNING)
        self.assertEqual(logger.level, logging.WARNING)

    def test_setLevel_non_integer_raises(self):
        logger = Log('shinken')
        self.assertRaises(TypeError, logger.setLevel, 1.0)

    def test_load_obj_must_not_change_level(self):
        logger = Log('shinken')
        # argl, load_obj() unsets the level! save and restore it
        logger.setLevel(logging.CRITICAL)
        logger.load_obj(Dummy())
        self.assertEqual(logger.level, logging.CRITICAL)

class TestBasics(unittest.TestCase):

    # no basiscs to test now
    pass


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

    def _prepare_logging(self):
        self._collector = Collector()
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        logger = Log('shinken')
        logger.load_obj(self._collector)
        return logger

    def _get_logging_output(self):
        msgs = list(self._get_brok_log_messages(self._collector))
        lines = sys.stdout.getvalue().splitlines()
        sys.stdout = self._stdout
        return msgs, lines

    def _put_log(self, log_method, *messages):
        try:
            for msg in messages:
                log_method(msg)
        finally:
            return self._get_logging_output()
    

class TestDefaultLoggingMethods(unittest.TestCase, LogCollectMixin):

    def test_basic_logging_debug_does_not_send_broks(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.DEBUG)
        msgs, lines = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)

    def test_basic_logging_info(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        msgs, lines = self._put_log(logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] INFO:\s+Some log-message\n$')

    def test_basic_logging_warning(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.WARNING)
        msgs, lines = self._put_log(logger.warning, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] WARNING:\s+Some log-message\n$')


    def test_basic_logging_error(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.ERROR)
        msgs, lines = self._put_log(logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] ERROR:\s+Some log-message\n$')

    def test_basic_logging_critical(self):
        logger = self._prepare_logging()
        msgs, lines = self._put_log(logger.critical, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] CRITICAL:\s+Some log-message\n$')

    def test_level_is_higher_then_the_one_set(self):
        logger = self._prepare_logging()
        # just test two samples
        logger.setLevel(logging.CRITICAL)
        msgs, lines = self._put_log(logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)

        # need to prepare again to have stdout=StringIO()
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        msgs, lines = self._put_log(logger.debug, 'Some log-message$')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)


class TestConsoleLogger(unittest.TestCase, LogCollectMixin):

    def _prepare_logging(self):
        self._collector = Collector()
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        logging.logger.load_obj(self._collector)
        console_logger = logging.console_logger
        assert console_logger.handlers[0].stream is self._stdout
        console_logger.handlers[0].stream = sys.stdout
        return logging.logger, console_logger

    def _get_logging_output(self):
        logger = logging.console_logger
        assert logger.handlers[0].stream is sys.stdout
        msgs, lines = super(TestConsoleLogger, self)._get_logging_output()
        logger.handlers[0].stream = self._stdout
        return msgs, lines

    def test_basic_logging_debug_does_not_send_broks(self):
        logger, console_logger = self._prepare_logging()
        console_logger.setLevel(logging.DEBUG)
        msgs, lines = self._put_log(console_logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 1)

    def test_basic_logging_info(self):
        logger, console_logger = self._prepare_logging()
        console_logger.setLevel(logging.INFO)
        msgs, lines = self._put_log(console_logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(lines[0], r'^\[.+?\] INFO:\s+Some log-message$')

    def test_basic_logging_warning(self):
        logger, console_logger = self._prepare_logging()
        console_logger.setLevel(logging.WARNING)
        msgs, lines = self._put_log(console_logger.warning, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] WARNING:\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[.+?\] WARNING:\s+Some log-message$')


    def test_basic_logging_error(self):
        logger, console_logger = self._prepare_logging()
        console_logger.setLevel(logging.ERROR)
        msgs, lines = self._put_log(console_logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] ERROR:\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[.+?\] ERROR:\s+Some log-message$')

    def test_basic_logging_critical(self):
        logger, console_logger = self._prepare_logging()
        msgs, lines = self._put_log(console_logger.critical, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] CRITICAL:\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[.+?\] CRITICAL:\s+Some log-message$')

    def test_level_is_higher_then_the_one_set(self):
        logger, console_logger = self._prepare_logging()
        # just test two samples
        console_logger.setLevel(logging.CRITICAL)
        msgs, lines = self._put_log(console_logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)

        # need to prepare again to have stdout=StringIO()
        logger, console_logger = self._prepare_logging()
        console_logger.setLevel(logging.INFO)
        msgs, lines = self._put_log(console_logger.debug, 'Some log-message$')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)


class TestWithLocalLogging(unittest.TestCase, LogCollectMixin):

    def _prepare_logging(self):
        logger = super(TestWithLocalLogging, self)._prepare_logging()
        # set up a temporary file for logging
        logfile = NamedTemporaryFile("w", delete=False)
        logfile.close()
        self.logfile_name = logfile.name
        logger.register_local_log(logfile.name)
        return logger

    def _get_logging_output(self):
        msgs, lines = super(TestWithLocalLogging, self)._get_logging_output()
        local_lines = list(open(self.logfile_name).readlines())
        os.remove(self.logfile_name)
        return msgs, lines, local_lines

    def test_register_local_log_keeps_level(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.ERROR)
        self.assertEqual(logger.level, logging.ERROR)
        logfile = NamedTemporaryFile("w", delete=False)
        logfile.close()
        logfile_name = logfile.name
        logger.register_local_log(logfile_name)
        self.assertEqual(logger.level, logging.ERROR)


    def test_basic_logging_debug_does_not_send_broks(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.DEBUG)
        msgs, lines, local_log = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r'^\[\d+\] DEBUG:\s+Some log-message$')

    def test_basic_logging_info(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        msgs, lines, local_log = self._put_log(logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r'^\[\d+\] INFO:\s+Some log-message\n$')

    def test_basic_logging_error(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.ERROR)
        msgs, lines, local_log = self._put_log(logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r'^\[\d+\] ERROR:\s+Some log-message\n$')

    def test_basic_logging_critical(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.CRITICAL)
        msgs, lines, local_log = self._put_log(logger.critical, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r'^\[\d+\] CRITICAL:\s+Some log-message\n$')

    def test_level_is_higher_then_the_one_set(self):
        logger = self._prepare_logging()
        # just test two samples
        logger.setLevel(logging.CRITICAL)
        msgs, lines, local_log = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 0)

        # need to prepare again to have stdout=StringIO() and a local log file
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        msgs, lines, local_log = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 0)


class TestNamedCollector(unittest.TestCase, LogCollectMixin):

    # :todo: add a test for the local log file, too

    def _prepare_logging(self):
        self._collector = Collector()
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        logger = Log('shinken')
        logger.load_obj(self._collector, 'Tiroler Schinken')
        return logger


    def test_basic_logging_info(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        msgs, lines = self._put_log(logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 0)
        self.assertRegexpMatches(msgs[0],
             r'^\[\d+\] INFO:\s+\[Tiroler Schinken\] Some log-message\n$')


if __name__ == '__main__':
    unittest.main()
