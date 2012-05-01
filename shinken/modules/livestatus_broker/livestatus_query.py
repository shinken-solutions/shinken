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

import os
import re
import time
import copy
from mapping import table_class_map, find_filter_converter, list_livestatus_attributes, Problem
from livestatus_response import LiveStatusResponse
from livestatus_stack import LiveStatusStack
from livestatus_constraints import LiveStatusConstraints


class LiveStatusQueryError(Exception):
    messages = {
        200: 'OK',
        404: 'Invalid GET request, no such table \'%s\'',
        450: 'Invalid GET request, no such column \'%s\'',
        452: 'Completely invalid GET request \'%s\'',
    }
    pass

class LiveStatusQuery(object):

    my_type = 'query'

    def __init__(self, datamgr, query_cache, db, pnp_path, return_queue, counters):
        # Runtime data form the global LiveStatus object
        self.datamgr = datamgr
        self.query_cache = query_cache
        self.db = db
        self.pnp_path = pnp_path
        self.return_queue = return_queue
        self.counters = counters

        # Private attributes for this specific request
        self.response = LiveStatusResponse()
        self.raw_data = ''
        self.authuser = None
        self.table = None
        self.columns = []
        self.filtercolumns = []
        self.prefiltercolumns = []
        self.outputcolumns = []
        self.stats_group_by = []
        self.stats_columns = []
        self.aliases = []
        self.limit = None
        self.extcmd = False

        # Initialize the stacks which are needed for the Filter: and Stats:
        # filter- and count-operations
        self.filter_stack = LiveStatusStack()
        self.stats_filter_stack = LiveStatusStack()
        self.stats_postprocess_stack = LiveStatusStack()
        self.stats_query = False

        # When was this query launched?
        self.tic = time.time()
        # Clients can also send their local time with the request
        self.client_localtime = self.tic

        # This is mostly used in the Response.format... which needs to know
        # the class behind a queries table
        self.table_class_map = table_class_map

    def __str__(self):
        output = "LiveStatusRequest:\n"
        for attr in ["table", "columns", "filtercolumns", "prefiltercolumns", "aliases", "stats_group_by", "stats_query"]:
            output += "request %s: %s\n" % (attr, getattr(self, attr))
        return output

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
        return cmd, [self.strip_table_from_column(c) for c in re.compile(r'\s+').split(columns)]

    def strip_table_from_column(self, column):
        """Cut off the table name, because it is possible 
        to say service_state instead of state"""
        bygroupmatch = re.compile('(\w+)by.*group').search(self.table)
        if bygroupmatch:
            return re.sub(re.sub('s$', '', bygroupmatch.group(1)) + '_', '', column, 1)
        else:
            return re.sub(re.sub('s$', '', self.table) + '_', '', column, 1)


    def parse_input(self, data):
        """Parse the lines of a livestatus request.
        
        This function looks for keywords in input lines and
        sets the attributes of the request object
        
        """
        self.raw_data = data
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET': # Get the name of the base table
                _, self.table = self.split_command(line)
                if self.table not in table_class_map.keys():
                    raise LiveStatusQueryError(404, self.table)
            elif keyword == 'Columns': # Get the names of the desired columns
                _, self.columns = self.split_option_with_columns(line)
                self.response.columnheaders = 'off'
            elif keyword == 'ResponseHeader':
                _, responseheader = self.split_option(line)
                self.response.responseheader = responseheader
            elif keyword == 'OutputFormat':
                _, outputformat = self.split_option(line)
                self.response.outputformat = outputformat
            elif keyword == 'KeepAlive':
                _, keepalive = self.split_option(line)
                self.response.keepalive = keepalive
            elif keyword == 'ColumnHeaders':
                _, columnheaders = self.split_option(line)
                self.response.columnheaders = columnheaders
            elif keyword == 'Limit':
                _, self.limit = self.split_option(line)
            elif keyword == 'AuthUser':
                if self.table in ['hosts', 'hostgroups', 'services', 'servicegroups']:
                    _, self.authuser = self.split_option(line)
                # else self.authuser stays None and will be ignored
            elif keyword == 'Filter':
                try:
                    _, attribute, operator, reference = self.split_option(line, 3)
                except:
                    _, attribute, operator, reference = self.split_option(line, 2) + ['']
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    # Cut off the table name
                    attribute = self.strip_table_from_column(attribute)
                    # Some operators can simply be negated
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = { '!>' : '<=', '!>=' : '<', '!<' : '>=', '!<=' : '>' }[operator]
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    self.filtercolumns.append(attribute)
                    self.prefiltercolumns.append(attribute)
                    self.filter_stack.put_stack(self.make_filter(operator, attribute, reference))
                    if self.table == 'log':
                        self.db.add_filter(operator, attribute, reference)
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif keyword == 'And':
                _, andnum = self.split_option(line)
                # Take the last andnum functions from the stack
                # Construct a new function which makes a logical and
                # Put the function back onto the stack
                self.filter_stack.and_elements(andnum)
                if self.table == 'log':
                    self.db.add_filter_and(andnum)
            elif keyword == 'Or':
                _, ornum = self.split_option(line)
                # Take the last ornum functions from the stack
                # Construct a new function which makes a logical or
                # Put the function back onto the stack
                self.filter_stack.or_elements(ornum)
                if self.table == 'log':
                    self.db.add_filter_or(ornum)
            elif keyword == 'Negate':
                self.filter_stack.not_elements()
                if self.table == 'log':
                    self.db.add_filter_not()
            elif keyword == 'StatsGroupBy':
                _, stats_group_by = self.split_option_with_columns(line)
                self.filtercolumns.extend(stats_group_by)
                self.stats_group_by.extend(stats_group_by)
                # Deprecated. If your query contains at least one Stats:-header
                # then Columns: has the meaning of the old StatsGroupBy: header
            elif keyword == 'Stats':
                self.stats_query = True
                try:
                    _, attribute, operator, reference = self.split_option(line, 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference.startswith('as '):
                        attribute, operator = operator, attribute
                        _, alias = reference.split(' ')
                        self.aliases.append(alias)
                    elif attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference == '=':
                        # Workaround for thruk-cmds like: Stats: sum latency =
                        attribute, operator = operator, attribute
                        reference = ''
                except:
                    _, attribute, operator = self.split_option(line, 3)
                    if attribute in ['sum', 'min', 'max', 'avg', 'std']:
                        attribute, operator = operator, attribute
                    reference = ''
                attribute = self.strip_table_from_column(attribute)
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = { '!>' : '<=', '!>=' : '<', '!<' : '>=', '!<=' : '>' }[operator]
                    self.filtercolumns.append(attribute)
                    self.stats_columns.append(attribute)
                    self.stats_filter_stack.put_stack(self.make_filter(operator, attribute, reference))
                    self.stats_postprocess_stack.put_stack(self.make_filter('count', attribute, None))
                elif operator in ['sum', 'min', 'max', 'avg', 'std']:
                    self.stats_columns.append(attribute)
                    self.stats_filter_stack.put_stack(self.make_filter('dummy', attribute, None))
                    self.stats_postprocess_stack.put_stack(self.make_filter(operator, attribute, None))
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif keyword == 'StatsAnd':
                _, andnum = self.split_option(line)
                self.stats_filter_stack.and_elements(andnum)
            elif keyword == 'StatsOr':
                _, ornum = self.split_option(line)
                self.stats_filter_stack.or_elements(ornum)
            elif keyword == 'Separators':
                _, sep1, sep2, sep3, sep4 = line.split(' ', 5)
                self.response.separators = map(lambda x: chr(int(x)), [sep1, sep2, sep3, sep4])
            elif keyword == 'Localtime':
                _, self.client_localtime = self.split_option(line)
            elif keyword == 'COMMAND':
                _, self.extcmd = line.split(' ', 1)
            else:
                # This line is not valid or not implemented
                print "Received a line of input which i can't handle : '%s'" % line
                pass


    def launch_query(self):
        """ Prepare the request object's filter stacks """
        
        # The Response object needs to access the Query
        self.response.load(self)

        # A minimal integrity check
        if not self.table:
            return []

        # Ask the cache if this request was already answered under the same
        # circumstances.
        cacheable, cache_hit, cached_response = self.query_cache.get_cached_query(self.raw_data)
        if cache_hit:
            self.columns = cached_response['columns']
            self.response.columnheaders = cached_response['columnheaders']
            return cached_response['result']

        # Make columns unique
        self.filtercolumns = list(set(self.filtercolumns))
        self.prefiltercolumns = list(set(self.prefiltercolumns))
        self.stats_columns = list(set(self.stats_columns))

        if self.stats_query:
            if len(self.columns) > 0:
                # StatsGroupBy is deprecated. Columns: can be used instead
                self.stats_group_by = self.columns
            elif len(self.stats_group_by) > 0:
                self.columns = self.stats_group_by + self.stats_columns
            #if len(self.stats_columns) > 0 and len(self.columns) == 0:
            if len(self.stats_columns) > 0:
                self.columns = self.stats_columns + self.columns
        else:
            if len(self.columns) == 0:
                self.outputcolumns = list_livestatus_attributes(self.table)
            else:
                self.outputcolumns = self.columns

        # Make one big filter where the single filters are anded
        self.filter_stack.and_elements(self.filter_stack.qsize())

        # Get the function which implements the Filter: statements
        filter_func     = self.filter_stack.get_stack()
        without_filter  = len(self.filtercolumns) == 0
        cs = LiveStatusConstraints(filter_func, without_filter, self.authuser)

        try:
            # Remember the number of stats filters. We need these numbers as columns later.
            # But we need to ask now, because get_live_data() will empty the stack
            num_stats_filters = self.stats_filter_stack.qsize()
            if self.table == 'log':
                result = self.get_live_data_log(cs)
            else:
                # If the pnpgraph_present column is involved, then check
                # with each request if the pnp perfdata path exists
                if 'pnpgraph_present' in self.columns + self.filtercolumns + self.prefiltercolumns and self.pnp_path and os.access(self.pnp_path, os.R_OK):
                    self.pnp_path_readable = True
                else:
                    self.pnp_path_readable = False
                # Apply the filters on the broker's host/service/etc elements
          
                result = self.get_live_data(cs)
                
            if self.stats_query:
                self.columns = range(num_stats_filters)
                if self.stats_group_by:
                    self.columns = tuple(list(self.stats_group_by) + list(self.columns))
                if len(self.aliases) == 0:
                    #If there were Stats: staments without "as", show no column headers at all
                    self.response.columnheaders = 'off'
                else:
                    self.response.columnheaders = 'on'

            if self.stats_query:
                result = self.statsify_result(result)
                # statsify_result returns a dict with column numers as keys
            elif self.table == 'columns':
                # With stats_request set to True, format_output expects result
                # to be a list of dicts instead a list of objects
                self.stats_query = True

        except Exception, e:
            import traceback
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print e
            traceback.print_exc(32) 
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            result = []

        if cacheable and not cache_hit:
            # We cannot cache generators, so we must first read them into a list
            result = [r for r in result]
            # Especially for stats requests also the columns and headers
            # are modified, so we need to save them too.
            self.query_cache.cache_query(self.raw_data, {
                'result': result,
                'columns': self.columns,
                'columnheaders': self.response.columnheaders,
            })
            
        return result

    
    def get_hosts_or_services_livedata(self, cs):
        def gen_all(values):
            for val in values:
                yield val
            return
        def gen_filtered(values, filterfunc):
            for val in gen_all(values):
                if filterfunc(val):
                    yield val
            return
        
        # This is a generator which returns up to <limit> elements
        def gen_limit(values, maxelements):
            loopcnt = 1
            for val in gen_all(values):
                if loopcnt > maxelements:
                    return
                else:
                    yield val
                    loopcnt += 1
        # This is a generator which returns up to <limit> elements
        # which passed the filter. If the limit has been reached
        # it is no longer necessary to loop through the original list.
        def gen_limit_filtered(values, maxelements, filterfunc):
            for val in gen_limit(gen_filtered(values, filterfunc), maxelements):
                yield val
            return

        def gen_auth(values, authuser):
            for val in values:
                # this is probably too sloooow to be run in the innermost loop
                if authuser in [c.get_name() for c in val.contacts]:
                    yield val
            return

        items = getattr(self.datamgr.rg, self.table).__itersorted__()
        if cs.authuser:
            items = gen_auth(items, cs.authuser)
        if not cs.without_filter:
            items = gen_filtered(items, cs.filter_func)
        if self.limit:
            items = gen_limit(items, self.limit)
        return (i for i in items)
        if cs.without_filter and not self.limit:
            # Simply format the output
            return [x for x in items]
        elif cs.without_filter and self.limit:
            # Simply format the output of a subset of the objects
            return (
                y for y in (
                    gen_limit((x for x in items.__itersorted__()), self.limit)
                )
            )
        elif not cs.without_filter and not self.limit:
            # Filter the objects and format the output. At least hosts
            # and services are already sorted by name.
            return (
                x for x in getattr(self.datamgr.rg, self.table).__itersorted__()
                    if cs.filter_func(x)
            ) 
            #  some day.....
            #  pool = multiprocessing.Pool(processes=4)
            #  return pool.map(cs.filter_func, getattr(self.datamgr.rg, self.table).__itersorted__())
        elif not cs.without_filter and self.limit:

            return (
                y for y in (
                    gen_limit_filtered((x for x in getattr(self.datamgr.rg, self.table).__itersorted__()), self.limit, cs.filter_func)
                )
            )
    
    def get_hosts_livedata(self, cs):
        return self.get_hosts_or_services_livedata(cs)
    

    def get_services_livedata(self, cs):
        return self.get_hosts_or_services_livedata(cs)


    def get_simple_livedata(self, cs):
        return [obj for obj in getattr(self.datamgr.rg, self.table)]


    def get_filtered_livedata(self, cs):
        items = getattr(self.datamgr.rg, self.table)
        if cs.without_filter:
            return [x for x in items]
        else:
            return [x for x in items if cs.filter_func(x)]


    def get_list_livedata(self, cs):
        t = self.table
        if cs.without_filter:
            res = [y for y in 
                        reduce(list.__add__
                            #, [ getattr(x, t) for x in self.datamgr.rg.services + self.datamgr.rg.hosts
                                   # if len(getattr(x, t)) > 0 ]
                            , [ getattr(x, t) for x in self.datamgr.rg.services 
                                    if len(getattr(x, t)) > 0 ] +
                             [ getattr(x, t) for x in self.datamgr.rg.hosts
                                    if len(getattr(x, t)) > 0 ]
                            , [])
            ]
        else:
            res = [c for c in reduce(list.__add__
                        , [ getattr(x, t) for x in self.datamgr.rg.services
                                if len(getattr(x, t)) > 0] +
                         [ getattr(x, t) for x in self.datamgr.rg.hosts
                                if len(getattr(x, t)) > 0]
                        , []
                        )
                    if cs.filter_func(c) ]
        return res
    
    
    def get_group_livedata(self, cs, objs, an, group_key, member_key):
        """
        return a list of elements from a "group" of 'objs'. group can be a hostgroup or a servicegroup.
        objs: the objects to get elements from.
        an: the attribute name to set on result.
        group_key: the key to be used to sort the group members.
        member_key: the key to be used to sort each resulting element of a group member.
        """
        def factory(obj, attribute, groupobj):
            setattr(obj, attribute, groupobj)

        return [x for x in (
                    svc for svc in (
                        factory(og[0], an, og[1]) or og[0] for og in ( #
                            ( copy.copy(item0), inner_list0[1]) for inner_list0 in (  # (copy(host), hostgroup)
                                (sorted(sg1.members, key = member_key), sg1) for sg1 in  #2 hosts (sort name) von hg, hg
                                    sorted([sg0 for sg0 in objs if sg0.members], key = group_key) #1 hgs mit members!=[]
                                ) for item0 in inner_list0[0] #3 item0 ist host
                            )
                        ) if (cs.without_filter or cs.filter_func(svc)))
        ]


    def get_hostbygroups_livedata(self, cs):
        member_key = lambda k: k.host_name
        group_key = lambda k: k.hostgroup_name
        return self.get_group_livedata(cs, self.datamgr.rg.hostgroups, 'hostgroup', group_key, member_key)        


    def get_servicebygroups_livedata(self, cs):
        member_key = lambda k: k.get_name()
        group_key = lambda k: k.servicegroup_name
        return self.get_group_livedata(cs, self.datamgr.rg.servicegroups, 'servicegroup', group_key, member_key)
    

    def get_problem_livedata(self, cs):
        # We will crate a problems list first with all problems and source in it
        # TODO : create with filter
        problems = []
        for h in self.datamgr.rg.hosts.__itersorted__():
            if h.is_problem:
                pb = Problem(h, h.impacts)
                problems.append(pb)
        for s in self.datamgr.rg.services.__itersorted__():
            if s.is_problem:
                pb = Problem(s, s.impacts)
                problems.append(pb)
        # Then return
        return problems


    def get_status_livedata(self, cs):
        return [c for c in self.datamgr.rg.configs.values()]


    def get_columns_livedata(self, cs):
        result = []
        # The first 5 lines must be hard-coded
        # description;name;table;type
        # A description of the column;description;columns;string
        # The name of the column within the table;name;columns;string
        # The name of the table;table;columns;string
        # The data type of the column (int, float, string, list);type;columns;string
        result.append({
            'description' : 'A description of the column' , 'name' : 'description' , 'table' : 'columns' , 'type' : 'string' })
        result.append({
            'description' : 'The name of the column within the table' , 'name' : 'name' , 'table' : 'columns' , 'type' : 'string' })
        result.append({
            'description' : 'The name of the table' , 'name' : 'table' , 'table' : 'columns' , 'type' : 'string' })
        result.append({
            'description' : 'The data type of the column (int, float, string, list)' , 'name' : 'type' , 'table' : 'columns' , 'type' : 'string' })
        tablenames = ['hosts', 'services', 'hostgroups', 'servicegroups', 'contacts', 'contactgroups', 'commands', 'downtimes', 'comments', 'timeperiods', 'status', 'log', 'hostsbygroup', 'servicesbygroup', 'servicesbyhostgroup', 'status']
        for table in tablenames:
            cls = self.table_class_map[table][1]
            for attribute in cls.lsm_columns:
                result.append({
                    'description' : getattr(cls, 'lsm_'+attribute).im_func.description,
                    'name' : attribute,
                    'table' : table,
                    'type' : {
                        int : 'int',
                        float : 'float',
                        bool : 'int',
                        list : 'list',
                        str : 'string',
                    }[getattr(cls, 'lsm_'+attribute).im_func.datatype],
                })
        self.columns = ['description', 'name', 'table', 'type']
        return result


    def get_servicebyhostgroups_livedata(self, cs):
        # to test..
        res = [x for x in (
                svc for svc in (
                    setattr(svchgrp[0], 'hostgroup', svchgrp[1]) or svchgrp[0] for svchgrp in (
                        # (service, hostgroup), (service, hostgroup), (service, hostgroup), ...  service objects are individuals
                        (copy.copy(item1), inner_list1[1]) for inner_list1 in (
                            # ([service, service, ...], hostgroup), ([service, ...], hostgroup), ...  flattened by host. only if a host has services. sorted by service_description
                            (sorted(item0.services, key = lambda k: k.service_description), inner_list0[1]) for inner_list0 in (
                                # ([host, host, ...], hostgroup), ([host, host, host, ...], hostgroup), ...  sorted by host_name
                                (sorted(hg1.members, key = lambda k: k.host_name), hg1) for hg1 in   # ([host, host], hg), ([host], hg),... hostgroup.members->explode->sort
                                    # hostgroups, sorted by hostgroup_name
                                    sorted([hg0 for hg0 in self.datamgr.rg.hostgroups if hg0.members], key = lambda k: k.hostgroup_name)
                            ) for item0 in inner_list0[0] if item0.services
                        ) for item1 in inner_list1[0]
                    )
                ) if (cs.without_filter or cs.filter_func(svc))
            )]
        return res

    objects_get_handlers = {
        'hosts':                get_hosts_livedata,
        'services':             get_services_livedata,
        'commands':             get_filtered_livedata,
        'schedulers':           get_simple_livedata,
        'brokers':              get_simple_livedata,
        'pollers':              get_simple_livedata,
        'reactionners':         get_simple_livedata,
        'contacts':             get_filtered_livedata,
        'contactgroups':        get_filtered_livedata,
        'hostgroups':           get_filtered_livedata,
        'servicegroups':        get_filtered_livedata,
        'timeperiods':          get_filtered_livedata,
        'downtimes':            get_list_livedata,
        'comments':             get_list_livedata,
        'hostsbygroup':         get_hostbygroups_livedata,
        'servicesbygroup':      get_servicebygroups_livedata,
        'problems':             get_problem_livedata,
        'status':               get_status_livedata,
        'columns':              get_columns_livedata,
        'servicesbyhostgroup':  get_servicebyhostgroups_livedata
    }


    def get_live_data(self, cs):
        """Find the objects which match the request.
        
        This function scans a list of objects (hosts, services, etc.) and
        applies the filter functions first. The remaining objects are
        converted to simple dicts which have only the keys that were
        requested through Column: attributes. """
        # We will use prefiltercolumns here for some serious speedup.
        # For example, if nagvis wants Filter: host_groups >= hgxy
        # we don't have to use the while list of hostgroups in
        # the innermost loop
        # Filter: host_groups >= linux-servers
        # host_groups is a service attribute
        # We can get all services of all hosts of all hostgroups and filter at the end
        # But it would save a lot of time to already filter the hostgroups. This means host_groups must be hard-coded
        # Also host_name, but then we must filter the second step.
        # And a mixture host_groups/host_name with FilterAnd/Or? Must have several filter functions
        
        handler = self.objects_get_handlers.get(self.table, None)
        if not handler:
            print("Got unhandled table: %s" % (self.table))
            return []
        
        result = handler(self, cs)
        # Now we have a list of full objects (Host, Service, ....)

        #if self.limit:
        #    if isinstance(res, list):
        #        res = res[:self.limit]
        #    else:
        #        res = list(res)[:self.limit]
            
        return result


    def prepare_output(self, item):
        """Convert an object to a dict with selected keys.""" 
        output = {} 
        # what to do with empty?
        #print "prepare coluns %s" % self.outputcolumns
        for column in self.outputcolumns:
            try:
                value = getattr(item, 'lsm_'+column)(self)
            except Exception:
                if hasattr(item, 'lsm_'+column):
                    print "THIS LOOKS LIKE A SERIOUS ERROR", column
                    value = getattr(item, 'lsm_'+column).im_func.default
                else:
                    print "THIS LOOKS LIKE A SERIOUS ERROR I CAN CATCH"
                    value = getattr(item, 'lsm_'+column).im_func.default
            output[column] = value
        return output

    def get_live_data_log(self, cs):
        firstdb = [x for x in self.db.get_live_data_log() ]
        dbresult = [z for z in (
            x.fill(self.datamgr) for x in [copy.copy(y) for y in firstdb]
 # we better manipulate a copy of the rg objects
            ) if (cs.without_filter or cs.filter_func(z))
        ]
        return dbresult


    def statsify_result(self, filtresult):
        """Applies the stats filter functions to the result.
        
        Explanation:
        stats_group_by is ["service_description", "host_name"]
        filtresult is a list of elements which have, among others, service_description and host_name attributes

        Step 1:
        groupedresult is a dict where the keys are unique combinations of the stats_group_by attributes
                                where the values are arrays of elements which have those attributes in common
        Example:
            groupedresult[("host1","svc1")] = { host_name : "host1", service_description : "svc1", state : 2, in_downtime : 0 }
            groupedresult[("host1","svc2")] = { host_name : "host1", service_description : "svc2", state : 0, in_downtime : 0 }
            groupedresult[("host1","svc2")] = { host_name : "host1", service_description : "svc2", state : 1, in_downtime : 1 }

        resultdict is a dict where the keys are unique combinations of the stats_group_by attributes
                            where the values are dicts
        resultdict values are dicts where the keys are attribute names from stats_group_by
                                   where the values are attribute values
        Example:
            resultdict[("host1","svc1")] = { host_name : "host1", service_description : "svc1" }
            resultdict[("host1","svc2")] = { host_name : "host1", service_description : "svc2" }
        These attributes are later used as output columns

        Step 2:
        Run the filters (1 filter for each Stats: statement) and the postprocessors (default: len)
        The filters are numbered. After each run, add the result to resultdictay as <filterno> : <result>
        Example for Stats: state = 0\nStats: state = 1\nStats: state = 2\nStats: state = 3\n
            resultdict[("host1","svc1")] = { host_name : "host1", service_description : "svc1", 0 : 0, 1 : 0, 2 : 1, 3 : 0 }
            resultdict[("host1","svc2")] = { host_name : "host1", service_description : "svc2", 0 : 1, 1 : 1, 2 : 0, 3 : 0 }

        Step 3:
        Create the final result array from resultdict
        
        """
        result = []
        resultdict = {}
        if self.stats_group_by:
            # stats_group_by is a list in newer implementations
            if isinstance(self.stats_group_by, list):
                self.stats_group_by = tuple(self.stats_group_by)
            else:
                self.stats_group_by = tuple([self.stats_group_by])
            # Break up filtresult and prepare resultdict
            # rseultarr is not a simple array (for a single result line)
            # It is a dict with the statsgroupyby: as key
            groupedresult = {}
            for elem in filtresult:
                # Make a tuple consisting of the stats_group_by values
                stats_group_by_values = tuple([getattr(elem, 'lsm_'+c)(self) for c in self.stats_group_by])
                if not stats_group_by_values in groupedresult:
                    groupedresult[stats_group_by_values] = []
                groupedresult[stats_group_by_values].append(elem)
            for group in groupedresult:
                # All possible combinations of stats_group_by values. group is a tuple
                resultdict[group] = dict(zip(self.stats_group_by, group))

        #The number of Stats: statements
        #For each statement there is one function on the stack
        maxidx = self.stats_filter_stack.qsize()
        for i in range(maxidx):
            # Stats:-statements were put on a Lifo, so we need to reverse the number
            #stats_number = str(maxidx - i - 1)
            stats_number = maxidx - i - 1
            # First, get a filter for the attributes mentioned in Stats: statements
            filtfunc = self.stats_filter_stack.get()
            # Then, postprocess (sum, max, min,...) the results
            postprocess = self.stats_postprocess_stack.get()
            if self.stats_group_by:
                # Calc statistics over _all_ elements of groups
                # which share the same stats_filter_by
                for group in groupedresult:
                    resultdict[group][stats_number] = postprocess(filter(filtfunc, groupedresult[group]))
            else:
                # Calc statistics over _all_ elements of filtresult
                if isinstance(filtresult, list):
                    resultdict[stats_number] = postprocess(filter(filtfunc, filtresult))
                else:
                    # it's a generator
                    filtresult = list(filtresult)
                    resultdict[stats_number] = postprocess(filter(filtfunc, filtresult))
        if self.stats_group_by:
            for group in resultdict:
                result.append(resultdict[group])
        else:
            # Without StatsGroupBy: we have only one line
            result = [resultdict]
        return result


    def make_filter(self, operator, attribute, reference):
        if reference is not None:
            # Reference is now datatype string. The referring object attribute on the other hand
            # may be an integer. (current_attempt for example)
            # So for the filter to work correctly (the two values compared must be
            # of the same type), we need to convert the reference to the desired type
            converter = find_filter_converter(self.table, 'lsm_'+attribute)
            if converter:
                reference = converter(reference)
        attribute = 'lsm_'+attribute
        # The filters are closures.
        # Add parameter Class (Host, Service), lookup datatype (default string), convert reference
        def eq_filter(item):
            try:
                return getattr(item, attribute)(self) == reference
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default == reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def match_filter(item):
            try:
                p = re.compile(reference)
                return p.search(getattr(item, attribute)(self))
            except Exception:
                raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def eq_nocase_filter(item):
            try:
                return getattr(item, attribute)(self).lower() == reference.lower()
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default == reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def match_nocase_filter(item):
            p = re.compile(reference, re.I)
            return p.search(getattr(item, attribute)(self))

        def lt_filter(item):
            try:
                return getattr(item, attribute)(self) < reference
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default < reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def gt_filter(item):
            try:
                return getattr(item, attribute)(self) > reference
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default > reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def le_filter(item):
            try:
                return getattr(item, attribute)(self) <= reference
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default <= reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def ge_contains_filter(item):
            try:
                if getattr(item, attribute).im_func.datatype == list:
                    return reference in getattr(item, attribute)(self)
                else:
                    return getattr(item, attribute)(self) >= reference
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default >= reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def ne_filter(item):
            try:
                return getattr(item, attribute)(self) != reference
            except Exception:
                if hasattr(item, attribute):
                    return getattr(item.__class__, attribute).im_func.default != reference
                else:
                    raise LiveStatusQueryError(450, attribute.replace('lsm_', ''))

        def not_match_filter(item):
            return not match_filter(item)

        def not_eq_nocase_filter(item):
            return eq_nocase_filter(item)

        def not_match_nocase_filter(item):
            return not match_nocase_filter(item)

        def dummy_filter(item):
            return True

        def count_postproc(item):
            return len(item)

        def extract_postproc(item):
            return [float(obj[attribute]) for obj in item]

        def sum_postproc(item):
            return sum(float(getattr(obj, attribute)(self)) for obj in item)

        def max_postproc(item):
            if item != []:
                return max(float(getattr(obj, attribute)(self)) for obj in item)
            return 0

        def min_postproc(item):
            if item != []:
                return min(float(getattr(obj, attribute)(self)) for obj in item)
            return 0

        def avg_postproc(item):
            if item != []:
                return sum(float(getattr(obj, attribute)(self)) for obj in item)
            return 0

        def std_postproc(item):
            return 0

        if operator == '=':
            return eq_filter
        elif operator == '~':
            return match_filter
        elif operator == '=~':
            return eq_nocase_filter
        elif operator == '~~':
            return match_nocase_filter
        elif operator == '<':
            return lt_filter
        elif operator == '>':
            return gt_filter
        elif operator == '<=':
            return le_filter
        elif operator == '>=':
            return ge_contains_filter
        elif operator == '!=':
            return ne_filter
        elif operator == '!~':
            return not_match_filter
        elif operator == '!=~':
            return ne_nocase_filter
        elif operator == '!~~':
            return not_match_nocase_filter
        elif operator == 'dummy':
            return dummy_filter
        elif operator == 'sum':
            return sum_postproc
        elif operator == 'max':
            return max_postproc
        elif operator == 'min':
            return min_postproc
        elif operator == 'avg':
            return avg_postproc
        elif operator == 'std':
            return std_postproc
        elif operator == 'count':
            # postprocess for stats
            return count_postproc
        elif operator == 'extract':
            # postprocess for max,min,...
            return extract_postproc
        else:
            raise "wrong operation", operator


