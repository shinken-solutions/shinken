#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from shinken.util import safe_print
from shinken.misc.perfdata import PerfDatas


# Will try to return a dict with:
# lnk : link to add in this perfdata thing
# title : text to show on it
# metrics : list of ('html color', percent) like [('#68f', 35), ('white', 64)]
def get_perfometer_table_values(elt):
    # first try to get the command name called
    cmd = elt.check_command.call.split('!')[0]
    print "Looking for perfometer value for command", cmd
    

    tab = {'check_http' : manage_check_http_command,
           'check_ping' : manage_check_ping_command,
           'check_tcp' : manage_check_tcp_command,
           'check_ftp' : manage_check_tcp_command,
        }

    f = tab.get(cmd, None)
    if f:
        return f(elt)

    return None



def manage_check_http_command(elt):
    safe_print('Get check_http perfdata of', elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if not 'time' in p:
        print "No time in p"
        return None

    m = p['time']
    v = m.value
    if not v:
        print "No value, I bailout"
        return None

    # Pourcent of ok should be time/10s
    pct = 100 * (v / 10)
    # go to int
    pct = int(pct)
    # But at least 1%
    pct = max(1, pct)
    #And max to 100%
    pct = min(pct, 100)
    lnk = '#'
    metrics = [('#68f', pct), ('white', 100-pct)]
    title = '%ss' % v
    print "HTTP: return", {'lnk' : lnk, 'metrics' : metrics, 'title' : title}
    return {'lnk' : lnk, 'metrics' : metrics, 'title' : title}



def manage_check_ping_command(elt):
    safe_print('Get check_ping perfdata of', elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if not 'rta' in p:
        print "No rta in p"
        return None

    m = p['rta']
    v = m.value
    crit = m.critical
    if not v or not crit:
        print "No value, I bailout"
        return None

    # Pourcent of ok should be time/10s
    pct = 100 * (v / crit)
    # go to int
    pct = int(pct)
    # But at least 1%
    pct = max(1, pct)
    #And max to 100%
    pct = min(pct, 100)
    lnk = '#'
    metrics = [('#68f', pct), ('white', 100-pct)]
    title = '%sms' % v
    print "HTTP: return", {'lnk' : lnk, 'metrics' : metrics, 'title' : title}
    return {'lnk' : lnk, 'metrics' : metrics, 'title' : title}




def manage_check_tcp_command(elt):
    safe_print('Get check_tcp perfdata of', elt.get_full_name())
    p = PerfDatas(elt.perf_data)
    if not 'time' in p:
        print "No time in p"
        return None

    m = p['time']
    v = m.value

    if not v or not m.max:
        print "No value, I bailout"
        return None

    # Pourcent of ok should be time/10s
    pct = 100 * (v / m.max)
    # go to int
    pct = int(pct)
    # But at least 1%
    pct = max(1, pct)
    #And max to 100%
    pct = min(pct, 100)
    lnk = '#'
    metrics = [('#68f', pct), ('white', 100-pct)]
    title = '%ss' % v
    print "HTTP: return", {'lnk' : lnk, 'metrics' : metrics, 'title' : title}
    return {'lnk' : lnk, 'metrics' : metrics, 'title' : title}
