#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import re
import time
import os

try:
    import sqlite3
except ImportError:
    try:
        import pysqlite2.dbapi2 as sqlite3
    except ImportError:
        import sqlite as sqlite3


from livestatus_query import LiveStatusQuery
from livestatus_response import LiveStatusResponse
from livestatus_constraints import LiveStatusConstraints

class LiveStatusWaitQuery(LiveStatusQuery):

    my_type = 'wait'

    def __init__(self, *args, **kwargs):
        #super(LiveStatusWaitQuery, self).__init__(*args, **kwargs)
        LiveStatusQuery.__init__(self, *args, **kwargs)
        self.response = LiveStatusResponse(responseheader = 'off', outputformat = 'csv', keepalive = 'off', columnheaders = 'off', separators = LiveStatusResponse.separators)
        self.wait_start = time.time()
        self.wait_timeout = 0
        self.wait_trigger = 'all'


    def parse_input(self, data):
        """Parse the lines of a livestatus request.
        
        This function looks for keywords in input lines and
        sets the attributes of the request object
        
        """
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space folowing the :
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'GET': # Get the name of the base table
                cmd, self.table = self.split_command(line)
                self.set_default_out_map_name()
            elif keyword == 'WaitObject': # Pick a specific object by name
                cmd, object = self.split_option(line)
                # It's like Filter: name = %s
                # Only for services it's host<blank>servicedesc
                if self.table == 'services':
                    host_name, service_description = object.split(' ', 1)
                    self.filtercolumns.append('host_name')
                    self.prefiltercolumns.append('host_name')
                    self.filter_stack.put(self.make_filter('=', 'host_name', host_name))
                    self.filtercolumns.append('description')
                    self.prefiltercolumns.append('description')
                    self.filter_stack.put(self.make_filter('=', 'description', service_description))
                    try:
                        # A WaitQuery works like an ordinary Query. But if
                        # we already know which object we're watching for
                        # changes, instead of scanning the entire list and
                        # applying a Filter:, we simply reduce the list
                        # so it has just one element.
                        self.services = { host_name + service_description : self.services[host_name + service_description] }
                    except:
                        pass
                elif self.table == 'hosts':
                    attribute = self.strip_table_from_column('name')
                    self.filtercolumns.append('name')
                    self.prefiltercolumns.append('name')
                    self.filter_stack.put(self.make_filter('=', 'name', object))
                    try:
                        self.hosts = { host_name : self.hosts[host_name] }
                    except:
                        pass
                else:
                    attribute = self.strip_table_from_column('name')
                    self.filtercolumns.append('name')
                    self.prefiltercolumns.append('name')
                    self.filter_stack.put(self.make_filter('=', 'name', object))
                    # For the other tables this works like an ordinary query.
                    # In the future there might be more lookup-tables
            elif keyword == 'WaitTrigger':
                cmd, self.wait_trigger = self.split_option(line)
                if self.wait_trigger not in ['check', 'state', 'log', 'downtime', 'comment', 'command']:
                    self.wait_trigger = 'all'
            elif keyword == 'WaitCondition':
                try:
                    cmd, attribute, operator, reference = self.split_option(line, 3)
                except:
                    cmd, attribute, operator, reference = self.split_option(line, 2) + ['']
                if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                    # We need to set columns, if not columnheaders will be set to "on"
                    self.columns.append(attribute)
                    # Cut off the table name
                    attribute = self.strip_table_from_column(attribute)
                    # Some operators can simply be negated
                    if operator in ['!>', '!>=', '!<', '!<=']:
                        operator = { '!>' : '<=', '!>=' : '<', '!<' : '>=', '!<=' : '>' }[operator]
                    # Put a function on top of the filter_stack which implements
                    # the desired operation
                    self.filtercolumns.append(attribute)
                    self.prefiltercolumns.append(attribute)
                    self.filter_stack.put(self.make_filter(operator, attribute, reference))
                    if self.table == 'log':
                        if attribute == 'time':
                            self.sql_filter_stack.put(self.make_sql_filter(operator, attribute, reference))
                else:
                    print "illegal operation", operator
                    pass # illegal operation
            elif keyword == 'WaitConditionAnd':
                cmd, andnum = self.split_option(line)
                # Take the last andnum functions from the stack
                # Construct a new function which makes a logical and
                # Put the function back onto the stack
                self.filter_stack.and_elements(andnum)
            elif keyword == 'WaitConditionOr':
                cmd, ornum = self.split_option(line)
                # Take the last ornum functions from the stack
                # Construct a new function which makes a logical or
                # Put the function back onto the stack
                self.filter_stack.or_elements(ornum)
            elif keyword == 'WaitTimeout':
                cmd, self.wait_timeout = self.split_option(line)
                self.wait_timeout = int(self.wait_timeout) / 1000
            else:
                # This line is not valid or not implemented
                print "Received a line of input which i can't handle : '%s'" % line
                pass
        # Make columns unique
        self.filtercolumns = list(set(self.filtercolumns))
        self.prefiltercolumns = list(set(self.prefiltercolumns))

        # Make one big filter where the single filters are anded
        self.filter_stack.and_elements(self.filter_stack.qsize())

        if self.table == 'log':
            self.sql_filter_stack.and_elements(self.sql_filter_stack.qsize())


    def launch_query(self):
        """ Prepare the request object's filter stacks """
        
        print "."
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
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print e
            traceback.print_exc(32) 
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
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
        filter_func     = self.filter_stack.get_stack()
        out_map         = self.out_map[self.out_map_name]
        filter_map      = dict([(k, out_map.get(k)) for k in self.filtercolumns])
        output_map      = dict([(k, out_map.get(k)) for k in self.columns]) or out_map
        without_filter  = len(self.filtercolumns) == 0

        cs = LiveStatusConstraints(filter_func, out_map, filter_map, output_map, without_filter)
        res = handler(self, cs)

        # A LiveStatusWaitQuery is launched several times, so we need to
        # put back the big filter function
        self.filter_stack.put_stack(filter_func)
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

        # We can apply the filterstack here as well. we have columns and filtercolumns.
        # the only additional step is to enrich log lines with host/service-attributes
        # A timerange can be useful for a faster preselection of lines
        filter_clause, filter_values = sql_filter_func()
        full_filter_clause = filter_clause
        matchcount = 0
        for m in re.finditer(r"\?", full_filter_clause):
            full_filter_clause = re.sub('\\?', str(filter_values[matchcount]), full_filter_clause, 1)
            matchcount += 1
        fromtime = 0
        totime = int(time.time()) + 1
        gtpat = re.search(r'^(\(*time|(.*\s+time))\s+>\s+(\d+)', full_filter_clause)
        gepat = re.search(r'^(\(*time|(.*\s+time))\s+>=\s+(\d+)', full_filter_clause)
        ltpat = re.search(r'^(\(*time|(.*\s+time))\s+<\s+(\d+)', full_filter_clause)
        lepat = re.search(r'^(\(*time|(.*\s+time))\s+<=\s+(\d+)', full_filter_clause)
        if gtpat != None:
            fromtime = int(gtpat.group(3)) + 1
        if gepat != None:
            fromtime = int(gepat.group(3))
        if ltpat != None:
            totime = int(ltpat.group(3)) - 1
        if lepat != None:
            totime = int(lepat.group(3))
        # now find the list of datafiles
        filtresult = []
        for dateobj, handle, archive, fromtime, totime in self.db.log_db_relevant_files(fromtime, totime):
            dbresult = self.select_live_data_log(filter_clause, filter_values, handle, archive, fromtime, totime)
            prefiltresult = [y for y in (x.fill(self.hosts, self.services, set(self.columns + self.filtercolumns)) for x in dbresult) if (without_filter or filter_func(self.create_output(filter_map, y)))]
            filtresult.extend([self.create_output(output_map, x) for x in prefiltresult])
        result = filtresult
        self.filter_stack.put_stack(filter_func)
        self.sql_filter_stack.put_stack(sql_filter_func)
        #print "result is", result
        return result


    def condition_fulfilled(self):
         result = self.launch_query()
         response = self.response
         response.format_live_data(result, self.columns, self.aliases)
         output, keepalive = response.respond()
         return output.strip()
