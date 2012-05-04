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


import time
import os
import re

from shinken.objects.item import Item, Items
from shinken.misc.perfdata import PerfDatas
from shinken.property import BoolProp, IntegerProp, FloatProp, CharProp, StringProp, ListProp
from shinken.log import logger

objs = {'hosts' : [], 'services' : []}

def critical(obj, output):
    logger.debug("[trigger::%s] I am in critical for object" % obj.get_name())
    now = time.time()
    cls = obj.__class__
    i = obj.launch_check(now, force=True)
    for chk in obj.actions:
        if chk.id == i:
            logger.debug("[trigger] I founded the check I want to change")
            c = chk
            # Now we 'transform the check into a result'
            # So exit_status, output and status is eaten by the host
            c.exit_status = 2
            c.get_outputs(output, obj.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = now
            #self.sched.nb_check_received += 1
            # Ok now this result will be read by scheduler the next loop


def perf(obj, name):
    p = PerfDatas(obj.perf_data)
    if name in p:
        logger.debug("[trigger] I found the perfdata")
        return p[name].value
    logger.debug("[trigger] I am in perf command")
    return 1


def get_object(name):
    if not '/' in name:
        return objs['hosts'].find_by_name(name)
    else:
        elts = name.split('/', 1)
        return objs['services'].find_srv_by_name_and_hostname(elts[0], elts[1])
        


class Trigger(Item):
    id = 1 # 0 is always special in database, so we do not take risk here
    my_type = 'trigger'

    properties = Item.properties.copy()
    properties.update({'trigger_name':     StringProp(fill_brok=['full_status']),
                       'code_src':        StringProp(default='', fill_brok=['full_status']),
                       })

    running_properties = Item.running_properties.copy()
    running_properties.update({
            'code_bin':        StringProp(default=None),
    })


    #For debugging purpose only (nice name)
    def get_name(self):
        try:
            return self.trigger_name
        except AttributeError:
            return 'UnnamedTrigger'


#    def __init__(self, ref, code):
#        self.ref = ref
#        self.code = code.replace(r'\n', '\n').replace(r'\t', '\t')


    def compile(self):
        logger.debug("[trigger::%s] compiling trigger" %  self.get_name())
        self.code_bin = compile(self.code_src, "<irc>", "exec")        


    # ctx is the object we are evaluating the code. In the code
    # it will be "self".
    def eval(myself, ctx):
        logger.debug("[trigger::%s] running following code: %s" % (myself.get_name(), myself.code_src))
        self = ctx

        locals()['perf'] = perf
        locals()['critical'] = critical
        locals()['get_object'] = get_object

        code = myself.code_bin#compile(myself.code_bin, "<irc>", "exec")
        exec code in dict(locals())


    def __getstate__(self):
        return {'trigger_name' : self.trigger_name, 'code_src' : self.code_src}

    def __setstate__(self, d):
        self.trigger_name = d['trigger_name']
        self.code_src = d['code_src']


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
                        logger.debug("[trigger] reading trigger: %s" % buf)
                        fd.close()
                    except IOError, exp:
                        logger.error("Cannot open trigger file '%s' for reading: %s" % (p, exp))
                        # ok, skip this one
                        continue
                    self.create_trigger(buf, file[:-5])
        

    # Create a trigger from the string src, and with the good name
    def create_trigger(self, src, name):
        # Ok, go compile the code
        logger.debug("[trigger] creating a trigger named %s" % name)
        t = Trigger({'trigger_name' : name, 'code_src' : src})
        t.compile()
        # Ok, add it
        self[t.id] = t
        return t


    def compile(self):
        for i in self:
            i.compile()


    def load_objects(self, conf):
        logger.debug("[trigger] loading objects in the triggers")
        global objs
        objs['hosts'] = conf.hosts
        objs['services'] = conf.services
