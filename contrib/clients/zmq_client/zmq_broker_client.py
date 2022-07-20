#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Thomas Cellerier, thomascellerier@gmail.com
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

# This is an example client for the zmq_broker module.
# This will listen for notifications using the given
# serialization method on the given ZeroMQ endpoint
# using the given ZeroMQ topic filter.
#
# Examples:
# python zmq_broker_client.py "json" "tcp://127.0.0.1:12345" "host"
# python zmq_broker_client.py "msgpack" "ipc:///tmp/shinken_pub" ""
# python zmq_broker_client.py "json" "tcp://172.23.2.189:9067" "log"

from __future__ import absolute_import, division, print_function, unicode_literals

import zmq
import sys

# Usage
if len(sys.argv) > 1:
    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("Usage: python zmq_broker_client.py [json|msgpack] [<zmq endpoint>] [<zmq topic>]")
        sys.exit(-1)

# Serialization method
method = ""
if len(sys.argv) < 2 or sys.argv[1] == "json":
	import json
	method = "json"
elif sys.argv[1] == "msgpack":
	import msgpack
	method = "msgpack"
else:
	print("Invalid serialization method.")
	sys.exit(-1)

# ZeroMQ endpoint
sub_endpoint = "tcp://127.0.0.1:12345"
if len(sys.argv) > 2:
	sub_endpoint = sys.argv[2]

# ZeroMQ Suscription Topic
topic = ""
if len(sys.argv) > 3:
	topic = sys.argv[3]

# Subscribe
context = zmq.Context()
s_sub = context.socket(zmq.SUB)
s_sub.setsockopt(zmq.SUBSCRIBE, topic)
s_sub.connect(sub_endpoint)
print("Listening for shinken notifications.")

# Process incoming messages
while True:
	topic = s_sub.recv()
	print("Got msg on topic: " + topic)
	data = s_sub.recv()
	if method == "json":
		json_data = json.loads(data)
		pretty_msg = json.dumps(json_data, sort_keys=True, indent=4)
		print(pretty_msg)
	elif method == "msgpack":
		msg = msgpack.unpackb(data, use_list=False)
		print(msg)
s_sub.close()
context.term()

