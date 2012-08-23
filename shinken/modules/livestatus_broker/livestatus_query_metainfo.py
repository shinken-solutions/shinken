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

import re
import time
from counter import Counter
from livestatus_stack import LiveStatusStack
from shinken.log import logger


def has_not_more_than(list1, list2):
    return len(set(list1).difference(set(list2))) == 0

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

"""
Sometimes it is possible to see from the list of filters that this query's purpose
s to find one specific host or service (ot the services of one specific host).
The service is therefore tagged with a hint type, helping an upper layer to limit
the number of objects to process.
"""
HINT_NONE = 0
HINT_HOST = 1
HINT_HOSTS = 2
HINT_SERVICES_BY_HOST = 3
HINT_SERVICE = 4
HINT_SERVICES_BY_HOSTS = 5
HINT_SERVICES = 6
HINT_HOSTS_BY_GROUP = 7
HINT_SERVICES_BY_HOSTGROUP = 8
HINT_SERVICES_BY_GROUP = 9


class LiveStatusQueryMetainfoFilterStack(LiveStatusStack):
    """
    This is a filterstack which produces a text representation of
    a and/or-filter-tree, similar to sql.
    It can be used some time for text analysis.
    """

    def __init__(self, *args, **kw):
        self.type = 'text'
        self.__class__.__bases__[0].__init__(self, *args, **kw)

    def not_elements(self):
        top_filter = self.get_stack()
        negate_filter = '(NOT ' + top_filter + ')'
        self.put_stack(negate_filter)

    def and_elements(self, num):
        """Take num filters from the stack, and them and put the result back"""
        if num > 1:
            filters = []
            for _ in range(num):
                filters.append(self.get_stack())
            and_filter = '(' + (' AND ').join(filters) + ')'
            self.put_stack(and_filter)

    def or_elements(self, num):
        """Take num filters from the stack, or them and put the result back"""
        if num > 1:
            filters = []
            for _ in range(num):
                filters.append(self.get_stack())
            or_filter = '(' + (' OR ').join(filters) + ')'
            self.put_stack(or_filter)

    def get_stack(self):
        """Return the top element from the stack or a filter which is always true"""
        if self.qsize() == 0:
            return ''
        else:
            return self.get()


class LiveStatusQueryMetainfo(object):
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
        self.cache_category = CACHE_IMPOSSIBLE
        self.query_hints = {
            'target': HINT_NONE,
        }
        self.keyword_counter = Counter()
        self.metainfo_filter_stack = LiveStatusQueryMetainfoFilterStack()
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
        text += "filter_columns %s\n" % list(set(self.filter_columns))
        text += "is_stats %s\n" % self.is_stats
        text += "is_cacheable %s\n" % str(self.cache_category != CACHE_IMPOSSIBLE)
        return text

    def add_filter(self, operator, attribute, reference):
        self.metainfo_filter_stack.put_stack(self.make_text_filter(operator, attribute, reference))

    def add_filter_and(self, andnum):
        self.metainfo_filter_stack.and_elements(andnum)

    def add_filter_or(self, ornum):
        self.metainfo_filter_stack.or_elements(ornum)

    def add_filter_not(self):
        self.metainfo_filter_stack.not_elements()

    def make_text_filter(self, operator, attribute, reference):
        return '%s%s%s' % (attribute, operator, reference)

    def structure(self, data):
        """
        Reformat the lines of a query so that they are a list of tuples
        where the first element is the keyword
        """
        self.structured_data = []
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the:
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET':
                self.table = self.split_command(line)[1]
                self.structured_data.append((keyword, self.split_command(line)[1]))
            elif keyword == 'Columns':  # Get the names of the desired columns
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
            elif keyword == 'AuthUser':
                _, authuser = self.split_option(line)
                self.structured_data.append((keyword, authuser))
                self.query_hints['authuser'] = authuser
            elif keyword == 'Filter':
                try:
                    _, attribute, operator, reference = re.split(r"[\s]+", line, 3)
                except:
                    _, attribute, operator = re.split(r"[\s]+", line, 2)
                    reference = ''
                self.metainfo_filter_stack.put_stack(self.make_text_filter(operator, attribute, reference))
                if reference != '_REALNAME':
                    attribute = self.strip_table_from_column(attribute)
                    self.structured_data.append((keyword, attribute, operator, reference))
            elif keyword == 'And':
                _, andnum = self.split_option(line)
                self.structured_data.append((keyword, andnum))
                self.metainfo_filter_stack.and_elements(andnum)
            elif keyword == 'Or':
                _, ornum = self.split_option(line)
                self.structured_data.append((keyword, ornum))
                self.metainfo_filter_stack.or_elements(ornum)
            elif keyword == 'Negate':
                self.structured_data.append((keyword,))
                self.metainfo_filter_stack.not_elements()
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
                logger.warning("[Livestatus Query Metainfo] Received a line of input which i can't handle: '%s'" % line)
                self.structured_data.append((keyword, 'Received a line of input which i can\'t handle: %s' % line))
            self.keyword_counter[keyword] += 1
        self.metainfo_filter_stack.and_elements(self.metainfo_filter_stack.qsize())
        self.flat_filter = self.metainfo_filter_stack.get_stack()

    def split_command(self, line, splits=1):
        """Create a list from the words of a line"""
        return line.split(' ', splits)

    def split_option(self, line, splits=1):
        """Like split_commands, but converts numbers to int data type"""
        x = map(lambda i: (i.isdigit() and int(i)) or i, [token.strip() for token in re.split(r"[\s]+", line, splits)])
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
        filters, stats or not,...) and find a suitable cache_category.
        """
        # self.table, self.structured_data
        if self.table == 'status' and has_not_more_than(self.columns, ['livestatus_version', 'program_version', 'program_start']):
            self.cache_category = CACHE_PROGRAM_STATIC
        elif not self.keyword_counter['Filter'] and self.table == 'host' and has_not_more_than(self.columns, ['name', 'custom_variable_names', 'custom_variable_values', 'services']):
            self.cache_category = CACHE_GLOBAL_STATS
        elif self.table == 'log' and self.is_stats and has_not_more_than(self.stats_columns, ['state']):
            # and only 1 timefilter which is >=
            self.cache_category = CACHE_GLOBAL_STATS
        elif self.table == 'services' and self.is_stats and has_not_more_than(self.stats_columns, ['state']):
            # and only 1 timefilter which is >=
            self.cache_category = CACHE_GLOBAL_STATS
        elif self.is_a_closed_chapter():
            self.cache_category = CACHE_IRREVERSIBLE_HISTORY
        elif self.table == 'services' and not self.is_stats and has_not_more_than(self.columns, ['host_name', 'description', 'state', 'state_type']):
            self.cache_category = CACHE_SERVICE_STATS
        else:
            pass
            logger.debug("[Livestatus Query Metainfo] I cannot cache this %s" % str(self))

        # Initial implementation only respects the = operator (~ may be an option in the future)
        all_filters = sorted([str(f[1]) for f in self.structured_data if (f[0] == 'Filter')])
        eq_filters = sorted([str(f[1]) for f in self.structured_data if (f[0] == 'Filter' and f[2] == '=')])
        unique_eq_filters = sorted({}.fromkeys(eq_filters).keys())
        ge_contains_filters = sorted([str(f[1]) for f in self.structured_data if (f[0] == 'Filter' and f[2] == '>=')])
        unique_ge_contains_filters = sorted({}.fromkeys(ge_contains_filters).keys())
        logger.debug("[Livestatus Query Metainfo] ge_contains_filters: %s" % str(ge_contains_filters))
        logger.debug("[Livestatus Query Metainfo] unique_ge_contains_filters: %s" % str(unique_ge_contains_filters))
        if [f for f in self.structured_data if f[0] == 'Negate']:
            # HANDS OFF!!!!
            # This might be something like:
            # NOT (description=test_ok_00 AND host_name=test_host_005)
            # Using hints to preselect the hosts/services will result in
            # absolutely wrong results.
            pass
        elif self.table == 'hosts' or self.table == 'hostsbygroup':
            # Do we have exactly 1 Filter, which is 'name'?
            if eq_filters == ['name']:
                if len(eq_filters) == len([f for f in self.structured_data if (f[0] == 'Filter' and f[1] == 'name')]):
                    self.query_hints['target'] = HINT_HOST
                    self.query_hints['host_name'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[2] == '=')][0]
                # this helps: thruk_host_detail, thruk_host_status_detail, thruk_service_detail, nagvis_host_icon
            elif unique_eq_filters ==  ['name']:
                # we want a lot of services selected by
                # Filter: host_name
                # Filter: host_name
                # ...
                # Or: n
                hosts = []
                only_hosts = True
                try:
                    num_hosts = 0
                    for i, _ in enumerate(self.structured_data):
                        if self.structured_data[i][0] == 'Filter' and self.structured_data[i][1] == 'host_name':
                            if self.structured_data[i+1][0] == 'Filter' and self.structured_data[i+1][1] == 'host_name':
                                num_hosts += 1
                                hosts.append(self.structured_data[i][3])
                            elif self.structured_data[i+1][0] == 'Or' and self.structured_data[i+1][1] == num_hosts + 1:
                                num_hosts += 1
                                hosts.append(self.structured_data[i][3])
                                only_hosts = True
                            else:
                                only_hosts = False
                except Exception, exp:
                    only_hosts = False
                if only_hosts:
                    if len(hosts) == len(filter(lambda x: x[0] == 'Filter' and x[1] == 'host_name', self.structured_data)):
                        hosts = list(set(hosts))
                        hosts.sort()
                        self.query_hints['target'] = HINT_HOSTS
                        self.query_hints['host_name'] = hosts
                # this helps: nagvis host icons
            elif ge_contains_filters == ['groups']:
                # we want the all the hosts in a hostgroup
                if len(ge_contains_filters) == len([f for f in self.structured_data if (f[0] == 'Filter' and (f[1] == 'groups' or f[1] == 'name'))]):
                    self.query_hints['target'] = HINT_HOSTS_BY_GROUP
                    self.query_hints['hostgroup_name'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[2] == '>=')][0]
                # this helps: nagvis hostgroup
        elif self.table == 'services' or self.table == 'servicesbygroup' or self.table == 'servicesbyhostgroup':
            if eq_filters == ['host_name']:
                # Do we have exactly 1 Filter, which is 'host_name'?
                # In this case, we want the services of this single host
                if len(eq_filters) == len([f for f in self.structured_data if (f[0] == 'Filter' and f[1] == 'host_name')]):
                    self.query_hints['target'] = HINT_SERVICES_BY_HOST
                    self.query_hints['host_name'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[2] == '=')][0]
                # this helps: multisite_host_detail
            elif eq_filters == ['description', 'host_name']:
                # We want one specific service
                self.query_hints['target'] = HINT_SERVICE
                self.query_hints['host_name'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[1] == 'host_name' and f[2] == '=')][0]
                self.query_hints['service_description'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[1] == 'description' and f[2] == '=')][0]
                # this helps: multisite_service_detail, thruk_service_detail, nagvis_service_icon
            elif unique_eq_filters ==  ['host_name']:
                # we want a lot of services selected by
                # Filter: host_name
                # Filter: host_name
                # ...
                # Or: n
                hosts = []
                only_hosts = True
                try:
                    num_hosts = 0
                    for i, _ in enumerate(self.structured_data):
                        if self.structured_data[i][0] == 'Filter' and self.structured_data[i][1] == 'host_name':
                            if self.structured_data[i+1][0] == 'Filter' and self.structured_data[i+1][1] == 'host_name':
                                num_hosts += 1
                                hosts.append(self.structured_data[i][3])
                            elif self.structured_data[i+1][0] == 'Or' and self.structured_data[i+1][1] == num_hosts + 1:
                                num_hosts += 1
                                hosts.append(self.structured_data[i][3])
                                only_hosts = True
                            else:
                                only_hosts = False
                except Exception, exp:
                    only_hosts = False
                if only_hosts:
                    if len(hosts) == len(filter(lambda x: x[0] == 'Filter' and x[1] == 'host_name', self.structured_data)):
                        hosts = list(set(hosts))
                        hosts.sort()
                        self.query_hints['target'] = HINT_SERVICES_BY_HOSTS
                        self.query_hints['host_name'] = hosts
                # this helps: nagvis host icons
            elif unique_eq_filters ==  ['description', 'host_name']:
                # we want a lot of services selected by
                # Filter: host_name
                # Filter: service_description
                # And: 2
                services = []
                only_services = True
                try:
                    for i, _ in enumerate(self.structured_data):
                        if self.structured_data[i][0] == 'Filter' and self.structured_data[i][1] == 'host_name':
                            if self.structured_data[i+1][0] == 'Filter' and self.structured_data[i+1][1] == 'description' and self.structured_data[i+2][0] == 'And' and self.structured_data[i+2][1] == 2:
                                services.append((self.structured_data[i][3], self.structured_data[i+1][3]))
                            elif self.structured_data[i-1][0] == 'Filter' and self.structured_data[i-1][1] == 'description' and self.structured_data[i+1][0] == 'And' and self.structured_data[i+1][1] == 2:
                                services.append((self.structured_data[i][3], self.structured_data[i-1][3]))
                            else:
                                only_services = False
                                break
                except Exception, exp:
                    only_services = False
                if only_services:
                    if len(services) == len(filter(lambda x: x[0] == 'Filter' and x[1] == 'description', self.structured_data)):
#len([None for stmt in self.structured_data if stmt[0] == 'Filter' and stmt[1] == 'description']):
                        services = set(services)
                        hosts = set([svc[0] for svc in services])
                        # num_hosts < num_services / 2
                        # hint : hosts_names
                        if len(hosts) == 1:
                            self.query_hints['target'] = HINT_SERVICES_BY_HOST
                            self.query_hints['host_name'] = hosts[0]
                        else:
                            self.query_hints['target'] = HINT_SERVICES
                            self.query_hints['host_names_service_descriptions'] = services
            elif ge_contains_filters == ['groups']:
                # we want the all the services in a servicegroup
                logger.debug("[Livestatus Query Metainfo] structure_date: %s" % str(self.structured_data))
                if len(ge_contains_filters) == len([f for f in self.structured_data if (f[0] == 'Filter' and (f[1] == 'groups' or f[1] == 'description'))]):
                    self.query_hints['target'] = HINT_SERVICES_BY_GROUP
                    self.query_hints['servicegroup_name'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[2] == '>=')][0]
                # this helps: nagvis servicegroup
            elif ge_contains_filters == ['host_groups']:
                # we want the services of all the hosts in a hostgroup
                pass
                # Do we have exactly 1 Filter, which is 'host_name'?
                # In this case, we want the services of this single host
                if len(ge_contains_filters) == len([f for f in self.structured_data if (f[0] == 'Filter' and f[1].startswith('host'))]):
                    self.query_hints['target'] = HINT_SERVICES_BY_HOSTGROUP
                    self.query_hints['hostgroup_name'] = [f[3] for f in self.structured_data if (f[0] == 'Filter' and f[2] == '>=')][0]
                # this helps: nagvis hostgroup

