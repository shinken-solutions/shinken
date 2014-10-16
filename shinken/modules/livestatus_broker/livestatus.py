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
import traceback
import cStringIO

from shinken.log import logger

from livestatus_counters import LiveStatusCounters
from livestatus_request import LiveStatusRequest
from livestatus_response import LiveStatusResponse
from livestatus_broker_common import LiveStatusQueryError

class LiveStatus(object):
    """A class that represents the status of all objects in the broker

    """

    def __init__(self, datamgr, query_cache, db, pnp_path, return_queue, counters=None):
        self.datamgr = datamgr
        self.query_cache = query_cache
        self.db = db
        self.pnp_path = pnp_path
        self.return_queue = return_queue
        if counters is None:
            counters = LiveStatusCounters()
        self.counters = counters

    def handle_request(self, data):
        try:
            return self.handle_request_and_fail(data)
        except LiveStatusQueryError, exp:
            # LiveStatusQueryError(404, table)
            # LiveStatusQueryError(450, column)
            code, detail = exp.args
            response = LiveStatusResponse()
            response.set_error(code, detail)
            if 'fixed16' in data:
                response.responseheader = 'fixed16'
            return response.respond()
        except Exception, exp:
            logger.error("[Livestatus] Exception! %s" % exp)
            # Also show the exception
            output = cStringIO.StringIO()
            traceback.print_exc(file=output)
            logger.error("[Livestatus] Back trace of this exception: %s" % (output.getvalue()))
            output.close()
            # Ok now we can return something
            response = LiveStatusResponse()
            response.set_error(452, data)
            if 'fixed16' in data:
                response.responseheader = 'fixed16'
            return response.respond()

    def handle_request_and_fail(self, data):
        """Execute the livestatus request.

        This function creates a LiveStatusRequest method, calls the parser,
        handles the execution of the request and formatting of the result.

        """
        request = LiveStatusRequest(data, self.datamgr, self.query_cache, self.db, self.pnp_path, self.return_queue, self.counters)
        request.parse_input(data)
        squeries = sorted([q.my_type for q in request.queries])
        if squeries == ['command', 'query', 'wait']:
            # The Multisite way
            for query in [q for q in request.queries if q.my_type == 'command']:
                result = query.launch_query()
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()
            output = [q for q in request.queries if q.my_type == 'wait'] + [q for q in request.queries if q.my_type == 'query']
        elif squeries == ['query', 'wait']:
            # The Thruk way
            output = [q for q in request.queries if q.my_type == 'wait'] + [q for q in request.queries if q.my_type == 'query']
            keepalive = True
        elif squeries == ['command', 'query']:
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

        elif squeries == ['query']:
            for query in [q for q in request.queries if q.my_type == 'query']:
                # This was a simple query, respond immediately
                result = query.launch_query()
                # Now bring the retrieved information to a form which can be sent back to the client
                response = query.response
                response.format_live_data(result, query.columns, query.aliases)
                output, keepalive = response.respond()

        elif squeries == ['command']:
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
            logger.error("[Livestatus] We currently do not handle this kind of composed request: %s" % squeries)

        logger.debug("[Livestatus] Request duration %.4fs" % (time.time() - request.tic))
        return output, keepalive

    def count_event(self, counter):
        self.counters.increment(counter)
