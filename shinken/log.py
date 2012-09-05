#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

import sys
import time
import logging
from logging import Handler, Formatter, StreamHandler, getLevelName
from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
from logging.handlers import TimedRotatingFileHandler

from brok import Brok


_brokhandler_ = None


brokFormatter = Formatter('[%(created)i] %(levelname)s: %(message)s')
brokFormatter_named = Formatter('[%(created)i] %(levelname)s: [%(name)s] %(message)s')
defaultFormatter = Formatter('[%(created)i] %(levelname)s: %(message)s')
humanFormatter = Formatter('[%(asctime)s] %(levelname)s: %(message)s',
                           '%a %b %d %H:%M:%S %Y')
CONSOLE_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'


class BrokHandler(Handler):
    """
    This log handler is forwarding log messages as broks to the broker.

    Only messages of level higher than DEBUG are send to other
    satellite to not risk overloading them.
    """

    def __init__(self, broker, name=None):
        # Only messages of level INFO or higher are passed on to the
        # broker. If the Logger level is higher then INFO, the logger
        # already skips the entry.
        Handler.__init__(self, logging.INFO)
        self._broker = broker

    def emit(self, record):
        try:
            msg = self.format(record)
            brok = Brok('log', {'log': msg + '\n'})
            self._broker.add(brok)
        except:
            self.handleError(record)


class Log(logging.Logger):
    """Shinken logger class, wrapping access to Python logging standard library."""

    def load_obj(self, object, name_=None):
        """ We load the object where we will put log broks
        with the 'add' method
        """
        global _brokhandler_
        _brokhandler_ = BrokHandler(object)
        if name_:
            self.name = name_
            _brokhandler_.setFormatter(brokFormatter_named)
        else:
            _brokhandler_.setFormatter(brokFormatter)
        self.addHandler(_brokhandler_)


    def register_local_log(self, path, level=None):
        """
        Add logging to a local log-file.

        The file will be rotated once a day
        """
        handler = TimedRotatingFileHandler(path, 'midnight', backupCount=5)
        if level is not None:
            handler.setLevel(level)
        handler.setFormatter(defaultFormatter)
        self.addHandler(handler)

    def set_human_format(self, on=True):
        """
        Set the output as human format.

        If the optional parameter `on` is False, the timestamp format
        will be reset to the default format.
        """
        if on:
            for handler in self.handlers:
                handler.setFormatter(humanFormatter)
        else:
            for handler in self.handlers:
                handler.setFormatter(defaultFormatter)


#--- create the main logger ---
# Restore original logger-class after creation, since this is the only
# logger of class `Log`,
lc = logging.getLoggerClass()
logging.setLoggerClass(Log)
logger = logging.getLogger('shinken')
logging.setLoggerClass(lc)
del lc

console_logger = logging.getLogger('shinken.console')
sh = StreamHandler(sys.stdout)
sh.setFormatter(Formatter(CONSOLE_FORMAT))
console_logger.addHandler(sh)
del sh

def send_result(result, *args):
    logger.debug(result)
    msg = "[%d] %s\n" % (time.time(), result)
    brok = Brok('log', {'log': msg})
    _brokhandler_._broker.add(brok)
