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

from shinken.autoslots import AutoSlots
from shinken.property import StringProp, BoolProp

# Ok, slots are fun : you cannot set the __autoslots__
# on the same class you use, fun isn't it? So we define*
# a dummy useless class to get such :)
class DummyCommandCall(object):
    pass

#This class is use when a service, contact or host define
#a command with args.
class CommandCall(DummyCommandCall):
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    #__slots__ = ('id', 'call', 'command', 'valid', 'args', 'poller_tag',
    #             'reactionner_tag', 'module_type', '__dict__')
    id = 0
    my_type = 'CommandCall'

    properties = {
        'call':            StringProp(),
        'command':         StringProp(),
        'poller_tag':      StringProp(default='None'),
        'reactionner_tag': StringProp(default='None'),
        'module_type':     StringProp(default=None),
        'valid' :          BoolProp(default=False),
        'args' :           StringProp(default=[]),
    }


    def __init__(self, commands, call, poller_tag='None', reactionner_tag='None'):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.call = call
        tab = call.split('!')
        self.command = tab[0]
        self.args = tab[1:]
        self.command = commands.find_by_name(self.command.strip())
        if self.command is not None:
            self.valid = True
        else:
            self.valid = False
            self.command = tab[0]
        if self.valid:
            #If the host/service do not give an override poller_tag, take
            #the one of the command
            self.poller_tag = poller_tag #from host/service
            self.reactionner_tag = reactionner_tag
            self.module_type = self.command.module_type
            if self.valid and poller_tag is 'None':
                self.poller_tag = self.command.poller_tag #from command if not set
            # Same for reactionner tag
            if self.valid and reactionner_tag is 'None':
                self.reactionner_tag = self.command.reactionner_tag #from command if not set



    def is_valid(self):
        return self.valid


    def __str__(self):
        return str(self.__dict__)


    def get_name(self):
        return self.call

