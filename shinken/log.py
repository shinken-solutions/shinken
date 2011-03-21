#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import time

from brok import Brok

obj = None
name = None
local_log = None

class Log:
    # We load the object where we will put log broks
    # with the 'add' method
    def load_obj(self, object, name_ = None):
        global obj
        global name
        obj = object
        name = name_

    # We enter a log message, we format it, and we add the log brok
    def log(self, message, format = None):
        global obj
        global name
        global local_log

        # If the daemon is launch with a non UTF8 shell
        # we can habe problem in printing
        try:
            print message
        except UnicodeEncodeError:
            print message.encode('ascii', 'ignore')

        if format is None:
            if name is None:
                # We format the log in UTF-8
                #message.decode('UTF-8', 'replace')
                s = u'[%d] %s\n' % (int(time.time()), message)
            else:
                s = u'[%d] [%s] %s\n' % (int(time.time()), name, message)
        else:
            s = format % message

        # We create and add the brok
        b = Brok('log', {'log' : s})
        obj.add(b)

        # If we want a local log write, do it
        if local_log is not None:
            local_log.write(s)
            local_log.flush()
            

    # The log can also write to a local file if need
    def register_local_log(self, path):
        global local_log
        local_log = open(path, 'a')
        

    # Clsoe the local log file at program exit
    def quit(self):
        global local_log
        if local_log:
            local_log.close()
        

logger = Log()
