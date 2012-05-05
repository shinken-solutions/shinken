#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import re
from copy import copy

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

    # The init of a discovery will set the property of 
    # Discoveryrun.properties as in setattr, but all others
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

        # In my own property : 
        #  -> in __dict__
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
            # each istance to have his own running prop!


    # Output name
    def get_name(self):
        try:
            return self.discoveryrun_name
        except AttributeError:
            return "UnnamedDiscoveryRun"


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
