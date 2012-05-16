#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    David GUENAULT, dguenault@monitoring-fr.org
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


import copy
import time
import sys

properties = {
    'daemons': ['broker'],
    'type': 'canopsis',
    'phases': ['running'],
    }


from shinken.basemodule import BaseModule
from shinken.log import logger


def de_unixify(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


class Canopsis_broker(BaseModule):

    """ This Class is a plugin for the Shinken Broker. It is in charge
    to brok information to rabbit mq. 
    """

    def __init__(self, conf):
        BaseModule.__init__(self, conf)

        self.host = conf.host
        self.port = conf.port
        self.user = conf.user
        self.password = conf.password
        self.virtual_host = conf.virtual_host
        self.exchange_name = conf.exchange_name

    def init(self):
        logger.info("I connect to canopsis server")

""" message format : 

Source : http://forge.canopsis.org/projects/canopsis/wiki/Event_format

Event :
{
  'connector':      'shinken',
  'connector_name': 'Connector name (nagios1, nagios2 ...)',
  'event_type':     Event type ('check', 'ack', 'notification', 'downtime'),
  'source_type':    Source type (component=service or resource=host),
  'component':      Component name,
  'resource':       Ressource name,
  'timestamp':      UNIX seconds timestamp,
  'state':          State (0 (Ok), 1 (Warning), 2 (Critical), 3 (Unknown)),
  'state_type':     State type (O (Soft), 1 (Hard)),
  'output':         Event message,
  'long_output':    Event long message,
  'perf_data':      see below
}

Perfdata :
    'perf_data':      Performance data ("Nagios format":http://nagiosplug.sourceforge.net/developer-guidelines.html#AEN201)
    or
    'perf_data_array': Array of performance data with metric's type ('GAUGE', 'DERIVE', 'COUNTER', 'ABSOLUTE'), Ex:
        [
          {'metric': 'shortterm', 'value': 0.25, 'unit': None, 'min': None, 'max': None, 'warn': None, 'crit': None, type: 'GAUGE' },
          {'metric': 'midterm',   'value': 0.16, 'unit': None, 'min': None, 'max': None, 'warn': None, 'crit': None, type: 'GAUGE' },
          {'metric': 'longterm',  'value': 0.12, 'unit': None, 'min': None, 'max': None, 'warn': None, 'crit': None, type: 'GAUGE' }
        ]
"""

    def manage_brok(self, b):
        logger.info("Got brok")        
        #new_b = copy.deepcopy(b)
        return
