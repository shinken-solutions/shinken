#!/usr/bin/env python2

#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#
import csv
import time
import sys
sys.path.append('gen-py')

try:
    from org.shinken_monitoring.tsca import StateService
    from org.shinken_monitoring.tsca.ttypes import *
except:
    print "Can't import tsca stub."
    print "Have you run thrift --gen py ../../../../shinken/modules/tsca/tsca.thrift ?"
    sys.exit(1)

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

try:

    # Make socket
    transport = TSocket.TSocket('localhost', 9090)

    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a client to use the protocol encoder
    client = StateService.Client(protocol)

    # Connect!
    transport.open()
    # Thrift server wait a list of list whith the following args:
    #      '''
    #      Read the list result
    #       Value n1: Timestamp
    #       Value n2: Hostname
    #       Value n3: Service
    #       Value n4: Return Code
    #       Value n5: Output
    #      '''
    states_list = []
    data = dataArgs()
    cr = csv.reader(open(sys.argv[1], "rb"))
    for elt in cr:
        trace = State()
        trace.timestamp = long(round(time.time()))
        trace.hostname = elt[0]
        trace.serv = elt[1]
        trace.output = elt[2]
        trace.rc = ReturnCode.OK
        states_list.append(trace)
    data.states = states_list
    client.submit_list(data)
    # Close!
    transport.close()

except Thrift.TException, tx:
    print '%s' % tx.message
