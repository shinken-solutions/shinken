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

from tempfile import NamedTemporaryFile

import __import_shinken
import logging
from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL, StreamHandler
from shinken.log import logger as shinken_logger, naglog_result, Log, human_timestamp_log
from shinken.log import defaultFormatter, BrokHandler, ColorStreamHandler

shinken_logger.set_log = True

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



#logger.load_obj(Dummy())



class TestLevels(NoSetup, ShinkenTest):

    def test_default_level(self):
        logger = Log(name=None, log_set=True)
        self.assertEqual(logger.level, logging.NOTSET)

    def test_setLevel(self):
        logger = Log(name=None, log_set=True)
        logger.setLevel(logging.WARNING)
        self.assertEqual(logger.level, min(WARNING, INFO))

    def test_setLevel_non_integer_raises(self):
        logger = Log(name=None, log_set=True)
        self.assertRaises(TypeError, logger.setLevel, 1.0)

    def test_load_obj_must_not_change_level(self):
        logger = Log(name=None, log_set=True)
        # argl, load_obj() unsets the level! save and restore it
        logger.setLevel(logging.CRITICAL)
        logger.load_obj(Dummy())
        self.assertEqual(logger.level, min(CRITICAL, INFO))


class TestBasics(NoSetup, ShinkenTest):

    def test_setting_and_unsetting_human_timestamp_format(self):
        # :hack: shinken.log.human_timestamp_log is a global variable
        self.assertEqual(shinken.log.human_timestamp_log, False)
        logger.set_human_format(True)
        self.assertEqual(shinken.log.human_timestamp_log, True)
        logger.set_human_format(False)
        self.assertEqual(shinken.log.human_timestamp_log, False)
        logger.set_human_format(True)
        self.assertEqual(shinken.log.human_timestamp_log, True)
        logger.set_human_format(False)
        self.assertEqual(shinken.log.human_timestamp_log, False)


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
        logger = Log(name=None, log_set=True)

        sh = StreamHandler(sys.stdout)
        sh.setFormatter(defaultFormatter)
        logger.addHandler(sh)
        logger.load_obj(self._collector)
        logger.pre_log_buffer = [] # reset the pre_log for several tests
        return logger


    def _get_logging_output(self):
        broklogs = list(self._get_brok_log_messages(self._collector))

        stdoutlogs = sys.stdout.getvalue().splitlines()
        sys.stdout = sys.__stdout__

        if hasattr(self, 'logfile_name'):
            f = open(self.logfile_name)
            filelogs = list(f.readlines())
            f.close()
            try:
                os.remove(self.logfile_name)
            except Exception: # On windows, the file is still lock. But should be close!?!
                pass
        else:
            filelogs = None
        return broklogs, stdoutlogs, filelogs


    def _put_log(self, log_method, *messages):
        #self._prepare_logging()
        try:
            for msg in messages:
                log_method(msg)
        finally:
            return self._get_logging_output()


    def generic_tst(self, fun, msg, lenlist, patterns):
        #sys.stdout = StringIO()
        loglist = self._put_log(fun, msg)
        for i, length in enumerate(lenlist):
            self.assertEqual(len(loglist[i]), length)
            if length != 0:
                self.assertRegexpMatches(loglist[i][0], patterns[i])
        return loglist


class TestDefaultLoggingMethods(NoSetup, ShinkenTest, LogCollectMixin):

    def test_basic_logging_log(self):
        sys.stdout = StringIO()
        self._collector = Collector()
        sh = StreamHandler(sys.stdout)
        sh.setFormatter(defaultFormatter)
        shinken_logger.handlers = []
        shinken_logger.addHandler(sh)
        shinken_logger.load_obj(self._collector)
        shinken_logger.log_set = True
        shinken_logger.setLevel(DEBUG)
        self.generic_tst(lambda x: naglog_result('info', x), 'Some log-message',
                         [1, 1], [r'^\[\d+\] Some log-message\n$', r'^\[\d+\] Some log-message$'])

    def test_basic_logging_debug_does_not_send_broks(self):
        logger = self._prepare_logging()
        logger.setLevel(DEBUG)
        self.generic_tst(logger.debug, 'Some log-message',
                         [0, 1], ['', r'^\[\d+\] DEBUG:\s+Some log-message$'])


    def test_basic_logging_info(self):
        logger = self._prepare_logging()
        logger.setLevel(INFO)
        self.generic_tst(logger.info, 'Some log-message',
                         [1, 1], [r'^\[\d+\] INFO:\s+Some log-message\n$', r'^\[\d+\] INFO:\s+Some log-message$'])


    def test_basic_logging_warning(self):
        logger = self._prepare_logging()
        logger.setLevel(WARNING)
        self.generic_tst(logger.warning, 'Some log-message',
                         [1, 1], [r'^\[\d+\] WARNING:\s+Some log-message\n$', r'^\[\d+\] WARNING:\s+Some log-message$'])

    def test_basic_logging_error(self):
        logger = self._prepare_logging()
        logger.setLevel(ERROR)
        self.generic_tst(logger.error, 'Some log-message',
                         [1, 1], [r'^\[\d+\] ERROR:\s+Some log-message\n$', r'^\[\d+\] ERROR:\s+Some log-message$'])


    def test_basic_logging_critical(self):
        logger = self._prepare_logging()
        logger.setLevel(CRITICAL)
        self.generic_tst(logger.critical, 'Some log-message',
                         [1, 1],
                         [r'^\[\d+\] CRITICAL:\s+Some log-message\n$', r'^\[\d+\] CRITICAL:\s+Some log-message$'])

    def test_level_is_higher_then_the_one_set(self):
        logger = self._prepare_logging()
        # just test two samples
        logger.setLevel(CRITICAL)
        self.generic_tst(logger.error, 'Some log-message',
                         [1, 0], [r'^\[\d+\] ERROR:\s+Some log-message\n$', ''])

        # need to prepare again to have stdout=StringIO()
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        self.generic_tst(logger.debug, 'Some log-message',
                         [0, 0], ['', ''])


    def test_human_timestamp_format(self):
        "test output using the human timestamp format"
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        logger.set_human_format(True)
        loglist = self.generic_tst(logger.info, 'Some ] log-message',
                         [1, 1], [r'^\[\d+\] INFO:\s+Some \] log-message\n$', r'^\[[^\]]+] INFO:\s+Some \] log-message$'])

        time.strptime(loglist[1][0].split(' INFO: ', 1)[0], '[%a %b %d %H:%M:%S %Y]')
        logger.set_human_format(False)

    def test_reset_human_timestamp_format(self):
        "test output after switching of the human timestamp format"
        # ensure the human timestamp format is set, ...
        self.test_human_timestamp_format()
        # ... then turn it off
        logger.set_human_format(False)
        # test whether the normal format is used again
        self.test_basic_logging_info()


class TestColorConsoleLogger(NoSetup, ShinkenTest, LogCollectMixin):

    def test_basic_logging_info_colored(self):
        shinken_logger.setLevel(INFO)
        self._collector = Collector()
        sys.stdout = StringIO()
        shinken_logger.handlers[0].stream = sys.stdout
        shinken_logger.load_obj(self._collector)
        if isinstance(shinken_logger.handlers[0], ColorStreamHandler):
            self.generic_tst(shinken_logger.info, 'Some log-message',
                             [1, 1],
                             [r'^\[.+?\] INFO: \[Shinken\] Some log-message$',
                              r'^\x1b\[95m\[.+?\] INFO: \[Shinken\] Some log-message\x1b\[0m$'])
        else:
            self.generic_tst(shinken_logger.info, 'Some log-message',
                             [1, 1],
                             [r'^\[.+?\] INFO:\s+Some log-message$',
                              r'^\[.+?\] INFO:\s+Some log-message$'])

    def test_human_timestamp_format(self):
        "test output using the human timestamp format"
        shinken_logger.setLevel(INFO)
        self._collector = Collector()
        sys.stdout = StringIO()
        shinken_logger.handlers[0].stream = sys.stdout
        shinken_logger.load_obj(self._collector)
        shinken_logger.set_human_format(True)
        if isinstance(shinken_logger.handlers[0], ColorStreamHandler):
            loglist = self.generic_tst(shinken_logger.info, 'Some log-message',
                             [1, 1],
                             [r'^\[.+?\] INFO: \[Shinken\] Some log-message$',
                              r'^\x1b\[95m\[.+?\] INFO: \[Shinken\] Some log-message\x1b\[0m$'])
        else:
            loglist = self.generic_tst(shinken_logger.info, 'Some log-message',
                             [1, 1],
                             [r'^\[.+?\] INFO: \[Shinken\] Some log-message$',
                              r'^\[.+?\] INFO: \[Shinken\] Some log-message$'])


        times = loglist[1][0].split(' INFO: ', 1)[0]
        _, time2 = times.rsplit('[', 1)
        time.strptime(time2.rsplit(']')[0], '%a %b %d %H:%M:%S %Y')

        logger.set_human_format(False)

    def test_reset_human_timestamp_format(self):
        "test output after switching of the human timestamp format"
        # ensure the human timestamp format is set, ...
        self.test_human_timestamp_format()
        # ... then turn it off
        logger.set_human_format(False)
        # test whether the normal format is used again
        self.test_basic_logging_info_colored()


class TestWithLocalLogging(NoSetup, ShinkenTest, LogCollectMixin):

    def _prepare_logging(self):
        logger = super(TestWithLocalLogging, self)._prepare_logging()
        # set up a temporary file for logging
        logfile = NamedTemporaryFile("w", delete=False)
        logfile.close()
        self.logfile_name = logfile.name
        logger.register_local_log(logfile.name, purge_buffer=False)
        return logger

    def test_register_local_log_keeps_level(self):
        logger = self._prepare_logging()
        logger.setLevel(ERROR)
        self.assertEqual(logger.level, min(ERROR, INFO))
        for handler in logger.handlers:
            if isinstance(handler, Collector) or isinstance(handler, BrokHandler):
                self.assertEqual(handler.level, INFO)
            else:
                self.assertEqual(handler.level, ERROR)
        logfile = NamedTemporaryFile("w", delete=False)
        logfile.close()
        logfile_name = logfile.name
        logger.register_local_log(logfile_name, purge_buffer=False)
        self.assertEqual(logger.level, min(ERROR, INFO))


    def test_basic_logging_log(self):
        sys.stdout = StringIO()
        self._collector = Collector()
        sh = StreamHandler(sys.stdout)
        sh.setFormatter(defaultFormatter)
        shinken_logger.handlers = []
        shinken_logger.addHandler(sh)
        shinken_logger.load_obj(self._collector)
        shinken_logger.log_set = True
        logfile = NamedTemporaryFile("w", delete=False)
        logfile.close()
        self.logfile_name = logfile.name
        shinken_logger.register_local_log(logfile.name, purge_buffer=False)
        shinken_logger.setLevel(DEBUG)
        self.generic_tst(lambda x: naglog_result('info', x), 'Some log-message',
                         [1, 1, 1], ['', r'^\[\d+\] Some log-message$', r'^\[\d+\] Some log-message$'])


    def test_basic_logging_debug_does_not_send_broks(self):
        logger = self._prepare_logging()
        logger.setLevel(DEBUG)
        self.generic_tst(logger.debug, 'Some log-message',
                         [0, 1, 1], ['', '', r'\[\d+\] DEBUG:\s+Some log-message$'])

    def test_basic_logging_info(self):
        logger = self._prepare_logging()
        logger.setLevel(INFO)
        self.generic_tst(logger.info, 'Some log-message',
                         [1, 1, 1], ['', '', r'\[\d+\] INFO:\s+Some log-message\n$'])

    def test_basic_logging_error(self):
        logger = self._prepare_logging()
        logger.setLevel(ERROR)
        self.generic_tst(logger.error, 'Some log-message',
                         [1, 1, 1], ['', '', r'\[\d+\] ERROR:\s+Some log-message\n$'])

    def test_basic_logging_critical(self):
        logger = self._prepare_logging()
        logger.setLevel(CRITICAL)
        self.generic_tst(logger.critical, 'Some log-message',
                         [1, 1, 1], ['', '', r'\[\d+\] CRITICAL:\s+Some log-message\n$'])

    def test_level_is_higher_then_the_one_set(self):
        logger = self._prepare_logging()
        # just test two samples
        logger.setLevel(CRITICAL)
        self.generic_tst(logger.debug, 'Some log-message', [0, 0, 0], ['', '', ''])

        # need to prepare again to have stdout=StringIO() and a local log file
        logger = self._prepare_logging()
        logger.setLevel(INFO)
        self.generic_tst(logger.debug, 'Some log-message', [0, 0, 0], ['', '', ''])

    def test_human_timestamp_format(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        logger.set_human_format(True)
        loglist = self.generic_tst(logger.info, 'Some log-message',
                         [1, 1, 1],
                         [r'', r'', r'\[[^\]]+] INFO:\s+Some log-message\n$'])

        # :fixme: Currently, the local log gets prefixed another
        # timestamp. As it is yet unclear, whether this intended or
        # not, we test it, too.
        times = loglist[2][0].split(' INFO:    ', 1)[0]
        _, time2 = times.rsplit('[', 1)
        time.strptime(time2.rsplit(']')[0], '%a %b %d %H:%M:%S %Y')
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
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        logger = Log(name=None, log_set=True)
        from shinken.log import defaultFormatter
        from logging import StreamHandler
        sh = StreamHandler(sys.stdout)
        sh.setFormatter(defaultFormatter)
        logger.addHandler(sh)
        logger.load_obj(self._collector, 'Tiroler Schinken')
        return logger

    def test_basic_logging_info(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        self.generic_tst(logger.info, 'Some log-message',
                         [1, 1],
                         [r'^\[\d+\] INFO:\s+\[Tiroler Schinken\] Some log-message\n$',
                          r'^\[\d+\] INFO:\s+\[Tiroler Schinken\] Some log-message$'])

    def test_human_timestamp_format(self):
        logger = self._prepare_logging()
        logger.setLevel(logging.INFO)
        logger.set_human_format(True)
        loglist = self.generic_tst(logger.info, 'Some ] log-message',
                         [1, 1],
                         [r'^\[\d+\] INFO:\s+\[Tiroler Schinken\] Some \] log-message\n$',
                          r'^\[[^\]]+] INFO:\s+\[Tiroler Schinken\] Some \] log-message$'])
        # No TS for broker!
        time.strptime(loglist[1][0].split(' INFO: ', 1)[0], '[%a %b %d %H:%M:%S %Y]')
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
