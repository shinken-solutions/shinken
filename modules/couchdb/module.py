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

import copy
couchdb = None
socket = None
try:
    # Failed import will be caught by __init__.py
    import couchdb as couchdb_imp
    couchdb = couchdb_imp
except ImportError:
    pass
import socket as socket_imp  # For Nagle HACK
socket = socket_imp

from shinken.basemodule import BaseModule


properties = {
    'daemons': ['broker'],
    'type': 'couchdb',
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):

    print "Get a Couchdb broker for plugin %s" % plugin.get_name()

    if not couchdb:
        logger.error("Error : cannot import couchdb module, so the plugin %s cannot load" % plugin.get_name())
        return None

    # TODO: catch errors
    host = plugin.host
    user = plugin.user
    password = plugin.password
    instance = Couchdb_broker(plugin, host, user, password)
    return instance




class Couchdb_broker(BaseModule):
    """
     This Class is a plugin for the Shinken Broker. It is in charge
     to brok information into the merlin database. for the moment
     only Mysql is supported. This code is __imported__ from Broker.
     The managed_brok function is called by Broker for manage the broks. It calls
     the manage_*_brok functions that create queries, and then run queries.

    """

    def __init__(self, modconf, host, user, password):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.user = user
        self.password = password

    # Called by Broker so we can do init stuff
    def init(self):
        print "I connect to Couchdb database"
        self.connect_database()

    # Get a brok, parse it, and put in in database
    # We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        # We will transform data of b, so copy it
        return BaseModule.manage_brok(self, copy.deepcopy(b))

    # Create the database connection
    # TODO: finish (begin :) ) error catch and conf parameters...
    def connect_database(self):
        # First connect to server
        s = couchdb.Server('http://127.0.0.1:5984/')
        # TODO add credentials with
        #db.resource.http.add_credentials

        # Hack because of the Nagle TCP algorithm: couchdb make
        # very small packets, so Nagle wait 40ms for more bits that will
        # never happen, so make a 40ms latency for all packets!
        # So: NO_DELAY :)
        for con in s.resource.http.connections:
            sock = s.resource.http.connections[con].sock
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        tables = ['commands', 'comments', 'contacts', 'contactgroups', 'downtimes', 'hosts',
                  'hostdependencies', 'hostescalations', 'hostgroups', 'notifications',
                  'program_status', 'scheduled_downtimes', 'services', 'serviceescalations',
                  'servicegroups', 'timeperiods', 'host_hostgroup', 'contact_contactgroup',
                  'service_servicegroup']

        # OK, now we store ours dbs
        self.dbs = {}
        # An we clean them
        for table in tables:
            # We get the database. From now, we drop all the database and recreate a new one
            # TODO: cleaner way of doing it!!
            try:
                s.delete(table)
            except couchdb.client.ResourceNotFound:
                pass
            self.dbs[table] = s.create(table)

    # Create a document table with all data of data (a dict)
    def create_document(self, table, data, key):
        db = self.dbs[table]

        # Couchdb index is _id
        if key is not None:
            data['_id'] = key

        # Now stringify datas in UTF-8
        for prop in data:
            val = data[prop]

            if isinstance(val, str):
                data[prop] = val.decode('utf-8')
                data[prop].replace("'", "''")
            else:
                data[prop] = val
        db.create(data)

    # Update a document into a table with data
    def update_document(self, table, data, key):
        db = self.dbs[table]

        # Couchdb index is _id
        if key is not None:
            data['_id'] = key

        # We take the original doc to update it
        doc = db[key]
        # TODO: find a better way of not having too much revisions...
        db.delete(doc)

        # Now stringify datas
        for prop in data:
            val = data[prop]

            if isinstance(val, str):
                data[prop] = val.decode('utf-8')
                data[prop].replace("'", "''")
            else:
                data[prop] = val

            doc[prop] = data[prop]
        db.update([doc])

    # Ok, we are at launch and a scheduler want him only, OK...
    # So it creates several queries with all tables we need to delete with
    # our instance_id
    # This brok must be sent at the beginning of a scheduler session,
    # if not, BAD THINGS MAY HAPPEN :)
    # TODO: Modify this comment to explain why we only do one thing here.
    def manage_clean_all_my_instance_id_brok(self, b):
        instance_id = b.data['instance_id']
        print("[%s] Cleaning id: %d" % (self.get_name(), instance_id))
        return

    # Program status is .. status of program? :)
    # Like pid, daemon mode, last activity, etc
    # We already clean database, so insert
    def manage_program_status_brok(self, b):
        #instance_id = b.data['instance_id']
        self.create_document('program_status', b.data, b.data['instance_name'])

    # Initial service status is at start. We need to insert because we
    # clean the base
    def manage_initial_service_status_brok(self, b):
        # It's a initial entry, so we need to create
        key = '%s,%s' % (b.data['host_name'], b.data['service_description'])
        self.create_document('services', b.data, key)

    # A service check has just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        key = '%s,%s' % (b.data['host_name'], b.data['service_description'])
        # We just impact the service :)
        self.update_document('services', data, key)

    # A full service status? Ok, update data
    def manage_update_service_status_brok(self, b):
        data = b.data
        key = '%s,%s' % (b.data['host_name'], b.data['service_description'])
        self.update_document('services', data, key)

    # A host has just been created, database is clean, we INSERT it
    def manage_initial_host_status_brok(self, b):
        key = b.data['host_name']
        self.create_document('hosts', b.data, key)

    # A new host group? Insert it
    # We need to do something for the members prop (host.id, host_name)
    # They are for host_hostgroup table, with just host.id hostgroup.id
    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data

        # Here we've got a special case: in data, there is members
        # and we do not want it in the INSERT query, so we create a
        # tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        self.create_document('hostgroups', tmp_data, data['hostgroup_name'])


        # Ok, the hostgroup table is uptodate, now we add relations
        # between hosts and hostgroups
        for (h_id, _) in b.data['members']:
            self.create_document('host_hostgroup', {'host': h_id, 'hostgroup': b.data['id']}, None)

    # same from hostgroup, but with servicegroup
    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data

        # Here we've got a special case: in data, there is members
        # and we do not want it in the INSERT query, so we create a
        # tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        self.create_document('servicegroups', tmp_data, data['servicegroup_name'])

        # Now the members part
        for (s_id, _) in b.data['members']:
            self.create_document(
                'service_servicegroup',
                {'service': s_id, 'servicegroup': b.data['id']},
                None)

    # Same than service result, but for host result
    def manage_host_check_result_brok(self, b):
        data = b.data
        # Only the host is impacted
        key = data['host_name']
        self.update_document('hosts', data, key)

    # Ok the host is updated
    def manage_update_host_status_brok(self, b):
        data = b.data
        # Only this host
        key = data['host_name']
        self.update_document('hosts', data, key)

    # A contact have just be created, database is clean, we INSERT it
    def manage_initial_contact_status_brok(self, b):
        self.create_document('contacts', b.data, b.data['contact_name'])

    # same from hostgroup, but with servicegroup
    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data

        # Here we've got a special case: in data, there is members
        # and we do not want it in the INSERT query, so we create a
        # tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        self.create_document('contactgroups', tmp_data, tmp_data['contactgroup_name'])

        # Now the members part
        for (c_id, _) in b.data['members']:
            self.create_document(
                'contact_contactgroup',
                {'contact': c_id, 'contactgroup': b.data['id']},
                None)

    # A notification has just been created, we INSERT it
    def manage_notification_raise_brok(self, b):
        self.create_document('notifications', b.data, b.data['id'])

    # Override abstract method
    def do_loop_turn(self):
        pass
