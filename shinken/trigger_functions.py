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

import time
import re

from shinken.misc.perfdata import PerfDatas
from shinken.log import logger

objs = {'hosts': [], 'services': []}
trigger_functions = {}


class declared(object):
    """ Decorator to add function in trigger environnement
    """
    def __init__(self, f):
        self.f = f
        global functions
        n = f.func_name
        # logger.debug("Initializing function %s %s" % (n, f))
        trigger_functions[n] = f

    def __call__(self, *args):
        logger.debug("Calling %s with arguments %s", self.f.func_name, args)
        return self.f(*args)

@declared
def up(obj, output):
    """ Set a host in UP state
    """
    set_value(obj, output, None, 0)


@declared
def down(obj, output):
    """ Set a host in DOWN state
    """
    set_value(obj, output, None, 1)


@declared
def ok(obj, output):
    """ Set a service in OK state
    """
    set_value(obj, output, None, 0)


@declared
def warning(obj, output):
    """ Set a service in WARNING state
    """
    set_value(obj, output, None, 1)


@declared
def critical(obj, output):
    """ Set a service in CRITICAL state
    """
    set_value(obj, output, None, 2)


@declared
def unknown(obj, output):
    """ Set a service in UNKNOWN state
    """
    set_value(obj, output, None, 3)


@declared
def set_value(obj_ref, output=None, perfdata=None, return_code=None):
    """ Set output, state and perfdata to a service or host
    """
    obj = get_object(obj_ref)
    if not obj:
        return
    output = output or obj.output
    perfdata = perfdata or obj.perf_data
    if return_code is None:
        return_code = obj.state_id

    logger.debug("[trigger] Setting %s %s %s for object %s",
                 output,
                 perfdata,
                 return_code,
                 obj.get_full_name())

    if perfdata:
        output = output + ' | ' + perfdata

    now = time.time()
    cls = obj.__class__
    i = obj.launch_check(now, force=True)
    for chk in obj.checks_in_progress:
        if chk.id == i:
            logger.debug("[trigger] I found the check I want to change")
            c = chk
            # Now we 'transform the check into a result'
            # So exit_status, output and status is eaten by the host
            c.exit_status = return_code
            c.get_outputs(output, obj.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = now
            # IMPORTANT: tag this check as from a trigger, so we will not
            # loop in an infinite way for triggers checks!
            c.from_trigger = True
            # Ok now this result will be read by scheduler the next loop


@declared
def perf(obj_ref, metric_name):
    """ Get perf data from a service
    """
    obj = get_object(obj_ref)
    p = PerfDatas(obj.perf_data)
    if metric_name in p:
        logger.debug("[trigger] I found the perfdata")
        return p[metric_name].value
    logger.debug("[trigger] I am in perf command")
    return None


@declared
def get_custom(obj_ref, cname, default=None):
    """ Get custom varialbe from a service or a host
    """
    obj = get_objects(obj_ref)
    if not obj:
        return default
    cname = cname.upper().strip()
    if not cname.startswith('_'):
        cname = '_' + cname
    return obj.customs.get(cname, default)


@declared
def perfs(objs_ref, metric_name):
    """ TODO: check this description
        Get perfdatas from multiple services/hosts
    """
    objs = get_objects(objs_ref)
    r = []
    for o in objs:
        v = perf(o, metric_name)
        r.append(v)
    return r


@declared
def allperfs(obj_ref):
    """ Get all perfdatas from a service or a host
    """
    obj = get_object(obj_ref)
    p = PerfDatas(obj.perf_data)
    logger.debug("[trigger] I get all perfdatas")
    return dict([(metric.name, p[metric.name]) for metric in p])


@declared
def get_object(ref):
    """ Retrive object (service/host) from name
    """
    # Maybe it's already a real object, if so, return it :)
    if not isinstance(ref, basestring):
        return ref

    # Ok it's a string
    name = ref
    if '/' not in name:
        return objs['hosts'].find_by_name(name)
    else:
        elts = name.split('/', 1)
        return objs['services'].find_srv_by_name_and_hostname(elts[0], elts[1])


@declared
def get_objects(ref):
    """ TODO: check this description
        Retrive objects (service/host) from names
    """
    # Maybe it's already a real object, if so, return it :)
    if not isinstance(ref, basestring):
        return ref

    name = ref
    # Maybe there is no '*'? if so, it's one element
    if '*' not in name:
        return get_object(name)

    # Ok we look for spliting the host or service thing
    hname = ''
    sdesc = ''
    if '/' not in name:
        hname = name
    else:
        elts = name.split('/', 1)
        hname = elts[0]
        sdesc = elts[1]
    logger.debug("[trigger get_objects] Look for %s %s", hname, sdesc)
    res = []
    hosts = []
    services = []

    # Look for host, and if need, look for service
    if '*' not in hname:
        h = objs['hosts'].find_by_name(hname)
        if h:
            hosts.append(h)
    else:
        hname = hname.replace('*', '.*')
        p = re.compile(hname)
        for h in objs['hosts']:
            logger.debug("[trigger] Compare %s with %s", hname, h.get_name())
            if p.search(h.get_name()):
                hosts.append(h)

    # Maybe the user ask for justs hosts :)
    if not sdesc:
        return hosts

    for h in hosts:
        if '*' not in sdesc:
            s = h.find_service_by_name(sdesc)
            if s:
                services.append(s)
        else:
            sdesc = sdesc.replace('*', '.*')
            p = re.compile(sdesc)
            for s in h.services:
                logger.debug("[trigger] Compare %s with %s", s.service_description, sdesc)
                if p.search(s.service_description):
                    services.append(s)

    logger.debug("Found the following services: %s", services)
    return services
