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


#This Class is a plugin for the Shinken Broker. It is in charge
#to brok information of the service perfdata into the file
#var/service-perfdata
#So it just manage the service_check_return
#Maybe one day host data will be usefull too
#It will need just a new file, and a new manager :)

import select
import socket
import sys
import os
import time
import errno
try:
    import sqlite3
except ImportError: # python 2.4 do not have it
    try:
        import pysqlite2.dbapi2 as sqlite3 # but need the pysqlite2 install from http://code.google.com/p/pysqlite/downloads/list
    except ImportError: # python 2.4 do not have it
        import sqlite as sqlite3 # one last try
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

from livestatus import LiveStatus, LOGCLASS_ALERT, LOGCLASS_PROGRAM, LOGCLASS_NOTIFICATION, LOGCLASS_PASSIVECHECK, LOGCLASS_COMMAND, LOGCLASS_STATE, LOGCLASS_INVALID, LOGOBJECT_INFO, LOGOBJECT_HOST, LOGOBJECT_SERVICE, Logline


properties = {
    'type' : 'livestatus',
    'external' : True,
    'phases' : ['running'],
    }


#Class for the Livestatus Broker
#Get broks and listen to livestatus query language requests
class Livestatus_broker(BaseModule):
    def __init__(self, mod_conf, host, port, socket, allowed_hosts, database_file, max_logs_age, pnp_path):
        BaseModule.__init__(self, mod_conf)
        self.host = host
        self.port = port
        self.socket = socket
        self.allowed_hosts = allowed_hosts
        self.database_file = database_file
        self.max_logs_age = max_logs_age
        self.pnp_path = pnp_path

        #Our datas
        self.configs = {}
        self.hosts = {}
        self.services = {}
        self.contacts = {}
        self.hostgroups = {}
        self.servicegroups = {}
        self.contactgroups = {}
        self.timeperiods = {}
        self.commands = {}
        #Now satellites
        self.schedulers = {}
        self.pollers = {}
        self.reactionners = {}
        self.brokers = {}

        self.hostname_lookup_table = {}
        self.servicename_lookup_table = {}

        self.number_of_objects = 0


    #Called by Broker so we can do init stuff
    def init(self):
        print "Initialisation of the livestatus broker"

        #to_queue is where we get broks from Broker
        #self.to_q = self.properties['to_queue']

        #from_quue is where we push back objects like
        #external commands to the broker
        #self.from_q = self.properties['from_queue']

        self.prepare_log_db()
        self.prepare_pnp_path()


        self.livestatus = LiveStatus(self.configs, self.hostname_lookup_table, self.servicename_lookup_table, self.hosts, self.services, self.contacts, self.hostgroups, self.servicegroups, self.contactgroups, self.timeperiods, self.commands, self.schedulers, self.pollers, self.reactionners, self.brokers, self.dbconn, self.pnp_path, self.from_q)

        m = MacroResolver()
        m.output_macros = ['HOSTOUTPUT', 'HOSTPERFDATA', 'HOSTACKAUTHOR', 'HOSTACKCOMMENT', 'SERVICEOUTPUT', 'SERVICEPERFDATA', 'SERVICEACKAUTHOR', 'SERVICEACKCOMMENT']


    def manage_program_status_brok(self, b):
        data = b.data
        c_id = data['instance_id']
        #print "Creating config:", c_id, data
        c = Config()
        for prop in data:
            setattr(c, prop, data[prop])
        #print "CFG:", c
        self.configs[c_id] = c


    def manage_update_program_status_brok(self, b):
        data = b.data
        c_id = data['instance_id']
        # We have only one config here, with id 0
        c = self.configs[0]
        self.update_element(c, data)
    

    def set_schedulingitem_values(self, i):
        i.check_period = self.get_timeperiod(i.check_period)
        i.notification_period = self.get_timeperiod(i.notification_period)
        i.contacts = self.get_contacts(i.contacts)
        #Escalations is not use for status_dat
        del i.escalations
        
    def set_ref_attributes_on_item(self, i):
        for g in i.comments, i.downtimes: 
            for e in g:
                e.ref = i
        
    def manage_initial_host_status_brok(self, b):
        data = b.data
        h_id = data['id']
        #print "Creating host:", h_id, data
        h = Host({})
        self.update_element(h, data)        
        self.set_schedulingitem_values(h)
        self.set_ref_attributes_on_item(h)
        
        h.service_ids = []
        h.services = []
        self.hosts[h_id] = h
        self.hostname_lookup_table[h.host_name] = h_id
        self.number_of_objects += 1

    #In fact, an update of a host is like a check return
    def manage_update_host_status_brok(self, b):
        self.manage_host_check_result_brok(b)
        data = b.data
        #In the status, we've got duplicated item, we must relink thems
        h = self.find_host(data['host_name'])
        if h == None:
            print "Warning : the host %s is unknown!" % data['host_name']
            return
        
        self.set_schedulingitem_values(h)
        self.set_ref_attributes_on_item(h)

    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data
        hg_id = data['id']
        members = data['members']
        del data['members']
        #print "Creating hostgroup:", hg_id, data
        hg = Hostgroup()
        self.update_element(hg, data)
        setattr(hg, 'members', [])
        for (h_id, h_name) in members:
            if h_id in self.hosts:
                hg.members.append(self.hosts[h_id])
        #print "HG:", hg
        self.hostgroups[hg_id] = hg
        self.number_of_objects += 1


    def manage_initial_service_status_brok(self, b):
        data = b.data
        s_id = data['id']
        #print "Creating Service:", s_id, data
        s = Service({})
        self.update_element(s, data)
        self.set_schedulingitem_values(s)
        self.set_ref_attributes_on_item(s)
        
        h = self.find_host(data['host_name'])
        if h != None:
            # Reconstruct the connection between hosts and services
            h.service_ids.append(s_id)
            h.services.append(s)
            # There is already a s.host_name, but a reference to the h object can be useful too
            s.host = h
        
        self.services[s_id] = s
        self.servicename_lookup_table[s.host_name + s.service_description] = s_id
        self.number_of_objects += 1


    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data
        sg_id = data['id']
        members = data['members']
        del data['members']
        #print "Creating servicegroup:", sg_id, data
        sg = Servicegroup()
        self.update_element(sg, data)
        setattr(sg, 'members', [])
        for (s_id, s_name) in members:
            if s_id in self.services:
                sg.members.append(self.services[s_id])
        #print "SG:", sg
        self.servicegroups[sg_id] = sg
        self.number_of_objects += 1


    def manage_initial_contact_status_brok(self, b):
        data = b.data
        c_id = data['id']
        #print "Creating Contact:", c_id, data
        c = Contact({})
        self.update_element(c, data)
        #print "C:", c
        self.contacts[c_id] = c
        self.number_of_objects += 1


    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data
        cg_id = data['id']
        members = data['members']
        del data['members']
        #print "Creating contactgroup:", cg_id, data
        cg = Contactgroup()
        self.update_element(cg, data)
        setattr(cg, 'members', [])
        for (c_id, c_name) in members:
            if c_id in self.contacts:
                cg.members.append(self.contacts[c_id])
        #print "CG:", cg
        self.contactgroups[cg_id] = cg
        self.number_of_objects += 1


    def manage_initial_timeperiod_status_brok(self, b):
        data = b.data
        tp_id = data['id']
        #print "Creating Timeperiod:", tp_id, data
        tp = Timeperiod({})
        self.update_element(tp, data)
        #print "TP:", tp
        self.timeperiods[tp_id] = tp
        self.number_of_objects += 1


    def manage_initial_command_status_brok(self, b):
        data = b.data
        c_id = data['id']
        #print "Creating Command:", c_id, data
        c = Command({})
        self.update_element(c, data)
        #print "CMD:", c
        self.commands[c_id] = c
        self.number_of_objects += 1


    def manage_initial_scheduler_status_brok(self, b):
        data = b.data
        sched_id = data['id']
        print "Creating Scheduler:", sched_id, data
        sched = SchedulerLink({})
        print "Created a new scheduler", sched
        self.update_element(sched, data)
        print "Updated scheduler"
        #print "CMD:", c
        self.schedulers[sched_id] = sched
        print "scheduler added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_scheduler_status_brok(self, b):
        data = b.data
        s = self.find_scheduler(data['scheduler_name'])
        if s != None:
            self.update_element(s, data)
            #print "S:", s


    def manage_initial_poller_status_brok(self, b):
        data = b.data
        reac_id = data['id']
        print "Creating Poller:", reac_id, data
        reac = PollerLink({})
        print "Created a new poller", reac
        self.update_element(reac, data)
        print "Updated poller"
        #print "CMD:", c
        self.pollers[reac_id] = reac
        print "poller added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_poller_status_brok(self, b):
        data = b.data
        s = self.find_poller(data['poller_name'])
        if s != None:
            self.update_element(s, data)
            #print "S:", s


    def manage_initial_reactionner_status_brok(self, b):
        data = b.data
        reac_id = data['id']
        print "Creating Reactionner:", reac_id, data
        reac = ReactionnerLink({})
        print "Created a new reactionner", reac
        self.update_element(reac, data)
        print "Updated reactionner"
        #print "CMD:", c
        self.reactionners[reac_id] = reac
        print "reactionner added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_reactionner_status_brok(self, b):
        data = b.data
        s = self.find_reactionner(data['reactionner_name'])
        if s != None:
            self.update_element(s, data)
            #print "S:", s


    def manage_initial_broker_status_brok(self, b):
        data = b.data
        reac_id = data['id']
        print "Creating Broker:", reac_id, data
        reac = BrokerLink({})
        print "Created a new broker", reac
        self.update_element(reac, data)
        print "Updated broker"
        #print "CMD:", c
        self.brokers[reac_id] = reac
        print "broker added"
        #print "MONCUL: Add a new scheduler ", sched
        self.number_of_objects += 1


    def manage_update_broker_status_brok(self, b):
        data = b.data
        s = self.find_broker(data['broker_name'])
        if s != None:
            self.update_element(s, data)
            #print "S:", s


    #A service check have just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        s = self.find_service(data['host_name'], data['service_description'])
        if s != None:
            self.update_element(s, data)
            #print "S:", s


    #A service check update have just arrived, we UPDATE data info with this
    def manage_service_next_schedule_brok(self, b):
        self.manage_service_check_result_brok(b)


    #In fact, an update of a service is like a check return
    def manage_update_service_status_brok(self, b):
        self.manage_service_check_result_brok(b)
        data = b.data
        #In the status, we've got duplicated item, we must relink thems
        s = self.find_service(data['host_name'], data['service_description'])
        if s == None:
            print "Warning : the service %s/%s is unknown!" % (data['host_name'], data['service_description'])
            return
        self.set_schedulingitem_values(s)
        
        ## damn:
        if False:
            self.set_ref_attributes_on_item(s)
            ## don't know why but this makes query3 of "test_status" of livestatus test fails :
# ======================================================================
#FAIL: test_status (__main__.TestConfigSmall)
#----------------------------------------------------------------------
#Traceback (most recent call last):
#  File "./test_livestatus_2.py", line xxx, in test_status
#    self.assert_(response == 'test_host_0;test_ok_0;1\n')
#AssertionError



    def manage_host_check_result_brok(self, b):
        data = b.data
        h = self.find_host(data['host_name'])
        if h != None:
            self.update_element(h, data)
            #print "H:", h


    # this brok should arrive within a second after the host_check_result_brok
    def manage_host_next_schedule_brok(self, b):
        self.manage_host_check_result_brok(b)


    #A log brok will be written into a database
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
            service_states = { 'OK' : 0, 'WARNING' : 1, 'CRITICAL' : 2, 'UNKNOWN' : 3, 'RECOVERY' : 0 }
            host_states = { 'UP' : 0, 'DOWN' : 1, 'UNREACHABLE' : 2, 'UNKNOWN': 3, 'RECOVERY' : 0 }

            # 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message',
            # 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type',
            # 0:info, 1:state, 2:program, 3:notification, 4:passive, 5:command

            # lineno, message?, plugin_output?
            logobject = LOGOBJECT_INFO
            logclass = LOGCLASS_INVALID
            attempt, state = [0] * 2
            command_name, comment, contact_name, host_name, message, options, plugin_output, service_description, state_type = [''] * 9
            time= line[1:11]
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
                host_name, service_description, state, state_type, attempt, plugin_output = options.split(';')
            elif type == 'INITIAL SERVICE STATE':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_STATE
                host_name, service_description, state, state_type, attempt, plugin_output = options.split(';')
            elif type == 'SERVICE ALERT':
                # SERVICE ALERT: srv-40;Service-9;CRITICAL;HARD;1;[Errno 2] No such file or directory
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_ALERT
                host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
                state = service_states[state]
            elif type == 'SERVICE DOWNTIME ALERT':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_ALERT
                host_name, service_description, state_type, comment = options.split(';')
            elif type == 'SERVICE FLAPPING ALERT':
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_ALERT
                host_name, service_description, state_type, comment = options.split(';')

            elif type == 'CURRENT HOST STATE':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_STATE
                host_name, state, state_type, attempt, plugin_output = options.split(';')
            elif type == 'INITIAL HOST STATE':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_STATE
                host_name, state, state_type, attempt, plugin_output = options.split(';')
            elif type == 'HOST ALERT':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_ALERT
                host_name, state, state_type, attempt, plugin_output = options.split(';')
                state = host_states[state]
            elif type == 'HOST DOWNTIME ALERT':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_ALERT
                host_name, state_type, comment = options.split(';')
            elif type == 'HOST FLAPPING ALERT':
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_ALERT
                host_name, state_type, comment = options.split(';')

            elif type == 'SERVICE NOTIFICATION':
                # tust_cuntuct;test_host_0;test_ok_0;CRITICAL;notify-service;i am CRITICAL  <-- normal
                # SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;DOWNTIMESTART (OK);notify-service;OK
                logobject = LOGOBJECT_SERVICE
                logclass = LOGCLASS_NOTIFICATION
                contact_name, host_name, service_description, state_type, command_name, check_plugin_output = options.split(';', 5)
                if '(' in state_type: # downtime/flapping/etc-notifications take the type UNKNOWN
                    state_type = 'UNKNOWN'
                state = service_states[state_type]
            elif type == 'HOST NOTIFICATION':
                # tust_cuntuct;test_host_0;DOWN;notify-host;i am DOWN
                logobject = LOGOBJECT_HOST
                logclass = LOGCLASS_NOTIFICATION
                contact_name, host_name, state_type, command_name, check_plugin_output = options.split(';')
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
                host_name, service_description, state, state_type, attempt, command_name = options.split(';')
                state = service_states[state]
            elif type == 'HOST EVENT HANDLER':
                logobject = LOGOBJECT_HOST
                host_name, state, state_type, attempt, command_name = options.split(';')
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


    #The contacts must not be duplicated
    def get_contacts(self, cs):
        r = []
        for c in cs:
            if c != None:
                find_c = self.find_contact(c.get_name())
                if find_c != None:
                    r.append(find_c)
                else:
                    print "Error : search for a contact %s that do not exists!" % c.get_name()
        return r


    #The timeperiods must not be duplicated
    def get_timeperiod(self, t):
        if t != None:
            find_t = self.find_timeperiod(t.get_name())
            if find_t != None:
                return find_t
            else:
                print "Error : search for a timeperiod %s that do not exists!" % t.get_name()
        else:
            return None


    def find_host(self, host_name):
        if host_name in self.hostname_lookup_table:
            return self.hosts[self.hostname_lookup_table[host_name]]
        for h in self.hosts.values():
            if h.host_name == host_name:
                return h
        return None


    def find_service(self, host_name, service_description):
        if host_name + service_description in self.servicename_lookup_table:
            return self.services[self.servicename_lookup_table[host_name + service_description]]
        for s in self.services.values():
            if s.host_name == host_name and s.service_description == service_description:
                return s
        return None


    def find_timeperiod(self, timeperiod_name):
        for t in self.timeperiods.values():
            if t.timeperiod_name == timeperiod_name:
                return t
        return None


    def find_contact(self, contact_name):
        for c in self.contacts.values():
            if c.contact_name == contact_name:
                return c
        return None

    ###Find satellites
    def find_scheduler(self, name):
        for s in self.schedulers.values():
            if s.scheduler_name == name:
                return s
        return None


    def find_poller(self, name):
        for s in self.pollers.values():
            if s.poller_name == name:
                return s
        return None


    def find_reactionner(self, name):
        for s in self.reactionners.values():
            if s.reactionner_name == name:
                return s
        return None


    def find_broker(self, name):
        for s in self.brokers.values():
            if s.broker_name == name:
                return s
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
        self.dbconn = sqlite3.connect(self.database_file)
        self.dbcursor = self.dbconn.cursor()
        # 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message',
        # 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type',
        cmd = "CREATE TABLE IF NOT EXISTS logs(logobject INT, attempt INT, class INT, command_name VARCHAR(64), comment VARCHAR(256), contact_name VARCHAR(64), host_name VARCHAR(64), lineno INT, message VARCHAR(512), options VARCHAR(512), plugin_output VARCHAR(256), service_description VARCHAR(64), state INT, state_type VARCHAR(10), time INT, type VARCHAR(64))"
        self.dbcursor.execute(cmd)
        cmd = "CREATE INDEX IF NOT EXISTS logs_time ON logs (time)"
        self.dbcursor.execute(cmd)
        self.dbconn.commit()
        # rowfactory will later be redefined (in livestatus.py)


    def cleanup_log_db(self):
        limit = int(time.time() - self.max_logs_age * 86400)
        print "Deleting messages from the log database older than %s" % time.asctime(time.localtime(limit))
        if sqlite3.paramstyle == 'pyformat':
            self.dbcursor.execute('DELETE FROM LOGS WHERE time < %(limit)s', { 'limit' : limit })
        else:
            self.dbcursor.execute('DELETE FROM LOGS WHERE time < ?', (limit,))
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
        print "[liveStatus] So I quit"
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


    def main(self):
        #I register my exit function
        self.set_exit_handler()

        last_number_of_objects = 0
        last_db_cleanup_time = 0
        backlog = 5
        size = 8192
        self.listeners = []
        if self.port:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setblocking(0)
            server.bind((self.host, self.port))
            server.listen(backlog)
            self.listeners.append(server)
        if self.socket:
            if os.path.exists(self.socket):
                os.remove(self.socket)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.setblocking(0)
            sock.bind(self.socket)
            sock.listen(backlog)
            self.listeners.append(sock)
        self.input = self.listeners[:]
        databuffer = {}
        open_connections = {}
 
        while not self.interrupted:
            try:
                b = self.to_q.get(True, .01)  # do not block indefinitely
                self.manage_brok(b)
            #We do not ware about Empty queue
            except Queue.Empty:
                pass
            except IOError, e:
                if e.errno != os.errno.EINTR:
                    raise
            #But others are importants
            except Exception, exp:
                print "Error : got an exeption (bad code?)", exp.__dict__, type(exp)
                raise
            inputready,outputready,exceptready = select.select(self.input,[],[], 0)

            now = time.time()
            # At the end of this loop we probably will discard connections
            kick_connections = []
            if len(exceptready) > 0:
                pass
            if len(outputready) > 0:
                pass
            if len(inputready) > 0:
                for s in inputready:
                # We will identify sockets by their filehandle number
                # during the rest of this loop
                    socketid = s.fileno()
                    if s in self.listeners:
                        # handle the server socket
                        client, address = s.accept()
                        if isinstance(address, tuple):
                            client_ip, client_port = address
                            if self.allowed_hosts and address not in self.allowed_hosts:
                                print "Connection attempt from illegal ip address", client_ip
                                try:
                                    #client.send('Buh!\n')
                                    client.shutdown(2)
                                except:
                                    client.close()
                                continue
                        self.input.append(client)
                    else:
                        if socketid in open_connections:
                            # This is a known connection. Register the activity
                            open_connections[socketid]['lastseen'] = now
                        else:
                            # This is a new connection
                            open_connections[socketid] = { 'keepalive' : False, 'lastseen' : now, 'buffer' : None, 'state' : 'receiving' }

                        data = ''
                        try:
                            data = s.recv(size)
                        except socket.error, e:
                            # Maybe the other side has already closed the socket
                            if e.args[0] == errno.EWOULDBLOCK:
                                # don't know yet how to handle this case
                                pass
                            else:
                                print "other error", errno

                        # These two flags decide whether the databuffer is
                        # passed to the livestatus module for execution
                        # and whether the socket will be closed afterwards
                        close_it = False
                        handle_it = False

                        # A connection has two states
                        # receiving = collect input until a query
                        #             is complete or aborted by empty input
                        # idle      = response was sent
                        if open_connections[socketid]['state'] == 'receiving':
                            if not data:
                                if open_connections[socketid]['buffer']:
                                    # Empty packet follows some input.
                                    # Request is considered to be complete
                                    handle_it = True
                                else:
                                    # Empty packet follows empty packet.
                                    # Terminate this connection
                                    close_it = True
                            else:
                                if open_connections[socketid]['buffer']:
                                    # Additional input was received
                                    open_connections[socketid]['buffer'] += data
                                else:
                                    # First input was received
                                    open_connections[socketid]['buffer'] = data
                                if open_connections[socketid]['buffer'].endswith('\n\n') or \
                                        open_connections[socketid]['buffer'].endswith('\r\n\r\n'):
                                    # Two \n (= an empty line) mean
                                    # client sends "request complete, go ahead"
                                    if open_connections[socketid]['buffer'].rstrip():
                                        handle_it = True
                                    else:
                                        # Someone with telnet hits the enter-key like crazy
                                        # Only whitespace is like an empty request
                                        close_it = True

                        elif open_connections[socketid]['state'] == 'idle':
                            if not data:
                                # Thats it. Client closed the connection
                                close_it = True
                            else:
                                # Got data after is sent a sresponse.
                                # Too late...."
                                close_it = True

                        else:
                            # This code should never be executed
                            if not data:
                                if open_connections[socketid]['buffer']:
                                    print "undef state nodata buffer", open_connections[socketid]['state']
                                else:
                                    print "undef state nodata nobuffer", open_connections[socketid]['state']
                            else:
                                if open_connections[socketid]['buffer']:
                                    print "undef state data buffer", open_connections[socketid]['state']
                                else:
                                    print "undef state data nobuffer", open_connections[socketid]['state']

                        if handle_it:
                            response, keepalive = self.livestatus.handle_request(open_connections[socketid]['buffer'].rstrip())
                            try:
                                s.send(response)
                            except:
                                # Maybe the request was an external command and
                                # the peer is not interested in a response at all
                                pass

                            # Write request/response in a tracefile
#                            if os.path.exists('/tmp/shinken.modules.livestatus.trace'):
#                               try:
#                                   trace = open('/tmp/shinken.modules.livestatus.trace', 'a')
#                                   trace.write("REQUEST>>>>>\n" + open_connections[socketid]['buffer'].rstrip() + "\n\n")
#                                   trace.write("RESPONSE<<<<\n" + response + "\n\n")
#                                   trace.close()
#                               except Exception , exp:
#                                   print str(exp)
#                                   print "please check the permissions on the tracefile"

                            # Empty the input buffer for the next request
                            open_connections[socketid]['buffer'] = None
                            if keepalive == 'on':
                                open_connections[socketid]['keepalive'] = True
                                open_connections[socketid]['state'] = 'receiving'
                            else:
                                open_connections[socketid]['state'] = 'idle'

                        if close_it:
                            # Register this socket for deletion
                            kick_connections.append(s.fileno())


                # Now the work is done. Cleanup
                for socketid in open_connections:
                    print "connection %d is idle since %d seconds (%s)\n" % (socketid, now - open_connections[socketid]['lastseen'], open_connections[socketid]['state'])
                    if now - open_connections[socketid]['lastseen'] > 300:
                        # After 5 minutes of inactivity we close connections
                        open_connections[socketid]['keepalive'] = False
                        open_connections[socketid]['state'] = 'idle'
                        kick_connections.append(socketid)

                # Close connections which timed out or are no longer needed
                for socketid in kick_connections:
                    kick_socket = None
                    for s in self.input:
                        if s.fileno() == socketid:
                            kick_socket = s
                    if kick_socket:
                        try:
                            kick_socket.shutdown(2)
                            del open_connections[socketid]
                            self.input.remove(kick_socket)
                            print "shutdown socket", socketid
                        except Exception , exp:
                            print exp
                            kick_socket.close()
                            del open_connections[socketid]
                            self.input.remove(kick_socket)
                            print "closed socket", socketid

            else:
                # There are no incoming requests, so there's time for some housekeeping
                if now - last_db_cleanup_time > 86400:
                    self.cleanup_log_db()
                    last_db_cleanup_time = now

            if self.number_of_objects > last_number_of_objects:
                # Still in the initialization phase
                # Maybe we should wait until there are no more initial broks
                # before we open the socket
                pass

        self.do_stop()

def livestatus_factory(cursor, row):
    return Logline(row)
