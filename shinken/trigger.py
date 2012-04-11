#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2011 :
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

from shinken.misc.perfdata import PerfDatas


def critical(obj, output):
    print "I am in critical for object", obj.get_name()
    now = time.time()
    cls = obj.__class__
    i = obj.launch_check(now, force=True)
    for chk in obj.actions:
        if chk.id == i:
            print 'I founded the check I want to change'
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
    p = PerfDatas(obj.perfdata)
    if name in p:
        print 'I found the perfdata'
        return p[name].value
    print 'I am in perf command'
    return 1


class Trigger(object):
    def __init__(self, ref, code):
        self.ref = ref
        self.code = code.replace(r'\n', '\n').replace(r'\t', '\t')


    def eval(myself):
        print 'WILL RUN THE CODE', myself.code
        self = myself.ref

        locals()['perf'] = perf
        locals()['critical'] = critical

        code = compile(myself.code, "<irc>", "exec")
        exec code in dict(locals())
        print 'after exec'
