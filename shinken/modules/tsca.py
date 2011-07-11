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

#This Class implement the Thrift Service Check Acceptor, an NSCA inspired
# interface to submiet checks results

#This text is print at the import
print "Detected module : TSCA module for Arbiter/receiver"

import os
import sys

#Thrift Specificities
sys.path.append('../thrift/gen-py')
from org.shinken_monitoring.tsca import StateService
from org.shinken_monitoring.tsca.ttypes import *
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand

properties = {
    'daemons' : ['arbiter', 'receiver'],
    'type' : 'tsca_server',
    'external' : True,
    'phases' : ['running'],
    }

#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a TSCA arbiter module for plugin %s" % plugin.get_name()

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

    instance = TSCA_arbiter(plugin, host, port)
    return instance

#Used by Thrift to handle client
class StateServiceHandler:
    def __init__(self, tsca_arbiter):
        self.state_list = []
        self.dataReturn = dataReturn()
        self.tsca_arbiter = tsca_arbiter
        self.currentlySendingData = False

    def submit_list(self, state_list):
        if self.state_list :
            self.state_list.extend(state_list.states)
        else :
            self.state_list = state_list.states
        self.send_data()
        return self.dataReturn

    def send_data(self):
        if (self.currentlySendingData == False) :
            self.currentlySendingData = True
            while self.state_list:
                (timestamp, rc, hostname, service, output)=self.tsca_arbiter.read_check_result(self.state_list[0])
                self.tsca_arbiter.post_command(timestamp,rc,hostname,service,output)
                self.state_list.pop(0)
            self.currentlySendingData = False

#Just print some stuff
class TSCA_arbiter(BaseModule):
    def __init__(self, modconf, host, port):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port


    #Ok, main function that is called in the CONFIGURATION phase
    def get_objects(self):
        print "[Dummy] ask me for objects to return"
        r = {'hosts' : []}
        h = {'name' : 'dummy host from dummy arbiter module',
             'register' : '0',
             }

        r['hosts'].append(h)
        print "[Dummy] Returning to Arbiter the hosts:", r
        return r


    def read_check_result(self, state):
        '''
         Read the list result
          Value n1 : Timestamp
          Value n2 : Hostname
          Value n3 : Service
          Value n4 : Return Code
          Value n5 : Output
        '''
        timestamp = state.timestamp
        hostname = state.hostname
        service = state.serv
        rc = state.rc
        output = state.output
        return (timestamp, rc, hostname, service, output)

    def post_command(self, timestamp, rc, hostname, service, output):
        '''
        Send a check result command to the arbiter
        '''
        if len(service) == 0:
            extcmd = "[%lu] PROCESS_HOST_CHECK_RESULT;%s;%d;%s\n" % (timestamp,hostname,rc,output)
        else:
            extcmd = "[%lu] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s\n" % (timestamp,hostname,service,rc,output)

        e = ExternalCommand(extcmd)
        self.from_q.put(e)


    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        self.set_exit_handler()

        handler = StateServiceHandler(self)
        processor = StateService.Processor(handler)
        transport = TSocket.TServerSocket(9090)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        # In order to accept multiple simultaneous clients, we use TThreadedServer
        server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
        server.serve()
