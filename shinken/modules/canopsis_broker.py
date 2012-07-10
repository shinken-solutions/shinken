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

# This Class is a plugin for the Shinken Broker. It's job is to write
# host and service perfdata to a file which can be processes by the
# canopsis daemon (http://pnp4nagios.org). It is a reimplementation of canopsis.c

import sys
import os
import pickle

from collections import deque

import traceback

from shinken.basemodule import BaseModule
from shinken.log import logger

from kombu import BrokerConnection
from kombu import Producer, Consumer, Exchange, Queue

properties = {
    'daemons': ['broker'],
    'type': 'canopsis',
    'external': False,
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    # logger.info("Info","Get a canopsis broker for plugin %s" % (str(plugin.get_name())))

    host            = getattr(plugin, 'host', None)
    port            = getattr(plugin, 'port', None)
    user            = getattr(plugin, 'user', None)
    password        = getattr(plugin, 'password', None)
    virtual_host    = getattr(plugin, 'virtual_host', None)
    exchange_name   = getattr(plugin, 'exchange_name', None)
    identifier      = getattr(plugin, 'identifier', None)
    maxqueuelength  = getattr(plugin, 'maxqueuelength', 10000)
    queue_dump_frequency = getattr(plugin, 'queue_dump_frequency', 300)

    return Canopsis_broker(plugin, host, port, user, password, virtual_host, exchange_name, identifier, maxqueuelength, queue_dump_frequency)


# Class for the canopsis Broker
class Canopsis_broker(BaseModule):
    def __init__(self, modconf, host, port, user, password, virtual_host, exchange_name, identifier, maxqueuelength, queue_dump_frequency):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.virtual_host = virtual_host
        self.exchange_name = exchange_name
        self.identifier = identifier
        self.maxqueuelength = maxqueuelength
        self.queue_dump_frequency = queue_dump_frequency

        self.canopsis = event2amqp(self.host, self.port, self.user, self.password, self.virtual_host, self.exchange_name, self.identifier, self.maxqueuelength, queue_dump_frequency)

    # We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        if b.type == "host_check_result":
            self.manage_host_check_result_brok(b)
        elif b.type == "service_check_result":
            self.manage_service_check_result_brok(b)
        if b.type == "initial_host_status":
            self.manage_initial_host_status_brok(b)
        elif b.type == "initial_service_status":
            self.manage_initial_service_status_brok(b)

    def manage_initial_host_status_brok(self, b):
        logger.log("[Canopsis] processing initial_host_status")

        if not hasattr(self, 'host_commands'):
            self.host_commands = {}

        if not hasattr(self, 'host_addresses'):
            self.host_addresses = {}

        if not hasattr(self, 'host_max_check_attempts'):
            self.host_max_check_attempts = {}

        # check commands does not appear in check results so build a dict of check_commands
        self.host_commands[b.data['host_name']] = b.data['check_command'].call

        # address does not appear in check results so build a dict of addresses
        self.host_addresses[b.data['host_name']] = b.data['address']

        # max_check_attempts does not appear in check results so build a dict of max_check_attempts
        self.host_max_check_attempts[b.data['host_name']] = b.data['max_check_attempts']

        logger.info("[canopsis] initial host max attempts: %s " % str(self.host_max_check_attempts))
        logger.info("[canopsis] initial host commands: %s " % str(self.host_commands))
        logger.info("[canopsis] initial host addresses: %s " % str(self.host_addresses))

    def manage_initial_service_status_brok(self, b):
        logger.log("[Canopsis] processing initial_service_status")

        if not hasattr(self, 'service_commands'):
            logger.log("[Canopsis] creating empty dict in service_commands")
            self.service_commands = {}

        if not hasattr(self, 'service_max_check_attempts'):
            logger.log("[Canopsis] creating empty dict in service_max_check_attempts")
            self.service_max_check_attempts = {}

        if not b.data['host_name'] in self.service_commands:
            logger.log("[Canopsis] creating empty dict for host %s service_commands" % b.data['host_name'])
            self.service_commands[b.data['host_name']] = {}

        self.service_commands[b.data['host_name']][b.data['service_description']] = b.data['check_command'].call

        if not b.data['host_name'] in self.service_max_check_attempts:
            logger.log("[Canopsis] creating empty dict for host %s service_max_check_attempts" % b.data['host_name'])
            self.service_max_check_attempts[b.data['host_name']] = {}

        self.service_max_check_attempts[b.data['host_name']][b.data['service_description']] = b.data['max_check_attempts']

    def manage_host_check_result_brok(self, b):
        message = self.create_message('component', 'check', b)
        if not message:
            logger.info("[Canopsis] Warning: Empty host check message")
        else:
            self.push2canopsis(message)

    # A service check has just arrived. Write the performance data to the file
    def manage_service_check_result_brok(self, b):
        try:
            message = self.create_message('resource', 'check', b)
        except:
            logger.error("[Canopsis] Error: there was an error while trying to create message for service")

        if not message:
            logger.info("[Canopsis] Warning: Empty service check message")
        else:
            self.push2canopsis(message)

    def create_message(self, source_type, event_type, b):
        """
            event_type should be one of the following:
                - check
                - ack
                - notification
                - downtime

            source_type should be one of the following:
                - component => host
                - resource => service

            message format (check):

            H S         field               desc
            x           'connector'         Connector type (gelf, nagios, snmp, ...)
            x           'connector_name':   Connector name (nagios1, nagios2 ...)
            x           'event_type'        Event type (check, log, trap, ...)
            x           'source_type'       Source type (component or resource)
            x           'component'         Component name
            x           'resource'          Resource name
            x           'timestamp'         UNIX seconds timestamp
            x           'state'             State (0 (Ok), 1 (Warning), 2 (Critical), 3 (Unknown))
            x           'state_type'        State type (O (Soft), 1 (Hard))
            x           'output'            Event message
            x           'long_output'       Event long message
            x           'perfdata'          nagios plugin perfdata raw (for the moment)
            x           'check_type'
            x           'current_attempt'
            x           'max_attempts'
            x           'execution_time'
            x           'latency'
            x           'command_name'
                        'address'
        """
        if source_type == 'resource':
            # service
            specificmessage = {
                'resource': b.data['service_description'],
                'command_name': self.service_commands[b.data['host_name']][b.data['service_description']],
                'max_attempts': self.service_max_check_attempts[b.data['host_name']][b.data['service_description']],
            }
        elif source_type == 'component':
            # host
            specificmessage = {
                'resource': None,
                'command_name': self.host_commands[b.data['host_name']],
                'max_check_attempts': self.host_max_check_attempts[b.data['host_name']]
            }
        else:
            # WTF?!
            logger.info("[Canopsis] Invalid source_type %s" % (source_type))
            return None

        commonmessage = {
            'connector': u'shinken',
            'connector_name': unicode(self.identifier),
            'event_type': event_type,
            'source_type': source_type,
            'component': b.data['host_name'],
            'timestamp': b.data['last_chk'],
            'state': b.data['state_id'],
            'state_type': b.data['state_type_id'],
            'output': b.data['output'],
            'long_output': b.data['long_output'],
            'perf_data': b.data['perf_data'],
            'check_type': b.data['check_type'],
            'current_attempt': b.data['attempt'],
            'execution_time': b.data['execution_time'],
            'latency': b.data['latency'],
            'address': self.host_addresses[b.data['host_name']]
        }

        return dict(commonmessage, **specificmessage)

    def push2canopsis(self, message):
        strmessage = str(message)
        self.canopsis.postmessage(message)
        #logger.info("[Canopsis] push2canopsis: %s" % (strmessage))

    def hook_tick(self, brok):
        if self.canopsis:
            self.canopsis.hook_tick(brok)


class event2amqp():

    def __init__(self, host, port, user, password, virtual_host, exchange_name, identifier, maxqueuelength, queue_dump_frequency):

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.virtual_host = virtual_host
        self.exchange_name = exchange_name
        self.identifier = identifier
        self.maxqueuelength = maxqueuelength
        self.queue_dump_frequency = queue_dump_frequency

        self.connection_string = None

        self.connection = None
        self.channel = None
        self.producer = None
        self.exchange = None
        self.queue = deque([])

        self.tickage = 0

        self.load_queue()

    def create_connection(self):
        self.connection_string = "amqp://%s:%s@%s:%s/%s" % (self.user, self.password, self.host, self.port, self.virtual_host)
        try:
            self.connection = BrokerConnection(self.connection_string)
            return True
        except:
            func = sys._getframe(1).f_code.co_name
            error = str(sys.exc_info()[0])
            logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
            return False

    def connect(self):
        logger.info("[Canopsis] connection with: %s" % self.connection_string)
        try:
            self.connection.connect()
            if not self.connected():
                return False
            else:
                self.get_channel()
                self.get_exchange()
                self.create_producer()
                return True
        except:
            func = sys._getframe(1).f_code.co_name
            error = str(sys.exc_info()[0])
            logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
            return False

    def disconnect(self):
        try:
            if self.connected():
                self.connection.release()
            return True
        except:
            func = sys._getframe(1).f_code.co_name
            error = str(sys.exc_info()[0])
            logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
            return False

    def connected(self):
        try:
            if self.connection.connected:
                return True
            else:
                return False
        except:
            return False

    def get_channel(self):
        try:
            self.channel = self.connection.channel()
        except:
            func = sys._getframe(1).f_code.co_name
            error = str(sys.exc_info()[0])
            logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
            return False

    def get_exchange(self):
        try:
            self.exchange = Exchange(self.exchange_name, "topic", durable=True, auto_delete=False)
        except:
            func = sys._getframe(1).f_code.co_name
            error = str(sys.exc_info()[0])
            logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
            return False

    def create_producer(self):
        try:
            self.producer = Producer(
                            channel=self.channel,
                            exchange=self.exchange,
                            routing_key=self.virtual_host
                            )
        except:
            func = sys._getframe(1).f_code.co_name
            error = str(sys.exc_info()[0])
            logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
            return False

    def postmessage(self, message, retry=False):

        # process enqueud events if possible
        self.pop_events()

        if message["source_type"] == "component":
            key = "%s.%s.%s.%s.%s" % (
                    message["connector"],
                    message["connector_name"],
                    message["event_type"],
                    message["source_type"],
                    message["component"]
                )
        else:
            key = "%s.%s.%s.%s.%s[%s]" % (
                    message["connector"],
                    message["connector_name"],
                    message["event_type"],
                    message["source_type"],
                    message["component"],
                    message["resource"]
                )

        # connection management
        if not self.connected():
            logger.error("[Canopsis] Create connection")
            self.create_connection()
            self.connect()

        # publish message
        if self.connected():
            logger.info("[Canopsis] using routing key %s" % key)
            logger.info("[Canopsis] sending %s" % str(message))
            try:
                self.producer.revive(self.channel)
                self.producer.publish(body=message, compression=None, routing_key=key, exchange=self.exchange_name)
                return True
            except:
                logger.error("[Canopsis] Not connected, going to queue messages until connection back")
                self.queue.append({"key": key, "message": message})
                func = sys._getframe(1).f_code.co_name
                error = str(sys.exc_info()[0])
                logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
                # logger.error(str(traceback.format_exc()))
                return False
        else:
            errmsg = "[Canopsis] Not connected, going to queue messages until connection back (%s items in queue | max %s)" % (str(len(self.queue)), str(self.maxqueuelength))
            logger.info(errmsg)
            #enqueue_cano_event(key,message)
            if len(self.queue) < int(self.maxqueuelength):
                self.queue.append({"key": key, "message": message})
                logger.info("[Canopsis] Queue length: %d" % len(self.queue))
                return True
            else:
                logger.error("[Canopsis] Maximum retention for event queue %s reached" % str(self.maxqueuelength))
                return False

    def errback(self, exc, interval):
        logger.warning("Couldn't publish message: %r. Retry in %ds" % (exc, interval))

    def pop_events(self):
        if self.connected():
            while len(self.queue) > 0:
                item = self.queue.pop()
                try:
                    logger.info("[Canopsis] Pop item from queue [%s]: %s" % (str(len(self.queue)), str(item)))
                    self.producer.revive(self.channel)
                    self.producer.publish(body=item["message"], compression=None, routing_key=item["key"], exchange=self.exchange_name)
                except:
                    self.queue.append(item)
                    func = sys._getframe(1).f_code.co_name
                    error = str(sys.exc_info()[0])
                    logger.error("[Canopsis] Unexpected error: %s in %s" % (error, func))
                    return False
        else:
            return False

    def hook_tick(self, brok):

        self.tickage += 1

        # queue retention saving
        if self.tickage >= int(self.queue_dump_frequency) and len(self.queue) > 0:
            # flush queue to disk if queue age reach queue_dump_frequency
            self.save_queue()
            self.tickage = 0

        return True

    def save_queue(self):
        retentionfile = "%s/canopsis.dat" % os.getcwd()
        logger.info("[Canopsis] saving to %s" % retentionfile)
        filehandler = open(retentionfile, 'w')
        pickle.dump(self.queue, filehandler)
        filehandler.close()

        return True

    def load_queue(self):
        retentionfile = "%s/canopsis.dat" % os.getcwd()
        logger.info("[Canopsis] loading from %s" % retentionfile)
        filehandler = open(retentionfile, 'r')

        try:
            self.queue = pickle.load(filehandler)
        except:
            pass
        return True
