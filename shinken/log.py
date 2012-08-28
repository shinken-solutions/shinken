#!/usr/bin/env python

# -*- coding: utf-8 -*-

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

import time
import logging
from logging import Handler, Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler

from brok import Brok

human_timestamp_log = False

_brokhandler_ = None


brokFormatter = Formatter('[%(created)i] %(levelname)s: %(message)s')
brokFormatter_named = Formatter('[%(created)i] %(levelname)s: [%(name)s] %(message)s')
defaultFormatter = Formatter('[%(created)i] %(levelname)s: %(message)s')


class BrokHandler(Handler):
    """
    This log handler is forwarding log messages as broks to the broker.

    Only messages of level higher than DEBUG are send to other
    satellite to not risk overloading them.
    """

    def __init__(self, broker, name=None):
        # Only messages of levelINFO or higher are passed on to the
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
    "Store the numeric value from python logging class"
    NOTSET   = logging.NOTSET
    DEBUG    = logging.DEBUG
    INFO     = logging.INFO
    WARNING  = logging.WARNING
    ERROR    = logging.ERROR
    CRITICAL = logging.CRITICAL


    def __init__(self, name='shinken', level=NOTSET):
        logging.Logger.__init__(self, name, level)

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


    @staticmethod
    def get_level_id(lvlName):
        """Convert a level name (string) to its integer value
           and vice-versa. Input a level and it will return a name.
           Raise KeyError when name or level not found
        """
        return logging._levelNames[lvlName]

    # We can have level as an int (logging.INFO) or a string INFO
    # if string, try to get the int value
    def get_level(self):
        return logging.getLogger().getEffectiveLevel()

    # We can have level as an int (logging.INFO) or a string INFO
    # if string, try to get the int value
    def set_level(self, level):
        if not isinstance(level, int):
            level = getattr(logging, level, None)
            if not level or not isinstance(level, int):
                raise TypeError('log level must be an integer')

        self._level = level
        logging.getLogger().setLevel(level)


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
        global human_timestamp_log
        human_timestamp_log = bool(on)

logger = Log()

class __ConsoleLogger:
    """
    This wrapper class for logging and printing messages to stdout, too.

    :fixme: Implement this using an additional stream-handler, as soon
    as the logging system is based on the standard Pytthon logging
    module.
    """
    def debug(self, msg, *args, **kwargs):
        self._log(Log.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        kwargs.setdefault('display_level', False)
        self._log(Log.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(Log.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(Log.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(Log.CRITICAL, msg, *args, **kwargs)

    def _log(self, *args, **kwargs):
        # if `print_it` is not passed as an argument, set it to `true`
        kwargs.setdefault('print_it', True)
        logger._log(*args, **kwargs)


console_logger = __ConsoleLogger()

def send_result(result, *args):
    console_logger.info(result)
