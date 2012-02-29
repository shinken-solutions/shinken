#!/usr/bin/python

# Copyright (C) 2009-2011 :
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
# to brok information into the database. For the moment
# only Mysql is supported. This code is __imported__ from Broker.
# The managed_brok function is called by Broker for manage the broks. It calls
# the manage_*_brok functions that create queries, and then run queries.


import copy
import time
import sys
import _mysql_exceptions

properties = {
    'daemons' : ['broker'],
    'type' : 'ndodb_mysql',
    'phases' : ['running'],
    }


from shinken.db_mysql import DBMysql
from shinken.basemodule import BaseModule
from shinken.log import logger


def de_unixify(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))



# Class for the NDO MySQL Broker
# Get broks and puts them in MySQL database
class Ndodb_Mysql_broker(BaseModule):
    def __init__(self, conf):
        BaseModule.__init__(self, conf)
        # Mapping for name of data and transform function
        self.mapping = {
            'program_status' : {
                                'program_start' : {'name' : 'program_start_time', 'transform' : de_unixify},
                                'pid' : {'name' : 'process_id', 'transform' : None},
                                'last_alive' : {'name' : 'status_update_time', 'transform' : de_unixify},
                                'is_running' : {'name' : 'is_currently_running', 'transform' : None}
                                },
            }
        
        self.host = conf.host
        self.user = conf.user
        self.password = conf.password
        self.database = conf.database
        self.character_set = conf.character_set
        self.port = int(getattr(conf, 'port', '3306'))
        
        # Centreon ndo add some fields like long_output that are not in the vanilla ndo
        self.centreon_version = False
        self.synchronise_database_id = int(conf.synchronise_database_id)


    # Called by Broker so we can do init stuff
    # TODO : add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        logger.log("I connect to NDO database")
        self.db = DBMysql(self.host, self.user, self.password, self.database, 
                          self.character_set, table_prefix='nagios_', port=self.port)
        self.connect_database()

        # Cache for hosts and services
        # The structure is as follow:
        # First the instance id then the host / (host,service desc) to access the wanted data
        self.services_cache_sync = {}
        self.hosts_cache_sync = {}

        # We need to search for centreon_specific fields, like long_output
        query = u"select TABLE_NAME from information_schema.columns where TABLE_SCHEMA='ndo' and TABLE_NAME='nagios_servicestatus' and COLUMN_NAME='long_output';"
        self.db.execute_query(query)
        row = self.db.fetchone()
        if row is None or len(row) < 1:
            self.centreon_version = False
        else:
            self.centreon_version = True
            logger.log("[MySQL/NDO] Using the centreon version")

        # Cache for database id
        # In order not to query the database every time
        self.database_id_cache = {}

        # Mapping service_id in Shinken and in database
        # Because can't acces host_name from a service everytime :(
        self.mapping_service_id = {}

        # Todo list to manage brok
        self.todo = []


    # Get a brok, parse it, and put in in database
    # We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        # We need to do some brok mod, so we copy it
        new_b = copy.deepcopy(b)
    
        # If we syncronize, must look for id change
        if self.synchronise_database_id != '0' and 'instance_id' in new_b.data:
            # If we use database sync, we have to synchronise database id
            # so we wait for the instance name
            if 'instance_name' not in new_b.data :
                self.todo.append(new_b)
                return  
                  
            # We convert the id to write properly in the base using the 
            # instance_name to reuse the instance_id in the base.
            else:
                new_b.data['instance_id'] = self.convert_id(new_b.data['instance_id'], new_b.data['instance_name'])
                self.todo.append(new_b)
                for brok in self.todo :
                    # We have to put the good instance ID to all brok waiting
                    # in the list then execute the query
                    brok.data['instance_id'] = new_b.data['instance_id']
                    queries = BaseModule.manage_brok(self, brok)
                    if queries is not None:
                        for q in queries :
                            self.db.execute_query(q)
                # We've finished to manage the todo, so we empty it
                self.todo = []
                return

        # Executed if we don't synchronise or there is no instance_id
        queries = BaseModule.manage_brok(self,new_b)
        
        if queries is not None:
            for q in queries :
                self.db.execute_query(q)
            return



    # Create the database connection
    # Exception is raised if a arg is bad.
    def connect_database(self):    
        try :
            self.db.connect_database()
        except _mysql_exceptions.OperationalError, exp:
            logger.log( "[MySQL/NDO] Module raise an exception : %s . Please check the arguments!" % exp)
            raise


    # Query the database to get the proper instance_id
    def get_instance_id(self,name):
        query1 = u"SELECT  max(instance_id) + 1 from nagios_instances"
        query2 = u"SELECT instance_id from nagios_instances where instance_name = '%s';" % name

        self.db.execute_query(query1)
        row1  = self.db.fetchone()

        self.db.execute_query(query2)
        row2 = self.db.fetchone()

        if len(row1)<1 :
            return -1
        # We are the first process writing in base      
        elif row1[0] is None:
            return 1
        # No previous instance found return max
        elif row2 is None :
            return row1[0]
        # Return the previous instance
        else:
            return row2[0]



    def convert_id(self, id, name):
        # Look if we have already encountered this id
        if id in self.database_id_cache :
            return self.database_id_cache[id]
        else :
            data_id = 1
            # If we disable the database sync, we are using the in-brok instance_id
            if self.synchronise_database_id == '0':
                data_id = id
            # Else : we are quering the database and get a new one
            else:
                data_id = self.get_instance_id(name)
            # cache this!
            self.database_id_cache[id] = data_id                
            return data_id



    def get_host_object_id_by_name_sync(self, host_name, instance_id):
        # First look in cache.
        if instance_id in self.hosts_cache_sync:
            if host_name in self.hosts_cache_sync[instance_id]:
                return self.hosts_cache_sync[instance_id][host_name]

        # Not in cache, not good
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='1' and instance_id='%s'" % (host_name,instance_id)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            if instance_id not in self.hosts_cache_sync:
                self.hosts_cache_sync[instance_id] = {}
            self.hosts_cache_sync[instance_id][host_name] = row[0]
            return row[0]



    def get_contact_object_id_by_name_sync(self, contact_name,instance_id):        
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='10' and instance_id='%s'" % (contact_name,instance_id)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]



    def get_hostgroup_object_id_by_name_sync(self, hostgroup_name, instance_id):
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='3' and instance_id='%s'" % (hostgroup_name,instance_id)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]



    def get_max_hostgroup_id_sync(self): 
        query = u"SELECT max(hostgroup_id) + 1 from nagios_hostgroups"
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]



    def get_service_object_id_by_name_sync(self, host_name, service_description, instance_id):
        if instance_id in self.services_cache_sync:
            if (host_name, service_description) in self.services_cache_sync[instance_id]:
                return self.services_cache_sync[instance_id][(host_name, service_description)]

        # else; not in cache :(
        query = u"SELECT object_id from nagios_objects where name1='%s' and name2='%s' and objecttype_id='2' and instance_id='%s'" % (host_name, service_description,instance_id)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            if instance_id not in self.services_cache_sync:
                self.services_cache_sync[instance_id] = {}
            self.services_cache_sync[instance_id][(host_name, service_description)] = row[0]
            return row[0]



    def get_servicegroup_object_id_by_name_sync(self, servicegroup_name, instance_id):
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='4' and instance_id='%s'" % (servicegroup_name,instance_id)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]
 
   
    
    def get_max_servicegroup_id_sync(self):
        query = u"SELECT max(servicegroup_id) + 1 from nagios_servicegroups"
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]


        
    def get_contactgroup_object_id_by_name_sync(self, contactgroup_name, instance_id):              
        query = u"SELECT object_id from nagios_objects where name1='%s' and objecttype_id='11'and instance_id='%s'" % (contactgroup_name,instance_id)
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]



    def get_max_contactgroup_id_sync(self):
        query = u"SELECT max(contactgroup_id) + 1 from nagios_contactgroups"
        self.db.execute_query(query)
        row = self.db.fetchone ()
        if row is None or len(row) < 1:
            return 0
        else:
            return row[0]



    # Ok, we are at launch time and a scheduler want him only, OK...
    # So create several queries with all tables we need to delete with
    # our instance_id
    # This brob must be send at the begining of a scheduler session,
    # if not, BAD THINGS MAY HAPPENED :)
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

        # We also clean cache, because we are not sure about this data now
        logger.log("[MySQL/NDO] Flushing caches (clean from instance %d)" % instance_id)
        self.services_cache_sync = {}
        self.hosts_cache_sync = {}

        return res



    # Program status is .. status of program? :)
    # Like pid, daemon mode, last activity, etc
    # We aleady clean database, so insert
    # TODO : fill nagios_instances
    def manage_program_status_brok(self, b):
        new_b = copy.deepcopy(b)

        # Must delete me first
        query_delete_instance = u"DELETE FROM %s WHERE instance_name = '%s' " % ('nagios_instances', b.data['instance_name'])

        query_instance = self.db.create_insert_query('instances', {'instance_name' : new_b.data['instance_name'],\
         'instance_description' : new_b.data['instance_name'], \
        'instance_id' : new_b.data['instance_id']
        })

        to_del = ['instance_name', 'command_file', 'check_external_commands', 'check_service_freshness',
                  'check_host_freshness']
        to_add = []
        mapping = self.mapping['program_status']
        for prop in new_b.data:
            # ex : 'name' : 'program_start_time', 'transform'
            if prop in mapping:
                #print "Got a prop to change", prop
                val = new_b.data[prop]
                if mapping[prop]['transform'] is not None:
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



    # TODO : fill nagios_instances
    def manage_update_program_status_brok(self, b):
        new_b = copy.deepcopy(b)
        to_del = ['instance_name', 'command_file', 'check_external_commands', 'check_service_freshness',
                  'check_host_freshness']
        to_add = []
        mapping = self.mapping['program_status']
        for prop in new_b.data:
            # ex : 'name' : 'program_start_time', 'transform'
            if prop in mapping:
                #print "Got a prop to change", prop
                val = new_b.data[prop]
                if mapping[prop]['transform'] is not None:
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



    # A host have just be create, database is clean, we INSERT it
    def manage_initial_host_status_brok(self, b):
        
        data = b.data

        # First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 1,
                        'name1' : data['host_name'], 'is_active' : data['active_checks_enabled']
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        host_id = self.get_host_object_id_by_name_sync(data['host_name'],data['instance_id'])

        #print "DATA:", data
        hosts_data = { 'instance_id' : data['instance_id'],
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
                      'obsess_over_host' : data['obsess_over_host'], 'notes' : data['notes'], 'notes_url' : data['notes_url'],
            }

        #print "HOST DATA", hosts_data
        query = self.db.create_insert_query('hosts', hosts_data)

        # Now create an hoststatus entry
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
                           'last_state_change' :  de_unixify(data['last_state_change']),
                           'last_notification' : de_unixify(data['last_notification']),
                           'current_notification_number' : data['current_notification_number'],
                           'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                           # set check to 1 so nagvis is happy
                           'has_been_checked' : 1, 'percent_state_change' : data['percent_state_change'], 'is_flapping' : data['is_flapping'],
                           'flap_detection_enabled' : data['flap_detection_enabled'],
                           }

        # Centreon add some fields
        if self.centreon_version:
            hoststatus_data['long_output'] = data['long_output']

        hoststatus_query = self.db.create_insert_query('hoststatus' , hoststatus_data)

        return [query, hoststatus_query]



    # A service have just been created, database is clean, we INSERT it
    def manage_initial_service_status_brok(self, b):
        #new_b = copy.deepcopy(b)

        data = b.data
        # First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 2,
                        'name1' : data['host_name'], 'name2' : data['service_description'], 'is_active' : data['active_checks_enabled']
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        host_id = self.get_host_object_id_by_name_sync(data['host_name'],data['instance_id'])
        service_id = self.get_service_object_id_by_name_sync(data['host_name'], data['service_description'],data['instance_id'])
        
        # TODO : Include with the service cache.
        self.mapping_service_id[data['id']] = service_id
        

        #print "DATA:", data
        #print "HOST ID:", host_id
        #print "SERVICE ID:", service_id
        services_data = { 'instance_id' : data['instance_id'],
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

        # Now create an hoststatus entry
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
                              'last_state_change' :  de_unixify(data['last_state_change']),
                              'last_notification' : de_unixify(data['last_notification']),
                              'current_notification_number' : data['current_notification_number'],
                              'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                              # set check to 1 so nagvis is happy
                              'has_been_checked' : 1, 'percent_state_change' : data['percent_state_change'], 'is_flapping' : data['is_flapping'],
                              'flap_detection_enabled' : data['flap_detection_enabled'],
                              }

        # Centreon add some fields
        if self.centreon_version:
            servicestatus_data['long_output'] = data['long_output']

        servicestatus_query = self.db.create_insert_query('servicestatus' , servicestatus_data)

        return [query, servicestatus_query]



    # A new host group? Insert it
    # We need to do something for the members prop (host.id, host_name)
    # They are for host_hostgroup table, with just host.id hostgroup.id
    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data

        # First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 3,
                        'name1' : data['hostgroup_name'], 'is_active' : 1
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        hostgroup_id = self.get_hostgroup_object_id_by_name_sync(data['hostgroup_name'],data['instance_id'])
        
        # We can't get the id of the hostgroup in the base because we don't have inserted it yet!
        # So we get a suitable id in this table an fix it for the hostgroup and hostgroup_member
        hostgp_id = self.get_max_hostgroup_id_sync()

        hostgroups_data = { 'hostgroup_id' : hostgp_id, 'instance_id' :  data['instance_id'],
                           'config_type' : 0, 'hostgroup_object_id' : hostgroup_id,
                           'alias' : data['alias']
            }

        query = self.db.create_insert_query('hostgroups', hostgroups_data)
        res = [query]

        # Ok, the hostgroups table is uptodate, now we add relations
        # between hosts and hostgroups
        for (h_id, h_name) in b.data['members']:
            host_id = self.get_host_object_id_by_name_sync(h_name,data['instance_id'])

            hostgroup_members_data = {'instance_id' : data['instance_id'], 'hostgroup_id' : hostgp_id,
                                      'host_object_id' : host_id}
            q = self.db.create_insert_query('hostgroup_members', hostgroup_members_data)
            res.append(q)
        return res



    # A new service group? Insert it
    # We need to do something for the members prop (serv.id, service_name)
    # They are for service_hostgroup table, with just service.id servicegroup.id
    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data

        # First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 4,
                        'name1' : data['servicegroup_name'], 'is_active' : 1
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        servicegroup_id = self.get_servicegroup_object_id_by_name_sync(data['servicegroup_name'],data['instance_id'])
        svcgp_id = self.get_max_servicegroup_id_sync()
        


        servicegroups_data = {'servicegroup_id' : svcgp_id, 'instance_id' :  data['instance_id'],
                           'config_type' : 0, 'servicegroup_object_id' : servicegroup_id,
                           'alias' : data['alias']
            }

        query = self.db.create_insert_query('servicegroups', servicegroups_data)
        res = [query]
        
                
        # Ok, the servicegroups table is up to date, now we add relations
        # between service and servicegroups
        for (s_id, s_name) in b.data['members']:
            # TODO : Include with the service cache.
            service_id = self.mapping_service_id[s_id]
            servicegroup_members_data = {'instance_id' : data['instance_id'], 'servicegroup_id' : svcgp_id,
                                         'service_object_id' : service_id}
            q = self.db.create_insert_query('servicegroup_members', servicegroup_members_data)
            res.append(q)
        return res



    # Same than service result, but for host result
    def manage_host_check_result_brok(self, b):
        data = b.data
        #print "DATA", data
        host_id = self.get_host_object_id_by_name_sync(data['host_name'],data['instance_id'])

        # Only the host is impacted
        where_clause = {'host_object_id' : host_id}
        host_check_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'is_raw_check' : 0, 'current_check_attempt' : data['attempt'],
                           'state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'start_time' : data['start_time'], 'start_time_usec' : 0,
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'return_code' : data['return_code'], 'output' : data['output'],
                           'perfdata' : data['perf_data']
        }
        # Centreon add some fields
        if self.centreon_version:
            host_check_data['long_output'] = data['long_output']

        query = self.db.create_update_query('hostchecks', host_check_data, where_clause)

        # Now servicestatus
        hoststatus_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'output' : data['output'], 'perfdata' : data['perf_data'], 'last_check' : de_unixify(data['last_chk']),
                           'percent_state_change' : data['percent_state_change'],
        }
        # Centreon add some fields
        if self.centreon_version:
            hoststatus_data['long_output'] = data['long_output']

        hoststatus_query = self.db.create_update_query('hoststatus' , hoststatus_data, where_clause)

        return [query, hoststatus_query]



    # The next schedule got it's own brok. got it and just update the
    # next_check with it
    def manage_host_next_schedule_brok(self, b):
        data = b.data
        
        host_id = self.get_host_object_id_by_name_sync(data['host_name'],data['instance_id'])

        # Only the host is impacted
        where_clause = {'host_object_id' : host_id}

        # Just update teh host status
        hoststatus_data = {'next_check' : de_unixify(data['next_chk'])}
        hoststatus_query = self.db.create_update_query('hoststatus' , hoststatus_data, where_clause)

        return [hoststatus_query]



    # Same than host result, but for service result
    def manage_service_check_result_brok(self, b):
        data = b.data
        #print "DATA", data
        service_id = self.get_service_object_id_by_name_sync(data['host_name'], data['service_description'],data['instance_id'])
        
        
        # Only the service is impacted
        where_clause = {'service_object_id' : service_id}
        service_check_data = {'instance_id' : data['instance_id'],
                           'check_type' : 0, 'current_check_attempt' : data['attempt'],
                           'state' : data['state_id'], 'state_type' : data['state_type_id'],
                           'start_time' : data['start_time'], 'start_time_usec' : 0,
                           'execution_time' : data['execution_time'], 'latency' : data['latency'],
                           'return_code' : data['return_code'], 'output' : data['output'],
                           'perfdata' : data['perf_data']
        }

        # Centreon add some fields
        if self.centreon_version:
            service_check_data['long_output'] = data['long_output']

        query = self.db.create_update_query('servicechecks', service_check_data, where_clause)

        # Now servicestatus
        servicestatus_data = {'instance_id' : data['instance_id'],
                              'check_type' : 0, 'current_check_attempt' : data['attempt'],
                              'current_state' : data['state_id'], 'state_type' : data['state_type_id'],
                              'execution_time' : data['execution_time'], 'latency' : data['latency'],
                              'output' : data['output'], 'perfdata' : data['perf_data'], 'last_check' : de_unixify(data['last_chk']),
                              'percent_state_change' : data['percent_state_change'],
        }

        # Centreon add some fields
        if self.centreon_version:
            servicestatus_data['long_output'] = data['long_output']

        servicestatus_query = self.db.create_update_query('servicestatus' , servicestatus_data, where_clause)

        return [query, servicestatus_query]



    # The next schedule got it's own brok. got it and just update the
    # next_check with it
    def manage_service_next_schedule_brok(self, b):
        data = b.data
        #print "DATA", data
        service_id = self.get_service_object_id_by_name_sync(data['host_name'], data['service_description'],data['instance_id'])
        
        
        # Only the service is impacted
        where_clause = {'service_object_id' : service_id}

        # Just update the service status
        servicestatus_data = {'next_check' : de_unixify(data['next_chk'])}
        servicestatus_query = self.db.create_update_query('servicestatus' , servicestatus_data, where_clause)

        return [servicestatus_query]



    # Ok the host is updated
    def manage_update_host_status_brok(self, b):
        data = b.data
        
        host_id = self.get_host_object_id_by_name_sync(data['host_name'],data['instance_id'])
            

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
        # Only the host is impacted
        where_clause = {'host_object_id' : host_id}

        query = self.db.create_update_query('hosts', hosts_data, where_clause)

        # Now update an hoststatus entry
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
                           'last_state_change' :  de_unixify(data['last_state_change']),
                           'last_notification' : de_unixify(data['last_notification']),
                           'current_notification_number' : data['current_notification_number'],
                           'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                           # set check to 1 so nagvis is happy
                           'has_been_checked' : 1, 'is_flapping' : data['is_flapping'], 'percent_state_change' : data['percent_state_change'], 
                           'flap_detection_enabled' : data['flap_detection_enabled'],
                           }

        # Centreon add some fields
        if self.centreon_version:
            hoststatus_data['long_output'] = data['long_output']

        hoststatus_query = self.db.create_update_query('hoststatus' , hoststatus_data, where_clause)

        return [query, hoststatus_query]



    # Ok the service is updated
    def manage_update_service_status_brok(self, b):
        data = b.data

        service_id = self.get_service_object_id_by_name_sync(data['host_name'], data['service_description'],data['instance_id'])


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

        # Only the service is impacted
        where_clause = {'service_object_id' : service_id, 'instance_id' : data['instance_id']}
        # where_clause = {'host_name' : data['host_name']}
        query = self.db.create_update_query('services', services_data, where_clause)

        # Now create an hoststatus entry
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
                              'last_state_change' :  de_unixify(data['last_state_change']),
                              'last_notification' : de_unixify(data['last_notification']),
                              'current_notification_number' : data['current_notification_number'],
                              'problem_has_been_acknowledged' : data['problem_has_been_acknowledged'], 'acknowledgement_type' : data['acknowledgement_type'],
                              # set check to 1 so nagvis is happy
                              'has_been_checked' : 1, 'is_flapping' : data['is_flapping'], 'percent_state_change' : data['percent_state_change'],
                              'flap_detection_enabled' : data['flap_detection_enabled'],
                              }

        # Centreon add some fields
        if self.centreon_version:
            servicestatus_data['long_output'] = data['long_output']

        where_clause = {'service_object_id' : service_id}
        servicestatus_query = self.db.create_update_query('servicestatus' , servicestatus_data, where_clause)

        return [query, servicestatus_query]




    # A host have just be create, database is clean, we INSERT it
    def manage_initial_contact_status_brok(self, b):
        data = b.data
        
        # First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 10,
                        'name1' : data['contact_name'], 'is_active' : 1
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        contact_obj_id = self.get_contact_object_id_by_name_sync(data['contact_name'],data['instance_id'])
        
        contacts_data = {'instance_id' : data['instance_id'],
                      'contact_object_id' : contact_obj_id,
                      'alias' : data['alias'],
                      'email_address' : data['email'], 'pager_address' : data['pager'],
                      'host_notifications_enabled' : data['host_notifications_enabled'],
                      'service_notifications_enabled' : data['service_notifications_enabled'],
            }

        #print "HOST DATA", hosts_data
        query = self.db.create_insert_query('contacts', contacts_data)
        return [query]



    # A new contact group? Insert it
    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data

        # First add to nagios_objects
        objects_data = {'instance_id' : data['instance_id'], 'objecttype_id' : 11,
                        'name1' : data['contactgroup_name'], 'is_active' : 1
                        }
        object_query = self.db.create_insert_query('objects', objects_data)
        self.db.execute_query(object_query)

        contactgroup_id = self.get_contactgroup_object_id_by_name_sync(data['contactgroup_name'],data['instance_id'])
        ctcgp_id = self.get_max_contactgroup_id_sync()

        contactgroups_data = {'contactgroup_id' : ctcgp_id, 'instance_id' :  data['instance_id'],
                           'config_type' : 0,
                           'contactgroup_object_id' : contactgroup_id,
                           'alias' : data['alias']
            }

        query = self.db.create_insert_query('contactgroups', contactgroups_data)
        res = [query]

        # Ok, the hostgroups table is uptodate, now we add relations
        # between hosts and hostgroups
        for (c_id, c_name) in b.data['members']:
            
            contact_obj_id = self.get_contact_object_id_by_name_sync(c_name,data['instance_id'])
            
            contactgroup_members_data = {'instance_id' : data['instance_id'],
                                         'contactgroup_id' : ctcgp_id,
                                         'contact_object_id' : contact_obj_id}
            q = self.db.create_insert_query('contactgroup_members', contactgroup_members_data)
            res.append(q)
        return res



    # A notification have just be created, we INSERT it
    def manage_notification_raise_brok(self, b):

        data = b.data
        #print "CREATING A NOTIFICATION", data
        if data['service_description'] != '':
             service_id = self.get_service_object_id_by_name_sync(data['host_name'], data['service_description'],data['instance_id'])
        else:
             host_id = self.get_host_object_id_by_name_sync(data['host_name'],data['instance_id'])

        notification_data = {'instance_id' :  data['instance_id'],
                             'start_time' : de_unixify(data['start_time']),
                             'end_time' : de_unixify(data['end_time']),
                             'state' : data['state']                             
                             }
        
        query = self.db.create_insert_query('notifications', notification_data)
        return [query]
