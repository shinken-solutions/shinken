# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012:
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
import re
import collections
from heapq import nsmallest
from operator import itemgetter


from livestatus_query import LiveStatusQuery
from livestatus_wait_query import LiveStatusWaitQuery
from livestatus_command_query import LiveStatusCommandQuery

CACHE_GLOBAL_STATS = 0
CACHE_GLOBAL_STATS_WITH_STATETYPE = 1
CACHE_HOST_STATS = 2
CACHE_SERVICE_STATS = 3

class Counter(dict):
    'Mapping where default values are zero'
    def __missing__(self, key):
        return 0

class LFU(object):
    def __init__(self, maxsize=100):
        self.storage = {}
        self.maxsize = maxsize
        self.hits = self.misses = 0
        self.use_count = Counter()           # times each key has been accessed
        self.kwd_mark = object()             # separate positional and keyword args

    def clear(self):
        self.storage = {}
        self.use_count = Counter()
        self.hits = self.misses = 0

    def get(self, key):
        self.use_count[key] += 1
        try:
            result = self.storage[key]
            self.hits += 1
        except KeyError:
            result = []
            self.misses += 1
        return result

    def put(self, key, data):
        self.storage[key] = data
        if len(self.storage) > self.maxsize:
            for key, _ in nsmallest(maxsize // 10, self.use_count.iteritems(), key=itemgetter(1)):
                del self.storage[key], self.use_count[key]
        pass

class LiveStatusQueryCache:

    """A class describing a livestatus query cache."""

    def __init__(self):
        self.categories = []
        # CACHE_GLOBAL_STATS
        self.categories.append(LFU())
        # CACHE_GLOBAL_STATS_WITH_STATETYPE
        self.categories.append(LFU())
        self.enabled = True

    def disable(self):
        self.enabled = False

    def invalidate_category(self, category):
        """
        Throw away all cached results of a certain class.
        For example, if there is a state change, we must recalculate
        the data for the tactical overview.
        """
        try:
            print "i wipe sub-cache", category
            self.categories[category].clear()
        except Exception:
            pass

    def wipeout(self):
        if not self.enabled:
            return
        for cat in range(len(self.categories)):
            print "WIPEOUT CAT", cat
            self.categories[cat].clear()

    def get_cached_query(self, data):
        if not self.enabled:
            return (False, [])
        print "I SEARCH THE CACHE FOR", data
        cacheable, category, key = self.strip_query(data)
        if self.categories[category].get(key):
            print "CACHE HIT"
        return (cacheable, self.categories[category].get(key))

    def split_command(self, line, splits=1):
        """Create a list from the words of a line"""
        return line.split(' ', splits)

    def split_option(self, line, splits=1):
        """Like split_commands, but converts numbers to int data type"""
        x = map (lambda i: (i.isdigit() and int(i)) or i, [token.strip() for token in re.split(r"[\s]+", line, splits)])
        return x

    def split_option_with_columns(self, line):
        """Split a line in a command and a list of words"""
        cmd, columns = self.split_option(line)
        return cmd, [c for c in re.compile(r'\s+').split(columns)]

    def strip_table_from_column(self, column):
        """Cut off the table name, because it is possible
        to say service_state instead of state"""
        bygroupmatch = re.compile('(\w+)by.*group').search(self.table)
        if bygroupmatch:
            return re.sub(re.sub('s$', '', bygroupmatch.group(1)) + '_', '', column, 1)
        else:
            return re.sub(re.sub('s$', '', self.table) + '_', '', column, 1)


    def prepare_data(self, data):
        """
        Reformat the lines of a query so that they are a list of tuples
        where the first element is the keyword
        """
        formal_line = []
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET':
                formal_line.append((keyword, self.split_command(line)[1]))
            elif keyword == 'Columns': # Get the names of the desired columns
                _, columns = self.split_option_with_columns(line)
                formal_line.append((keyword, columns))
            elif keyword == 'ResponseHeader':
                _, responseheader = self.split_option(line)
                formal_line.append((keyword, responseheader))
            elif keyword == 'OutputFormat':
                _, outputformat = self.split_option(line)
                formal_line.append((keyword, outputformat))
            elif keyword == 'KeepAlive':
                _, keepalive = self.split_option(line)
                formal_line.append((keyword, keepalive))
            elif keyword == 'ColumnHeaders':
                _, columnheaders = self.split_option(line)
                formal_line.append((keyword, columnheaders))
            elif keyword == 'Limit':
                _, limit = self.split_option(line)
                formal_line.append((keyword, limit))
            elif keyword == 'Filter':
                try:
                    _, attribute, operator, reference = re.split(r"[\s]+", line, 3)
                except:
                    _, attribute, operator = re.split(r"[\s]+", line, 2)
                    reference = ''
                formal_line.append((keyword, attribute, operator, reference))
            elif keyword == 'And':
                _, andnum = self.split_option(line)
                formal_line.append((keyword, andnum))
            elif keyword == 'Or':
                _, ornum = self.split_option(line)
                formal_line.append((keyword, ornum))
            elif keyword == 'StatsGroupBy':
                _, columns = self.split_option_with_columns(line)
                formal_line.append((keyword, columns))
            elif keyword == 'Stats':
                try:
                    _, attribute, operator, reference = self.split_option(line, 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference.startswith('as '):
                        attribute, operator = operator, attribute
                    elif attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference == '=':
                        attribute, operator = operator, attribute
                        reference = ''
                except:
                    _, attribute, operator = self.split_option(line, 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std']:
                        attribute, operator = operator, attribute
                    reference = ''
                formal_line.append((keyword, attribute, operator, reference))
            elif keyword == 'StatsAnd':
                _, andnum = self.split_option(line)
                formal_line.append((keyword, andnum))
            elif keyword == 'StatsOr':
                _, ornum = self.split_option(line)
                formal_line.append((keyword, ornum))
            elif keyword == 'Separators':
                _, sep1, sep2, sep3, sep4 = line.split(' ', 5)
                formal_line.append((keyword, sep1, sep2, sep3, sep4))
            elif keyword == 'Localtime':
                _, client_localtime = self.split_option(line)
                # NO # formal_line.append((keyword, client_localtime))
            else:
                print "Received a line of input which i can't handle : '%s'" % line
                formal_line.append((keyword, 'Received a line of input which i can\'t handle: %s' % line))
        return formal_line



    def strip_query(self, data):
        cacheable = True
        category = CACHE_GLOBAL_STATS
        formal_data = self.prepare_data(data)
        if 'Columns' in [f[0] for f in formal_data]:
            if [c for c in [f[1] for f in formal_data if f[0] == 'Columns'][0] if c.endswith('state_type')]:
                category = CACHE_GLOBAL_STATS_WITH_STATETYPE
        if 'Filter' in [f[0] for f in formal_data]:
            if 'time' in [f[1] for f in formal_data if f[0] == 'Filter']:
                # That's a showstopper. We can't cache time-critical
                # informations, because within one second a lot of things
                # can change.
                cacheable = False
     
        if cacheable:
            return (cacheable, category, hash(str(formal_data)))
        else:
            return (False, None, None)

            

    def find_query(self, data):
        pass

    def query_hash(self, data):
        pass

    def query_hash_with_time(self, data):
        pass

    def cache_query(self, data, result):
        """Puts the result of a livestatus query into the cache."""

        if not self.enabled:
            return
        _, category, key = self.strip_query(data)
        print "I PUT IN THE CACHE FOR", key
        self.categories[category].put(key, result)
        print self.prepare_data(data)

    def impact_assessment(self, brok, obj):
        """
        Find out if there are changes to the object which will affect
        the validity of cached data.
        """
        if not self.enabled:
            return
        try:
            if brok.data['state_id'] != obj.state_id:
                print "DETECTED STATECHANGE", obj
                self.invalidate_category(CACHE_GLOBAL_STATS)
            if brok.data['state_type_id'] != obj.state_type_id:
                print "DETECTED STATETYPECHANGE", obj
                self.invalidate_category(CACHE_GLOBAL_STATS_WITH_STATETYPE)
            print obj.state_id, obj.state_type_id, brok.data['state_id'], brok.data['state_type_id']
        except Exception:
            pass

