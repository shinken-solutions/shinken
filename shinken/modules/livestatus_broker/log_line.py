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
