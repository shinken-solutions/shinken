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

from livestatus_query import LiveStatusQuery
from shinken.external_command import ExternalCommand
from shinken.log import logger


class LiveStatusCommandQuery(LiveStatusQuery):

    my_type = 'command'

    def parse_input(self, data):
        """Parse the lines of a livestatus request.

        This function looks for keywords in input lines and
        sets the attributes of the request object

        """
        for line in data.splitlines():
            line = line.strip()
            # Tools like NagVis send KEYWORK:option, and we prefer to have
            # a space following the:
            if ':' in line and not ' ' in line:
                line = line.replace(':', ': ')
            keyword = line.split(' ')[0].rstrip(':')
            if keyword == 'COMMAND':
                _, self.extcmd = line.split(' ', 1)
            else:
                # This line is not valid or not implemented
                logger.warning("[Livestatus Broker Command Query] Received a line of input which i can't handle: '%s'" % line)
                pass

    def launch_query(self):
        """ Prepare the request object's filter stacks """

        # The Response object needs to access the Query
        self.response.load(self)

        if self.extcmd:
            # External command are send back to broker
            self.extcmd = self.extcmd.decode('utf8', 'replace')
            e = ExternalCommand(self.extcmd)
            self.return_queue.put(e)
            return []
