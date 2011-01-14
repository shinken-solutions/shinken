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
#to brok information into the merlin database. for the moment
#only Mysql is supported. This code is __imported__ from Broker.
#The managed_brok function is called by Broker for manage the broks. It calls
#the manage_*_brok functions that create queries, and then run queries.


import copy
import time

try:
    from shinken.db_mysql import DBMysql
except : # TODO : fix this, python2.4 is not happy here?
    from db_mysql import DBMysql


def de_unixify(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))



#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Ndodb_broker:
    def __init__(self, name, host, user, password, database, character_set):
        #Mapping for name of dataand transform function
        self.mapping = {
            'program_status' : {'program_start' : {'name' : 'program_start_time', 'transform' : de_unixify},
                                'pid' : {'name' : 'process_id', 'transform' : None},
                                'last_alive' : {'name' : 'status_update_time', 'transform' : de_unixify},
                                'is_running' : {'name' : 'is_currently_running', 'transform' : None}
                                },
            }
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.character_set = character_set



    #The classic has : do we have a prop or not?
    def has(self, prop):
        return hasattr(self, prop)


    def get_name(self):
        return self.name


    #Called by Broker so we can do init stuff
    #TODO : add conf param to get pass with init
    #Conf from arbiter!
    def init(self):
        print "I connect to NDO database"
        self.db = DBMysql(self.host, self.user, self.password, self.database, self.character_set, table_prefix='nagios_')
        self.connect_database()

        #Cache for hosts and services
        #will be flushed when we got a net instance id
        #or something like that
        self.services_cache = {}
        self.hosts_cache = {}


    #Get a brok, parse it, and put in in database
    #We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        type = b.type
        manager = 'manage_'+type+'_brok'
        #We've got problem with instance_id == 0 so we add 1 every where
        if 'instance_id' in b.data:
            b.data['instance_id'] = b.data['instance_id'] + 1
        #print "(Ndo) I search manager:", manager
        if self.has(manager):
            f = getattr(self, manager)
            queries = f(b)
            #Ok, we've got queries, now : run them!
            for q in queries :
                self.db.execute_query(q)
            return
        #print "(ndodb)I don't manage this brok type", b


    #Create the database connexion
    #TODO : finish (begin :) ) error catch and conf parameters...
    def connect_database(self):
        self.db.connect_database()


    def get_host_object_id_by_name(self, host_name):
        #First look in cache.
        if host_name in self.hosts_cache:
            return self.hosts_cache[host_name]

        #Not in cache, not good
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='1'" % host_name
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row == None or len(row) < 1:
            return 0
        else:
            self.hosts_cache[host_name] = row[0]
            return row[0]


    def get_hostgroup_object_id_by_name(self, hostgroup_name):
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='3'" % hostgroup_name
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row == None or len(row) < 1:
            return 0
        else:
            return row[0]


    def get_service_object_id_by_name(self, host_name, service_description):
        #first look in cache
        if (host_name, service_description) in self.services_cache:
            return self.services_cache[(host_name, service_description)]

        #else; not in cache :(
        query = u"SELECT object_id from nagios_objects where name1='%s' and name2='%s' and objecttype_id='2'" % (host_name, service_description)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row == None or len(row) < 1:
            return 0
        else:
            self.services_cache[(host_name, service_description)] = row[0]
            return row[0]


    def get_servicegroup_object_id_by_name(self, servicegroup_name):
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='4'" % servicegroup_name
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row == None or len(row) < 1:
            return 0
        else:
            return row[0]


    #Ok, we are at launch and a scheduler want him only, OK...
    #So ca create several queries with all tables we need to delete with
    #our instance_id
    #This brob must be send at the begining of a scheduler session,
    #if not, BAD THINGS MAY HAPPENED :)
    def manage_clean_all_my_instance_id_brok(self, b):
        instance_id = b.data['instance_id']
        tables = ['commands', 'contacts', 'contactgroups', 'hosts',
                  'hostescalations', 'hostgroups', 'notifications',
                  'services',  'serviceescalations', 'programstatus',
                  'servicegroups', 'timeperiods', 'hostgroup_members',
                  'contactgroup_members', 'objects', 'hoststatus',
                  'servicestatus', 'instances', 'servicegroup_members']
        res = []
        for table in tables:
            q = "DELETE FROM %s WHERE instance_id = '%s' " % ('nagios_'+table, instance_id)
            res.append(q)

        #We also clean cache, because we are not sure about this data now
        print "[MySQL/NDO] Flushing caches"
        self.services_cache = {}
        self.hosts_cache = {}

        return res


    #Program status is .. status of program? :)
    #Like pid, daemon mode, last activity, etc
    #We aleady clean database, so insert

    #TODO : fill nagios_instances
    def manage_program_status_brok(self, b):
        new_b = copy.deepcopy(b)

        #Must delete me first
        query_delete_instance = u"DELETE FROM %s WHERE instance_name = '%s' " % ('nagios_instances', b.data['instance_name'])

        query_instance = self.db.create_insert_query('instances', {'instance_name' : new_b.data['instance_name'],\
         'instance_description' : new_b.data['instance_name'], \
        'instance_id' : new_b.data['instance_id']
        })

        to_del = ['instance_name', 'command_file']
        to_add = []
        mapping = self.mapping['program_status']
        for prop in new_b.data:
            #ex : 'name' : 'program_start_time', 'transform'
            if prop in mapping:
                #print "Got a prop to change", prop
                val = new_b.data[prop]
                if mapping[prop]['transform'] != None:
                    f = mapping[prop]['transform']
                    val = f(val)
                new_name = mapping[prop]['name']
                to_add.append((new_name, val))
                to_del.append(prop)
        for prop in to_del:
            del new_b.data[prop]
        for (name, val) in to_add:
            new_b.data[name] = val
        query = self.db.create_insert_query('programstatus', new_b.data)
        return [query_delete_instance, query_instance, query]


    #TODO : fill nagios_instances
    def manage_update_program_status_brok(self, b):
        new_b = copy.deepcopy(b)
        to_del = ['instance_name', 'command_file']
        to_add = []
        mapping = self.mapping['program_status']
        for prop in new_b.data:
            #ex : 'name' : 'program_start_time', 'transform'
            if prop in mapping:
                #print "Got a prop to change", prop
                val = new_b.data[prop]
                if mapping[prop]['transform'] != None:
                    f = mapping[prop]['transform']
                    val = f(val)
                new_name = mapping[prop]['name']
                to_add.append((new_name, val))
                to_del.append(prop)
        for prop in to_del:
            del new_b.data[prop]
        for (name, val) in to_add:
            new_b.data[name] = val
        where_clause = {'instance_id' : new_b.data['instance_id']}
        query = self.db.create_update_query('programstatus', new_b.data, where_clause)
        return [query]


    #A host have just be create, database is clean, we INSERT it
    def manage_initial_host_status_brok(self, b):
        #new_b = copy.deepcopy(b)

        data = b.data

        #First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 1,
                        'name1' : data['host_name'], 'is_active' : data['active_checks_enabled']
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        host_id = self.get_host_object_id_by_name(data['host_name'])

        #print "DATA:", data
        hosts_data = {'host_id' : data['id'], 'instance_id' : data['instance_id'],
                      'host_object_id' : host_id, 'alias' : data['alias'],
                      'display_name' : data['display_name'], 'address' : data['address'],
                      'failure_prediction_options' : '0', 'check_interval' : data['check_interval'],
                      'retry_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                      'first_notification_delay' : data['first_notification_delay'], 'notification_interval' : data['notification_interval'],
                      'flap_detection_enabled' : data['flap_detection_enabled'], 'low_flap_threshold' : data['low_flap_threshold'],
                      'high_flap_threshold' : data['high_flap_threshold'], 'process_performance_data' : data['process_perf_data'],
                      'freshness_checks_enabled' : data['check_freshness'], 'freshness_threshold' : data['freshness_threshold'],
                      'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                      'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                      'obsess_over_host' : data['obsess_over_host'], 'notes' : data['notes'], 'notes_url' : data['notes_url']
            }

        #print "HOST DATA", hosts_data
        query = self.db.create_insert_query('hosts', hosts_data)

        #Now create an hoststatus entry
        hoststatus_data = {'instance_id' : data['instance_id'],
                           'host_object_id' : host_id,
                           'normal_check_interval' : data['check_interval'],
                           'retry_check_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                           'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                           'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                           'obsess_over_host' : data['obsess_over_host'],'process_performance_data' : data['process_perf_data'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'output' : data['output'], 'perfdata' : data['perf_data'],'last_check' : de_unixify(data['last_chk']),
                           'last_hard_state_change' :  de_unixify(data['last_hard_state_change']),
                           'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                           #set check to 1 so nagvis is happy
                           'has_been_checked' : 1,
                           }
        hoststatus_query = self.db.create_insert_query('hoststatus' , hoststatus_data)

        return [query, hoststatus_query]


    #A host have just be create, database is clean, we INSERT it
    def manage_initial_service_status_brok(self, b):
        #new_b = copy.deepcopy(b)

        data = b.data
        #First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 2,
                        'name1' : data['host_name'], 'name2' : data['service_description'], 'is_active' : data['active_checks_enabled']
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        host_id = self.get_host_object_id_by_name(data['host_name'])
        service_id = self.get_service_object_id_by_name(data['host_name'], data['service_description'])

        #print "DATA:", data
        #print "HOST ID:", host_id
        #print "SERVICE ID:", service_id
        services_data = {'service_id' : data['id'], 'instance_id' : data['instance_id'],
                      'service_object_id' : service_id, 'host_object_id' : host_id,
                      'display_name' : data['display_name'],
                      'failure_prediction_options' : '0', 'check_interval' : data['check_interval'],
                      'retry_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                      'first_notification_delay' : data['first_notification_delay'], 'notification_interval' : data['notification_interval'],
                      'flap_detection_enabled' : data['flap_detection_enabled'], 'low_flap_threshold' : data['low_flap_threshold'],
                      'high_flap_threshold' : data['high_flap_threshold'], 'process_performance_data' : data['process_perf_data'],
                      'freshness_checks_enabled' : data['check_freshness'], 'freshness_threshold' : data['freshness_threshold'],
                      'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                      'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                      'obsess_over_service' : data['obsess_over_service'], 'notes' : data['notes'], 'notes_url' : data['notes_url']
            }

        #print "HOST DATA", hosts_data
        query = self.db.create_insert_query('services', services_data)

        #Now create an hoststatus entry
        servicestatus_data = {'instance_id' : data['instance_id'],
                              'service_object_id' : service_id,
                              'normal_check_interval' : data['check_interval'],
                              'retry_check_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                              'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                              'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                              'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                              'obsess_over_service' : data['obsess_over_service'],'process_performance_data' : data['process_perf_data'],

                              'check_type' : 0, 'current_check_attempt' : data['attempt'],
                              'execution_time' : data['execution_time'], 'latency' : data['latency'],
                              'output' : data['output'], 'perfdata' : data['perf_data'], 'last_check' : de_unixify(data['last_chk']),
                              'last_hard_state_change' :  de_unixify(data['last_hard_state_change']),
                              'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                              #set check to 1 so nagvis is happy
                              'has_been_checked' : 1,
                              }
        servicestatus_query = self.db.create_insert_query('servicestatus' , servicestatus_data)

        return [query, servicestatus_query]



    #A new host group? Insert it
    #We need to do something for the members prop (host.id, host_name)
    #They are for host_hostgroup table, with just host.id hostgroup.id
    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data

        #First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 3,
                        'name1' : data['hostgroup_name'], 'is_active' : 1
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        hostgroup_id = self.get_hostgroup_object_id_by_name(data['hostgroup_name'])

        hostgroups_data = {'hostgroup_id' : data['id'], 'instance_id' :  data['instance_id'],
                           'config_type' : 0, 'hostgroup_object_id' : hostgroup_id,
                           'alias' : data['alias']
            }

        query = self.db.create_insert_query('hostgroups', hostgroups_data)
        res = [query]

        #Ok, the hostgroups table is uptodate, now we add relations
        #between hosts and hostgroups
        for (h_id, h_name) in b.data['members']:
            hostgroup_members_data = {'instance_id' : data['instance_id'], 'hostgroup_id' : data['id'],
                                      'host_object_id' : h_id}
            q = self.db.create_insert_query('hostgroup_members', hostgroup_members_data)
            res.append(q)
        return res



    #A new host group? Insert it
    #We need to do something for the members prop (host.id, host_name)
    #They are for host_hostgroup table, with just host.id hostgroup.id
    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data

        #First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 4,
                        'name1' : data['servicegroup_name'], 'is_active' : 1
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        servicegroup_id = self.get_servicegroup_object_id_by_name(data['servicegroup_name'])


        servicegroups_data = {'servicegroup_id' : data['id'], 'instance_id' :  data['instance_id'],
                           'config_type' : 0, 'servicegroup_object_id' : servicegroup_id,
                           'alias' : data['alias']
            }

        query = self.db.create_insert_query('servicegroups', servicegroups_data)
        res = [query]

        #Ok, the hostgroups table is uptodate, now we add relations
        #between hosts and hostgroups
        for (s_id, s_name) in b.data['members']:
            servicegroup_members_data = {'instance_id' : data['instance_id'], 'servicegroup_id' : data['id'],
                                         'service_object_id' : s_id}
            q = self.db.create_insert_query('servicegroup_members', servicegroup_members_data)
            res.append(q)
        return res


    #Same than service result, but for host result
    def manage_host_check_result_brok(self, b):
        data = b.data
        #print "DATA", data
        host_id = self.get_host_object_id_by_name(data['host_name'])
        #Only the host is impacted
        where_clause = {'host_object_id' : host_id}
        host_check_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'is_raw_check' : 0, 'current_check_attempt' : data['attempt'],
                           'state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'start_time' : data['start_time'], 'start_time_usec' : 0,
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'return_code' : data['return_code'], 'output' : data['output'],
                           'perfdata' : data['perf_data']
        }
        query = self.db.create_update_query('hostchecks', host_check_data, where_clause)

        #Now servicestatus
        hoststatus_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'output' : data['output'], 'perfdata' : data['perf_data'], 'last_check' : de_unixify(data['last_chk'])
        }
        hoststatus_query = self.db.create_update_query('hoststatus' , hoststatus_data, where_clause)

        return [query, hoststatus_query]

    #The next schedule got it's own brok. got it and just update the
    #next_check with it
    def manage_host_next_schedule_brok(self, b):
        data = b.data
        host_id = self.get_host_object_id_by_name(data['host_name'])
        #Only the host is impacted
        where_clause = {'host_object_id' : host_id}

        #Just update teh host status
        hoststatus_data = {'next_check' : de_unixify(data['next_chk'])}
        hoststatus_query = self.db.create_update_query('hoststatus' , hoststatus_data, where_clause)

        return [hoststatus_query]


    #Same than service result, but for host result
    def manage_service_check_result_brok(self, b):
        data = b.data
        #print "DATA", data
        service_id = self.get_service_object_id_by_name(data['host_name'], data['service_description'])

        #Only the service is impacted
        where_clause = {'service_object_id' : service_id}
        service_check_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'start_time' : data['start_time'], 'start_time_usec' : 0,
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'return_code' : data['return_code'], 'output' : data['output'],
                           'perfdata' : data['perf_data']
        }
        query = self.db.create_update_query('servicechecks', service_check_data, where_clause)

        #Now servicestatus
        servicestatus_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'output' : data['output'], 'perfdata' : data['perf_data'], 'last_check' : de_unixify(data['last_chk'])
        }

        servicestatus_query = self.db.create_update_query('servicestatus' , servicestatus_data, where_clause)

        return [query, servicestatus_query]


    #The next schedule got it's own brok. got it and just update the
    #next_check with it
    def manage_service_next_schedule_brok(self, b):
        data = b.data
        #print "DATA", data
        service_id = self.get_service_object_id_by_name(data['host_name'], data['service_description'])

        #Only the service is impacted
        where_clause = {'service_object_id' : service_id}

        #Just update the service status
        servicestatus_data = {'next_check' : de_unixify(data['next_chk'])}
        servicestatus_query = self.db.create_update_query('servicestatus' , servicestatus_data, where_clause)

        return [servicestatus_query]



    #Ok the host is updated
    def manage_update_host_status_brok(self, b):
        data = b.data
        host_id = self.get_host_object_id_by_name(data['host_name'])

        hosts_data = {'instance_id' : data['instance_id'],
                      'failure_prediction_options' : '0', 'check_interval' : data['check_interval'],
                      'retry_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                      'first_notification_delay' : data['first_notification_delay'], 'notification_interval' : data['notification_interval'],
                      'flap_detection_enabled' : data['flap_detection_enabled'], 'low_flap_threshold' : data['low_flap_threshold'],
                      'high_flap_threshold' : data['high_flap_threshold'], 'process_performance_data' : data['process_perf_data'],
                      'freshness_checks_enabled' : data['check_freshness'], 'freshness_threshold' : data['freshness_threshold'],
                      'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                      'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                      'obsess_over_host' : data['obsess_over_host'], 'notes' : data['notes'], 'notes_url' : data['notes_url']
            }
        #Only the host is impacted
        where_clause = {'host_object_id' : host_id}

        query = self.db.create_update_query('hosts', hosts_data, where_clause)

        #Now update an hoststatus entry
        hoststatus_data = {'instance_id' : data['instance_id'],
                           'host_object_id' : host_id,
                           'normal_check_interval' : data['check_interval'],
                           'retry_check_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                           'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                           'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                           'obsess_over_host' : data['obsess_over_host'],'process_performance_data' : data['process_perf_data'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'output' : data['output'], 'perfdata' : data['perf_data'],'last_check' : de_unixify(data['last_chk']),
                           'last_hard_state_change' :  de_unixify(data['last_hard_state_change']),
                           'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                           #set check to 1 so nagvis is happy
                           'has_been_checked' : 1,
                           }
        hoststatus_query = self.db.create_update_query('hoststatus' , hoststatus_data, where_clause)

        return [query, hoststatus_query]


    #Ok the host is updated
    def manage_update_service_status_brok(self, b):
        data = b.data

        service_id = self.get_service_object_id_by_name(data['host_name'], data['service_description'])



        services_data = {'instance_id' : data['instance_id'],
                      'display_name' : data['display_name'],
                      'failure_prediction_options' : '0', 'check_interval' : data['check_interval'],
                      'retry_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                      'first_notification_delay' : data['first_notification_delay'], 'notification_interval' : data['notification_interval'],
                      'flap_detection_enabled' : data['flap_detection_enabled'], 'low_flap_threshold' : data['low_flap_threshold'],
                      'high_flap_threshold' : data['high_flap_threshold'], 'process_performance_data' : data['process_perf_data'],
                      'freshness_checks_enabled' : data['check_freshness'], 'freshness_threshold' : data['freshness_threshold'],
                      'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                      'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                      'obsess_over_service' : data['obsess_over_service'], 'notes' : data['notes'], 'notes_url' : data['notes_url']
            }

        #Only the service is impacted
        where_clause = {'service_object_id' : service_id, 'service_id' : data['id']}
        #where_clause = {'host_name' : data['host_name']}
        query = self.db.create_update_query('services', services_data, where_clause)

        #Now create an hoststatus entry
        servicestatus_data = {'instance_id' : data['instance_id'],
                              'service_object_id' : service_id,
                              'normal_check_interval' : data['check_interval'],
                              'retry_check_interval' : data['retry_interval'], 'max_check_attempts' : data['max_check_attempts'],
                              'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                              'passive_checks_enabled' : data['passive_checks_enabled'], 'event_handler_enabled' : data['event_handler_enabled'],
                              'active_checks_enabled' : data['active_checks_enabled'], 'notifications_enabled' : data['notifications_enabled'],
                              'obsess_over_service' : data['obsess_over_service'],'process_performance_data' : data['process_perf_data'],

                              'check_type' : 0, 'current_check_attempt' : data['attempt'],
                              'execution_time' : data['execution_time'], 'latency' : data['latency'],
                              'output' : data['output'], 'perfdata' : data['perf_data'], 'last_check' : de_unixify(data['last_chk']),
                              'last_hard_state_change' :  de_unixify(data['last_hard_state_change']),
                              'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                              #set check to 1 so nagvis is happy
                              'has_been_checked' : 1,
                              }

        where_clause = {'service_object_id' : service_id}
        servicestatus_query = self.db.create_update_query('servicestatus' , servicestatus_data, where_clause)

        return [query, servicestatus_query]



    #A host have just be create, database is clean, we INSERT it
    def manage_initial_contact_status_brok(self, b):
        #new_b = copy.deepcopy(b)
        data = b.data
        #print "DATA:", data

        contacts_data = {'contact_id' : data['id'], 'instance_id' : data['instance_id'],
                      'contact_object_id' : data['id'], 'contact_object_id' : data['id'],
                      'alias' : data['alias'],
                      'email_address' : data['email'], 'pager_address' : data['pager'],
                      'host_notifications_enabled' : data['host_notifications_enabled'],
                      'service_notifications_enabled' : data['service_notifications_enabled'],
            }

        #print "HOST DATA", hosts_data
        query = self.db.create_insert_query('contacts', contacts_data)
        return [query]



    #A new host group? Insert it
    #We need to do something for the members prop (host.id, host_name)
    #They are for host_hostgroup table, with just host.id hostgroup.id
    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data

        contactgroups_data = {'contactgroup_id' : data['id'], 'instance_id' :  data['instance_id'],
                           'config_type' : 0, 'contactgroup_object_id' : data['id'],
                           'alias' : data['alias']
            }

        query = self.db.create_insert_query('contactgroups', contactgroups_data)
        res = [query]

        #Ok, the hostgroups table is uptodate, now we add relations
        #between hosts and hostgroups
        for (c_id, c_name) in b.data['members']:
            #print c_name
            contactgroup_members_data = {'instance_id' : data['instance_id'], 'contactgroup_id' : data['id'],
                                         'contact_object_id' : c_id}
            q = self.db.create_insert_query('contactgroup_members', contactgroup_members_data)
            res.append(q)
        return res



    #A notification have just be created, we INSERT it
    #def manage_notification_raise_brok(self, b):
    #    query = self.db.create_insert_query('notification', b.data)
    #    return [query]
