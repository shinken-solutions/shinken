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

from livestatus_query import LiveStatusQuery
from livestatus_wait_query import LiveStatusWaitQuery
from livestatus_command_query import LiveStatusCommandQuery


class LiveStatusRequest:

    """A class describing a livestatus request."""

    def __init__(self, data, datamgr, query_cache, db, pnp_path, return_queue, counters):
        self.data = data
        # Runtime data form the global LiveStatus object
        self.datamgr = datamgr
        self.query_cache = query_cache
        self.db = db
        self.pnp_path = pnp_path
        self.return_queue = return_queue
        self.counters = counters

        self.queries = []
        # Set a timestamp for this specific request
        self.tic = time.time()

    def parse_input(self, data):
        """Parse the lines of a livestatus request.

        This function looks for keywords in input lines and
        sets the attributes of the request object

        """
        external_cmds = []
        query_cmds = []
        wait_cmds = []
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the:
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if len(line) == 0:
                pass
            elif keyword in ('GET'):
                query_cmds.append(line)
                wait_cmds.append(line)
            elif keyword in ('WaitObject', 'WaitCondition', 'WaitConditionOr', 'WaitConditionAnd', 'WaitTrigger', 'WaitTimeout'):
                wait_cmds.append(line)
            elif keyword in ('COMMAND'):
                external_cmds.append(line)
            else:
                query_cmds.append(line)
        if len(external_cmds) > 0:
            for external_cmd in external_cmds:
                query = LiveStatusCommandQuery(self.datamgr, self.query_cache, self.db, self.pnp_path, self.return_queue, self.counters)
                query.parse_input(external_cmd)
                self.queries.append(query)
        if len(wait_cmds) > 1:
            query = LiveStatusWaitQuery(self.datamgr, self.query_cache, self.db, self.pnp_path, self.return_queue, self.counters)
            query.parse_input('\n'.join(wait_cmds))
            self.queries.append(query)
        if len(query_cmds) > 0:
            query = LiveStatusQuery(self.datamgr, self.query_cache, self.db, self.pnp_path, self.return_queue, self.counters)
            query.parse_input('\n'.join(query_cmds))
            self.queries.append(query)
