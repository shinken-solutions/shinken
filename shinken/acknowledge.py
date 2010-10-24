#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#Allows you to acknowledge the current problem for the specified service.
#By acknowledging the current problem, future notifications (for the same
#servicestate) are disabled.
class Acknowledge:
    id = 0

    #Allows you to acknowledge the current problem for the specified service.
    #By acknowledging the current problem, future notifications (for the
    #same servicestate) are disabled.
    #If the "sticky" option is set to one (1), the acknowledgement will remain
    #until the service returns to an OK state. Otherwise the acknowledgement
    #will automatically be removed when the service changes state. In this case
    #Web interfaces set a value of (2).
    #If the "notify" option is set to one (1), a notification will be sent out to
    #contacts indicating that the current service problem has been acknowledged.
    #If the "persistent" option is set to one (1), the comment associated with
    #the acknowledgement will survive across restarts of the Shinken process.
    #If not, the comment will be deleted the next time Nagios restarts.
    #"persistent" not only means "survive restarts", but also
    def __init__(self, ref, sticky, notify, persistent, author, comment):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.ref = ref #pointer to srv or host we are apply
        self.sticky = sticky
        self.notify = notify
        self.author = author
        self.comment = comment
