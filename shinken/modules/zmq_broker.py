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
#
# The monitoring data itself is serialized
# using either json or msgpack depending on
# the module configuration.
#

from shinken.basemodule import BaseModule
from shinken.log import logger

# Check for JSON library
try:
    import json
except ImportError:
    # python 2.5
    import simplejson as json

properties = {
    'daemons': ['broker'],
    'type': 'zmq_broker',
    'external': False,
    }

# called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[Zmq Broker] Get a Zmq broker module for plugin %s" % mod_conf.get_name())

    # Check for ZeroMQ library
    try:
        import zmq
    except ImportError:
        logger.info("[Zmq Broker] Could not find python zmq library")
        return None

    # Get module configuration
    pub_endpoint = getattr(mod_conf, 'pub_endpoint', "tcp://127.0.0.1:22777")
    serialize_to = getattr(mod_conf, 'serialize_to', "json")
    instance = Zmq_broker(mod_conf, pub_endpoint, serialize_to)
    return instance


# Json custom encoder, encodes sets to lists
class SetEncoder(json.JSONEncoder):
    def default(self, obj):
	if isinstance(obj, set):
	    return list(obj)
	return json.JSONEncoder.default(self, obj)

# Msgpack custom encoder, encodes set to lists
def encode_monitoring_data(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj

# Class for the ZeroMQ broker
class Zmq_broker(BaseModule):
    context = None
    s_pub = None
    pub_endpoint = None
    serialize_to = None
    serialize = None

    def __init__(self, mod_conf, pub_endpoint, serialize_to):
        from zmq import Context, PUB
        BaseModule.__init__(self, mod_conf)
        self.pub_endpoint = pub_endpoint
        self.serialize_to = serialize_to
        logger.info("[Zmq Broker] Binding to endpoint " + self.pub_endpoint)

        # This doesn't work properly in init()
        # sometimes it ends up beings called several
        # times and the address becomes already in use.
        self.context = Context()
        self.s_pub = self.context.socket(PUB)
        self.s_pub.bind(self.pub_endpoint)

        # Load the correct serialization function
        # depending on the serialization method
        # chosen in the configuration.
        if self.serialize_to == "msgpack":
            from msgpack import Packer
            packer = Packer(default = encode_monitoring_data)
            self.serialize = lambda msg: packer.pack(msg)
        elif self.serialize_to == "json":
            self.serialize = lambda msg: json.dumps(msg, cls=SetEncoder)
        else:
            raise Exception("[Zmq Broker] No valid serialization method defined (Got "+str(self.serialize_to)+")!")
		
	
    # Called by Broker to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[Zmq Broker] Initialization of the Zmq broker module")

    # Publish to the ZeroMQ socket
    # using the chosen serialization method
    def publish(self, msg, topic=""):
        from zmq import SNDMORE
        data = self.serialize(msg)
        self.s_pub.send(topic, SNDMORE)
        self.s_pub.send(data)
		
    # An host check have just arrived, we UPDATE data info with this
    def manage_brok(self, b):
        logger.debug("[Zmq Broker] Got broker update: " + str(b.data))

        #Publish update data to the ZeroMQ endpoint.
        msg = b.data
        self.publish(msg, b.type)

    # Properly close down this thing.
    def do_stop(self):
        self.s_pub.close()
        self.context.term()
    
