#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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

import os
import re
import traceback

from shinken.objects.item import Item, Items
from shinken.property import BoolProp, StringProp
from shinken.log import logger
from shinken.trigger_functions import objs, trigger_functions, set_value


class Trigger(Item):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'trigger'

    properties = Item.properties.copy()
    properties.update({'trigger_name': StringProp(fill_brok=['full_status']),
                       'code_src': StringProp(default='', fill_brok=['full_status']),
                       })

    running_properties = Item.running_properties.copy()
    running_properties.update({'code_bin': StringProp(default=None),
                               'trigger_broker_raise_enabled': BoolProp(default=False)
                               })

    # For debugging purpose only (nice name)
    def get_name(self):
        try:
            return self.trigger_name
        except AttributeError:
            return 'UnnamedTrigger'

    def compile(self):
        self.code_bin = compile(self.code_src, "<irc>", "exec")

    # ctx is the object we are evaluating the code. In the code
    # it will be "self".
    def eval(myself, ctx):
        self = ctx

        # Ok we can declare for this trigger call our functions
        for (n, f) in trigger_functions.iteritems():
            locals()[n] = f

        code = myself.code_bin  # Comment? => compile(myself.code_bin, "<irc>", "exec")
        try:
            exec code in dict(locals())
        except Exception as err:
            set_value(self, "UNKNOWN: Trigger error: %s" % err, "", 3)
            logger.error('%s Trigger %s failed: %s ; '
                         '%s' % (self.host_name, myself.trigger_name, err, traceback.format_exc()))


    def __getstate__(self):
        return {'trigger_name': self.trigger_name,
                'code_src': self.code_src,
                'trigger_broker_raise_enabled': self.trigger_broker_raise_enabled}

    def __setstate__(self, d):
        self.trigger_name = d['trigger_name']
        self.code_src = d['code_src']
        self.trigger_broker_raise_enabled = d['trigger_broker_raise_enabled']


class Triggers(Items):
    name_property = "trigger_name"
    inner_class = Trigger

    # We will dig into the path and load all .trig files
    def load_file(self, path):
        # Now walk for it
        for root, dirs, files in os.walk(path):
            for file in files:
                if re.search("\.trig$", file):
                    p = os.path.join(root, file)
                    try:
                        fd = open(p, 'rU')
                        buf = fd.read()
                        fd.close()
                    except IOError, exp:
                        logger.error("Cannot open trigger file '%s' for reading: %s", p, exp)
                        # ok, skip this one
                        continue
                    self.create_trigger(buf, file[:-5])

    # Create a trigger from the string src, and with the good name
    def create_trigger(self, src, name):
        # Ok, go compile the code
        t = Trigger({'trigger_name': name, 'code_src': src})
        t.compile()
        # Ok, add it
        self[t.id] = t
        return t

    def compile(self):
        for i in self:
            i.compile()

    def load_objects(self, conf):
        global objs
        objs['hosts'] = conf.hosts
        objs['services'] = conf.services
