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

properties = {
    'daemons' : ['broker'],
    'type' : 'canopsis',
    'external' : False,
    'phases' : ['running'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a canopsis broker for plugin %s" % plugin.get_name()
    host            = getattr(plugin, 'host', None)
    port            = getattr(plugin, 'port', None)
    user            = getattr(plugin, 'user', None)
    password        = getattr(plugin, 'password', None)
    virtual_host    = getattr(plugin, 'virtual_host', None)                
    exchange_name   = getattr(plugin, 'exchange_name', None)                

    instance = Canopsis_broker(plugin, host, port, user, password, virtual_host, exchange_name)
    # instance = Canopsis_broker(plugin)
    return instance


#Class for the Npcd Broker
#Get broks and put them well-formatted in a spool file
class Canopsis_broker(BaseModule):
    def __init__(self, modconf, host, port, user, password, virtual_host, exchange_name):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.virtual_host = virtual_host
        self.exchange_name = exchange_name

    #We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        print "[Canopsis] Info : manage_brok %s" % (b.type)
#        if b.type == "host_check_result":
#            self.manage_host_check_result_brok(b)
#        elif b.type == "service_check_result":
#            self.manage_service_check_result_brok(b)
        # elif b.type == "update_service_status":
        #     self.manage_update_service_status_brok(b)
        # else:
        #     print "[Canopsis] Warning : unmanaged brok type %s" % (b.type)

    # A host check has just arrived. Write the performance data to the file
    def manage_host_check_result_brok(self, b):
        message = self.create_message('component','check',b)
        print message

    # A service check has just arrived. Write the performance data to the file
    def manage_service_check_result_brok(self, b):
        message = self.create_message('ressource','check',b)
        print message

    # def manage_update_service_status_brok(self,b):
    #     print "[Canopsis] Info : in manage_update_service_status_brok"              

    # def manage_notification_raise_brok(self, b):


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

            message format : 
                {
                  'connector':      Connector type (gelf, nagios, snmp, ...),
                  'connector_name': Connector name (nagios1, nagios2 ...),
                  'event_type':     Event type (check, log, trap, ...),
                  'source_type':    Source type (component or resource),
                  'component':      Component name,
                  'resource':       Ressource name,
                  'timestamp':      UNIX seconds timestamp,
                  'state':          State (0 (Ok), 1 (Warning), 2 (Critical), 3 (Unknown)),
                  'state_type':     State type (O (Soft), 1 (Hard)),
                  'output':         Event message,
                  'long_output':    Event long message,
                }

        """

        if source_type == 'ressource':
            #service
            specificmessage={
                'ressource' : b.data['service_description'],
                'command_name' : b.data['check_command'].get_name(),
                'max_attempts' : b.data['max_check_attempts'].get_name()
            }
        elif source_type == 'component':
            #host
            specificmessage={
                'ressource' : None,
                'max_attempts' : 1,
                'command_name' : None
            }
        else:
            return None

        commonmessage={
            'connector' : 'shinken',
            'connector_name' : 'shinken',
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
            'command_name' : b.data['check_command'].get_name(),
            'address' : ', '.join(b.data['hosts'])
        }


        return dict(commonmessage,**specificmessage)
