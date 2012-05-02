#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012 :
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
from util import if_else

obj = None
name = None
local_log = None
human_timestamp_log = False

class Log:
    """Please Add a Docstring to describe the class here"""
    NOTSET   = logging.NOTSET
    DEBUG    = logging.DEBUG
    INFO     = logging.INFO
    WARNING  = logging.WARNING
    ERROR    = logging.ERROR
    CRITICAL = logging.CRITICAL

    def load_obj(self, object, name_=None):
        """ We load the object where we will put log broks
        with the 'add' method
        """
        global obj
        global name
        obj = object
        name = name_

        self._level = logging.NOTSET
    
    @staticmethod
    def get_level_id(lvlName):
        """Convert a level name (string) to its integer value

           Raise KeyError when name not found
        """
        return logging._levelNames[lvlName]
    
    def set_level(self, level):
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
        """Old log method, kept for NAGIOS compatibility"""
        self._log(logging.INFO, message, format, print_it, display_level=False)

    def _log(self, level, message, format=None, print_it=False, display_level=True):
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

            fmt = u'[%%(date)s] %s%%(name)s%%(msg)s\n' % (if_else(display_level, '%(level)s : ', ''))
            args = {
                'date' : if_else(human_timestamp_log, time.asctime(time.localtime(time.time())), int(time.time())),
                'level': lvlname.capitalize(),
                'name' : if_else(name is None, '', '[%s] ' % name),
                'msg'  : message
            }
            s = fmt % args
        else:
            s = format % message

        if print_it and len(s) > 1:
            # If the daemon is launched with a non UTF8 shell
            # we can have problems in printing
            try:
                print s[:-1]
            except UnicodeEncodeError:
                print s.encode('ascii', 'ignore')


        # We create and add the brok but not for debug that don't need
        # to do a brok for it, and so go in all satellites. Debug
        # should keep locally
        if level != logging.DEBUG:
            b = Brok('log', {'log': s})
            obj.add(b)

        # If we want a local log write, do it
        if local_log is not None:
            logging.log(level, s.strip())


    def register_local_log(self, path, level=None):
        """The log can also write to a local file if needed
        and return the file descriptor so we can avoid to
        close it
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


    def set_human_format(self):
        """Set the output as human format"""
        global human_timestamp_log
        human_timestamp_log = True


logger = Log()
