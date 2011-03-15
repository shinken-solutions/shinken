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

import re

from shinken.objects.item import Item, Items
from shinken.property import IntegerProp, StringProp, ListProp

class Discoveryrun(Item):
    id = 1 #0 is always special in database, so we do not take risk here
    my_type = 'discoveryrun'

    properties = {
        'discoveryrun_name':            StringProp (),
        'discoveryrun_command':         StringProp (),
    }

    running_properties = {}

    macros = {}

    # Output name
    def get_name(self):
        return self.discoveryrun_name



class Discoveryruns(Items):
    name_property = "discoveryrun_name"
    inner_class = Discoveryrun

