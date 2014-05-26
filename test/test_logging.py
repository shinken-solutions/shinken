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
from shinken.log import logger, Log
import shinken.log as logging
from shinken.brok import Brok
from shinken_test import *

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


class NoSetup:
    def setUp(self):
        pass



logger.load_obj(Dummy())



class TestLevels(NoSetup, ShinkenTest):

    def test_get_level_id(self):
        for name , level in (
            ('NOTSET',   logger.NOTSET),
            ('DEBUG',    logger.DEBUG),
            ('INFO',     logger.INFO),
            ('WARNING',  logger.WARNING),
            ('ERROR',    logger.ERROR),
            ('CRITICAL', logger.CRITICAL),
            ):
            self.assertEqual(logger.get_level_id(level), name)

    def test_get_level_id_unknown_level_raises(self):
        self.assertRaises(KeyError, logger.get_level_id, 'MYLEVEL')

    def test_default_level(self):
        logger = Log()
        # :fixme: `_level` is private, needs an official accessor
        self.assertEqual(logger._level, logger.NOTSET)

    def test_set_level(self):
        logger.set_level(logger.WARNING)
        self.assertEqual(logger._level, logger.WARNING)

    def test_set_level_non_integer_raises(self):
        self.assertRaises(TypeError, logger.set_level, 1.0)
        # Why raise if there is an easy way to give the value like this string?
        #self.assertRaises(TypeError, logger.set_level, 'INFO')

    def test_load_obj_must_not_change_level(self):
        # argl, load_obj() unsets the level! save and restore it
        logger.set_level(logger.CRITICAL)
        logger.load_obj(Dummy())
        self.assertEqual(logger._level, logger.CRITICAL)

class TestBasics(NoSetup, ShinkenTest):

    def test_setting_and_unsetting_human_timestamp_format(self):
        # :hack: logging.human_timestamp_log is a global variable
        self.assertEqual(logging.human_timestamp_log, False)
        logger.set_human_format(True)
        self.assertEqual(logging.human_timestamp_log, True)
        logger.set_human_format(False)
        self.assertEqual(logging.human_timestamp_log, False)
        logger.set_human_format(True)
        self.assertEqual(logging.human_timestamp_log, True)
        logger.set_human_format(False)
        self.assertEqual(logging.human_timestamp_log, False)


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
        logger.load_obj(self._collector)
        self._stdout = sys.stdout
        sys.stdout = StringIO()

    def _get_logging_output(self):
        msgs = list(self._get_brok_log_messages(self._collector))
        lines = sys.stdout.getvalue().splitlines()
        sys.stdout = self._stdout
        return msgs, lines

    def _put_log(self, log_method, *messages):
        self._prepare_logging()
        try:
            for msg in messages:
                log_method(msg)
        finally:
            return self._get_logging_output()
    

class TestDefaultLoggingMethods(NoSetup, ShinkenTest, LogCollectMixin):

    def test_basic_logging_log(self):
        msgs, lines = self._put_log(logger.log, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[\d+\] Some log-message$')

    def test_basic_logging_debug_does_not_send_broks(self):
        logger.set_level(logger.DEBUG)
        msgs, lines = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(lines[0], r'^\[\d+\] Debug :\s+Some log-message$')

    def test_basic_logging_info(self):
        logger.set_level(logger.INFO)
        msgs, lines = self._put_log(logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Info :\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[\d+\] Info :\s+Some log-message$')

    def test_basic_logging_warning(self):
        logger.set_level(logger.WARNING)
        msgs, lines = self._put_log(logger.warning, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Warning :\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[\d+\] Warning :\s+Some log-message$')


    def test_basic_logging_error(self):
        logger.set_level(logger.ERROR)
        msgs, lines = self._put_log(logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Error :\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[\d+\] Error :\s+Some log-message$')

    def test_basic_logging_critical(self):
        msgs, lines = self._put_log(logger.critical, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0], r'^\[\d+\] Critical :\s+Some log-message\n$')
        self.assertRegexpMatches(lines[0], r'^\[\d+\] Critical :\s+Some log-message$')

    def test_level_is_higher_then_the_one_set(self):
        # just test two samples
        logger.set_level(logger.CRITICAL)
        msgs, lines = self._put_log(logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)

        logger.set_level(logger.INFO)
        msgs, lines = self._put_log(logger.debug, 'Some log-message$')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)

    def test_human_timestamp_format(self):
        "test output using the human timestamp format"
        logger.set_level(logger.INFO)
        logger.set_human_format(True)
        msgs, lines = self._put_log(logger.info, 'Some ] log-message')
        self.assertRegexpMatches(msgs[0],
            r'^\[[^\]]+] Info :\s+Some \] log-message\n$')
        time.strptime(msgs[0].split(' Info :    ', 1)[0], '[%a %b %d %H:%M:%S %Y]')
        self.assertRegexpMatches(lines[0],
            r'^\[[^\]]+] Info :\s+Some \] log-message$')
        time.strptime(msgs[0].split(' Info :    ', 1)[0], '[%a %b %d %H:%M:%S %Y]')
        logger.set_human_format(False)

    def test_reset_human_timestamp_format(self):
        "test output after switching of the human timestamp format"
        # ensure the human timestamp format is set, ...
        self.test_human_timestamp_format()
        # ... then turn it off
        logger.set_human_format(False)
        # test whether the normal format is used again
        self.test_basic_logging_info()


class TestWithLocalLogging(NoSetup, ShinkenTest, LogCollectMixin):

    def _prepare_logging(self):
        super(TestWithLocalLogging, self)._prepare_logging()
        # set up a temporary file for logging
        logfile = NamedTemporaryFile("w")
        logfile.close()
        self.logfile_name = logfile.name
        logger.register_local_log(logfile.name)

    def _get_logging_output(self):
        msgs, lines = super(TestWithLocalLogging, self)._get_logging_output()
        f = open(self.logfile_name)
        local_lines = list(f.readlines())
        f.close()
        try:
            os.remove(self.logfile_name)
        except : # On windows, the file is still lock. But should be close!?!
            pass
        return msgs, lines, local_lines
    

    def test_register_local_log_keeps_level(self):
        logger.set_level(logger.ERROR)
        self.assertEqual(logger._level, logger.ERROR)
        logfile = NamedTemporaryFile("w")
        logfile.close()
        logfile_name = logfile.name
        logger.register_local_log(logfile_name)
        self.assertEqual(logger._level, logger.ERROR)

    def test_basic_logging_log(self):
        msgs, lines, local_log = self._put_log(logger.log, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0], r' \[\d+\] Some log-message\n$')

    def test_basic_logging_debug_does_not_send_broks(self):
        logger.set_level(logger.DEBUG)
        msgs, lines, local_log = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r' \[\d+\] Debug :\s+Some log-message$')

    def test_basic_logging_info(self):
        logger.set_level(logger.INFO)
        msgs, lines, local_log = self._put_log(logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r' \[\d+\] Info :\s+Some log-message\n$')

    def test_basic_logging_error(self):
        logger.set_level(logger.ERROR)
        msgs, lines, local_log = self._put_log(logger.error, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(local_log), 1)
        print >> sys.stderr, local_log[0]
        self.assertRegexpMatches(local_log[0],
            r' \[\d+\] Error :\s+Some log-message\n$')

    def test_basic_logging_critical(self):
        logger.set_level(logger.CRITICAL)
        msgs, lines, local_log = self._put_log(logger.critical, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r' \[\d+\] Critical :\s+Some log-message\n$')

    def test_level_is_higher_then_the_one_set(self):
        # just test two samples
        logger.set_level(logger.CRITICAL)
        msgs, lines, local_log = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 0)

        logger.set_level(logger.INFO)
        msgs, lines, local_log = self._put_log(logger.debug, 'Some log-message')
        self.assertEqual(len(msgs), 0)
        self.assertEqual(len(lines), 0)
        self.assertEqual(len(local_log), 0)


    def test_human_timestamp_format(self):
        logger.set_level(logger.INFO)
        logger.set_human_format(True)
        msgs, lines, local_log = self._put_log(logger.info, 'Some ] log-message')
        self.assertEqual(len(local_log), 1)
        self.assertRegexpMatches(local_log[0],
            r' \[[^\]]+] Info :\s+Some \] log-message\n$')
        # :fixme: Currently, the local log gets prefixed another
        # timestamp. As it is yet unclear, whether this intended or
        # not, we test it, too.
        times = local_log[0].split(' Info :    ', 1)[0]
        time1, time2 = times.rsplit('[', 1)
        time.strptime(time1.rsplit(',')[0], '%Y-%m-%d %H:%M:%S')
        time.strptime(time2, '%a %b %d %H:%M:%S %Y]')
        logger.set_human_format(False)

    def test_reset_human_timestamp_format(self):
        "test output after switching of the human timestamp format"
        # ensure the human timestamp format is set, ...
        self.test_human_timestamp_format()
        # ... then turn it off
        logger.set_human_format(False)
        # test whether the normal format is used again
        self.test_basic_logging_info()


class TestNamedCollector(NoSetup, ShinkenTest, LogCollectMixin):

    # :todo: add a test for the local log file, too

    def _prepare_logging(self):
        self._collector = Collector()
        logger.load_obj(self._collector, 'Tiroler Schinken')
        self._stdout = sys.stdout
        sys.stdout = StringIO()


    def test_basic_logging_info(self):
        logger.set_level(logger.INFO)
        msgs, lines = self._put_log(logger.info, 'Some log-message')
        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(lines), 1)
        self.assertRegexpMatches(msgs[0],
             r'^\[\d+\] Info :\s+\[Tiroler Schinken\] Some log-message\n$')
        self.assertRegexpMatches(lines[0],
             r'^\[\d+\] Info :\s+\[Tiroler Schinken\] Some log-message$')

    def test_human_timestamp_format(self):
        logger.set_level(logger.INFO)
        logger.set_human_format(True)
        msgs, lines = self._put_log(logger.info, 'Some ] log-message')
        self.assertRegexpMatches(msgs[0],
            r'^\[[^\]]+] Info :\s+\[Tiroler Schinken\] Some \] log-message\n$')
        time.strptime(msgs[0].split(' Info :    ', 1)[0], '[%a %b %d %H:%M:%S %Y]')
        self.assertRegexpMatches(lines[0],
            r'^\[[^\]]+] Info :\s+\[Tiroler Schinken\] Some \] log-message$')
        time.strptime(msgs[0].split(' Info :    ', 1)[0], '[%a %b %d %H:%M:%S %Y]')
        logger.set_human_format(False)

    def test_reset_human_timestamp_format(self):
        # ensure human timestamp format is set and working
        self.test_human_timestamp_format()
        # turn of human timestamp format
        logger.set_human_format(False)
        # test for normal format
        self.test_basic_logging_info()


if __name__ == '__main__':
    unittest.main()
