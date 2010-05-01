#!/usr/bin/python
#Copyright (C) 2010 Gabes Jean, naparuba@gmail.com
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

class Comment:
    id = 1

    #Adds a comment to a particular service. If the "persistent" field 
    #is set to zero (0), the comment will be deleted the next time
    #Nagios is restarted. Otherwise, the comment will persist 
    #across program restarts until it is deleted manually.
    def __init__(self, ref, persistent, author, comment, comment_type, entry_type, source, expires, expire_time):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.ref = ref #pointer to srv or host we are apply
        self.entry_time = int(time.time())
        self.persistent = persistent
        self.author = author
        self.comment = comment
        #Now the hidden attributes
        #HOST_COMMENT=1,SERVICE_COMMENT=2
        self.comment_type = comment_type
        #USER_COMMENT=1,DOWNTIME_COMMENT=2,FLAPPING_COMMENT=3,ACKNOWLEDGEMENT_COMMENT=4
        self.entry_type = entry_type
        #COMMENTSOURCE_INTERNAL=0,COMMENTSOURCE_EXTERNAL=1
        self.source = source
        self.expires = expires
        self.expire_time = expire_time
        self.can_be_deleted = False


    def __str__(self):
        return "%s Comment id=%d %s" % (active, self.id, self.comment)

