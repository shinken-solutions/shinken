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

# This Class implement the Thrift Service Check Acceptor, an NSCA inspired
# interface to submiet checks results

import os
import sys
import time

# Thrift Specificities
sys.path.append(os.path.abspath(__file__).rsplit("/", 3)[0] + "/thrift/gen-py")
try:
    from org.shinken_monitoring.tsca import StateService
    from org.shinken_monitoring.tsca.ttypes import *
    from thrift.transport import TSocket
    from thrift.transport import TTransport
    from thrift.protocol import TBinaryProtocol
    from thrift.server import TServer
except ImportError:
    TServer = None

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'tsca_server',
    'external': True,
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.debug("Get a TSCA arbiter module for plugin %s" % plugin.get_name())
    if not TServer:
        raise Exception('Module python-thrift not found. Please install it.')

    if hasattr(plugin, 'host'):
        if plugin.host == '*':
            host = ''
        else:
            host = plugin.host
    else:
        host = '127.0.0.1'
    if hasattr(plugin, 'port'):
        port = int(plugin.port)
    else:
        port = 9090
    if hasattr(plugin, 'max_packet_age'):
        max_packet_age = min(plugin.max_packet_age, 900)
    else:
        max_packet_age = 30

    instance = TSCA_arbiter(plugin, host, port, max_packet_age)
    return instance


# Used by Thrift to handle client
class StateServiceHandler:
    def __init__(self, tsca_arbiter):
        self.state_list = []
        self.dataReturn = dataReturn()
        self.tsca_arbiter = tsca_arbiter
        self.currentlySendingData = False

    def submit_list(self, state_list):
        if self.state_list:
            self.state_list.extend(state_list.states)
        else:
            self.state_list = state_list.states
        self.send_data()
        return self.dataReturn

    def send_data(self):
        if (self.currentlySendingData == False):
            self.currentlySendingData = True
            while self.state_list:
                check_result = self.tsca_arbiter.read_check_result(self.state_list[0])
                if check_result is not None:
                    (timestamp, rc, hostname, service, output) = check_result
                    try:
                        self.tsca_arbiter.post_command(timestamp, rc, hostname, service, output)
                    except:
                        logger.error("Failed sending a check result command to the arbiter")
                        pass
                self.state_list.pop(0)
            self.currentlySendingData = False


# Just print some stuff
class TSCA_arbiter(BaseModule):
    def __init__(self, modconf, host, port, max_packet_age):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.max_packet_age = max_packet_age

    # Ok, main function that is called in the CONFIGURATION phase
    def get_objects(self):
        logger.info "dummy ask me for objects to return"
        r = {'hosts': []}
        h = {'name': 'dummy host from dummy arbiter module',
             'register': '0',
             }

        r['hosts'].append(h)
        logger.info "dummy returning to Arbiter the hosts:", r
        return r

    def read_check_result(self, state):
        '''
         Read the list result
          Value n1: Timestamp
          Value n2: Hostname
          Value n3: Service
          Value n4: Return Code
          Value n5: Output
        '''
        timestamp = state.timestamp
        hostname = state.hostname
        service = state.serv
        rc = state.rc
        output = state.output

        current_time = time.time()
        check_result_age = current_time - timestamp
        if timestamp > current_time:
            logger.warning("Dropping packet with future timestamp.")
        elif check_result_age > self.max_packet_age:
            logger.warning("Dropping packet with stale timestamp - packet was %s seconds old." % check_result_age)
        else:
            return (timestamp, rc, hostname, service, output)

    def post_command(self, timestamp, rc, hostname, service, output):
        '''
        Send a check result command to the arbiter
        '''
        if len(service) == 0:
            extcmd = "[%lu] PROCESS_HOST_CHECK_RESULT;%s;%d;%s\n" % (timestamp, hostname, rc, output)
        else:
            extcmd = "[%lu] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s\n" % (timestamp, hostname, service, rc, output)

        e = ExternalCommand(extcmd)
        self.from_q.put(e)

    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        self.set_proctitle(self.name)

        self.set_exit_handler()
        try:
            handler = StateServiceHandler(self)
            processor = StateService.Processor(handler)
            transport = TSocket.TServerSocket("0.0.0.0", 9090)
            tfactory = TTransport.TBufferedTransportFactory()
            pfactory = TBinaryProtocol.TBinaryProtocolFactory()
            # In order to accept multiple simultaneous clients, we use TThreadedServer
            server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
            server.serve()
        except:
            logger.error("Error while trying to launch TSCA module")
