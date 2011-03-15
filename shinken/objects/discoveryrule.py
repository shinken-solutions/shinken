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

class Discoveryrule(Item):
    id = 1 #0 is always special in database, so we do not take risk here
    my_type = 'discoveryrule'

    properties = {
        'discoveryrule_name':    StringProp (),
        'check_command':         StringProp (),
        'service_description':   StringProp (),
        'use':                   StringProp(),
    }

    running_properties = {}

    macros = {}


    # The init of a discovery will set the property of 
    # Discoveryrule.properties as in setattr, but all others
    # will be in a list because we need to have all names
    # and not lost all in __dict__
    def __init__(self, params={}):
        cls = self.__class__
        
        # We have our own id of My Class type :)
        # use set attr for going into the slots
        # instead of __dict__ :)
        setattr(self, 'id', cls.id)
        cls.id += 1

        self.matches = {} # for custom variables

        # In property : in __dict__
        # if not, in matches
        for key in params:
            if key in cls.properties:
                setattr(self, key, params[key])
            else:
                self.matches[key] = params[key]


    # Output name
    def get_name(self):
        return self.discoveryrule_name


    # Try to see if the key,value is matching one or
    # our rule. If value got ',' we must look for each value
    def is_matching(self, key, value):
        # If we do not even have the key, we bailout
        if not key.strip() in self.matches:
            return False
        # Get my matching patern
        m = self.matches[key]
        if ',' in m:
            matchings = [mt.strip() for mt in m.split(',')]
        else:
            matchings = [m]
        for m in matchings:
            if re.search(m, value):
                return True
        
    # Look if we match all discovery data or not
    # a disco data look as a list of (key, values)
    def is_matching_all_disco_data(self, datas):
        if len(datas) == 0:
            return False
        for (k, v) in datas:
            if not self.is_matching(k, v):
                return False
        return True
        


class Discoveryrules(Items):
    name_property = "discoveryrule_name"
    inner_class = Discoveryrule

