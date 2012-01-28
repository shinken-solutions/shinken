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

from item import Item, Items
from service import Service
from host import Host 
from shinken.property import StringProp, ListProp
from copy import copy

class Discoveryrule(Item):
    id = 1 #0 is always special in database, so we do not take risk here
    my_type = 'discoveryrule'

    properties = Item.properties.copy()
    properties.update({
        'discoveryrule_name':    StringProp (),
        'creation_type':         StringProp (default='service'),
#        'check_command':         StringProp (),
#        'service_description':   StringProp (),
#        'use':                   StringProp(),
    })

    running_properties = {
        'configuration_errors': ListProp(default=[]),
        }

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

        self.matches = {} # for matching rules
        self.not_matches = {} # for rules that should NOT match
        self.writing_properties = {}

        # Get the properties of the Class we want
        if not 'creation_type' in params:
            params['creation_type'] = 'service'

        map = {'service' : Service, 'host' : Host}
        t =  params['creation_type']
        if not t in map:
            return
        tcls = map[t]

        # In my own property : 
        #  -> in __dict__
        # In the properties of the 'creation_type' Class:
        #  -> in self.writing_properties
        # if not, in matches or not match (if key starts
        # with a !, it's a not rule)
        # -> in self.matches or self.not_matches
        # in writing properties if start with + (means 'add this')
        for key in params:
            # Some key are quite special
            if key in ['use']:
                self.writing_properties[key] = params[key]
            elif key.startswith('+'):
                self.writing_properties[key] = params[key]
            elif key in cls.properties:
                setattr(self, key, params[key])
            elif key in tcls.properties:
                self.writing_properties[key] = params[key]
            else:
                if key.startswith('!'):
                    key = key.split('!')[1]
                    self.not_matches[key] = params['!'+key]
                else:
                    self.matches[key] = params[key]

        # Then running prop :)
        cls = self.__class__
        # adding running properties like latency, dependency list, etc
        for prop, entry in cls.running_properties.items():
            # Copy is slow, so we check type
            # Type with __iter__ are list or dict, or tuple.
            # Item need it's own list, so qe copy
            val = entry.default
            if hasattr(val, '__iter__'):
                setattr(self, prop, copy(val))
            else:
                setattr(self, prop, val)
            #eatch istance to have his own running prop!


    # Output name
    def get_name(self):
        try:
            return self.discoveryrule_name
        except AttributeError:
            return "UnnamedDiscoveryRule"


    # Try to see if the key,value is matching one or
    # our rule. If value got ',' we must look for each value
    # If one match, we quit
    # We can find in matches or not_matches
    def is_matching(self, key, value, look_in='matches'):
        if look_in == 'matches':
            d = self.matches
        else:
            d = self.not_matches
        # If we do not even have the key, we bailout
        if not key.strip() in d:
            return False

        # Get my matching patern
        m = d[key]
        if ',' in m:
            matchings = [mt.strip() for mt in m.split(',')]
        else:
            matchings = [m]
        
        # Split the alue by , too
        values = value.split(',')
        for m in matchings:
            for v in values:
                #print "Try to match", m, v
                if re.search(m, v):
                    return True
        return False


    # Look if we match all discovery data or not
    # a disco data look as a list of (key, values)
    def is_matching_disco_datas(self, datas):
        # If we got not data, no way we can match
        if len(datas) == 0:
            return False
        
        # First we look if it's possible to match
        # we must match All self.matches things
        for m in self.matches:
            #print "Compare to", m
            match_one = False
            for (k, v) in datas.iteritems():
                # We found at least one of our match key
                if m == k:
                    if self.is_matching(k, v):
                        #print "Got matching with", m, k, v
                        match_one = True
                        continue
            if not match_one:
                # It match none
                #print "Match none, FAlse"
                return False
        #print "It's possible to be OK"

        # And now look if ANY of not_matches is reach. If so
        # it's False
        for m in self.not_matches:
            #print "Compare to NOT", m
            match_one = False
            for (k, v) in datas.iteritems():
                #print "K,V", k,v
                # We found at least one of our match key
                if m == k:
                    #print "Go loop"
                    if self.is_matching(k, v, look_in='not_matches'):
                        #print "Got matching with", m, k, v
                        match_one = True
                        continue
            if match_one:
                #print "I match one, I quit"
                return False

        # Ok we match ALL rules in self.matches
        # and NONE of self.not_matches, we can go :)
        return True
                    

        


class Discoveryrules(Items):
    name_property = "discoveryrule_name"
    inner_class = Discoveryrule

