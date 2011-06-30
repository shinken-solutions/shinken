#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


LOGCLASS_INFO         = 0 # all messages not in any other class
LOGCLASS_ALERT        = 1 # alerts: the change service/host state
LOGCLASS_PROGRAM      = 2 # important programm events (restart, ...)
LOGCLASS_NOTIFICATION = 3 # host/service notifications
LOGCLASS_PASSIVECHECK = 4 # passive checks
LOGCLASS_COMMAND      = 5 # external commands
LOGCLASS_STATE        = 6 # initial or current states
LOGCLASS_INVALID      = -1 # never stored
LOGCLASS_ALL          = 0xffff
LOGOBJECT_INFO        = 0
LOGOBJECT_HOST        = 1
LOGOBJECT_SERVICE     = 2
LOGOBJECT_CONTACT     = 3


class Logline(dict):
    """A class which represents a line from the logfile
    
    Public functions:
    fill -- Attach host and/or service objects to a Logline object
    
    """
    
    def __init__(self, cursor, row):
        for idx, col in enumerate(cursor.description):
            setattr(self, col[0], row[idx])


    def fill(self, hosts, services, columns):
        """Attach host and/or service objects to a Logline object
        
        Lines describing host or service events only contain host_name
        and/or service_description. This method finds the corresponding
        objects and adds them to the line as attributes log_host
        and/or log_service
        
        """
        if self.logobject == LOGOBJECT_HOST:
            try:
                setattr(self, 'log_host', hosts[self.host_name])
            except:
                pass
        elif self.logobject == LOGOBJECT_SERVICE:
            try:
                setattr(self, 'log_host', hosts[self.host_name])
                setattr(self, 'log_service', services[self.host_name + self.service_description])
            except:
                pass
        return self
