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


from item import Item, Items

from shinken.property import StringProp
from shinken.eventhandler import EventHandler
from shinken.macroresolver import MacroResolver


class Discoveryrun(Item):
    id = 1 #0 is always special in database, so we do not take risk here
    my_type = 'discoveryrun'

    properties = Item.properties.copy()
    properties.update({
        'discoveryrun_name':            StringProp (),
        'discoveryrun_command':         StringProp (),
    })

    running_properties = Item.running_properties.copy()
    running_properties.update({
        'current_launch': StringProp(default=None),
    })

    # Output name
    def get_name(self):
        return self.discoveryrun_name

    # Get an eventhandler object and launch it
    def launch(self, timeout=300):
        m = MacroResolver()
        data = []
        cmd = m.resolve_command(self.discoveryrun_command, data)
        self.current_launch = EventHandler(cmd, timeout=timeout)
        self.current_launch.execute()

    def check_finished(self):
        max_output = 10**9
        #print "Max output", max_output
        self.current_launch.check_finished(max_output)

    # Look if the current launch is done or not
    def is_finished(self):
        if self.current_launch == None:
            return True
        if self.current_launch.status in ('done', 'timeout'):
            return True
        return False
        
    # we use an EventHandler object, so we have output with a single line
    # and longoutput with the rest. We just need to return all
    def get_output(self):
        return '\n'.join([self.current_launch.output, self.current_launch.long_output])

        


class Discoveryruns(Items):
    name_property = "discoveryrun_name"
    inner_class = Discoveryrun


    def linkify(self, commands):
        for r in self:
            r.linkify_one_command_with_commands(commands, 'discoveryrun_command')
