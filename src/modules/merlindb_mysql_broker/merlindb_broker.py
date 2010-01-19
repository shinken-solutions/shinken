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
import MySQLdb
from MySQLdb import IntegrityError
from MySQLdb import ProgrammingError



#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Merlindb_broker:
    def __init__(self, name, host, user, password, database, character_set):
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
        print "I connect to Merlin database"
        self.connect_database()
    

    #Get a brok, parse it, and put in in database
    #We call functions like manage_ TYPEOFBROK _brok that return us queries
    def manage_brok(self, b):
        type = b.type
        manager = 'manage_'+type+'_brok'
        #print "(Merlin) I search manager:", manager
        if self.has(manager):
            f = getattr(self, manager)
            queries = f(b)
            #Ok, we've got queries, now : run them!
            for q in queries :
                self.execute_query(q)
            return


    #Create the database connexion
    #TODO : finish (begin :) ) error catch and conf parameters...
    def connect_database(self):
        #self.db = MySQLdb.connect (host = "localhost", user = "root", passwd = "root", db = "merlin")
        self.db = MySQLdb.connect (host = self.host, user = self.user, \
                                       passwd = self.password, db = self.database)
        self.db.set_character_set(self.character_set)
        self.db_cursor = self.db.cursor ()
        self.db_cursor.execute('SET NAMES %s;' % self.character_set)
        self.db_cursor.execute('SET CHARACTER SET %s;' % self.character_set)
        self.db_cursor.execute('SET character_set_connection=%s;' % self.character_set)


    #Just run the query
    #TODO: finish catch
    def execute_query(self, query):
        #print "I run query", query, "\n"
        try:
            self.db_cursor.execute(query)
            self.db.commit ()
        except IntegrityError as exp:
            print "[Merlindb] Warning : a query raise an integrity error : %s, %s" % (query, exp) 
        except ProgrammingError as exp:
            print "[Merlindb] Warning : a query raise a programming error : %s, %s" % (query, exp) 
        

    #Create a INSERT query in table with all data of data (a dict)
    def create_insert_query(self, table, data):
        query = "INSERT INTO %s " % table
        props_str = ' ('
        values_str = ' ('
        i = 0 #for the ',' problem... look like C here...
        for prop in data:
            i += 1
            val = data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0
            if i == 1:
                props_str = props_str + "%s " % prop
                values_str = values_str + "'%s' " % str(val).replace("'", "''")
            else:
                props_str = props_str + ", %s " % prop
                values_str = values_str + ", '%s' " % str(val).replace("'", "''")

        #Ok we've got data, let's finish the query
        props_str = props_str + ' )'
        values_str = values_str + ' )'
        query = query + props_str + 'VALUES' + values_str
        return query

    
    #Create a update query of table with data, and use where data for
    #the WHERE clause
    def create_update_query(self, table, data, where_data):
        query = "UPDATE %s set " % table
		
        #First data manage
        query_folow = ''
        i = 0 #for the , problem...
        for prop in data:
            i += 1
            val = data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0
            if i == 1:
                query_folow += "%s='%s' " % (prop, str(val).replace("'", "''"))
            else:
                query_folow += ", %s='%s' " % (prop, str(val).replace("'", "''"))
                
        #Ok for data, now WHERE, same things
        where_clause = " WHERE "
        i = 0 # For the 'and' problem
        for prop in where_data:
            i += 1
            val = where_data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0
            if i == 1:
                where_clause += "%s='%s' " % (prop, val)
            else:
                where_clause += "and %s='%s' " % (prop, val)

        query = query + query_folow + where_clause
        return query
    
    
    #Ok, we are at launch and a scheduler want him only, OK...
    #So ca create several queries with all tables we need to delete with
    #our instance_id
    #This brob must be send at the begining of a scheduler session, 
    #if not, BAD THINGS MAY HAPPENED :)
    def manage_clean_all_my_instance_id_brok(self, b):
        instance_id = b.data['instance_id']
        tables = ['command', 'comment', 'contact', 'contactgroup', 'downtime', 'host', 
                  'hostdependency', 'hostescalation', 'hostgroup', 'notification', 'program_status', 
                  'scheduled_downtime', 'service',  'serviceescalation',
                  'servicegroup', 'timeperiod']
        res = []
        for table in tables:
            q = "DELETE FROM %s WHERE instance_id = '%s' " % (table, instance_id)
            res.append(q)
        return res


    #Program status is .. status of program? :)
    #Like pid, daemon mode, last activity, etc
    #We aleady clean database, so insert
    def manage_program_status_brok(self, b):
	instance_id = b.data['instance_id']
	del_query = "DELETE FROM program_status WHERE instance_id = '%s' " % instance_id
        query = self.create_insert_query('program_status', b.data)
        return [del_query,query]


    #Initial service status is at start. We need an insert because we 
    #clean the base
    def manage_initial_service_status_brok(self, b):
        #It's a initial entry, so we need insert
        query = self.create_insert_query('service', b.data)		
        return [query]


    #A service check have just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        #We just impact the service :)
        where_clause = {'host_name' : data['host_name'] , 'service_description' : data['service_description']}
        query = self.create_update_query('service', data, where_clause)
        return [query]


    #A full service status? Ok, update data
    def manage_update_service_status_brok(self, b):
        data = b.data
        where_clause = {'host_name' : data['host_name'] , 'service_description' : data['service_description']}
        query = self.create_update_query('service', data, where_clause)
        return [query]


    #A host have just be create, database is clean, we INSERT it
    def manage_initial_host_status_brok(self, b):
        query = self.create_insert_query('host', b.data)
        return [query]


    #A new host group? Insert it
    #We need to do something for the members prop (host.id, host_name)
    #They are for host_hostgroup table, with just host.id hostgroup.id
    def manage_initial_hostgroup_status_brok(self, b):
        data = b.data

        #Here we've got a special case : in data, there is members
        #and we do not want it in the INSERT query, so we crate a 
        #tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        query = self.create_insert_query('hostgroup', tmp_data)
        res = [query]
		
        #Ok, the hostgroup table is uptodate, now we add relations 
        #between hosts and hostgroups
        for (h_id, h_name) in b.data['members']:
            #First clean
            q_del = "DELETE FROM host_hostgroup WHERE host = '%s' and hostgroup='%s'" % (h_id, b.data['id'])
            res.append(q_del)
            #Then add
            q = "INSERT INTO host_hostgroup (host, hostgroup) VALUES ('%s', '%s')" % (h_id, b.data['id'])
            res.append(q)
        return res


    #same from hostgroup, but with servicegroup
    def manage_initial_servicegroup_status_brok(self, b):
        data = b.data

        #Here we've got a special case : in data, there is members
        #and we do not want it in the INSERT query, so we create a
        #tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        query = self.create_insert_query('servicegroup', tmp_data)
        res = [query]

        #Now the members part
        for (s_id, s_name) in b.data['members']:
            #first clean
            q_del = "DELETE FROM service_servicegroup WHERE service='%s' and servicegroup='%s'" % (s_id, b.data['id'])
            res.append(q_del)
            #Then add
            q = "INSERT INTO service_servicegroup (service, servicegroup) VALUES ('%s', '%s')" % (s_id, b.data['id'])
            res.append(q)
        return res


    #Same than service result, but for host result
    def manage_host_check_result_brok(self, b):
        data = b.data
        #Only the host is impacted
        where_clause = {'host_name' : data['host_name']}
        query = self.create_update_query('host', data, where_clause)
        return [query]


    #Ok the host is updated
    def manage_update_host_status_brok(self, b):
        data = b.data
        #Only this host
        where_clause = {'host_name' : data['host_name']}
        query = self.create_update_query('host', data, where_clause)
        return [query]


    #A contact have just be created, database is clean, we INSERT it
    def manage_initial_contact_status_brok(self, b):
        query = self.create_insert_query('contact', b.data)
        return [query]

    #same from hostgroup, but with servicegroup
    def manage_initial_contactgroup_status_brok(self, b):
        data = b.data

        #Here we've got a special case : in data, there is members
        #and we do not want it in the INSERT query, so we create a
        #tmp_data without it
        tmp_data = copy.copy(data)
        del tmp_data['members']
        query = self.create_insert_query('contactgroup', tmp_data)
        res = [query]

        #Now the members part
        for (c_id, c_name) in b.data['members']:
            #first clean
            q_del = "DELETE FROM contact_contactgroup WHERE contact='%s' and contactgroup='%s'" % (c_id, b.data['id'])
            res.append(q_del)
            #Then add
            q = "INSERT INTO contact_contactgroup (contact, contactgroup) VALUES ('%s', '%s')" % (c_id, b.data['id'])
            res.append(q)
        return res

    #A notification have just be created, we INSERT it
    def manage_notification_raise_brok(self, b):
        query = self.create_insert_query('notification', b.data)
        return [query]
