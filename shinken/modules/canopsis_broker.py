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

#This Class is a plugin for the Shinken Broker. It's job is to write
#host and service perfdata to a file which can be processes by the
#canopsis daemon (http://pnp4nagios.org). It is a reimplementation of canopsis.c

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons' : ['broker'],
    'type' : 'canopsis',
    'external' : False,
    'phases' : ['running'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    # logger.info("Info","Get a canopsis broker for plugin %s" % (str(plugin.get_name())))

    host            = getattr(plugin, 'host', None)
    port            = getattr(plugin, 'port', None)
    user            = getattr(plugin, 'user', None)
    password        = getattr(plugin, 'password', None)
    virtual_host    = getattr(plugin, 'virtual_host', None)                
    exchange_name   = getattr(plugin, 'exchange_name', None)  
    identifier      = getattr(plugin, 'identifier', None)               

    return Canopsis_broker(plugin, host, port, user, password, virtual_host, exchange_name,identifier)


#Class for the Npcd Broker
#Get broks and put them well-formatted in a spool file
class Canopsis_broker(BaseModule):
    def __init__(self, modconf, host, port, user, password, virtual_host, exchange_name, identifier):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.virtual_host = virtual_host
        self.exchange_name = exchange_name
        self.identifier = identifier

    #We call functions like manage_ TYPEOFBROK _brok that return us queries
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

        if not hasattr(self,'host_commands'):
            self.host_commands = {}

        if not hasattr(self,'host_addresses'):
            self.host_addresses = {}

        if not hasattr(self,'host_max_check_attempts'):
            self.host_max_check_attempts = {}

        # check commands does not appear in check results so build a dict of check_commands
        self.host_commands[b.data['host_name']] = b.data['check_command'].call

        # address does not appear in check results so build a dict of addresses
        self.host_addresses[b.data['host_name']] = b.data['address']

        # max_check_attempts does not appear in check results so build a dict of max_check_attempts
        self.host_max_check_attempts[b.data['host_name']] = b.data['max_check_attempts']

        logger.info("[canopsis] initial host max attempts : %s " % str(self.host_max_check_attempts))
        logger.info("[canopsis] initial host commands : %s " % str(self.host_commands))        
        logger.info("[canopsis] initial host addresses : %s " % str(self.host_addresses))        


    def manage_initial_service_status_brok(self, b):
        logger.log("[Canopsis] processing initial_service_status")

        if not hasattr(self,'service_commands'):
            logger.log("[Canopsis] creating empty dict in service_commands")
            self.service_commands = {}

        if not hasattr(self,'service_max_check_attempts'):
            logger.log("[Canopsis] creating empty dict in service_max_check_attempts")
            self.service_max_check_attempts = {}

        if not b.data['host_name'] in self.service_commands:
            logger.log("[Canopsis] creating empty dict for host %s service_commands" % b.data['host_name'])            
            self.service_commands[b.data['host_name']] = {}

        self.service_commands[b.data['host_name']][b.data['service_description']] = b.data['check_command'].call

        if not b.data['host_name'] in self.service_max_check_attempts:
            logger.log("[Canopsis] creating empty dict for host %s service_max_check_attempts" % b.data['host_name'])            
            self.service_commands[b.data['host_name']] = {}

        self.service_max_check_attempts[b.data['host_name']][b.data['service_description']] = b.data['max_check_attempts']



    def manage_host_check_result_brok(self, b):
        message = self.create_message('component','check',b)
        if not message:
            logger.info("[Canopsis] Warning : Empty host check message")
        else:
            self.push2canopsis(message)

    # A service check has just arrived. Write the performance data to the file
    def manage_service_check_result_brok(self, b):
        message = self.create_message('ressource','check',b)
        if not message:
            logger.info("[Canopsis] Warning : Empty service check message")
        else:
            self.push2canopsis(message)

    def create_message(self,source_type,event_type,b):
        """
            event_type should be one of the following :
                - check
                - ack
                - notification
                - downtime

            source_type should be one of the following :
                - component => host
                - ressource => service

            message format (check): 

            H S         field               desc
            x           'connector'         Connector type (gelf, nagios, snmp, ...)
            x           'connector_name':   Connector name (nagios1, nagios2 ...)
            x           'event_type'        Event type (check, log, trap, ...)
            x           'source_type'       Source type (component or resource)
            x           'component'         Component name
            x           'resource'          Ressource name
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

        if source_type == 'ressource':
            #service
            specificmessage={
                'ressource' : b.data['service_description'],
                'command_name' : self.service_commands[b.data['host_name']][b.data['service_description']],
                'max_attempts' : self.service_max_check_attempts[b.data['host_name']][b.data['service_description']],
            }
        elif source_type == 'component':
            #host
            specificmessage={
                'ressource' : None,
                'command_name' : self.host_commands[b.data['host_name']],
                'max_check_attempts' : self.host_max_check_attempts[b.data['host_name']]
            }
        else:
            # WTF ?!
            logger.info("[Canopsis] Invalid source_type %s" %(source_type))
            return None

        commonmessage={
            'connector' : u'shinken',
            'connector_name' : unicode(self.identifier),
            'event_type' : event_type,
            'source_type' : source_type,
            'component' : b.data['host_name'],
            'timestamp' : b.data['last_chk'],
            'state' : b.data['state_id'],
            'state_type' : b.data['state_type_id'],
            'output' : b.data['output'],
            'long_output' : b.data['long_output'],
            'perf_data' : b.data['perf_data'],
            'check_type' : b.data['check_type'],
            'current_attempt' : b.data['attempt'],
            'execution_time' : b.data['execution_time'],
            'latency' : b.data['latency'],
            'address' : self.host_addresses[b.data['host_name']]
        }

        return dict(commonmessage,**specificmessage)

    def push2canopsis(self,message):
        strmessage=str(message)
        logger.info("[Canopsis] push2canopsis : %s" % (strmessage))