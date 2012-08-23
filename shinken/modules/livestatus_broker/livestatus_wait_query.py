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

import time
import os

from shinken.log import logger
from livestatus_query import LiveStatusQuery
from livestatus_response import LiveStatusResponse
from livestatus_constraints import LiveStatusConstraints
from livestatus_query_metainfo import LiveStatusQueryMetainfo


class LiveStatusWaitQuery(LiveStatusQuery):

    my_type = 'wait'

    def __init__(self, *args, **kwargs):
        #super(LiveStatusWaitQuery, self).__init__(*args, **kwargs)
        LiveStatusQuery.__init__(self, *args, **kwargs)
        self.response = LiveStatusResponse(responseheader='off', outputformat='csv', keepalive='off', columnheaders='undef', separators=LiveStatusResponse.separators)
        self.response = LiveStatusResponse()
        self.wait_start = time.time()
        self.wait_timeout = 0
        self.wait_trigger = 'all'

    def parse_input(self, data):
        """Parse the lines of a livestatus request.

        This function looks for keywords in input lines and
        sets the attributes of the request object.
        WaitCondition statements are written into the metafilter string as if they
        were ordinary Filter:-statements. (metafilter is then used for a MetaData object)

        """
        metafilter = ""
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the:
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET':  # Get the name of the base table
                _, self.table = self.split_command(line)
                metafilter += "GET %s\n" % self.table
            elif keyword == 'WaitObject':  # Pick a specific object by name
                _, item = self.split_option(line)
                # It's like Filter: name = %s
                # Only for services it's host<blank>servicedesc
                if self.table == 'services':
                    if ';' in item:
                        host_name, service_description = item.split(';', 1)
                    else:
                        host_name, service_description = item.split(' ', 1)
                    self.filtercolumns.append('host_name')
                    self.prefiltercolumns.append('host_name')
                    self.filter_stack.put(self.make_filter('=', 'host_name', host_name))
                    self.filtercolumns.append('description')
                    self.prefiltercolumns.append('description')
                    self.filter_stack.put(self.make_filter('=', 'description', service_description))
                    # A WaitQuery works like an ordinary Query. But if
                    # we already know which object we're watching for
                    # changes, instead of scanning the entire list and
                    # applying a Filter:, we simply reduce the list
                    # so it has just one element.
                    metafilter += "Filter: host_name = %s\n" % host_name
                    metafilter += "Filter: service_description = %s\n" % service_description
                elif self.table == 'hosts':
                    attribute = self.strip_table_from_column('name')
                    self.filtercolumns.append('name')
                    self.prefiltercolumns.append('name')
                    self.filter_stack.put(self.make_filter('=', 'name', item))
                    metafilter += "Filter: host_name = %s\n" % (item,)
                else:
                    attribute = self.strip_table_from_column('name')
                    self.filtercolumns.append('name')
                    self.prefiltercolumns.append('name')
                    self.filter_stack.put(self.make_filter('=', 'name', item))
                    # For the other tables this works like an ordinary query.
                    # In the future there might be more lookup-tables
            elif keyword == 'WaitTrigger':
                _, self.wait_trigger = self.split_option(line)
                if self.wait_trigger not in ['check', 'state', 'log', 'downtime', 'comment', 'command']:
                    self.wait_trigger = 'all'
            elif keyword == 'WaitCondition':
                try:
                    _, attribute, operator, reference = self.split_option(line, 3)
                except:
                    _, attribute, operator, reference = self.split_option(line, 2) + ['']
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    # We need to set columns, if not columnheaders will be set to "on"
                    self.columns.append(attribute)
                    # Cut off the table name
                    attribute = self.strip_table_from_column(attribute)
                    # Some operators can simply be negated
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = {'!>': '<=', '!>=': '<', '!<': '>=', '!<=': '>'}[operator]
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    self.filtercolumns.append(attribute)
                    self.prefiltercolumns.append(attribute)
                    self.filter_stack.put(self.make_filter(operator, attribute, reference))
                    if self.table == 'log':
                        self.db.add_filter(operator, attribute, reference)
                else:
                    logger.warning("[Livestatus Wait Query] Illegal operation: %s" % str(operator))
                    pass  # illegal operation
            elif keyword == 'WaitConditionAnd':
                _, andnum = self.split_option(line)
                # Take the last andnum functions from the stack
                # Construct a new function which makes a logical and
                # Put the function back onto the stack
                self.filter_stack.and_elements(andnum)
                if self.table == 'log':
                    self.db.add_filter_and(andnum)
            elif keyword == 'WaitConditionOr':
                _, ornum = self.split_option(line)
                # Take the last ornum functions from the stack
                # Construct a new function which makes a logical or
                # Put the function back onto the stack
                self.filter_stack.or_elements(ornum)
                if self.table == 'log':
                    self.db.add_filter_or(ornum)
            elif keyword == 'WaitTimeout':
                _, self.wait_timeout = self.split_option(line)
                self.wait_timeout = int(self.wait_timeout) / 1000
            else:
                # This line is not valid or not implemented
                logger.warning("[Livestatus Wait Query] Received a line of input which i can't handle: '%s'" % line)
                pass
        # Make columns unique
        self.filtercolumns = list(set(self.filtercolumns))
        self.prefiltercolumns = list(set(self.prefiltercolumns))

        # Make one big filter where the single filters are anded
        self.filter_stack.and_elements(self.filter_stack.qsize())

        if self.table == 'log':
            self.sql_filter_stack.and_elements(self.sql_filter_stack.qsize())

        self.metainfo = LiveStatusQueryMetainfo(metafilter)

    def launch_query(self):
        """ Prepare the request object's filter stacks """

        # The Response object needs to access the Query
        self.response.load(self)

        # A minimal integrity check
        if not self.table:
            return []

        try:
            # Remember the number of stats filters. We need these numbers as columns later.
            # But we need to ask now, because get_live_data() will empty the stack
            if self.table == 'log':
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
        except Exception, e:
            import traceback
            logger.error("[Livestatus Wait Query]  Error: %s" % e)
            traceback.print_exc(32)
            result = []
        return result

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

        handler = self.objects_get_handlers.get(self.table, None)
        if not handler:
            print("Got unhandled table: %s" % (self.table))
            return []

        # Get the function which implements the Filter: statements
        filter_func = self.filter_stack.get_stack()
        without_filter = len(self.filtercolumns) == 0

        cs = LiveStatusConstraints(filter_func, without_filter, self.authuser)
        result = handler(self, cs)

        # A LiveStatusWaitQuery is launched several times, so we need to
        # put back the big filter function
        self.filter_stack.put_stack(filter_func)
        return result

    def condition_fulfilled(self):
        # The result of launch_query is non-empty when an item matches the filter criteria
        # We cannot return res, because in most cases it is a generator object, which always
        # evaluates to a true value.
        # In order to account for [] we must read the generator
        return [x for x in self.launch_query()]
