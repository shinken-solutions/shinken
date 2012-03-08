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


import re
import time
from heapq import nsmallest
from operator import itemgetter

"""
There are several categories for queries. Their main difference is the kind
of event which invalidates the corresponding cache.

- CACHE_IMPOSSIBLE

- CACHE_PROGRAM_STATIC
applies to queries which ask for version numbers etc.

- CACHE_GLOBAL_STATS
applies to stats queries which ask for state only and don't refer to a specific host/service.
invalidated by a state change (check_result_brok)

- CACHE_GLOBAL_STATS_WITH_STATETYPE
the same, but takes hard/soft states into account.
invalidated by a state change 
invalidated by a state_type change 

- CACHE_GLOBAL_STATS_WITH_STATUS
applies to queries which ask for status (in_downtime/active/pasive/...)
invalidated by changes in status update broks

- CACHE_HOST_STATS

- CACHE_SERVICE_STATS

- CACHE_IRREVERSIBLE_HISTORY
applies to queries which want to read log data from a time in the past.
If the columns are not of any type which can change later, this query
can be cached forever.

"""
CACHE_IMPOSSIBLE = 0
CACHE_PROGRAM_STATIC = 1
CACHE_GLOBAL_STATS = 2
CACHE_GLOBAL_STATS_WITH_STATETYPE = 3
CACHE_HOST_STATS = 4
CACHE_SERVICE_STATS = 5
CACHE_IRREVERSIBLE_HISTORY = 6

def has_not_more_than(list1, list2):
    return len(set(list1).difference(set(list2))) == 0

class Counter(dict):
    """
    This is a special kind of dictionary. It is used to store the usage number
    for each key. For non-existing keys it simply returns 0.
    Methods __init__ and __getitem__ are only needed until that happy day
    when we finally get rid of Python 2.4
    """
    def __init__(self, default_factory=None, *a, **kw): 
        dict.__init__(self, *a, **kw) 
 
    def __getitem__(self, key): 
        try: 
            return dict.__getitem__(self, key) 
        except KeyError: 
            self[key] = 0
            return self.__missing__(key) 

    def __missing__(self, key):
        return 0

class LFUCacheMiss(Exception):
    pass

class LFU(object):
    """
    This class implements a dictionary which has a limited number of elements.
    Whenever the maximum number of elements is reached during a write operation
    the element which was read least times is deleted.
    It was inspired by 
    http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/
    but LFU is much more simpler.
    """
    def __init__(self, maxsize=100):
        self.storage = {}
        self.maxsize = maxsize
        self.hits = self.misses = 0
        self.use_count = Counter()           # times each key has been accessed

    def clear(self):
        self.storage = {}
        self.use_count = Counter()
        self.hits = self.misses = 0

    def get(self, key):
        self.use_count[key] += 1
        try:
            result = self.storage[key]
            print "CACHE HIT"
            self.hits += 1
        except KeyError:
            result = []
            self.misses += 1
            raise LFUCacheMiss
        return result

    def put(self, key, data):
        self.storage[key] = data
        if len(self.storage) > self.maxsize:
            for key, _ in nsmallest(self.maxsize // 10, self.use_count.iteritems(), key=itemgetter(1)):
                del self.storage[key], self.use_count[key]
        pass

    def __str__(self):
        text = 'LFU-------------------\n'
        try:
            text += 'hit rate %.2f%%\n' % (100 * self.hits / (self.hits + self.misses))
        except ZeroDivisionError:
            text += 'hit rate 0%\n'
        for k in self.storage:
            text += 'key %10s (%d used)\n' % (str(k), self.use_count[k])
        return text
        

class QueryData(object):
    """
    This class implements a more "machine-readable" form of a livestatus query.
    The lines of a query text are split up in a list of tuples,
    where the first element is the lql statement and the remaining elements 
    are columns, attributes, operators etc.
    It's main purpose is to provide methods which are used to rank the query
    in specific categories.
    """
    def __init__(self, data):
        self.data = data
        self.category = CACHE_IMPOSSIBLE
        self.keyword_counter = Counter()
        self.structure(data)
        self.key = hash(str(self.structured_data))
        self.is_stats = self.keyword_counter['Stats'] > 0
        self.client_localtime = int(time.time())
        self.stats_columns = [f[1] for f in self.structured_data if f[0] == 'Stats']
        self.filter_columns = [f[1] for f in self.structured_data if f[0] == 'Filter']
        self.columns = [x for f in self.structured_data if f[0] == 'Columns' for x in f[1]]
        self.categorize()

    def __str__(self):
        text = "table %s\n" % self.table
        text += "columns %s\n" % self.columns
        text += "stats_columns %s\n" % self.stats_columns
        text += "filter_columns %s\n" % self.filter_columns
        text += "is_stats %s\n" % self.is_stats
        text += "is_cacheable %s\n" % str(self.category != CACHE_IMPOSSIBLE)
        return text

    def structure(self, data):
        """
        Reformat the lines of a query so that they are a list of tuples
        where the first element is the keyword
        """
        self.structured_data = []
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET':
                self.table = self.split_command(line)[1]
                self.structured_data.append((keyword, self.split_command(line)[1]))
            elif keyword == 'Columns': # Get the names of the desired columns
                _, columns = self.split_option_with_columns(line)
                self.structured_data.append((keyword, columns))
            elif keyword == 'ResponseHeader':
                _, responseheader = self.split_option(line)
                self.structured_data.append((keyword, responseheader))
            elif keyword == 'OutputFormat':
                _, outputformat = self.split_option(line)
                self.structured_data.append((keyword, outputformat))
            elif keyword == 'KeepAlive':
                _, keepalive = self.split_option(line)
                self.structured_data.append((keyword, keepalive))
            elif keyword == 'ColumnHeaders':
                _, columnheaders = self.split_option(line)
                self.structured_data.append((keyword, columnheaders))
            elif keyword == 'Limit':
                _, limit = self.split_option(line)
                self.structured_data.append((keyword, limit))
            elif keyword == 'Filter':
                try:
                    _, attribute, operator, reference = re.split(r"[\s]+", line, 3)
                except:
                    _, attribute, operator = re.split(r"[\s]+", line, 2)
                    reference = ''
                if reference != '_REALNAME':
                    self.structured_data.append((keyword, attribute, operator, reference))
            elif keyword == 'And':
                _, andnum = self.split_option(line)
                self.structured_data.append((keyword, andnum))
            elif keyword == 'Or':
                _, ornum = self.split_option(line)
                self.structured_data.append((keyword, ornum))
            elif keyword == 'Negate':
                self.structured_data.append((keyword, ))
            elif keyword == 'StatsGroupBy':
                _, columns = self.split_option_with_columns(line)
                self.structured_data.append((keyword, columns))
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
                self.structured_data.append((keyword, attribute, operator, reference))
            elif keyword == 'StatsAnd':
                _, andnum = self.split_option(line)
                self.structured_data.append((keyword, andnum))
            elif keyword == 'StatsOr':
                _, ornum = self.split_option(line)
                self.structured_data.append((keyword, ornum))
            elif keyword == 'Separators':
                _, sep1, sep2, sep3, sep4 = line.split(' ', 5)
                self.structured_data.append((keyword, sep1, sep2, sep3, sep4))
            elif keyword == 'Localtime':
                _, self.client_localtime = self.split_option(line)
                # NO # self.structured_data.append((keyword, client_localtime))
            else:
                print "Received a line of input which i can't handle : '%s'" % line
                self.structured_data.append((keyword, 'Received a line of input which i can\'t handle: %s' % line))
            self.keyword_counter[keyword] += 1

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

    def columns(self):
        try:
            return set([l for l in self.structured_data if l[0] == 'Columns'][1])
        except Exception:
            return set([])

    def is_a_closed_chapter(self):
        """
        When the query is asking for log events from a time interval in the
        past, we can assume that the response will be a good candidate for
        caching. A precondition is, that only attributes are involved, which
        can not change over time. (ex. current_host_num_critical_services)
        """
        logline_elements = ['attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'message', 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type']
        logline_elements.extend(['current_host_groups', 'current_service_groups'])
        if self.table == 'log':
            limits = sorted([(f[2], int(f[3])) for f in self.structured_data if f[0] == 'Filter' and f[1] == 'time'], key=lambda x: x[1])
             
            if len(limits) == 2 and limits[1][1] <= int(time.time()) and limits[0][0].startswith('>') and limits[1][0].startswith('<'):
                if has_not_more_than(self.columns, logline_elements):
                    return True
        return False

    def categorize(self):
        """
        Analyze the formalized query (which table, which columns, which
        filters, stats or not,...) and find a suitable category.
        """
        # self.table, self.structured_data
        if self.table == 'status' and has_not_more_than(self.columns, ['livestatus_version', 'program_version', 'program_start']):
            self.category = CACHE_PROGRAM_STATIC
        elif not self.keyword_counter['Filter'] and self.table == 'host' and has_not_more_than(self.columns, ['name', 'custom_variable_names', 'custom_variable_values', 'services']):
            self.category = CACHE_GLOBAL_STATS
        elif self.table == 'log' and self.is_stats and has_not_more_than(self.stats_columns, ['state']):
            # and only 1 timefilter which is >=
            self.category = CACHE_GLOBAL_STATS
        elif self.table == 'services' and self.is_stats and has_not_more_than(self.stats_columns, ['state']):
            # and only 1 timefilter which is >=
            self.category = CACHE_GLOBAL_STATS
        elif self.is_a_closed_chapter():
            self.category = CACHE_IRREVERSIBLE_HISTORY
        elif self.table == 'services' and not self.is_stats and has_not_more_than(self.columns, ['host_name', 'description', 'state', 'state_type']):
            self.category = CACHE_SERVICE_STATS
        else:
            pass
            print "i cannot cache this", self



class LiveStatusQueryCache(object):
    """
    A class describing a collection of livestatus query caches.
    As we have several categories of queries, we also have several caches.
    The validity of each of it can be influenced by different changes through
    update broks.
    """

    def __init__(self):
        self.categories = []
        # CACHE_GLOBAL_STATS
        self.categories.append(LFU())
        # CACHE_GLOBAL_STATS_WITH_STATETYPE
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
        self.categories.append(LFU())
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
            #print "i wipe sub-cache", category
            self.categories[category].clear()
        except Exception:
            pass

    def wipeout(self):
        if not self.enabled:
            return
        for cat in range(len(self.categories)):
            self.categories[cat].clear()

    def get_cached_query(self, data):
        if not self.enabled:
            return (False, False, [])
        query = QueryData(data)
        #print "I SEARCH THE CACHE FOR", query.category, query.key, data
        try:
            return (query.category != CACHE_IMPOSSIBLE, True, self.categories[query.category].get(query.key))
        except LFUCacheMiss:
            return (query.category != CACHE_IMPOSSIBLE, False, [])

    def cache_query(self, data, result):
        """Puts the result of a livestatus query into the cache."""

        if not self.enabled:
            return
        query = QueryData(data)
        #print "I PUT IN THE CACHE FOR", query.category, query.key
        self.categories[query.category].put(query.key, result)

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
                self.invalidate_category(CACHE_SERVICE_STATS)
            if brok.data['state_type_id'] != obj.state_type_id:
                print "DETECTED STATETYPECHANGE", obj
                self.invalidate_category(CACHE_GLOBAL_STATS_WITH_STATETYPE)
                self.invalidate_category(CACHE_SERVICE_STATS)
            print obj.state_id, obj.state_type_id, brok.data['state_id'], brok.data['state_type_id']
        except Exception:
            pass

