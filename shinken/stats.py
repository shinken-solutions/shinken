#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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

import threading
import time

from log import logger

class Stats(object):
    def __init__(self):
        print "WTF REAPER"*100
        self.name = ''
        self.app = None
        self.stats = {}


    def launch_reaper_thread(self):
        self.reaper_thread = threading.Thread(None, target=self.reaper, name='stats-reaper')
        self.reaper_thread.daemon = True
        self.reaper_thread.start()


    def register(self, name, _type):
        self.name = name
        self.type = _type
        

    # Will increment a stat key, if None, start at 0
    def incr(self, k, v):
        _min, _max, nb, _sum = self.stats.get(k, (None, None, 0, 0))
        nb += 1
        _sum += v
        if _min is None or v < _min:
            _min = v
        if _max is None or v > _max:
            _max = v
        self.stats[k] = (_min, _max, nb, _sum)



    def reaper(self):
        while True:
            now = int(time.time())
            print "REAPER LOOP LOOP"
            logger.debug('REAPER loop')
            stats = self.stats
            self.stats = {}

            if len(stats) != 0:
                s = ', '.join(['%s:%s' % (k,v) for (k,v) in stats.iteritems()])
                logger.debug("REAPER: %s " % s)
            # If we are not in an initializer daemon we skip, we cannot have a real name, it sucks
            # to find the data after this
            if not self.name:
                time.sleep(10)
                continue

            logger.debug('REAPER we got a name')
            metrics = []
            for (k,e) in stats.iteritems():
                nk = '%s.%s' % (self.name, k)
                logger.debug('REAP %s:%s' % (nk, e))
                _min, _max, nb, _sum = e
                _avg = float(_sum) / nb
                # nb can't be 0 here and _min_max can't be None too
                s = '%s.avg %f %d' % (nk, _avg, now)
                metrics.append(s)
                s = '%s.min %f %d' % (nk, _min, now)
                metrics.append(s)
                s = '%s.max %f %d' % (nk, _max, now)
                metrics.append(s)
                s = '%s.count %f %d' % (nk, nb, now)
                metrics.append(s)

            logger.debug('REAPER metrics to send %s (%d)' % (metrics, len(str(metrics))) )
            time.sleep(10)


statsmgr = Stats()
