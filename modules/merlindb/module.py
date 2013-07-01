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
import time

from shinken.basemodule import BaseModule





properties = {
    'daemons': ['broker'],
    'type': 'merlindb',
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Merlin broker for plugin %s" % plugin.get_name()
    print "Get backend", plugin.backend
    backend = plugin.backend


    # Now load the goo module for the backend
    if backend == 'mysql':
        try:
            host = plugin.host
            user = plugin.user
            password = plugin.password
            database = plugin.database
            if hasattr(plugin, 'character_set'):
                character_set = plugin.character_set
            else:
                character_set = 'utf8'

            instance = Merlindb_broker(plugin, backend, host=host, user=user, password=password, database=database, character_set=character_set)
            return instance

        except ImportError, exp:
            print "Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp)
            return None

    if backend == 'sqlite':
        try:
            database_path = plugin.database_path
            instance = Merlindb_broker(plugin, backend, database_path=database_path)
            return instance

        except ImportError, exp:
            print "Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp)
            return None

    print "Not creating a instance!!!"
    return None




def get_objs_names(objs):
    s = ''
    for o in objs:
        s += get_obj_name(o)
    return s


def get_obj_name(obj):
    print "ARG", obj
    print "Get name on", obj.get_name()
    return obj.get_name()


def list_to_comma(lst):
    # For ['d', 'r', 'u'] will return d,r,u
    return ','.join(lst)


def last_hard_state_to_int(lst):
    return 1


# Class for the Merlindb Broker
# Get broks and puts them in merlin database
class Merlindb_broker(BaseModule):
    def __init__(self, modconf, backend, host=None, user=None, password=None, database=None, character_set=None, database_path=None):
        # Mapping for name of data, rename attributes and transform function
        self.mapping = {
            # Program status
            'program_status': {'program_start': {'transform': None},
                                'pid': {'transform': None},
                                'last_alive': {'transform': None},
                                'is_running': {'transform': None},
                                'instance_id': {'transform': None},
                                },
            # Program status update (every 10s)
            'update_program_status': {'program_start': {'transform': None},
                                'pid': {'transform': None},
                                'last_alive': {'transform': None},
                                'is_running': {'transform': None},
                                'instance_id': {'transform': None},
                                },
            # Host
            'initial_host_status': {
                'id': {'transform': None},
                'instance_id': {'transform': None},
                'host_name': {'transform': None},
                'alias': {'transform': None},
                'display_name': {'transform': None},
                'address': {'transform': None},
                'contact_groups': {'transform': None},
                'contacts': {'transform': None},
                'initial_state': {'transform': None},
                'max_check_attempts': {'transform': None},
                'check_interval': {'transform': None},
                'retry_interval': {'transform': None},
                'active_checks_enabled': {'transform': None},
                'passive_checks_enabled': {'transform': None},
                'obsess_over_host': {'transform': None},
                'check_freshness': {'transform': None},
                'freshness_threshold': {'transform': None},
                'event_handler_enabled': {'transform': None},
                'low_flap_threshold': {'transform': None},
                'high_flap_threshold': {'transform': None},
                'flap_detection_enabled': {'transform': None},
                'process_perf_data': {'transform': None},
                'notification_interval': {'transform': None},
                'first_notification_delay': {'transform': None},
                'notifications_enabled': {'transform': None},
                'notes': {'transform': None},
                'notes_url': {'transform': None},
                'action_url': {'transform': None},
                'last_chk': {'transform': None, 'name': 'last_check'},
                'next_chk': {'transform': None, 'name': 'next_check'},
                'attempt': {'transform': None, 'name': 'current_attempt'},
                'state_id': {'transform': None, 'name': 'current_state'},
                'state_type_id': {'transform': None, 'name': 'state_type'},
                'current_event_id': {'transform': None},
                'last_event_id': {'transform': None},
                'last_state_id': {'transform': None, 'name': 'last_state'},
                'last_state_change': {'transform': None},
                'last_hard_state_change': {'transform': None},
                'last_hard_state': {'transform': last_hard_state_to_int},
                'is_flapping': {'transform': None},
                'flapping_comment_id': {'transform': None},
                'percent_state_change': {'transform': None},
                'problem_has_been_acknowledged': {'transform': None},
                'acknowledgement_type': {'transform': None},
                'check_type': {'transform': None},
                'has_been_checked': {'transform': None},
                'should_be_scheduled': {'transform': None},
                'last_problem_id': {'transform': None},
                'current_problem_id': {'transform': None},
                'execution_time': {'transform': None},
                'last_notification': {'transform': None},
                'current_notification_number': {'transform': None},
                'current_notification_id': {'transform': None},
                'check_flapping_recovery_notification': {'transform': None},
                'scheduled_downtime_depth': {'transform': None},
                'pending_flex_downtime': {'transform': None},
                },
            'update_host_status': {
                'id': {'transform': None},
                'instance_id': {'transform': None},
                'host_name': {'transform': None},
                'alias': {'transform': None},
                'display_name': {'transform': None},
                'address': {'transform': None},
                'initial_state': {'transform': None},
                'max_check_attempts': {'transform': None},
                'check_interval': {'transform': None},
                'retry_interval': {'transform': None},
                'active_checks_enabled': {'transform': None},
                'passive_checks_enabled': {'transform': None},
                'obsess_over_host': {'transform': None},
                'check_freshness': {'transform': None},
                'freshness_threshold': {'transform': None},
                'event_handler_enabled': {'transform': None},
                'low_flap_threshold': {'transform': None},
                'high_flap_threshold': {'transform': None},
                'flap_detection_enabled': {'transform': None},
                'process_perf_data': {'transform': None},
                'notification_interval': {'transform': None},
                'first_notification_delay': {'transform': None},
                'notifications_enabled': {'transform': None},
                'notes': {'transform': None},
                'notes_url': {'transform': None},
                'action_url': {'transform': None},
                'last_chk': {'transform': None, 'name': 'last_check'},
                'next_chk': {'transform': None, 'name': 'next_check'},
                'attempt': {'transform': None, 'name': 'current_attempt'},
                'state_id': {'transform': None, 'name': 'current_state'},
                'state_type_id': {'transform': None, 'name': 'state_type'},
                'current_event_id': {'transform': None},
                'last_event_id': {'transform': None},
                'last_state_id': {'transform': None, 'name': 'last_state'},
                'last_state_change': {'transform': None},
                'last_hard_state_change': {'transform': None},
                'last_hard_state': {'transform': last_hard_state_to_int},
                'is_flapping': {'transform': None},
                'flapping_comment_id': {'transform': None},
                'percent_state_change': {'transform': None},
                'problem_has_been_acknowledged': {'transform': None},
                'acknowledgement_type': {'transform': None},
                'check_type': {'transform': None},
                'has_been_checked': {'transform': None},
                'should_be_scheduled': {'transform': None},
                'last_problem_id': {'transform': None},
                'current_problem_id': {'transform': None},
                'execution_time': {'transform': None},
                'last_notification': {'transform': None},
                'current_notification_number': {'transform': None},
                'current_notification_id': {'transform': None},
                'check_flapping_recovery_notification': {'transform': None},
                'scheduled_downtime_depth': {'transform': None},
                'pending_flex_downtime': {'transform': None},
                },
            'host_check_result': {
                'latency': {'transform': None},
                'last_time_unreachable': {'transform': None},
                'attempt': {'transform': None, 'name': 'current_attempt'},
                'check_type': {'transform': None},
                'state_type_id': {'transform': None, 'name': 'state_type'},
                'execution_time': {'transform': None},
                'start_time': {'transform': None},
                'acknowledgement_type': {'transform': None},
                'return_code': {'transform': None},
                'last_time_down': {'transform': None},
                'instance_id': {'transform': None},
                'long_output': {'transform': None},
                'end_time': {'transform': None},
                'last_chk': {'transform': None, 'name': 'last_check'},
                'timeout': {'transform': None},
                'output': {'transform': None},
                'state_id': {'transform': None, 'name': 'current_state'},
                'last_time_up': {'transform': None},
                'early_timeout': {'transform': None},
                'perf_data': {'transform': None},
                'host_name': {'transform': None},
                },
            'host_next_schedule': {
                'instance_id': {'transform': None},
                'next_chk': {'transform': None, 'name': 'next_check'},
                'host_name': {'transform': None},
                },
            # Service
            'initial_service_status': {
                'id': {'transform': None},
                'instance_id': {'transform': None},
                'host_name': {'transform': None},
                'service_description': {'transform': None},
                'display_name': {'transform': None},
                'is_volatile': {'transform': None},
                'initial_state': {'transform': None},
                'max_check_attempts': {'transform': None},
                'check_interval': {'transform': None},
                'retry_interval': {'transform': None},
                'active_checks_enabled': {'transform': None},
                'passive_checks_enabled': {'transform': None},
                'obsess_over_service': {'transform': None},
                'check_freshness': {'transform': None},
                'freshness_threshold': {'transform': None},
                'event_handler_enabled': {'transform': None},
                'low_flap_threshold': {'transform': None},
                'high_flap_threshold': {'transform': None},
                'flap_detection_enabled': {'transform': None},
                'process_perf_data': {'transform': None},
                'notification_interval': {'transform': None},
                'first_notification_delay': {'transform': None},
                'notifications_enabled': {'transform': None},
                'notes': {'transform': None},
                'notes_url': {'transform': None},
                'action_url': {'transform': None},
                'last_chk': {'transform': None, 'name': 'last_check'},
                'next_chk': {'transform': None, 'name': 'next_check'},
                'attempt': {'transform': None, 'name': 'current_attempt'},
                'state_id': {'transform': None, 'name': 'current_state'},
                'current_event_id': {'transform': None},
                'last_event_id': {'transform': None},
                'last_state_id': {'transform': None, 'name': 'last_state'},
                'last_state_change': {'transform': None},
                'last_hard_state_change': {'transform': None},
                'last_hard_state': {'transform': last_hard_state_to_int},
                'state_type_id': {'transform': None, 'name': 'state_type'},
                'is_flapping': {'transform': None},
                'flapping_comment_id': {'transform': None},
                'percent_state_change': {'transform': None},
                'problem_has_been_acknowledged': {'transform': None},
                'acknowledgement_type': {'transform': None},
                'check_type': {'transform': None},
                'has_been_checked': {'transform': None},
                'should_be_scheduled': {'transform': None},
                'last_problem_id': {'transform': None},
                'current_problem_id': {'transform': None},
                'execution_time': {'transform': None},
                'last_notification': {'transform': None},
                'current_notification_number': {'transform': None},
                'current_notification_id': {'transform': None},
                'check_flapping_recovery_notification': {'transform': None},
                'scheduled_downtime_depth': {'transform': None},
                'pending_flex_downtime': {'transform': None},
                },
            'update_service_status': {
                'id': {'transform': None},
                'instance_id': {'transform': None},
                'host_name': {'transform': None},
                'service_description': {'transform': None},
                'display_name': {'transform': None},
                'is_volatile': {'transform': None},
                'initial_state': {'transform': None},
                'max_check_attempts': {'transform': None},
                'check_interval': {'transform': None},
                'retry_interval': {'transform': None},
                'active_checks_enabled': {'transform': None},
                'passive_checks_enabled': {'transform': None},
                'obsess_over_service': {'transform': None},
                'check_freshness': {'transform': None},
                'freshness_threshold': {'transform': None},
                'event_handler_enabled': {'transform': None},
                'low_flap_threshold': {'transform': None},
                'high_flap_threshold': {'transform': None},
                'flap_detection_enabled': {'transform': None},
                'process_perf_data': {'transform': None},
                'notification_interval': {'transform': None},
                'first_notification_delay': {'transform': None},
                'notifications_enabled': {'transform': None},
                'notes': {'transform': None},
                'notes_url': {'transform': None},
                'action_url': {'transform': None},
                'last_chk': {'transform': None, 'name': 'last_check'},
                'next_chk': {'transform': None, 'name': 'next_check'},
                'attempt': {'transform': None, 'name': 'current_attempt'},
                'state_id': {'transform': None, 'name': 'current_state'},
                'current_event_id': {'transform': None},
                'last_event_id': {'transform': None},
                'last_state_id': {'transform': None, 'name': 'last_state'},
                'last_state_change': {'transform': None},
                'last_hard_state_change': {'transform': None},
                'last_hard_state': {'transform': last_hard_state_to_int},
                'state_type_id': {'transform': None, 'name': 'current_state'},
                'is_flapping': {'transform': None},
                'flapping_comment_id': {'transform': None},
                'percent_state_change': {'transform': None},
                'problem_has_been_acknowledged': {'transform': None},
                'acknowledgement_type': {'transform': None},
                'check_type': {'transform': None},
                'has_been_checked': {'transform': None},
                'should_be_scheduled': {'transform': None},
                'last_problem_id': {'transform': None},
                'current_problem_id': {'transform': None},
                'execution_time': {'transform': None},
                'last_notification': {'transform': None},
                'current_notification_number': {'transform': None},
                'current_notification_id': {'transform': None},
                'check_flapping_recovery_notification': {'transform': None},
                'scheduled_downtime_depth': {'transform': None},
                'pending_flex_downtime': {'transform': None},
                },
            'service_check_result': {
                'check_type': {'transform': None},
                'last_time_critical': {'transform': None},
                'last_time_warning': {'transform': None},
                'latency': {'transform': None},
                'last_chk': {'transform': None, 'name': 'last_check'},
                'last_time_ok': {'transform': None},
                'end_time': {'transform': None},
                'last_time_unknown': {'transform': None},
                'execution_time': {'transform': None},
                'start_time': {'transform': None},
                'return_code': {'transform': None},
                'output': {'transform': None},
                'service_description': {'transform': None},
                'early_timeout': {'transform': None},
                'attempt': {'transform': None, 'name': 'current_attempt'},
                'state_type_id': {'transform': None, 'name': 'state_type'},
                'acknowledgement_type': {'transform': None},
                'instance_id': {'transform': None},
                'long_output': {'transform': None},
                'host_name': {'transform': None},
                'timeout': {'transform': None},
                'state_id': {'transform': None, 'name': 'current_state'},
                'perf_data': {'transform': None},
                },
            'service_next_schedule': {
                'next_chk': {'transform': None, 'name': 'next_check'},
                'service_description': {'transform': None},
                'instance_id': {'transform': None},
                'host_name': {'transform': None},
                },

            # Contact
            'initial_contact_status': {
                'service_notifications_enabled': {'transform': None},
                'can_submit_commands': {'transform': None},
                'contact_name': {'transform': None},
                'id': {'transform': None},
                'retain_status_information': {'transform': None},
                'address1': {'transform': None},
                'address2': {'transform': None},
                'address3': {'transform': None},
                'address4': {'transform': None},
                'address5': {'transform': None},
                'address6': {'transform': None},
                #'service_notification_commands': {'transform': get_objs_names},
                'pager': {'transform': None},
                #'host_notification_period': {'transform': get_obj_name},
                'host_notifications_enabled': {'transform': None},
                #'host_notification_commands': {'transform': get_objs_names},
                #'service_notification_period': {'transform': get_obj_name},
                'email': {'transform': None},
                'alias': {'transform': None},
                'host_notification_options': {'transform': list_to_comma},
                'service_notification_options': {'transform': list_to_comma},
                },
            # Contact group
            'initial_contactgroup_status': {
                'contactgroup_name': {'transform': None},
                'alias': {'transform': None},
                'instance_id': {'transform': None},
                'id': {'transform': None},
                'members': {'transform': None},
                },
            # Host group
            'initial_hostgroup_status': {
                'hostgroup_name': {'transform': None},
                'notes': {'transform': None},
                'instance_id': {'transform': None},
                'action_url': {'transform': None},
                'notes_url': {'transform': None},
                'members': {'transform': None},
                'id': {'transform': None},
                }
            }
        BaseModule.__init__(self, modconf)
        self.backend = backend
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.character_set = character_set
        self.database_path = database_path


        # Now get a backend_db of our backend type
        if backend == 'mysql':
            #from mysql_backend import Mysql_backend
            from shinken.db_mysql import DBMysql
            print "Creating a mysql backend"
            self.db_backend = DBMysql(host, user, password, database, character_set)

        if backend == 'sqlite':
            #from sqlite_backend import Sqlite_backend
            from shinken.db_sqlite import DBSqlite
            print "Creating a sqlite backend"
            self.db_backend = DBSqlite(self.database_path)

    def preprocess(self, type, brok):
        new_brok = copy.deepcopy(brok)
        # Only preprocess if we can apply a mapping
        if type in self.mapping:
            to_del = []
            to_add = []
            mapping = self.mapping[brok.type]
            for prop in new_brok.data:
            # ex: 'name': 'program_start_time', 'transform'
                if prop in mapping:
                    #print "Got a prop to change", prop
                    val = brok.data[prop]
                    if mapping[prop]['transform'] is not None:
                        #print "Call function for", type, prop
                        f = mapping[prop]['transform']
                        val = f(val)
                    name = prop
                    if 'name' in mapping[prop]:
                        name = mapping[prop]['name']
                    to_add.append((name, val))
                    to_del.append(prop)
                else:
                    to_del.append(prop)
            for prop in to_del:
                del new_brok.data[prop]
            for (name, val) in to_add:
                new_brok.data[name] = val
        else:
            print "No preprocess type", brok.type
            print brok.data
        return new_brok

    # Called by Broker so we can do init stuff
    # TODO: add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        print "I connect to Merlin database"
        self.db_backend.connect_database()

    # Get a brok, parse it, and put in in database
    # We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        type = b.type
        manager = 'manage_' + type + '_brok'
        #print "(Merlin) I search manager:", manager
        if hasattr(self, manager):
            new_b = self.preprocess(type, b)
            f = getattr(self, manager)
            queries = f(new_b)
            # Ok, we've got queries, now: run them!
            for q in queries:
                self.db_backend.execute_query(q)
            return

    # Ok, we are at launch and a scheduler want him only, OK...
    # So ca create several queries with all tables we need to delete with
    # our instance_id
    # This brok must be send at the beginning of a scheduler session,
    # if not, BAD THINGS MAY HAPPENED :)
    def manage_clean_all_my_instance_id_brok(self, b):
        instance_id = b.data['instance_id']
        tables = ['command', 'comment', 'contact', 'contactgroup', 'downtime', 'host',
                  'hostdependency', 'hostescalation', 'hostgroup', 'notification', 'program_status',
                  'scheduled_downtime', 'service', 'serviceescalation',
                  'servicegroup', 'timeperiod']
        res = []
        for table in tables:
            q = "DELETE FROM %s WHERE instance_id = '%s' " % (table, instance_id)
            res.append(q)
        return res

    # Program status is .. status of program? :)
    # Like pid, daemon mode, last activity, etc
    # We already clean database, so insert
    def manage_program_status_brok(self, b):
        instance_id = b.data['instance_id']
        del_query = "DELETE FROM program_status WHERE instance_id = '%s' " % instance_id
        query = self.db_backend.create_insert_query('program_status', b.data)
        return [del_query, query]

    # Program status is .. status of program? :)
    # Like pid, daemon mode, last activity, etc
    # We already clean database, so insert
    def manage_update_program_status_brok(self, b):
        instance_id = b.data['instance_id']
        del_query = "DELETE FROM program_status WHERE instance_id = '%s' " % instance_id
        query = self.db_backend.create_insert_query('program_status', b.data)
        return [del_query, query]

    # Initial service status is at start. We need an insert because we
    # clean the base
    def manage_initial_service_status_brok(self, b):
        b.data['last_update'] = time.time()
        # It's a initial entry, so we need insert
        query = self.db_backend.create_insert_query('service', b.data)
        return [query]

    # A service check have just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        b.data['last_update'] = time.time()
        # We just impact the service :)
        where_clause = {'host_name': data['host_name'], 'service_description': data['service_description']}
        query = self.db_backend.create_update_query('service', data, where_clause)
        return [query]

    # A new service schedule have just arrived, we UPDATE data info with this
    def manage_service_next_schedule_brok(self, b):
        data = b.data
        # We just impact the service :)
        where_clause = {'host_name': data['host_name'], 'service_description': data['service_description']}
        query = self.db_backend.create_update_query('service', data, where_clause)
        return [query]

    # A full service status? Ok, update data
    def manage_update_service_status_brok(self, b):
        data = b.data
        b.data['last_update'] = time.time()
        where_clause = {'host_name': data['host_name'], 'service_description': data['service_description']}
        query = self.db_backend.create_update_query('service', data, where_clause)
        return [query]

    # A host have just be create, database is clean, we INSERT it
    def manage_initial_host_status_brok(self, b):
        b.data['last_update'] = time.time()
        tmp_data = copy.copy(b.data)
        del tmp_data['contacts']
        del tmp_data['contact_groups']
        query = self.db_backend.create_insert_query('host', tmp_data)
        res = [query]

        for cg_name in b.data['contact_groups'].split(','):
            q_del = "DELETE FROM host_contactgroup WHERE host = '%s' and contactgroup = (SELECT id FROM contactgroup WHERE contactgroup_name = '%s')" % (b.data['id'], cg_name)
            res.append(q_del)
            q = "INSERT INTO host_contactgroup (host, contactgroup) VALUES ('%s', (SELECT id FROM contactgroup WHERE contactgroup_name = '%s'))" % (b.data['id'], cg_name)
            res.append(q)
        return res

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
        query = self.db_backend.create_insert_query('hostgroup', tmp_data)
        res = [query]

        # Ok, the hostgroup table is uptodate, now we add relations
        # between hosts and hostgroups
        for (h_id, h_name) in b.data['members']:
            # First clean
            q_del = "DELETE FROM host_hostgroup WHERE host = '%s' and hostgroup='%s'" % (h_id, b.data['id'])
            res.append(q_del)
            # Then add
            q = "INSERT INTO host_hostgroup (host, hostgroup) VALUES ('%s', '%s')" % (h_id, b.data['id'])
            res.append(q)
        return res

    # same from hostgroup, but with servicegroup
    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data

        # Here we've got a special case: in data, there is members
        # and we do not want it in the INSERT query, so we create a
        # tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        query = self.db_backend.create_insert_query('servicegroup', tmp_data)
        res = [query]

        # Now the members part
        for (s_id, s_name) in b.data['members']:
            # first clean
            q_del = "DELETE FROM service_servicegroup WHERE service='%s' and servicegroup='%s'" % (s_id, b.data['id'])
            res.append(q_del)
            # Then add
            q = "INSERT INTO service_servicegroup (service, servicegroup) VALUES ('%s', '%s')" % (s_id, b.data['id'])
            res.append(q)
        return res

    # Same than service result, but for host result
    def manage_host_check_result_brok(self, b):
        b.data['last_update'] = time.time()
        data = b.data
        # Only the host is impacted
        where_clause = {'host_name': data['host_name']}
        query = self.db_backend.create_update_query('host', data, where_clause)
        return [query]

    # Same than service result, but for host new scheduling
    def manage_host_next_schedule_brok(self, b):
        data = b.data
        # Only the host is impacted
        where_clause = {'host_name': data['host_name']}
        query = self.db_backend.create_update_query('host', data, where_clause)
        return [query]

    # Ok the host is updated
    def manage_update_host_status_brok(self, b):
        b.data['last_update'] = time.time()
        data = b.data
        # Only this host
        where_clause = {'host_name': data['host_name']}
        query = self.db_backend.create_update_query('host', data, where_clause)
        return [query]

    # A contact have just be created, database is clean, we INSERT it
    def manage_initial_contact_status_brok(self, b):
        query = self.db_backend.create_insert_query('contact', b.data)
        return [query]

    # same from hostgroup, but with servicegroup
    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data

        # Here we've got a special case: in data, there is members
        # and we do not want it in the INSERT query, so we create a
        # tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        query = self.db_backend.create_insert_query('contactgroup', tmp_data)
        res = [query]

        # Now the members part
        for (c_id, c_name) in b.data['members']:
            # first clean
            q_del = "DELETE FROM contact_contactgroup WHERE contact='%s' and contactgroup='%s'" % (c_id, b.data['id'])
            res.append(q_del)
            # Then add
            q = "INSERT INTO contact_contactgroup (contact, contactgroup) VALUES ('%s', '%s')" % (c_id, b.data['id'])
            res.append(q)
        return res

    # A notification have just be created, we INSERT it
    def manage_notification_raise_brok(self, b):
        n_data = {}
        t = ['reason_type', 'service_description', 'ack_data', 'contacts_notified', 'start_time', 'escalated', 'instance_id',
         'state', 'end_time', 'ack_author', 'notification_type', 'output', 'id', 'host_name']
        for prop in t:
            n_data[prop] = b.data[prop]
        query = self.db_backend.create_insert_query('notification', n_data)
        return [query]
