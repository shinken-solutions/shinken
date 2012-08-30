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
from logging.handlers import TimedRotatingFileHandler

from brok import Brok

obj = None
name = None
local_log = None
human_timestamp_log = False


class Log:
    """Shinken logger class, wrapping access to Python logging standard library."""
    "Store the numeric value from python logging class"
    NOTSET   = logging.NOTSET
    DEBUG    = logging.DEBUG
    INFO     = logging.INFO
    WARNING  = logging.WARNING
    ERROR    = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self):
        self._level = logging.NOTSET

    def load_obj(self, object, name_=None):
        """ We load the object where we will put log broks
        with the 'add' method
        """
        global obj
        global name
        obj = object
        name = name_


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

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def log(self, message, format=None, print_it=True):
        """Old log method, kept for NAGIOS compatibility
        What strings should not use the new format ??"""
        self._log(logging.INFO, message, format, print_it, display_level=False)

    def _log(self, level, message, format=None, print_it=True, display_level=True):
        """We enter a log message, we format it, and we add the log brok"""
        global obj
        global name
        global local_log
        global human_timestamp_log

        # ignore messages when message level is lower than Log level
        if level < self._level:
            return

        # We format the log in UTF-8
        if isinstance(message, str):
            message = message.decode('UTF-8', 'replace')

        if format is None:
            lvlname = logging.getLevelName(level)

            if display_level:
                fmt = u'[%(date)s] %(level)-9s %(name)s%(msg)s\n'
            else:
                fmt = u'[%(date)s] %(name)s%(msg)s\n'

            args = {
                'date': (human_timestamp_log and time.asctime()
                         or int(time.time())),
                'level': lvlname.capitalize()+' :',
                'name': name and ('[%s] ' % name) or '',
                'msg': message
            }
            s = fmt % args
        else:
            s = format % message

        if print_it and len(s) > 1:
            # Print to standard output.
            # If the daemon is launched with a non UTF8 shell
            # we can have problems in printing, work around it.
            try:
                print s[:-1]
            except UnicodeEncodeError:
                print s.encode('ascii', 'ignore')


        # We create the brok and load the log message
        # DEBUG level logs are logged by the daemon locally
        # and must not be forwarded to other satelittes, or risk overloading them.
        if level != logging.DEBUG:
            b = Brok('log', {'log': s})
            obj.add(b)

        # If local logging is enabled, log to the defined handler, file.
        if local_log is not None:
            logging.log(level, s.strip())

    def register_local_log(self, path, level=None):
        """The shiken logging wrapper can write to a local file if needed
        and return the file descriptor so we can avoid to
        close it.
        """
        global local_log

        if level is not None:
            self._level = level

        # Open the log and set to rotate once a day
        basic_log_handler = TimedRotatingFileHandler(path,
                                                     'midnight',
                                                     backupCount=5)
        basic_log_handler.setLevel(self._level)
        basic_log_formatter = logging.Formatter('%(asctime)s %(message)s')
        basic_log_handler.setFormatter(basic_log_formatter)
        logger = logging.getLogger()
        logger.addHandler(basic_log_handler)
        logger.setLevel(self._level)
        local_log = basic_log_handler

        # Return the file descriptor of this file
        return basic_log_handler.stream.fileno()

    def quit(self):
        """Close the local log file at program exit"""
        global local_log
        if local_log:
            self.debug("Closing %s local_log" % str(local_log))
            local_log.close()

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
