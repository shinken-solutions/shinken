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


# File for a Thrift class which can be used by the status-dat-broker
import re
import copy
import os
import time

from shinken.external_command import ExternalCommand
from shinken.util import from_bool_to_int, from_float_to_int, to_int, to_split, get_customs_keys, get_customs_values

from shinken.modules.livestatus_broker.hooker import Hooker
from shinken.modules.livestatus_broker.mapping import out_map
from shinken.modules.livestatus_broker.livestatus_counters import LiveStatusCounters
from shinken.modules.livestatus_broker.log_line import Logline


def join_with_separators(prop, ref, request, *args):
    if request.response.outputformat == 'csv':
        return request.response.separators[3].join([str(arg) for arg in args])
    elif request.response.outputformat == 'json' or request.response.outputformat == 'python':
        return args
    else:
        return None
    pass


def worst_host_state(state_1, state_2):
    """Return the worst of two host states."""
    # lambda x: reduce(lambda g, c: c if g == 0 else (c if c == 1 else g), (y.state_id for y in x), 0),
    if state_2 == 0:
        return state_1
    if state_1 == 1:
        return state_1
    return state_2


def worst_service_state(state_1, state_2):
    """Return the worst of two service states."""
    # reduce(lambda g, c: c if g == 0 else (c if c == 2 else (c if (c == 3 and g != 2) else g)), (z.state_id for y in x for z in y.services if z.state_type_id == 1), 0),
    if state_2 == 0:
        return state_1
    if state_1 == 2:
        return state_1
    if state_1 == 3 and state_2 != 2:
        return state_1
    return state_2


class Thrift_status(object, Hooker):
    """A class that represents the status of all objects in the broker

    """
    # Use out_map from the mapping.py file
    out_map = out_map

    def __init__(self, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, pollers, reactionners, brokers, dbconn, pnp_path, return_queue):
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
        Thrift_status.pnp_path = pnp_path
        self.debuglevel = 2
        self.dbconn.row_factory = self.row_factory
        self.return_queue = return_queue

        self.create_out_map_delegates()
        self.create_out_map_hooks()

        # add Host attributes to Hostsbygroup etc.
        for attribute in Thrift_status.out_map['Host']:
            Thrift_status.out_map['Hostsbygroup'][attribute] = Thrift_status.out_map['Host'][attribute]
        for attribute in self.out_map['Service']:
            Thrift_status.out_map['Servicesbygroup'][attribute] = Thrift_status.out_map['Service'][attribute]
        for attribute in self.out_map['Service']:
            Thrift_status.out_map['Servicesbyhostgroup'][attribute] = Thrift_status.out_map['Service'][attribute]

        self.counters = LiveStatusCounters()

    def row_factory(self, cursor, row):
        """Handler for the sqlite fetch method."""
        return Logline(cursor, row)

    def handle_request(self, data):
        """Execute the thrift request.

        This function creates a ThriftRequest method, calls the parser,
        handles the execution of the request and formatting of the result.

        """
        request = ThriftRequest(data, self.configs, self.hosts, self.services,
            self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands,
            self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.return_queue, self.counters)
        request.parse_input(data)
        # print "REQUEST\n%s\n" % data
        to_del = []
        if sorted([q.my_type for q in request.queries]) == ['command', 'query', 'wait']:
            # The Multisite way
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
            output = [q for q in request.queries if q.my_type == 'wait'] + [q for q in request.queries if q.my_type == 'query']
        elif sorted([q.my_type for q in request.queries]) == ['query', 'wait']:
            # The Thruk way
            output = [q for q in request.queries if q.my_type == 'wait'] + [q for q in request.queries if q.my_type == 'query']
            keepalive = True
        elif sorted([q.my_type for q in request.queries]) == ['command', 'query']:
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
            for query in [q for q in request.queries if q.my_type == 'query']:
                # This was a simple query, respond immediately
                result = query.launch_query()
                # Now bring the retrieved information to a form which can be sent back to the client
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()

        elif sorted([q.my_type for q in request.queries]) == ['query']:
            for query in [q for q in request.queries if q.my_type == 'query']:
                # This was a simple query, respond immediately
                result = query.launch_query()
                # Now bring the retrieved information to a form which can be sent back to the client
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
        elif sorted([q.my_type for q in request.queries]) == ['command']:
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
        elif [q.my_type for q in request.queries if q.my_type != 'command'] == []:
            # Only external commands. Thruk uses it when it sends multiple
            # objects into a downtime.
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
        else:
            # We currently do not handle this kind of composed request
            output = ""
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "We currently do not handle this kind of composed request"
            print sorted([q.my_type for q in request.queries])

        # print "RESPONSE\n%s\n" % output
        print "DURATION %.4fs" % (time.time() - request.tic)
        return output, keepalive

    def create_out_map_delegates(self):
        """Add delegate keys for certain attributes.

        Some attributes are not directly reachable via prop or
        need a complicated depythonize function.
        Example: Logline (the objects created for a "GET log" request
        have the column current_host_state. The Logline object does
        not have an attribute of this name, but a log_host attribute.
        The Host object represented by log_host has an attribute state
        which is the desired current_host_state. Because it's the same
        for all columns starting with current_host, a rule can
        be applied that automatically redirects the resolving to the
        corresponding object. Instead of creating a complicated
        depythonize handler which gets log_host and then state, two new
        keys for Logline/current_host_state are added:
        delegate = log_host
        as = state
        This instructs the hook function to first get attribute state of
        the object represented by log_host.

        """
        delegate_map = {
            'Logline': {
                'current_service_': 'log_service',
                'current_host_': 'log_host',
            },
            'Service': {
                'host_': 'host',
            },
            'Comment': {
                'service_': 'ref',
                'host_': 'ref',
            },
            'Downtime': {
                'service_': 'ref',
                'host_': 'ref',
            }
        }
        for objtype in Thrift_status.out_map:
            for attribute in Thrift_status.out_map[objtype]:
                entry = Thrift_status.out_map[objtype][attribute]
                if objtype in delegate_map:
                    for prefix in delegate_map[objtype]:
                        if attribute.startswith(prefix):
                            if 'delegate' not in entry:
                                entry['delegate'] = delegate_map[objtype][prefix]
                                entry['as'] = attribute.replace(prefix, '')

    def count_event(self, counter):
        self.counters.increment(counter)
