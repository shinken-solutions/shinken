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

try:
    import sqlite3
except ImportError:
    try:
        import pysqlite2.dbapi2 as sqlite3
    except ImportError:
        import sqlite as sqlite3

from shinken.modules.livestatus_broker.hooker import Hooker
from shinken.modules.livestatus_broker.mapping import out_map as LSout_map
from thrift_response import ThriftResponse
from shinken.modules.livestatus_broker.livestatus_stack import LiveStatusStack
from shinken.modules.livestatus_broker.livestatus_constraints import LiveStatusConstraints


class Problem:
    def __init__(self, source, impacts):
        self.source = source
        self.impacts = impacts


class ThriftQuery(Hooker):

    my_type = 'query'

    def __init__(self, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, pollers, reactionners, brokers, dbconn, pnp_path, return_queue, counters):
        # Runtime data form the global Thrift object
        print "ThriftQuery.__init__()"
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.schedulers = schedulers
        self.pollers = pollers
        self.reactionners = reactionners
        self.brokers = brokers
        self.dbconn = dbconn
        self.pnp_path = pnp_path
        self.return_queue = return_queue
        self.counters = counters

        # Private attributes for this specific request
        self.response = ThriftResponse(responseheader='off', outputformat='csv', keepalive='off', columnheaders='undef', separators=ThriftResponse.separators)
        self.table = None
        self.columns = []
        self.filtercolumns = []
        self.prefiltercolumns = []
        self.stats_group_by = []
        self.stats_columns = []
        self.aliases = []
        self.limit = None
        self.extcmd = False
        self.out_map = self.copy_out_map_hooks()

        # Initialize the stacks which are needed for the Filter: and Stats:
        # filter- and count-operations
        self.filter_stack = LiveStatusStack()
        self.sql_filter_stack = LiveStatusStack()
        self.sql_filter_stack.type = 'sql'
        self.stats_filter_stack = LiveStatusStack()
        self.stats_postprocess_stack = LiveStatusStack()
        self.stats_request = False

        # When was this query launched?
        self.tic = time.time()
        # Clients can also send their local time with the request
        self.client_localtime = self.tic

    def find_converter(self, attribute):
        """Return a function that converts textual numbers
        in the request to the correct data type"""
        out_map = LSout_map[self.out_map_name]
        if attribute in out_map and 'type' in out_map[attribute]:
            if out_map[attribute]['type'] == 'int':
                return int
            elif out_map[attribute]['type'] == 'float':
                return float
        return None

    def set_default_out_map_name(self):
        """Translate the table name to the corresponding out_map key."""
        try:
            self.out_map_name = {
                'hosts': 'Host',
                'services': 'Service',
                'hostgroups': 'Hostgroup',
                'servicegroups': 'Servicegroup',
                'contacts': 'Contact',
                'contactgroups': 'Contactgroup',
                'comments': 'Comment',
                'downtimes': 'Downtime',
                'commands': 'Command',
                'timeperiods': 'Timeperiod',
                'hostsbygroup': 'Hostsbygroup',
                'servicesbygroup': 'Servicesbygroup',
                'servicesbyhostgroup': 'Servicesbyhostgroup',
                'status': 'Config',
                'log': 'Logline',
                'schedulers': 'SchedulerLink',
                'pollers': 'PollerLink',
                'reactionners': 'ReactionnerLink',
                'brokers': 'BrokerLink',
                'problems': 'Problem',
                'columns': 'Config', # just a dummy
            }[self.table]
        except:
            self.out_map_name = 'hosts'

    def copy_out_map_hooks(self):
        """Update the hooks for some out_map entries.

        Thrift columns which have a fulldepythonize postprocessor
        need an updated argument list. The third argument needs to
        be the request object. (When the out_map is first supplied
        with hooks, the third argument is the Thrift object.)

        """
        new_map = {}
        for objtype in LSout_map:
            new_map[objtype] = {}
            for attribute in LSout_map[objtype]:
                new_map[objtype][attribute] = {}
                entry = LSout_map[objtype][attribute]
                if 'hooktype' in entry:
                    if 'prop' not in entry or entry['prop'] is None:
                        prop = attribute
                    else:
                        prop = entry['prop']
                    if 'default' in entry:
                        default = entry['default']
                    else:
                        if entry['type'] == 'int' or entry['type'] == 'float':
                            default = 0
                        else:
                            default = ''
                    func = entry['fulldepythonize']
                    new_map[objtype][attribute]['hook'] = self.make_hook('get_prop_full_depythonize', prop, default, func, None)
                else:
                    new_map[objtype][attribute]['hook'] = entry['hook']
        return new_map

    def __str__(self):
        output = "ThriftRequest:\n"
        for attr in ["table", "columns", "filtercolumns", "prefiltercolumns", "aliases", "stats_group_by", "stats_request"]:
            output += "request %s: %s\n" % (attr, getattr(self, attr))
        return output

    def split_command(self, line, splits=1):
        """Create a list from the words of a line"""
        return line.split(' ', splits)

    def split_option(self, line, splits=1):
        """Like split_commands, but converts numbers to int data type"""
        #x = [int(i) if i.isdigit() else i for i in [token.strip() for token in re.split(r"[\s]+", line, splits)]]
        x = map(lambda i: (i.isdigit() and int(i)) or i, [token.strip() for token in re.split(r"[\s]+", line, splits)])
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

    def launch_query(self):
        """ Prepare the request object's filter stacks """
        print "launch_query"

        # A minimal integrity check
        if not self.table:
            return []

        # Make columns unique
        self.filtercolumns = list(set(self.filtercolumns))
        self.prefiltercolumns = list(set(self.prefiltercolumns))
        self.stats_columns = list(set(self.stats_columns))

        if self.stats_request:
            if len(self.columns) > 0:
                # StatsGroupBy is deprecated. Columns: can be used instead
                self.stats_group_by = self.columns
            elif len(self.stats_group_by) > 0:
                self.columns = self.stats_group_by + self.stats_columns
            #if len(self.stats_columns) > 0 and len(self.columns) == 0:
            if len(self.stats_columns) > 0:
                self.columns = self.stats_columns + self.columns

        # Make one big filter where the single filters are anded
        self.filter_stack.and_elements(self.filter_stack.qsize())
        try:
            # Remember the number of stats filters. We need these numbers as columns later.
            # But we need to ask now, because get_live_data() will empty the stack
            num_stats_filters = self.stats_filter_stack.qsize()
            if self.table == 'log':
                self.sql_filter_stack.and_elements(self.sql_filter_stack.qsize())
                result = self.get_live_data_log()
            else:
                # If the pnpgraph_present column is involved, then check
                # with each request if the pnp perfdata path exists
                if 'pnpgraph_present' in self.columns + self.filtercolumns + self.prefiltercolumns and self.pnp_path and os.access(self.pnp_path, os.R_OK):
                    self.pnp_path_readable = True
                else:
                    self.pnp_path_readable = False
                # Apply the filters on the broker's host/service/etc elements

                result = self.get_live_data()

            if self.stats_request:
                self.columns = range(num_stats_filters)
                if self.stats_group_by:
                    self.columns = tuple(list(self.stats_group_by) + list(self.columns))
                if len(self.aliases) == 0:
                    # If there were Stats: staments without "as", show no column headers at all
                    self.response.columnheaders = 'off'
                else:
                    self.response.columnheaders = 'on'

        except Exception, e:
            import traceback
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print e
            traceback.print_exc(32)
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            result = []

        return result

    def get_hosts_or_services_livedata(self, cs):
        if cs.without_filter and not self.limit:
            # Simply format the output
            return (self.create_output(cs.output_map, x) for x in getattr(self, self.table).itervalues())
        elif cs.without_filter and self.limit:
            # Simply format the output of a subset of the objects
            return (self.create_output(cs.output_map, x) for x in getattr(self, self.table).values()[:self.limit])
        else:
            # Filter the objects and format the output. At least hosts
            # and services are already sorted by name.
            return (
                self.create_output(cs.output_map, y) for y in (
                    x for x in getattr(self, self.table).itervalues()
                    if cs.without_filter or cs.filter_func(self.create_output(cs.filter_map, x)))
            )

    def get_hosts_livedata(self, cs):
        return self.get_hosts_or_services_livedata(cs)

    def get_services_livedata(self, cs):
        return self.get_hosts_or_services_livedata(cs)

    def get_simple_livedata(self, cs):
        objects = getattr(self, self.table)
        return [self.create_output(cs.output_map, obj) for obj in objects.values()]

    def get_filtered_livedata(self, cs):
        objects = getattr(self, self.table).values()
        if cs.without_filter:
            return [y for y in [self.create_output(cs.output_map, x) for x in objects] if cs.filter_func(y)]
        res = [x for x in objects if cs.filter_func(self.create_output(cs.filter_map, x))]
        return [self.create_output(cs.output_map, x) for x in res]

    def get_list_livedata(self, cs):
        t = self.table
        if cs.without_filter:
            res = [self.create_output(cs.output_map, y) for y in
                        reduce(list.__add__
                            , [getattr(x, t) for x in self.services.values() + self.hosts.values()
                                    if len(getattr(x, t)) > 0]
                            , [])
            ]
        else:
            res = [c for c in reduce(list.__add__
                        , [getattr(x, t) for x in self.services.values() + self.hosts.values()
                                if len(getattr(x, t)) > 0]
                        , []
                        )
                    if cs.filter_func(self.create_output(cs.filter_map, c))]
            res = [self.create_output(cs.output_map, x) for x in res]
        return res

    def get_group_livedata(self, cs, objs, an, group_key, member_key):
        """ return a list of elements from a "group" of 'objs'. group can be a hostgroup or a servicegroup.
objs: the objects to get elements from.
an: the attribute name to set on result.
group_key: the key to be used to sort the group members.
member_key: the key to be used to sort each resulting element of a group member. """
        return [self.create_output(cs.output_map, x) for x in (
                    svc for svc in (
                        setattr(og[0], an, og[1]) or og[0] for og in (
                            (copy.copy(item0), inner_list0[1]) for inner_list0 in (
                                (sorted(sg1.members, key=member_key), sg1) for sg1 in
                                    sorted([sg0 for sg0 in objs if sg0.members], key=group_key)
                                ) for item0 in inner_list0[0]
                            )
                        ) if (cs.without_filter or cs.filter_func(self.create_output(cs.filter_map, svc))))
        ]

    def get_hostbygroups_livedata(self, cs):
        member_key = lambda k: k.host_name
        group_key = lambda k: k.hostgroup_name
        return self.get_group_livedata(cs, self.hostgroups.values(), 'hostgroup', group_key, member_key)

    def get_servicebygroups_livedata(self, cs):
        member_key = lambda k: k.get_name()
        group_key = lambda k: k.servicegroup_name
        return self.get_group_livedata(cs, self.servicegroups.values(), 'servicegroup', group_key, member_key)

    def get_problem_livedata(self, cs):
        # We will crate a problems list first with all problems and source in it
        # TODO: create with filter
        problems = []
        for h in self.hosts.values():
            if h.is_problem:
                pb = Problem(h, h.impacts)
                problems.append(pb)
        for s in self.services.values():
            if s.is_problem:
                pb = Problem(s, s.impacts)
                problems.append(pb)
        # Then return
        return [self.create_output(cs.output_map, pb) for pb in problems]

    def get_status_livedata(self, cs):
        cs.out_map = self.out_map['Config']
        return [self.create_output(cs.output_map, c) for c in self.configs.values()]

    def get_columns_livedata(self, cs):
        result = []
        result.append({
            'description': 'A description of the column', 'name': 'description', 'table': 'columns', 'type': 'string'})
        result.append({
            'description': 'The name of the column within the table', 'name': 'name', 'table': 'columns', 'type': 'string'})
        result.append({
            'description': 'The name of the table', 'name': 'table', 'table': 'columns', 'type': 'string'})
        result.append({
            'description': 'The data type of the column (int, float, string, list)', 'name': 'type', 'table': 'columns', 'type': 'string'})
        tablenames = {'Host': 'hosts', 'Service': 'services', 'Hostgroup': 'hostgroups', 'Servicegroup': 'servicegroups', 'Contact': 'contacts', 'Contactgroup': 'contactgroups', 'Command': 'commands', 'Downtime': 'downtimes', 'Comment': 'comments', 'Timeperiod': 'timeperiods', 'Config': 'status', 'Logline': 'log', 'Statsbygroup': 'statsgroupby', 'Hostsbygroup': 'hostsbygroup', 'Servicesbygroup': 'servicesbygroup', 'Servicesbyhostgroup': 'servicesbyhostgroup'}
        for obj in sorted(LSout_map, key=lambda x: x):
            if obj in tablenames:
                for attr in LSout_map[obj]:
                    if 'description' in LSout_map[obj][attr] and LSout_map[obj][attr]['description']:
                        result.append({'description': LSout_map[obj][attr]['description'], 'name': attr, 'table': tablenames[obj], 'type': LSout_map[obj][attr]['type']})
                    else:
                        result.append({'description': 'to_do_desc', 'name': attr, 'table': tablenames[obj], 'type': LSout_map[obj][attr]['type']})
        return result

    def get_servicebyhostgroups_livedata(self, cs):
        # to test..
        res = [self.create_output(cs.output_map, x) for x in (
                svc for svc in (
                    setattr(svchgrp[0], 'hostgroup', svchgrp[1]) or svchgrp[0] for svchgrp in (
                        # (service, hostgroup), (service, hostgroup), (service, hostgroup), ...  service objects are individuals
                        (copy.copy(item1), inner_list1[1]) for inner_list1 in (
                            # ([service, service, ...], hostgroup), ([service, ...], hostgroup), ...  flattened by host. only if a host has services. sorted by service_description
                            (sorted(item0.services, key=lambda k: k.service_description), inner_list0[1]) for inner_list0 in (
                                # ([host, host, ...], hostgroup), ([host, host, host, ...], hostgroup), ...  sorted by host_name
                                (sorted(hg1.members, key=lambda k: k.host_name), hg1) for hg1 in   # ([host, host], hg), ([host], hg),... hostgroup.members->explode->sort
                                    # hostgroups, sorted by hostgroup_name
                                    sorted([hg0 for hg0 in self.hostgroups.values() if hg0.members], key=lambda k: k.hostgroup_name)
                            ) for item0 in inner_list0[0] if item0.services
                        ) for item1 in inner_list1[0]
                    )
                ) if (cs.without_filter or cs.filter_func(self.create_output(cs.filter_map, svc)))
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

    def get_live_data(self):
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
        print "get_live_data()"

        handler = self.objects_get_handlers.get(self.table, None)
        if not handler:
            print("Got unhandled table: %s" % (self.table))
            return []

        # Get the function which implements the Filter: statements
        filter_func = self.filter_stack.get_stack()
        out_map = self.out_map[self.out_map_name]
        filter_map = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter = len(self.filtercolumns) == 0

        cs = LiveStatusConstraints(filter_func, out_map, filter_map, output_map, without_filter)
        res = handler(self, cs)

        if self.limit:
            if isinstance(res, list):
                res = res[:self.limit]
            else:
                res = list(res)[:self.limit]

        if self.stats_request:
            res = self.statsify_result(res)

        return res

    def get_live_data_log(self):
        """Like get_live_data, but for log objects"""
        filter_func = self.filter_stack.get_stack()
        sql_filter_func = self.sql_filter_stack.get_stack()
        out_map = self.out_map[self.out_map_name]
        filter_map = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter = len(self.filtercolumns) == 0
        result = []
        if self.table == 'log':
            out_map = self.out_map['Logline']
            # We can apply the filterstack here as well. we have columns and filtercolumns.
            # the only additional step is to enrich log lines with host/service-attributes
            # A timerange can be useful for a faster preselection of lines
            filter_clause, filter_values = sql_filter_func()
            c = self.dbconn.cursor()
            try:
                if sqlite3.paramstyle == 'pyformat':
                    matchcount = 0
                    for m in re.finditer(r"\?", filter_clause):
                        filter_clause = re.sub('\\?', '%(' + str(matchcount) + ')s', filter_clause, 1)
                        matchcount += 1
                    filter_values = dict(zip([str(x) for x in xrange(len(filter_values))], filter_values))
                c.execute('SELECT * FROM logs WHERE %s' % filter_clause, filter_values)
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]
            dbresult = c.fetchall()
            if sqlite3.paramstyle == 'pyformat':
                dbresult = [self.row_factory(c, d) for d in dbresult]

            prefiltresult = [y for y in (x.fill(self.hosts, self.services, set(self.columns + self.filtercolumns)) for x in dbresult) if (without_filter or filter_func(self.create_output(filter_map, y)))]
            filtresult = [self.create_output(output_map, x) for x in prefiltresult]
            if self.stats_request:
                result = self.statsify_result(filtresult)
            else:
                # Results are host/service/etc dicts with the requested attributes
                # Columns: = keys of the dicts
                result = filtresult

        #print "result is", result
        return result

    def create_output(self, out_map, elt):
        """Convert an object to a dict with selected keys."""
        output = {}
        for display in out_map.keys():
            try:
                value = out_map[display]['hook'](elt)
            except:
                value = ''
            output[display] = value
        return output

    def statsify_result(self, filtresult):
        """Applies the stats filter functions to the result.

        Explanation:
        stats_group_by is ["service_description", "host_name"]
        filtresult is a list of elements which have, among others, service_description and host_name attributes

        Step 1:
        groupedresult is a dict where the keys are unique combinations of the stats_group_by attributes
                                where the values are arrays of elements which have those attributes in common
        Example:
            groupedresult[("host1","svc1")] = { host_name: "host1", service_description: "svc1", state: 2, in_downtime: 0 }
            groupedresult[("host1","svc2")] = { host_name: "host1", service_description: "svc2", state: 0, in_downtime: 0 }
            groupedresult[("host1","svc2")] = { host_name: "host1", service_description: "svc2", state: 1, in_downtime: 1 }

        resultdict is a dict where the keys are unique combinations of the stats_group_by attributes
                            where the values are dicts
        resultdict values are dicts where the keys are attribute names from stats_group_by
                                   where the values are attribute values
        Example:
            resultdict[("host1","svc1")] = { host_name: "host1", service_description: "svc1" }
            resultdict[("host1","svc2")] = { host_name: "host1", service_description: "svc2" }
        These attributes are later used as output columns

        Step 2:
        Run the filters (1 filter for each Stats: statement) and the postprocessors (default: len)
        The filters are numbered. After each run, add the result to resultdictay as <filterno>: <result>
        Example for Stats: state = 0\nStats: state = 1\nStats: state = 2\nStats: state = 3\n
            resultdict[("host1","svc1")] = { host_name: "host1", service_description: "svc1", 0: 0, 1: 0, 2: 1, 3: 0 }
            resultdict[("host1","svc2")] = { host_name: "host1", service_description: "svc2", 0: 1, 1: 1, 2: 0, 3: 0 }

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
                stats_group_by_values = tuple([elem[c] for c in self.stats_group_by])
                if not stats_group_by_values in groupedresult:
                    groupedresult[stats_group_by_values] = []
                groupedresult[stats_group_by_values].append(elem)
            for group in groupedresult:
                # All possible combinations of stats_group_by values. group is a tuple
                resultdict[group] = dict(zip(self.stats_group_by, group))

        # The number of Stats: statements
        # For each statement there is one function on the stack
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
            converter = self.find_converter(attribute)
            if converter:
                reference = converter(reference)

        # The filters are closures.
        # Add parameter Class (Host, Service), lookup datatype (default string), convert reference
        def eq_filter(ref):
            return ref[attribute] == reference

        def eq_nocase_filter(ref):
            return ref[attribute].lower() == reference.lower()

        def ne_filter(ref):
            return ref[attribute] != reference

        def gt_filter(ref):
            return ref[attribute] > reference

        def ge_filter(ref):
            return ref[attribute] >= reference

        def lt_filter(ref):
            return ref[attribute] < reference

        def le_filter(ref):
            return ref[attribute] <= reference

        def contains_filter(ref):
            return reference in ref[attribute].split(',')

        def match_filter(ref):
            p = re.compile(reference)
            return p.search(ref[attribute])

        def match_nocase_filter(ref):
            p = re.compile(reference, re.I)
            return p.search(ref[attribute])

        def ge_contains_filter(ref):
            if isinstance(ref[attribute], list):
                return reference in ref[attribute]
            else:
                return ref[attribute] >= reference

        def dummy_filter(ref):
            return True

        def count_postproc(ref):
            return len(ref)

        def extract_postproc(ref):
            return [float(obj[attribute]) for obj in ref]

        def sum_postproc(ref):
            return sum(float(obj[attribute]) for obj in ref)

        def max_postproc(ref):
            if ref != []:
                return max(float(obj[attribute]) for obj in ref)
            return 0

        def min_postproc(ref):
            if ref != []:
                return min(float(obj[attribute]) for obj in ref)
            return 0

        def avg_postproc(ref):
            if ref != []:
                return sum(float(obj[attribute]) for obj in ref) / len(ref)
            return 0

        def std_postproc(ref):
            return 0

        if operator == '=':
            return eq_filter
        elif operator == '!=':
            return ne_filter
        elif operator == '>':
            return gt_filter
        elif operator == '>=':
            return ge_contains_filter
        elif operator == '<':
            return lt_filter
        elif operator == '<=':
            return le_filter
        elif operator == '=~':
            return eq_nocase_filter
        elif operator == '~':
            return match_filter
        elif operator == '~~':
            return match_nocase_filter
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

    def make_sql_filter(self, operator, attribute, reference):

        # The filters are text fragments which are put together to form a sql where-condition finally.
        # Add parameter Class (Host, Service), lookup datatype (default string), convert reference
        def eq_filter():
            if reference == '':
                return ['%s IS NULL' % attribute, ()]
            else:
                return ['%s = ?' % attribute, (reference,)]

        def ne_filter():
            if reference == '':
                return ['%s IS NOT NULL' % attribute, ()]
            else:
                return ['%s != ?' % attribute, (reference,)]

        def gt_filter():
            return ['%s > ?' % attribute, (reference,)]

        def ge_filter():
            return ['%s >= ?' % attribute, (reference,)]

        def lt_filter():
            return ['%s < ?' % attribute, (reference,)]

        def le_filter():
            return ['%s <= ?' % attribute, (reference,)]

        def match_filter():
            return ['%s LIKE ?' % attribute, ('%' + reference + '%',)]
        if operator == '=':
            return eq_filter
        if operator == '>':
            return gt_filter
        if operator == '>=':
            return ge_filter
        if operator == '<':
            return lt_filter
        if operator == '<=':
            return le_filter
        if operator == '!=':
            return ne_filter
        if operator == '~':
            return match_filter
