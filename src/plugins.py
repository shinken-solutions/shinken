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


#This class is use to mnager plugins and call callback

from item import Items
from plugin import Plugin

class Plugins(Items):
    name_property = "name" #use for the search by name
    inner_class = Plugin #use for know what is in items

    def register(self):
        ndomod = Ndomod()
	ndomod.init('')
        self.items.append(ndomod)

    
    def go_for(self, callback, data):
        for plug in self:
            plug.go_for(callback, data)

