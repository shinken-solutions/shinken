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
import sys
from logging import Handler, Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler

from brok import Brok

def is_tty():
    # Look if we are in a tty or not
    if hasattr(sys.stdout, 'isatty'):
        return sys.stdout.isatty()
    return False

if is_tty():
    # Try to load the terminal color. Won't work under python 2.4
    try:
        from shinken.misc.termcolor import cprint
    except (SyntaxError, ImportError), exp:
        # Outch can't import a cprint, do a simple print
        def cprint(s, color='', end=''):
            print s
# Ok it's a daemon mode, if so, just print
else:
    def cprint(s, color='', end=''):
        print s


obj = None
name = None
human_timestamp_log = False

_brokhandler_ = None


brokFormatter = Formatter('[%(created)i] %(levelname)s: %(message)s')
brokFormatter_named = Formatter('[%(created)i] %(levelname)s: [%(name)s] %(message)s')
defaultFormatter = Formatter('[%(created)i] %(levelname)s: %(message)s')
humanFormatter = Formatter('[%(asctime)s] %(levelname)s: %(message)s',
                           '%a %b %d %H:%M:%S %Y')

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
        self.display_time = True                                                                                                                                                            
        self.display_level = True                                                                                                                                                           
        self.log_colors = {Log.WARNING:'yellow', Log.CRITICAL:'magenta', Log.ERROR:'red'}    

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
        """The shinken logging wrapper can write to a local file if needed
        and return the file descriptor so we can avoid to
        close it.

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

        If the optional parameter `on` is False, the timestamps format
        will be reset to the default format.
        """
        global human_timestamp_log
        human_timestamp_log = bool(on)




#--- create the main logger ---
logging.setLoggerClass(Log)
logger = logging.getLogger('shinken')

console_logger = logging.getLogger('shinken.console')
console_logger.addHandler(StreamHandler(sys.stdout))

def send_result(result, *args):
    console_logger.info(result)
