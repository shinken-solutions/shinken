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

import re
from shinken.util import to_best_int_float

perfdata_split_pattern = re.compile('([^=]+=\S+)')
# TODO: Improve this regex to not match strings like this:
# 'metric=45+e-456.56unit;50;80;0;45+-e45e-'
metric_pattern = \
    re.compile(
        '^([^=]+)=([\d\.\-\+eE]+)([\w\/%]*)'
        ';?([\d\.\-\+eE:~@]+)?;?([\d\.\-\+eE:~@]+)?;?([\d\.\-\+eE]+)?;?([\d\.\-\+eE]+)?;?\s*'
    )
quote_pattern = re.compile("^'(.+)'$")
replace1_pattern = re.compile('\1')


# If we can return an int or a float, or None
# if we can't
def guess_int_or_float(val):
    try:
        return to_best_int_float(val)
    except Exception, exp:
        return None


# Class for one metric of a perf_data
class Metric:
    def __init__(self, s):
        self.name = self.value = self.uom = \
            self.warning = self.critical = self.min = self.max = None
        s = s.strip()
        # print "Analysis string", s
        r = metric_pattern.match(s)
        if r:
            # Strip outer quotes, and replace double quotes with single
            self.name = re.sub(r"^'(.+)'$", r'\1', r.group(1)).replace("''", "'")
            self.value = guess_int_or_float(r.group(2))
            self.uom = r.group(3)
            self.warning = guess_int_or_float(r.group(4))
            self.critical = guess_int_or_float(r.group(5))
            self.min = self.min_supplied = guess_int_or_float(r.group(6))
            self.max = self.max_supplied = guess_int_or_float(r.group(7))
            # print 'Name', self.name
            # print "Value", self.value
            # print "Res", r
            # print r.groups()
            if self.uom == '%':
                self.min = 0 if self.min is None else self.min
                self.max = 100 if self.max is None else self.max

    def __str__(self):
        # Restore double quotes in nae
        name = self.name.replace("'", "''")
        # Quote whole name if it contains a space
        if " " in name:
            name = "'" + name + "'"
        min = self.min_supplied
        max = self.max_supplied
        components = ["%s=%s%s" % (name, self.value, self.uom), self.warning, self.critical, min, max]
        while components[-1] is None:
            components.pop()
        return ";".join(map(lambda v: "" if v is None else str(v), components))


class PerfDatas:
    def __init__(self, s):
        s = s or ''
        elts = perfdata_split_pattern.findall(s)
        elts = [e for e in elts if e != '']
        self.metrics = {}
        for e in elts:
            m = Metric(e)
            if m.name is not None:
                self.metrics[m.name] = m

    def __iter__(self):
        return self.metrics.itervalues()

    def __len__(self):
        return len(self.metrics)

    def __getitem__(self, key):
        return self.metrics[key]

    def __contains__(self, key):
        return key in self.metrics

