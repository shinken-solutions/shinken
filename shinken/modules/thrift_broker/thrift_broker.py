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


# This Class is a plugin for the Shinken Broker. It is in charge
# to brok information of the service perfdata into the file
# var/service-perfdata
# So it just manage the service_check_return
# Maybe one day host data will be usefull too
# It will need just a new file, and a new manager :)

import select
import socket
import sys
import os
import time
import errno
import re
import traceback
import threading

try:
    import sqlite3
except ImportError:  # python 2.4 do not have it
    try:
        import pysqlite2.dbapi2 as sqlite3  # but need the pysqlite2 install from http://code.google.com/p/pysqlite/downloads/list
    except ImportError:  # python 2.4 do not have it
        import sqlite as sqlite3  # one last try
import Queue

from shinken.objects import Host
from shinken.objects import Hostgroup
from shinken.objects import Service
from shinken.objects import Servicegroup
from shinken.objects import Contact
from shinken.objects import Contactgroup
from shinken.objects import Timeperiod
from shinken.objects import Command
from shinken.objects import Config
from shinken.schedulerlink import SchedulerLink
from shinken.reactionnerlink import ReactionnerLink
from shinken.pollerlink import PollerLink
from shinken.brokerlink import BrokerLink
from shinken.macroresolver import MacroResolver
from shinken.basemodule import BaseModule
from shinken.message import Message
from shinken.sorteddict import SortedDict

from shinken.modules.livestatus_broker.livestatus import LiveStatus as Thrift_status
from shinken.modules.livestatus_broker.mapping import out_map
from shinken.modules.livestatus_broker.hooker import Hooker
from thrift_query import ThriftQuery
from thrift_command_query import ThriftCommandQuery
from shinken.modules.livestatus_broker.log_line import LOGCLASS_ALERT, LOGCLASS_PROGRAM, LOGCLASS_NOTIFICATION, LOGCLASS_PASSIVECHECK, LOGCLASS_COMMAND, LOGCLASS_STATE, LOGCLASS_INVALID, LOGOBJECT_INFO, LOGOBJECT_HOST, LOGOBJECT_SERVICE, Logline

sys.path.append('/home/a2683/cvs/shinken/thrift/gen-py/')

from org.shinkenmonitoring.broker import Broker
from org.shinkenmonitoring.broker.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

properties = {
    'daemons': ['broker'],
    'type': 'thrift',
    'external': True,
    'phases': ['running'],
    }

tables = ["hosts", ""]


class Thrift_brokerHandler(Hooker):
    out_map = out_map

    def __init__(self, configs, hosts, services, contacts, hostgroups, servicegroups, contactgroups, timeperiods, commands, schedulers, pollers, reactionners, brokers, dbconn, pnp_path, return_queue):
        self.configs = configs
        self.hosts = hosts
        self.services = services
        self.contacts = contacts
        self.hostgroups = hostgroups
        self.servicegroups = servicegroups
        self.contactgroups = contactgroups
        self.timeperiods = timeperiods
        self.commands = commands
        self.schedulers = schedulers
        self.pollers = pollers
        self.reactionners = reactionners
        self.brokers = brokers
        self.dbconn = dbconn
        self.debuglevel = 2
        self.return_queue = return_queue

        #self.create_out_map_delegates()
        self.create_out_map_hooks()

    def sendCommand(self, command):
        print "sendCommand()"
        try:
            cmd = ThriftCommandQuery(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, '', self.return_queue, None)
            timestamp = time.time()
            cmd.extcmd = "[%lu] %s\n" % (timestamp, command)
            print cmd.extcmd
            cmd.launch_query()
        except Exception, e:
            print e

    def get(self, request):

        r = GetResponse()

        try:
            query = ThriftQuery(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, '', self.return_queue, None)

            # We build the query here, bypassing all parse functions of livestatus
            print request.table
            query.table = Table._VALUES_TO_NAMES[request.table]
            print query.table
            query.set_default_out_map_name()
            print query.out_map_name

            print "Using output parameters"
            if request.output is not None:
                query.limit = request.output.limit
                query.columns = request.output.columns

            print "Using filters parameters"
            if request.filters is not None:
                for filter in request.filters:
                    operator = filter.operator
                    if operator == "Or":
                        query.filter_stack.or_elements(int(filter.reference))
                    elif operator == "And":
                        query.filter_stack.and_elements(int(filter.reference))
                    else:
                        attribute = query.strip_table_from_column(filter.attribute)
                        if operator in ['!>', '!>=', '!<', '!<=']:
                            operator = {'!>': '<=', '!>=': '<', '!<': '>=', '!<=': '>'}[operator]
                        query.filtercolumns.append(attribute)
                        query.prefiltercolumns.append(attribute)
                        query.filter_stack.put(query.make_filter(operator, attribute, filter.reference))

            print "Using stats parameters"
            if request.stats is not None:
                query.stats_request = True
                for stat in request.stats:
                    operator = stat.operator
                    if operator == 'And':
                        query.stats_filter_stack.and_elements(int(stat.reference))
                    elif operator == 'Or':
                        query.stats_filter_stack.or_elements(int(stat.reference))
                    else:
                        if stat.attribute in ['sum', 'min', 'max', 'avg', 'std'] and reference.find('as ', 3) != -1:
                            query.aliases.append(alias)
                        attribute = query.strip_table_from_column(stat.attribute)
                        if operator in ['=', '>', '>=', '<', '<=', '=~', '~', '~~', '!=', '!>', '!>=', '!<', '!<=']:
                            if operator in ['!>', '!>=', '!<', '!<=']:
                                operator = {'!>': '<=', '!>=': '<', '!<': '>=', '!<=': '>'}[operator]
                            query.filtercolumns.append(attribute)
                            query.stats_columns.append(attribute)
                            query.stats_filter_stack.put(query.make_filter(operator, attribute, stat.reference))
                            query.stats_postprocess_stack.put(query.make_filter('count', attribute, None))
                        elif operator in ['sum', 'min', 'max', 'avg', 'std']:
                            query.stats_columns.append(attribute)
                            query.stats_filter_stack.put(query.make_filter('dummy', attribute, None))
                            query.stats_postprocess_stack.put(query.make_filter(operator, attribute, None))

            print "run query"
            result = query.launch_query()
            print query.response
            query.response.outputformat = 'csv'
            query.response.format_live_data(result, query.columns, query.aliases)
            output, keepalive = query.response.respond()
            print output
            r.result_table = output
        except Exception, e:
            r.rc = 1
            print e

        r.rc = 0

        return r


# Class for the Thrift Broker
# Get broks and listen to thrift query language requests
class Thrift_broker(BaseModule):
    def __init__(self, mod_conf, host, port, socket, allowed_hosts, database_file, max_logs_age, pnp_path, debug=None, debug_queries=False):
        BaseModule.__init__(self, mod_conf)
        self.host = host
        self.port = port
        self.socket = socket
        self.allowed_hosts = allowed_hosts
        self.database_file = database_file
        self.max_logs_age = max_logs_age
        self.pnp_path = pnp_path
        self.debug = debug
        self.debug_queries = debug_queries

        # Our datas
        self.configs = {}
        self.hosts = SortedDict()
        self.services = SortedDict()
        self.contacts = SortedDict()
        self.hostgroups = SortedDict()
        self.servicegroups = SortedDict()
        self.contactgroups = SortedDict()
        self.timeperiods = SortedDict()
        self.commands = SortedDict()
        # Now satellites
        self.schedulers = SortedDict()
        self.pollers = SortedDict()
        self.reactionners = SortedDict()
        self.brokers = SortedDict()
        self.service_id_cache = {}

        self.instance_ids = []

        self.number_of_objects = 0
        self.last_need_data_send = time.time()

    # Called by Broker so we can do init stuff
    def init(self):
        print "Initialisation of the thrift broker"

        # to_queue is where we get broks from Broker
        #self.to_q = self.properties['to_queue']

        # from_quue is where we push back objects like
        # external commands to the broker
        #self.from_q = self.properties['from_queue']

        # db has to be opened in the manage_brok thread
        self.prepare_log_db()
        self.prepare_pnp_path()

        self.thrift = Thrift_status(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.from_q)

        m = MacroResolver()
        m.output_macros = ['HOSTOUTPUT', 'HOSTPERFDATA', 'HOSTACKAUTHOR', 'HOSTACKCOMMENT', 'SERVICEOUTPUT', 'SERVICEPERFDATA', 'SERVICEACKAUTHOR', 'SERVICEACKCOMMENT']

    def manage_program_status_brok(self, b):
        data = b.data
        c_id = data['instance_id']
        print "Creating config:", c_id, data
        c = Config()
        for prop in data:
            setattr(c, prop, data[prop])
        #print "CFG:", c
        self.configs[0] = c
        # And we save that we got data from this instance_id
        self.instance_ids.append(c_id)

        # We should clean all previously added hosts and services
        inst_id = data['instance_id']
        to_del = []
        to_del_srv = []
        for h in self.hosts.values():
            # If the host was in this instance, del it
            if h.instance_id == inst_id:
                to_del.append(h.host_name)


        for s in self.services.values():
            if s.instance_id == inst_id:
                to_del_srv.append(s.host_name + s.service_description)

        # Now clean hostgroups too
        for hg in self.hostgroups.values():
            print "Len before exclude", len(hg.members)
            # Exclude from members the hosts with this inst_id
            hg.members = [h for h in hg.members if h.instance_id != inst_id]
            print "Len after", len(hg.members)

        # Now clean service groups
        for sg in self.servicegroups.values():
            sg.members = [s for s in sg.members if s.instance_id != inst_id]

        # Ok, really clean the hosts
        for i in to_del:
            try:
                del self.hosts[i]
            except KeyError:  # maybe it was not inserted in a good way, pass it
                pass

        # And services
        for i in to_del_srv:
            try:
                del self.services[i]
            except KeyError:  # maybe it was not inserted in a good way, pass it
                pass

    def manage_update_program_status_brok(self, b):
        data = b.data
        c_id = data['instance_id']

        if c_id not in self.instance_ids:
            # Do not ask data too quickly, very dangerous
            # one a minute
            if time.time() - self.last_need_data_send > 60:
                print "I ask the broker for instance id data:", c_id
                msg = Message(id=0, type='NeedData', data={'full_instance_id': c_id})
                self.from_q.put(msg)
                self.last_need_data_send = time.time()
            return

        # We have only one config here, with id 0
        c = self.configs[0]
        self.update_element(c, data)

    def set_schedulingitem_values(self, i):
        i.check_period = self.get_timeperiod(i.check_period)
        i.notification_period = self.get_timeperiod(i.notification_period)
        i.contacts = self.get_contacts(i.contacts)
        i.rebuild_ref()
        #Escalations is not use for status_dat
        del i.escalations

    def manage_initial_host_status_brok(self, b):
        data = b.data

        host_name = data['host_name']
        inst_id = data['instance_id']
        #print "Creating host:", h_id, b
        h = Host({})
        self.update_element(h, data)
        self.set_schedulingitem_values(h)

        h.service_ids = []
        h.services = []
        h.instance_id = inst_id
        # We need to rebuild Downtime and Comment relationship
        for dtc in h.downtimes + h.comments:
            dtc.ref = h
        self.hosts[host_name] = h
        self.number_of_objects += 1

    # In fact, an update of a host is like a check return
    def manage_update_host_status_brok(self, b):
        self.manage_host_check_result_brok(b)
        data = b.data
        host_name = data['host_name']
        # In the status, we've got duplicated item, we must relink thems
        try:
            h = self.hosts[host_name]
        except KeyError:
            print "Warning: the host %s is unknown!" % host_name
            return
        self.update_element(h, data)
        self.set_schedulingitem_values(h)
        for dtc in h.downtimes + h.comments:
            dtc.ref = h
        self.thrift.count_event('host_checks')

    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data
        hostgroup_name = data['hostgroup_name']
        members = data['members']
        del data['members']

        # Maybe we already got this hostgroup. If so, use the existing object
        # because in different instance, we will ahve the same group with different
        # elements
        try:
            hg = self.hostgroups[hostgroup_name]
        except KeyError:
            # If we got none, create a new one
            #print "Creating hostgroup:", hg_id, data
            hg = Hostgroup()
            # Set by default members to a void list
            setattr(hg, 'members', [])

        self.update_element(hg, data)

        for (h_id, h_name) in members:
            if h_name in self.hosts:
                hg.members.append(self.hosts[h_name])
                # Should got uniq value, do uniq this list
                hg.members = list(set(hg.members))

        #print "HG:", hg
        self.hostgroups[hostgroup_name] = hg
        self.number_of_objects += 1

    def manage_initial_service_status_brok(self, b):
        data = b.data
        s_id = data['id']
        host_name = data['host_name']
        service_description = data['service_description']
        inst_id = data['instance_id']

        #print "Creating Service:", s_id, data
        s = Service({})
        s.instance_id = inst_id

        self.update_element(s, data)
        self.set_schedulingitem_values(s)

        try:
            h = self.hosts[host_name]
            # Reconstruct the connection between hosts and services
            h.services.append(s)
            # There is already a s.host_name, but a reference to the h object can be useful too
            s.host = h
        except Exception:
            return
        for dtc in s.downtimes + s.comments:
            dtc.ref = s
        self.services[host_name + service_description] = s
        self.number_of_objects += 1
        # We need this for manage_initial_servicegroup_status_brok where it
        # will speed things up dramatically
        self.service_id_cache[s.id] = s

    # In fact, an update of a service is like a check return
    def manage_update_service_status_brok(self, b):
        self.manage_service_check_result_brok(b)
        data = b.data
        host_name = data['host_name']
        service_description = data['service_description']
        # In the status, we've got duplicated item, we must relink thems
        try:
            s = self.services[host_name + service_description]
        except KeyError:
            print "Warning: the service %s/%s is unknown!" % (host_name, service_description)
            return
        self.update_element(s, data)
        self.set_schedulingitem_values(s)
        for dtc in s.downtimes + s.comments:
            dtc.ref = s
        self.thrift.count_event('service_checks')

    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data
        sg_id = data['id']
        servicegroup_name = data['servicegroup_name']
        members = data['members']
        del data['members']

        # Like for hostgroups, maybe we already got this
        # service group from another instance, need to
        # factorize all
        try:
            sg = self.servicegroups[servicegroup_name]
        except KeyError:
            #print "Creating servicegroup:", sg_id, data
            sg = Servicegroup()
            # By default set members as a void list
            setattr(sg, 'members', [])

        self.update_element(sg, data)

        for (s_id, s_name) in members:
            # A direct lookup by s_host_name+s_name is not possible
            # because we don't have the host_name in members, only ids.
            try:
                sg.members.append(self.service_id_cache[s_id])
            except Exception:
                pass

        sg.members = list(set(sg.members))
        self.servicegroups[servicegroup_name] = sg
        self.number_of_objects += 1

    def manage_initial_contact_status_brok(self, b):
        data = b.data
        contact_name = data['contact_name']
        #print "Creating Contact:", c_id, data
        c = Contact({})
        self.update_element(c, data)
        #print "C:", c
        self.contacts[contact_name] = c
        self.number_of_objects += 1

    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data
        contactgroup_name = data['contactgroup_name']
        members = data['members']
        del data['members']
        #print "Creating contactgroup:", cg_id, data
        cg = Contactgroup()
        self.update_element(cg, data)
        setattr(cg, 'members', [])
        for (c_id, c_name) in members:
            if c_name in self.contacts:
                cg.members.append(self.contacts[c_name])
        #print "CG:", cg
        self.contactgroups[contactgroup_name] = cg
        self.number_of_objects += 1

    def manage_initial_timeperiod_status_brok(self, b):
        data = b.data
        timeperiod_name = data['timeperiod_name']
        #print "Creating Timeperiod:", tp_id, data
        tp = Timeperiod({})
        self.update_element(tp, data)
        #print "TP:", tp
        self.timeperiods[timeperiod_name] = tp
        self.number_of_objects += 1

    def manage_initial_command_status_brok(self, b):
        data = b.data
        command_name = data['command_name']
        #print "Creating Command:", c_id, data
        c = Command({})
        self.update_element(c, data)
        #print "CMD:", c
        self.commands[command_name] = c
        self.number_of_objects += 1

    def manage_initial_scheduler_status_brok(self, b):
        data = b.data
        scheduler_name = data['scheduler_name']
        print "Creating Scheduler:", scheduler_name, data
        sched = SchedulerLink({})
        print "Created a new scheduler", sched
        self.update_element(sched, data)
        print "Updated scheduler"
        #print "CMD:", c
        self.schedulers[scheduler_name] = sched
        print "scheduler added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1

    def manage_update_scheduler_status_brok(self, b):
        data = b.data
        scheduler_name = data['scheduler_name']
        try:
            s = self.schedulers[scheduler_name]
            self.update_element(s, data)
            #print "S:", s
        except Exception:
            pass

    def manage_initial_poller_status_brok(self, b):
        data = b.data
        poller_name = data['poller_name']
        print "Creating Poller:", poller_name, data
        poller = PollerLink({})
        print "Created a new poller", poller
        self.update_element(poller, data)
        print "Updated poller"
        #print "CMD:", c
        self.pollers[poller_name] = poller
        print "poller added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1

    def manage_update_poller_status_brok(self, b):
        data = b.data
        poller_name = data['poller_name']
        try:
            s = self.pollers[poller_name]
            self.update_element(s, data)
        except Exception:
            pass

    def manage_initial_reactionner_status_brok(self, b):
        data = b.data
        reactionner_name = data['reactionner_name']
        print "Creating Reactionner:", reactionner_name, data
        reac = ReactionnerLink({})
        print "Created a new reactionner", reac
        self.update_element(reac, data)
        print "Updated reactionner"
        #print "CMD:", c
        self.reactionners[reactionner_name] = reac
        print "reactionner added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1

    def manage_update_reactionner_status_brok(self, b):
        data = b.data
        reactionner_name = data['reactionner_name']
        try:
            s = self.reactionners[reactionner_name]
            self.update_element(s, data)
        except Exception:
            pass

    def manage_initial_broker_status_brok(self, b):
        data = b.data
        broker_name = data['broker_name']
        print "Creating Broker:", broker_name, data
        broker = BrokerLink({})
        print "Created a new broker", broker
        self.update_element(broker, data)
        print "Updated broker"
        #print "CMD:", c
        self.brokers[broker_name] = broker
        print "broker added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1

    def manage_update_broker_status_brok(self, b):
        data = b.data
        broker_name = data['broker_name']
        try:
            s = self.brokers[broker_name]
            self.update_element(s, data)
        except Exception:
            pass

    # A service check have just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        host_name = data['host_name']
        service_description = data['service_description']
        try:
            s = self.services[host_name + service_description]
            self.update_element(s, data)
        except Exception:
            pass

    # A service check update have just arrived, we UPDATE data info with this
    def manage_service_next_schedule_brok(self, b):
        self.manage_service_check_result_brok(b)

    def manage_host_check_result_brok(self, b):
        data = b.data
        host_name = data['host_name']
        try:
            h = self.hosts[host_name]
            self.update_element(h, data)
        except Exception:
            pass

    # this brok should arrive within a second after the host_check_result_brok
    def manage_host_next_schedule_brok(self, b):
        self.manage_host_check_result_brok(b)

    # A log brok will be written into a database
    def manage_log_brok(self, b):
        data = b.data
        line = data['log'].encode('UTF-8').rstrip()
        # split line and make sql insert
        #print "LOG--->", line
        # [1278280765] SERVICE ALERT: test_host_0
        # split leerzeichen
        if line[0] != '[' and line[11] != ']':
            pass
            print "INVALID"
            # invalid
        else:
            service_states = {'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'UNKNOWN': 3, 'RECOVERY': 0}
            host_states = {'UP': 0, 'DOWN': 1, 'UNREACHABLE': 2, 'UNKNOWN': 3, 'RECOVERY': 0}

            # 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message',
            # 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type',
            # 0:info, 1:state, 2:program, 3:notification, 4:passive, 5:command

            # lineno, message?, plugin_output?
            logobject = LOGOBJECT_INFO
            logclass = LOGCLASS_INVALID
            attempt, state = [0] * 2
            command_name, comment, contact_name, host_name, message, options, plugin_output, service_description, state_type = [''] * 9
            time = line[1:11]
            #print "i start with a timestamp", time
            first_type_pos = line.find(' ') + 1
            last_type_pos = line.find(':')
            first_detail_pos = last_type_pos + 2
            type = line[first_type_pos:last_type_pos]
            options = line[first_detail_pos:]
            message = line
            if type == 'CURRENT SERVICE STATE':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_STATE
                host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
            elif type == 'INITIAL SERVICE STATE':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_STATE
                host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
            elif type == 'SERVICE ALERT':
                # SERVICE ALERT: srv-40;Service-9;CRITICAL;HARD;1;[Errno 2] No such file or directory
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_ALERT
                host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
                state = service_states[state]
            elif type == 'SERVICE DOWNTIME ALERT':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_ALERT
                host_name, service_description, state_type, comment = options.split(';', 3)
            elif type == 'SERVICE FLAPPING ALERT':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_ALERT
                host_name, service_description, state_type, comment = options.split(';', 3)

            elif type == 'CURRENT HOST STATE':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_STATE
                host_name, state, state_type, attempt, plugin_output = options.split(';', 4)
            elif type == 'INITIAL HOST STATE':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_STATE
                host_name, state, state_type, attempt, plugin_output = options.split(';', 4)
            elif type == 'HOST ALERT':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_ALERT
                host_name, state, state_type, attempt, plugin_output = options.split(';', 4)
                state = host_states[state]
            elif type == 'HOST DOWNTIME ALERT':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_ALERT
                host_name, state_type, comment = options.split(';', 2)
            elif type == 'HOST FLAPPING ALERT':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_ALERT
                host_name, state_type, comment = options.split(';', 2)

            elif type == 'SERVICE NOTIFICATION':
                # tust_cuntuct;test_host_0;test_ok_0;CRITICAL;notify-service;i am CRITICAL  <-- normal
                # SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;DOWNTIMESTART (OK);notify-service;OK
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_NOTIFICATION
                contact_name, host_name, service_description, state_type, command_name, check_plugin_output = options.split(';', 5)
                if '(' in state_type:  # downtime/flapping/etc-notifications take the type UNKNOWN
                    state_type = 'UNKNOWN'
                state = service_states[state_type]
            elif type == 'HOST NOTIFICATION':
                # tust_cuntuct;test_host_0;DOWN;notify-host;i am DOWN
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_NOTIFICATION
                contact_name, host_name, state_type, command_name, check_plugin_output = options.split(';', 4)
                if '(' in state_type:
                    state_type = 'UNKNOWN'
                state = host_states[state_type]

            elif type == 'PASSIVE SERVICE CHECK':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_PASSIVECHECK
                host_name, service_description, state, check_plugin_output = options.split(';', 3)
            elif type == 'PASSIVE HOST CHECK':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_PASSIVECHECK
                host_name, state, check_plugin_output = options.split(';', 2)

            elif type == 'SERVICE EVENT HANDLER':
                # SERVICE EVENT HANDLER: test_host_0;test_ok_0;CRITICAL;SOFT;1;eventhandler
                logobject = LOGOBJECT_SERVICE
                host_name, service_description, state, state_type, attempt, command_name = options.split(';', 5)
                state = service_states[state]
            elif type == 'HOST EVENT HANDLER':
                logobject = LOGOBJECT_HOST
                host_name, state, state_type, attempt, command_name = options.split(';', 4)
                state = host_states[state]

            elif type == 'EXTERNAL COMMAND':
                logobject = LOGOBJECT_INFO
                logclass = LOGCLASS_COMMAND
            elif type.startswith('starting...') or \
                 type.startswith('shutting down...') or \
                 type.startswith('Bailing out') or \
                 type.startswith('active mode...') or \
                 type.startswith('standby mode...'):
                logobject = LOGOBJECT_INFO
                logclass = LOGCLASS_PROGRAM
            else:
                pass
                #print "does not match"

            lineno = 0

            try:
                values = (logobject, attempt, logclass, command_name, comment, contact_name, host_name, lineno, message, options, plugin_output, service_description, state, state_type, time, type)
            except:
                print "Unexpected error:", sys.exc_info()[0]
            #print "LOG:", logobject, logclass, type, host_name, service_description, state, state_type, attempt, plugin_output, contact_name, comment, command_name
            #print "LOG:", values
            try:
                if logclass != LOGCLASS_INVALID:
                    if sqlite3.paramstyle == 'pyformat':
                        values = dict(zip([str(x) for x in xrange(len(values))], values))
                        self.dbcursor.execute('INSERT INTO LOGS VALUES(%(0)s, %(1)s, %(2)s, %(3)s, %(4)s, %(5)s, %(6)s, %(7)s, %(8)s, %(9)s, %(10)s, %(11)s, %(12)s, %(13)s, %(14)s, %(15)s)', values)
                    else:
                        self.dbcursor.execute('INSERT INTO LOGS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', values)
                    self.dbconn.commit()
            except sqlite3.Error, e:
                print "An error occurred:", e.args[0]
                print "DATABASE ERROR!!!!!!!!!!!!!!!!!"
        self.thrift.count_event('log_message')

    # The contacts must not be duplicated
    def get_contacts(self, cs):
        r = []
        for c in cs:
            if c is not None:
                find_c = self.find_contact(c.get_name())
                if find_c is not None:
                    r.append(find_c)
                else:
                    print "Error: search for a contact %s that do not exists!" % c.get_name()
        return r

    # The timeperiods must not be duplicated
    def get_timeperiod(self, t):
        if t is not None:
            find_t = self.find_timeperiod(t.get_name())
            if find_t is not None:
                return find_t
            else:
                print "Error: search for a timeperiod %s that do not exists!" % t.get_name()
        else:
            return None

    def find_timeperiod(self, timeperiod_name):
        try:
            return self.timeperiods[timeperiod_name]
        except KeyError:
            return None

    def find_contact(self, contact_name):
        try:
            return self.contacts[contact_name]
        except KeyError:
            return None

    def update_element(self, e, data):
        #print "........%s........" % type(e)
        for prop in data:
            #if hasattr(e, prop):
            #    print "%-20s\t%s\t->\t%s" % (prop, getattr(e, prop), data[prop])
            #else:
            #    print "%-20s\t%s\t->\t%s" % (prop, "-", data[prop])
            setattr(e, prop, data[prop])

    def prepare_log_db(self):
        # create db file and tables if not existing
        self.dbconn = sqlite3.connect(self.database_file, check_same_thread=False)
        self.dbcursor = self.dbconn.cursor()
        # 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message',
        # 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type',
        cmd = "CREATE TABLE IF NOT EXISTS logs(logobject INT, attempt INT, class INT, command_name VARCHAR(64), comment VARCHAR(256), contact_name VARCHAR(64), host_name VARCHAR(64), lineno INT, message VARCHAR(512), options VARCHAR(512), plugin_output VARCHAR(256), service_description VARCHAR(64), state INT, state_type VARCHAR(10), time INT, type VARCHAR(64))"
        self.dbcursor.execute(cmd)
        cmd = "CREATE INDEX IF NOT EXISTS logs_time ON logs (time)"
        self.dbcursor.execute(cmd)
        cmd = "PRAGMA journal_mode=truncate"
        self.dbcursor.execute(cmd)
        self.dbconn.commit()
        # rowfactory will later be redefined (in thrift.py)

    def cleanup_log_db(self):
        limit = int(time.time() - self.max_logs_age * 86400)
        print "Deleting messages from the log database older than %s" % time.asctime(time.localtime(limit))
        if sqlite3.paramstyle == 'pyformat':
            self.dbcursor.execute('DELETE FROM LOGS WHERE time < %(limit)s', {'limit': limit})
        else:
            self.dbcursor.execute('DELETE FROM LOGS WHERE time < ?', (limit,))
        self.dbconn.commit()
        # This is necessary to shrink the database file
        try:
            self.dbcursor.execute('VACUUM')
        except sqlite3.DatabaseError, exp:
            print "WARNING: yit seems your database is corrupted. Please recreate it"
        self.dbconn.commit()

    def prepare_pnp_path(self):
        if not self.pnp_path:
            self.pnp_path = False
        elif not os.access(self.pnp_path, os.R_OK):
            print "PNP perfdata path %s is not readable" % self.pnp_path
        elif not os.access(self.pnp_path, os.F_OK):
            print "PNP perfdata path %s does not exist" % self.pnp_path
        if self.pnp_path and not self.pnp_path.endswith('/'):
            self.pnp_path += '/'

    def do_stop(self):
        print "[thrift] So I quit"
        for s in self.input:
            try:
                s.shutdown()
                s.close()
            except:
                # no matter what comes, i'm finished
                pass
        try:
            self.dbconn.commit()
            self.dbconn.close()
        except:
            pass

    def set_debug(self):
        fdtemp = os.open(self.debug, os.O_CREAT | os.O_WRONLY | os.O_APPEND)

        ## We close out and err
        os.close(1)
        os.close(2)

        os.dup2(fdtemp, 1)  # standard output (1)
        os.dup2(fdtemp, 2)  # standard error (2)

    def main(self):
        try:
            #import cProfile
            #cProfile.runctx('''self.do_main()''', globals(), locals(),'/tmp/thrift.profile')
            self.do_main()
        except Exception, exp:

            msg = Message(id=0, type='ICrash', data={'name': self.get_name(), 'exception': exp, 'trace': traceback.format_exc()})
            self.from_q.put(msg)
            # wait 2 sec so we know that the broker got our message, and die
            time.sleep(2)
            raise

    def manage_broks(self, *args):
        while True:
            try:
                l = self.to_q.get(True, .01)
                for b in l:
                    # unserialize the brok beofre use it
                    b.prepare()
                    self.manage_brok(b)
            except Queue.Empty:
                pass
            except IOError, e:
                if hasattr(os, 'errno') and e.errno != os.errno.EINTR:
                    raise
            # But others are importants
            except Exception, exp:
                print "Error: got an exeption (bad code?)", exp.__dict__, type(exp)
                raise

    def do_main(self):
        # I register my exit function
        self.set_exit_handler()

        # Maybe we got a debug dump to do
        if self.debug:
            self.set_debug()

        # Start the thread to manage brok
        broks_manager_thread = threading.Thread(None, self.manage_broks, "broks manager", args=[self])
        broks_manager_thread.start()

        # Start the thrift server
        handler = Thrift_brokerHandler(self.configs, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.from_q)
        processor = Broker.Processor(handler)
        transport = TSocket.TServerSocket("0.0.0.0", self.port)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

        print 'Starting the server...'
        server.serve()
        print 'done.'

        self.do_stop()

        return


def thrift_factory(cursor, row):
    return Logline(row)
