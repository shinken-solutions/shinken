#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2011 :
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
    """Please Add a Docstring to describe the class here"""

    def load_obj(self, object, name_=None):
        """ We load the object where we will put log broks
        with the 'add' method
        """
        global obj
        global name
        obj = object
        name = name_

    def log(self, message, format=None, print_it=True):
        """We enter a log message, we format it, and we add the log brok"""
        global obj
        global name
        global local_log
        global human_timestamp_log

        if print_it:
            # If the daemon is launched with a non UTF8 shell
            # we can have problems in printing
            try:
                print message
            except UnicodeEncodeError:
                print message.encode('ascii', 'ignore')

        # We format the log in UTF-8
        if isinstance(message, str):
            message = message.decode('UTF-8', 'replace')

        if format is None:
            if name is None:
                if human_timestamp_log:
                    s = u'[%s] %s\n' % \
                        (time.asctime(time.localtime(time.time())), message)
                else:
                    s = u'[%d] %s\n' % (int(time.time()), message)
            else:
                if human_timestamp_log:
                    s = u'[%s] [%s] %s\n' % \
                        (time.asctime(time.localtime(time.time())),
                                                     name,
                                                     message)
                else:
                    s = u'[%d] [%s] %s\n' % (int(time.time()), name, message)
        else:
            s = format % message

        # We create and add the brok
        b = Brok('log', {'log': s})
        obj.add(b)

        # If we want a local log write, do it
        if local_log is not None:
            logging.info(s)

    def register_local_log(self, path):
        """The log can also write to a local file if needed
        and return the file descriptor so we can avoid to
        close it
        """
        global local_log

        # Open the log and set to rotate once a day
        log_level = logging.DEBUG
        basic_log_handler = TimedRotatingFileHandler(path,
                                                     'midnight',
                                                     backupCount=5)
        basic_log_handler.setLevel(log_level)
        basic_log_formatter = logging.Formatter('%(asctime)s %(message)s')
        basic_log_handler.setFormatter(basic_log_formatter)
        logger = logging.getLogger()
        logger.addHandler(basic_log_handler)
        logger.setLevel(log_level)
        local_log = basic_log_handler

        # Return the file descriptor of this file
        return basic_log_handler.stream.fileno()

    def quit(self):
        """Close the local log file at program exit"""
        global local_log
        if local_log:
            print "Closing local_log ..", local_log
            local_log.close()

    def set_human_format(self):
        """Set the output as human format"""
        global human_timestamp_log
        human_timestamp_log = True

logger = Log()
