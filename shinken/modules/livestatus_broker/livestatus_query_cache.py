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

class QueryData(object):
    def __init__(self, data):
        self.data = data
        self.category = CACHE_IMPOSSIBLE
        self.keyword_counter = Counter()
        self.structure(data)
        self.key = hash(str(self.structured_data))
        self.is_stats = self.keyword_counter['Stats'] > 0
        self.stats_columns = [f[1] for f in self.structured_data if f[0] == 'Stats']
        self.filter_columns = [item for sublist in [f[1] for f in self.structured_data if f[0] == 'Filter'] for item in sublist]
        self.categorize()
        print self
        print self.category

    def __str__(self):
        text = "table %s\n" % self.table
        text += "columns %s\n" % self.columns
        text += "stats_columns %s\n" % self.stats_columns
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
                _, client_localtime = self.split_option(line)
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
        if self.keyword_counter['Filter'] == 2:
            pass
            # there must be a >/>= and a </<= and the interval must be 
            # in the past
        return False

    def categorize(self):
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
            
        # if log and <> time is an interval in the past
        # and we have the usual alert history columns
        # then we can cache it, global and for specific host/service
        elif self.table == 'log' and self.is_a_closed_chapter() and has_not_more_than(self.columns, 'class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups'.split(' ')):
            category = CACHE_IRREVERSIBLE_HISTORY



class LiveStatusQueryCache(object):

    """A class describing a livestatus query cache."""

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
        query = QueryData(data)
        if self.categories[query.category].get(query.key):
            print "CACHE HIT"
        return (query.category != CACHE_IMPOSSIBLE, self.categories[query.category].get(query.key))



            

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
        query = QueryData(data)
        print "I PUT IN THE CACHE FOR", query.key
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
            if brok.data['state_type_id'] != obj.state_type_id:
                print "DETECTED STATETYPECHANGE", obj
                self.invalidate_category(CACHE_GLOBAL_STATS_WITH_STATETYPE)
            print obj.state_id, obj.state_type_id, brok.data['state_id'], brok.data['state_type_id']
        except Exception:
            pass

