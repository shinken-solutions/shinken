#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2013:
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

# This Class is a plugin for the Shinken Broker.
# Its job is to publish monitoring updates to the
# specified ZeroMQ endpoint point by use of a
# ZeroMQ broker.
#
# A ZeroMQ endpoint can be tcp, ipc, or inproc.
# E.g:
# tcp://127.0.0.1:22777
# ipc:///tmp/shinken_pub
# inproc://shinken_pub

from shinken.basemodule import BaseModule
from shinken.log import logger
import zmq
import json

properties = {
    'daemons': ['broker'],
    'type': 'zmq_broker',
    'external': False,
    }


# called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[Zmq Broker] Get a Zmq broker module for plugin %s" % mod_conf.get_name())
    pub_endpoint = getattr(mod_conf, 'pub_endpoint', "tcp://127.0.0.1:22777")
    serialize_to = getattr(mod_conf, 'serialize_to', "json")
    instance = Zmq_broker(mod_conf, pub_endpoint, serialize_to)
    return instance


# Class for the ZeroMQ broker
class Zmq_broker(BaseModule):
    context = None
    s_pub = None
    pub_endpoint = None
    serialize_to = None
    serialize = None

    def __init__(self, mod_conf, pub_endpoint, serialize_to):
        BaseModule.__init__(self, mod_conf)
        self.pub_endpoint = pub_endpoint
        self.serialize_to = serialize_to
        logger.info("[Zmq Broker] Binding to endpoint " + self.pub_endpoint)

        # This doesn't work properly in init()
        # sometimes it ends up beings called several
        # times and the address becomes already in use.
        self.context = zmq.Context()
        self.s_pub = self.context.socket(zmq.PUB)
        self.s_pub.bind(self.pub_endpoint)

        # Load the correct serialization function
        # depending on the serialization method
        # chosen in the configuration.
        if self.serialize_to == "msgpack":
            from msgpack import packb
            self.serialize = packb
        elif self.serialize_to == "json":
            from json import dumps
            self.serialize = dumps
        else:
            raise Exception("[Zmq Broker] No valid serialization method defined (Got "+str(self.serializ_to)+")!")
  	
	
    # Called by Broker to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[Zmq Broker] Initialization of the Zmq broker module")

    # Publish to the ZeroMQ socket
    # using the chosen serialization method
    def publish(self, msg):
        data = self.serialize(msg)
        self.s_pub.send(data)
		
    # An host check have just arrived, we UPDATE data info with this
    def manage_brok(self, b):
        logger.debug("[Zmq Broker] Got broker update: " + str(b.data))

        #Publish update data to the ZeroMQ endpoint.
        msg = b.data
        self.publish(msg)

    # Properly close down this thing.
    def do_stop(self):
        self.s_pub.close()
        self.context.term()
    
