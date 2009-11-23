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

from item import Item, Items

class Plugin(Item):
    id = 1#0 is always special in database, so we do not take risk here
    my_type = 'plugin'

    properties={'plugin_name' : {'required':True},
                'plugin_type' : {'required':True}
                }

    running_properties = {}

    
    macros = {}


    #For debugging purpose only (nice name)
    def get_name(self):
        return self.plugin_name


class Plugins(Items):
    name_property = "plugin_name"
    inner_class = Plugin

    def linkify(self):
        pass


    #We look for contacts property in contacts and
    def explode(self):
        pass
