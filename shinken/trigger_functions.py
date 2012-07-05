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

objs = {'hosts': [], 'services': []}
trigger_functions = {}

class declared(object):
    def __init__(self, f):
        self.f = f
        global functions
        n = f.func_name
        print "Adding the declared function", n, f
        trigger_functions[n] = f


    def __call__(self, *args):
        print "Calling", self.f.func_name, 'with', args
        return self.f(*args)


@declared                
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


@declared
def perf(obj_ref, metric_name):
    obj = get_object(obj_ref)
    p = PerfDatas(obj.perf_data)
    if metric_name in p:
        logger.debug("[trigger] I found the perfdata")
        return p[metric_name].value
    logger.debug("[trigger] I am in perf command")
    return 1


@declared
def get_object(ref):
    # Maybe it's already a real object, if so, return it :)
    if not isinstance(ref, basestring):
        return ref
    # Ok it's a string
    name = ref
    if not '/' in name:
        return objs['hosts'].find_by_name(name)
    else:
        elts = name.split('/', 1)
        return objs['services'].find_srv_by_name_and_hostname(elts[0], elts[1])

