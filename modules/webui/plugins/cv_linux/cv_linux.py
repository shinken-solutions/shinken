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

from shinken.webui.bottle import redirect
from shinken.misc.perfdata import PerfDatas

### Will be populated by the UI with it's own value
app = None

def find_disks(h):
    all_disks = []
    disks_state = 'UNKNOWN'
    s = h.find_service_by_name('Disks')
    print "Service found", s.get_full_name()
    if not s:
        return disks_state,all_disks
    disks_state = s.state
    p = PerfDatas(s.perf_data)
    print "PERFDATA", p, p.__dict__
    for m in p:
        print "KEY", m
        # Skip void disks?
        if not m.name or m.value is None or m.max is None or m.max == 0:
            continue
        # Skip device we don't care about
        if m.name == '/dev' or m.name.startswith('/sys/'):
            continue

        pct = 100*float(m.value)/m.max
        pct = int(pct)
        print m.value, m.max, pct
        
        all_disks.append((m.name, pct))

    return disks_state,all_disks


def get_memory(h):

    mem_state = swap_state = 'UNKNOWN'
    
    s = h.find_service_by_name('Memory')
    print "Service found", s.get_full_name()
    if not s:
        return (mem_state,swap_state,0,0)

    mem_state = swap_state = s.state
    # Now grep perfdata in it
    p = PerfDatas(s.perf_data)
    print "PERFDATA", p, p.__dict__
    mem = 0
    swap = 0
    
    if 'ram_used' in p:
        m = p['ram_used']
        # Maybe it's an invalid metric?
        if m.name and m.value is not None and m.max is not None and m.max != 0:
            # Classic pct compute
            pct = 100*float(m.value)/m.max
            mem = int(pct)
            print "Mem", m.value, m.max, pct

    if 'swap_used' in p:
        m = p['swap_used']
        # Maybe it's an invalid metric?
        if m.name and m.value is not None and m.max is not None and m.max != 0:
            # Classic pct compute
            pct = 100*float(m.value)/m.max
            swap = int(pct)
            print "Swap", m.value, m.max, pct

    return mem_state,swap_state,mem,swap



def get_cpu(h):
    cpu_state = 'UNKNOWN'
    s = h.find_service_by_name('Cpu')
    print "Service found", s.get_full_name()
    if not s:
        return cpu_state,0

    cpu_state = s.state
    # Now perfdata
    p = PerfDatas(s.perf_data)
    print "PERFDATA", p, p.__dict__
    cpu = 0
    
    if 'cpu_prct_used' in p:
        m = p['cpu_prct_used']
        # Maybe it's an invalid metric?
        if m.name and m.value is not None:
            cpu = m.value
            print "Cpu", m.value

    return cpu_state, cpu


def compute_worst_state(d):
    _ref = {'OK':0, 'UP':0, 'DOWN':3, 'UNREACHABLE':1, 'UNKNOWN':1, 'CRITICAL':3, 'WARNING':2, 'PENDING' :1}
    cur_level = _ref[d['global']]
    for (k,v) in d.iteritems():
        level = _ref[v]
        cur_level = max(cur_level, level)
    return {3:'CRITICAL', 2:'WARNING', 1:'UNKNOWN', 0:'OK'}[cur_level]


def get_page(hname):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")

    # Ok, we can lookup it
    h = app.datamgr.get_host(hname)

    all_perfs = {"swap": 0, "all_disks": [], "cpu": 0, "memory": 0}
    all_states = {"disks": "UNKNOWN", "global": "UNKNOWN", "swap": "UNKNON", "memory": "UNKNOWN", "cpu": "UNKNOWN"}

    print "\n"*5, "Find host?", h
    if h:
        # Set the host state firt
        all_states["global"] = h.state
        # First look at disks
        disks_state, all_disks = find_disks(h)
        all_perfs['all_disks'] = all_disks
        all_states["disks"] = disks_state
        # Then memory
        mem_state, swap_state, mem,swap = get_memory(h)
        all_perfs["memory"] = mem
        all_perfs["swap"] = swap
        all_states['swap'] = swap_state
        all_states['memory'] = mem_state
        # And CPU too
        all_states['cpu'], all_perfs['cpu'] = get_cpu(h)
        all_states["global"] = compute_worst_state(all_states)
        

    print "ALL PERFS", all_perfs
    
    return {'app': app, 'elt': h, 'all_perfs':all_perfs, 'all_states':all_states}




# Void plugin
pages = {get_page: {'routes': ['/cv/linux/:hname'], 'view': 'cv_linux', 'static': True}}
