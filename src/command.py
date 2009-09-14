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


class Command:
    id = 0
    def __init__(self, params={}):
        self.id = self.__class__.id
        self.__class__.id += 1
        for key in params:
            setattr(self, key, params[key])

    def pythonize(self):
        self.command_name = self.command_name.strip()

    def clean(self):
        pass

    def __str__(self):
        return str(self.__dict__)



#This class is use when a service, contact or host define
#a command with args.
class CommandCall:
    id = 0
    def __init__(self, commands, call):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.call = call
        tab = call.split('!')
        self.command = tab[0]
        self.args = tab[1:]
        self.command=commands.find_cmd_by_name(self.command)
        if self.command is not None:
            self.valid = True
        else:
            self.valid = False
        #print "Call:", call, 'To:', self.command, 'and', self.args


    def is_valid(self):
        return self.valid


    def __str__(self):
        return str(self.__dict__)
        #return "%d %s" % (self.command, self.args)

    def get_name(self):
        return self.call


class Commands:
    def __init__(self, commands):
        self.commands = {}
        for c in commands:
            self.commands[c.id] = c

    
    def __str__(self):
        s = ''
        for c in self.commands.values():
            s += str(c)
        return s

    
    def find_cmd_id_by_name(self, name):
        for id in self.commands:
            if self.commands[id].command_name == name:
                return id
        return None

    def find_cmd_by_name(self, name):
        id = self.find_cmd_id_by_name(name)
        if id is not None:
            return self.commands[id]
        else:
            return None

