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

from shinken.brok import Brok
from shinken.property import StringProp, BoolProp, IntegerProp
from shinken.autoslots import AutoSlots
from shinken.commandcall import CommandCall

# Ok, slots are fun : you cannot set the __autoslots__
# on the same class you use, fun isn't it? So we define*
# a dummy useless class to get such :)
class DummyCommand(object):
    pass

class Command(DummyCommand):
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    id = 0
    my_type = "command"

    properties = {
        'command_name': StringProp(fill_brok=['full_status']),
        'command_line': StringProp(fill_brok=['full_status']),
        'poller_tag':   StringProp(default='None'),
        'reactionner_tag':   StringProp(default='None'),
        'module_type':  StringProp(default=None),
    }

    def __init__(self, params={}):
        setattr(self, 'id', self.__class__.id)
        #self.id = self.__class__.id
        self.__class__.id += 1
        for key in params:
            setattr(self, key, params[key])
        if not hasattr(self, 'poller_tag'):
            self.poller_tag = 'None'
        if not hasattr(self, 'reactionner_tag'):
            self.reactionner_tag = 'None'
        if not hasattr(self, 'module_type'):
            # If the command satr with a _, set the module_type
            # as the name of the command, without the _
            if getattr(self, 'command_line', '').startswith('_'):
                module_type = getattr(self, 'command_line', '').split(' ')[0]
                # and we remove the first _
                self.module_type = module_type[1:]
            # If no command starting with _, be fork :)
            else:
                self.module_type = 'fork'


    def pythonize(self):
        self.command_name = self.command_name.strip()


    def clean(self):
        pass


    def __str__(self):
        return str(self.__dict__)


    #Get a brok with initial status
    def get_initial_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        data = {'id' : self.id}

        self.fill_data_brok_from(data, 'full_status')
        b = Brok('initial_'+my_type+'_status', data)
        return b


    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        #Now config properties
        for prop, entry in cls.properties.items():
            #Is this property intended for brokking?
#            if 'fill_brok' in entry[prop]:
            if brok_type in entry.fill_brok:
                if hasattr(self, prop):
                    data[prop] = getattr(self, prop)
                #elif 'default' in entry[prop]:
                #    data[prop] = entry.default





class Commands(object):
    def __init__(self, commands):
        self.commands = {}
        for c in commands:
            self.commands[c.id] = c


    def __iter__(self):
        return self.commands.itervalues()


    def __str__(self):
        s = ''
        for c in self.commands.values():
            s += str(c)
        return s


    def find_cmd_id_by_name(self, name):
        for id in self.commands:
            if getattr(self.commands[id], 'command_name', '') == name:
                return id
        return None

    def find_cmd_by_name(self, name):
        id = self.find_cmd_id_by_name(name)
        if id is not None:
            return self.commands[id]
        else:
            return None
