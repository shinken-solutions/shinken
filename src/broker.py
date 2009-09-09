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


#This class is an interface for Broker
#The broker listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where broker will take broks.
#When already launch and have a conf, broker still listen to arbiter (one a timeout)
#if arbiter whant it to have a new conf, broker forgot old chedulers (and broks into)
#take new ones and do the (new) job.

from Queue import Empty
from multiprocessing import Process, Queue
import time
import sys
import Pyro.core
import select
import copy

from message import Message
from worker import Worker
from util import get_sequence
from plugins import Plugins


#Interface for Arbiter, our big MASTER
#It put us our conf
class IForArbiter(Pyro.core.ObjBase):
	#We keep app link because we are just here for it
	def __init__(self, app):
		Pyro.core.ObjBase.__init__(self)
		self.app = app
		self.schedulers = app.schedulers


	#function called by arbiter for giving us our conf
	#conf must be a dict with:
	#'schedulers' : schedulers dict (by id) with address and port
	def put_conf(self, conf):
		self.app.have_conf = True
		print "Sending us ", conf
		#If we've got something in the schedulers, we do not want it anymore
		self.schedulers.clear()
		for sched_id in conf['schedulers'] :
			s = conf['schedulers'][sched_id]
			self.schedulers[sched_id] = s
			self.schedulers[sched_id]['uri'] = "PYROLOC://%s:%d/Broks" % (s['address'], s['port'])
			self.schedulers[sched_id]['broks'] = {}
			self.schedulers[sched_id]['instance_id'] = s['instance_id']
			self.schedulers[sched_id]['running_id'] = 0
			#We cannot reinit connexions because this code in in a thread, and
			#pyro do not allow thread to create new connexions...
			#So we do it just after.
		print "We have our schedulers :", self.schedulers
		

	#Use for arbiter to know if we are alive
	def ping(self):
		print "We ask us for a ping"
		return True



#Our main APP class
class Broker:
	def __init__(self):
		#Bool to know if we have received conf from arbiter
		self.have_conf = False
		#self.s = Queue() #Global Master -> Slave
		#self.m = Queue() #Slave -> Master

		#Ours schedulers
		self.schedulers = {}
		self.mods = [] # for brokers from plugins
		#self.workers = {} #dict of active workers
		##self.newzombies = [] #list of fresh new zombies, will be join the next loop
		#self.zombies = [] #list of quite old zombies, will be join now		
		#self.seq_worker = get_sequence()


	#The classic has : do we have a prop or not?
	def has(self, prop):
		return hasattr(self, prop)


	#initialise or re-initialise connexion with scheduler
	def pynag_con_init(self, id):
		print "init de connexion avec", self.schedulers[id]['uri']
		self.schedulers[id]['con'] = Pyro.core.getProxyForURI(self.schedulers[id]['uri'])
		try:
			self.schedulers[id]['con'].ping()
			new_run_id = self.schedulers[id]['con'].get_running_id()
		except Pyro.errors.ProtocolError, exp:
			print exp
			return
		except Pyro.errors.NamingError, exp:
			print "Scheduler is not initilised", exp
			self.schedulers[id]['con'] = None
			return
		#The schedulers have been restart : it has a new run_id.
		#So we clear all verifs, they are obsolete now.
		if self.schedulers[id]['running_id'] != 0 and new_run_id != running_id:
			self.schedulers[id]['broks'].clear()
		self.schedulers[id]['running_id'] = new_run_id
		print "Connexion OK"



	#Use to wait conf from arbiter.
	#It send us conf in our daemon. It put the have_conf prop if he send us something
	#(it can just do a ping)
	def wait_for_initial_conf(self):
		print "Waiting for initial configuration"
		timeout = 1.0
		#Arbiter do not already set our have_conf param
		while not self.have_conf :
			socks = self.daemon.getServerSockets()
			avant = time.time()
			ins,outs,exs = select.select(socks,[],[],timeout)   # 'foreign' event loop
			if ins != []:
				for sock in socks:
					if sock in ins:
						self.daemon.handleRequests()
						print "Apres handle : Have conf?", self.have_conf
						apres = time.time()
						diff = apres-avant
						timeout = timeout - diff
						break    # no need to continue with the for loop
			else: #Timeout
				print "Waiting for a configuration"
				timeout = 1.0

			if timeout < 0:
				timeout = 1.0		

				
	#The arbiter can resent us new conf in the daemon port.
	#We do not want to loose time about it, so it's not a bloking wait, timeout = 0s
	#If it send us a new conf, we reinit the connexions of all schedulers
	def watch_for_new_conf(self):
		timeout_daemon = 0.0
		socks = self.daemon.getServerSockets()
		ins,outs,exs = select.select(socks,[],[],timeout_daemon)   # 'foreign' event loop
		if ins != []:
			for sock in socks:
				if sock in ins:
					self.daemon.handleRequests()
					for sched_id in self.schedulers:
						print self.schedulers[sched_id]
						self.pynag_con_init(sched_id)


	#Create the database connexion
	#TODO : finish error catch
	def connect_database(self):
		import MySQLdb
		self.db = MySQLdb.connect (host = "localhost", user = "root", passwd = "root",db = "merlin")
		self.db_cursor = self.db.cursor ()


	#Just run the query
	#TODO: finish catch
	def execute_query(self, query):
		#print "I run query", query, "\n"
		self.db_cursor.execute (query)
		self.db.commit ()


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
				values_str = values_str + "'%s' " % val
			else:
				props_str = props_str + ", %s " % prop
				values_str = values_str + ", '%s' " % val

		#Ok we've got data, let's finish the query
		props_str = props_str + ' )'
		values_str = values_str + ' )'
		query = query + props_str + 'VALUES' + values_str
		return query

	
	#Create a update query of table with data, and use where data for the WHERE clause
	def create_update_query(self, table, data, where_data):
		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
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
				query_folow += "%s='%s' " % (prop, val)
			else:
				query_folow += ", %s='%s' " % (prop, val)

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

		query = query + query_folow + where_clause#" WHERE host_name = '%s' AND service_description = '%s'" % (data['host_name'] , data['service_description'])				
		return query


	#Ok, we are at launch and a scheduler want him only, OK...
	#So ca create several queries with all tables we need to delete with our instance_id
	#This brob must be send at the begining of a scheduler session, if not, BAD THINGS MAY HAPPENED :)
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


	#Get a brok, parse it, and return the queries for database
	def manage_program_status_brok(self, b):
		data = b.data

		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = self.create_insert_query('program_status', data)

		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_initial_service_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		#delete_query = "DELETE FROM service WHERE host_name = '%s' AND service_description = '%s'" % (data['host_name'], data['service_description'])

		query = self.create_insert_query('service', data)		

		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_service_check_result_brok(self, b):
		data = b.data
		
		where_clause = {'host_name' : data['host_name'] , 'service_description' : data['service_description']}
		query = self.create_update_query('service', data, where_clause)

		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_update_service_status_brok(self, b):
		data = b.data
		
		where_clause = {'host_name' : data['host_name'] , 'service_description' : data['service_description']}
		query = self.create_update_query('service', data, where_clause)

		return [query]



	#Get a brok, parse it, and return the query for database
	def manage_initial_host_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		#delete_query = "DELETE FROM host WHERE host_name = '%s'" % data['host_name']

		query = self.create_insert_query('host', data)

		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_initial_hostgroup_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		#delete_query = "DELETE FROM hostgroup WHERE hostgroup_name = '%s'" % data['hostgroup_name']

		#Here we've got a special case : in data, there is members
		#and we do not want it in the INSERT query, so we crate a tmp_data without it
		tmp_data = copy.copy(data)
		del tmp_data['members']
		query = self.create_insert_query('hostgroup', tmp_data)

		res = [query]
		
		#Ok, the hostgroup table is uptodate, now we add relations between hosts and hostgroups
		for (h_id, h_name) in b.data['members']:
			#First clean
			q_del = "DELETE FROM host_hostgroup WHERE host = '%s' and hostgroup='%s'" % (h_id, b.data['id'])
			res.append(q_del)
			#Then add
			q = "INSERT INTO host_hostgroup (host, hostgroup) VALUES ('%s', '%s')" % (h_id, b.data['id'])
			res.append(q)
		return res


	#Get a brok, parse it, and return the query for database
	def manage_initial_servicegroup_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		delete_query = "DELETE FROM servicegroup WHERE servicegroup_name = '%s'" % data['servicegroup_name']

		#Here we've got a special case : in data, there is members
		#and we do not want it in the INSERT query, so we crate a tmp_data without it
		tmp_data = copy.copy(data)
		del tmp_data['members']
		query = self.create_insert_query('servicegroup', tmp_data)

		res = [delete_query, query]

		for (s_id, s_name) in b.data['members']:
			#first clean
			q_del = "DELETE FROM service_servicegroup WHERE service='%s' and servicegroup='%s'" % (s_id, b.data['id'])
			res.append(q_del)
			#Then add
			q = "INSERT INTO service_servicegroup (service, servicegroup) VALUES ('%s', '%s')" % (s_id, b.data['id'])
			res.append(q)
		return res


	#Get a brok, parse it, and return the query for database
	def manage_host_check_result_brok(self, b):
		data = b.data
		
		where_clause = {'host_name' : data['host_name']}
		query = self.create_update_query('host', data, where_clause)

		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_update_host_status_brok(self, b):
		data = b.data

		where_clause = {'host_name' : data['host_name']}
		query = self.create_update_query('host', data, where_clause)

		return [query]



	#Get a brok, parse it, and put in in database
	#We call functions like manage_ TYPEOFBROK _brok that return us queries
	def manage_brok(self, b):
		#type = b.type
		#manager = 'manage_'+type+'_brok'
		
		#Call all plugins if they catch the call
		for mod in self.mods:
			mod.manage_brok(b)
			#if hasattr(mod, manager):
			#	f = getattr(mod, manager)
			#	f(b)
		
		#if self.has(manager):
		#	f = getattr(self, manager)
		#	queries = f(b)
		#	for q in queries :
                #                self.execute_query(q)
                #        return
		#print "Unknown Brok type!!", b


	#We get new broks from schedulers
	def get_new_broks(self):
		new_broks = {}
		#We check for new check in each schedulers and put the result in new_checks
		for sched_id in self.schedulers:
			try:
				con = self.schedulers[sched_id]['con']
				if con is not None: #None = not initilized
					tmp_broks = con.get_broks()
					#print "We've got new broks" , tmp_broks.values()
					for b in tmp_broks.values():
						b.instance_id = self.schedulers[sched_id]['instance_id']
					new_broks.update(tmp_broks)
				else: #no con? make the connexion
					self.pynag_con_init(sched_id)
			except KeyError as exp: #Ok, con is not know, so we create it
				self.pynag_con_init(sched_id)
			except Pyro.errors.ProtocolError as exp:
				print exp
				#we reinitialise the ccnnexion to pynag
				self.pynag_con_init(sched_id)
			except AttributeError as exp: #scheduler must not be initialized
				print exp
			except Pyro.errors.NamingError as exp:#scheduler must not have checks
				print exp
			except Exception,x: # What the F**k? We do not know what happenned, so.. bye bye :)
				print ''.join(Pyro.util.getPyroTraceback(x))
				sys.exit(0)
		#Ok, we've got new broks in new_broks
		#print "New Broks:", new_broks
		for b in new_broks.values():
			#Ok, we can get the brok, and doing something with it
			self.manage_brok(b)


	#Main function, will loop forever
	def main(self):
                #Daemon init
		Pyro.core.initServer()
		self.port = int(sys.argv[1])
		print "Port:", self.port
		self.daemon = Pyro.core.Daemon(port=self.port)
		#If the port is not free, pyro take an other. I don't like that!
		if self.daemon.port != self.port:
			print "Sorry, the port %d was not free" % self.port
			sys.exit(1)
		self.uri2 = self.daemon.connect(IForArbiter(self),"ForArbiter")

                #We wait for initial conf
		self.wait_for_initial_conf()


		#Do the plugins part
		self.plugins_manager = Plugins()
		self.plugins_manager.load()
		#self.plugins_manager.init()
		self.mods = self.plugins_manager.get_brokers()
		for mod in self.mods:
			mod.init()

		#Init database
		self.connect_database()

                #Connexion init with PyNag server
		for sched_id in self.schedulers:
			self.pynag_con_init(sched_id)

                #Allocate Mortal Threads
		#for i in xrange(1, 5):
		#	self.create_and_launch_worker() #create mortal worker

		#Now main loop
		i = 0
		timeout = 1.0
		while True:
			i = i + 1
			if not i % 50:
				print "Loop ",i
			begin_loop = time.time()

			#Now we check if arbiter speek to us in the daemon. If so, we listen for it
			#When it push us conf, we reinit connexions
			self.watch_for_new_conf()
			
			#try:
			#	msg = self.m.get(timeout=timeout)
			#	after = time.time()
			#	timeout -= after-begin_loop
				
                                #Manager the msg like check return
			#	self.manage_msg(msg)
            
                                #We add the time pass on the workers'idle time
			#	for id in self.workers:
			#		self.workers[id].add_idletime(after-begin_loop)
					
			#except Empty as exp: #Time out Part
			#after = time.time()
			timeout = 1.0
				
                                #We join (old)zombies and we move new ones in the old list
			#	for id in self.zombies:
			#		self.workers[id].join()
			#		del self.workers[id]
				#We switch so zombie will be kill, and new ones wil go in newzombies
			#self.zombies = self.newzombies
			#self.newzombies = []

				#Maybe we do not have enouth workers, we check for it
				#and launch new ones if need
			#self.adjust_worker_number_by_load()
                
				#Now we can get new actions from schedulers
			self.get_new_broks()
			time.sleep(1)
                                #We send all finished checks
			#self.manage_return()
            
				#We add the time pass on the workers
			#for id in self.workers:
			#self.workers[id].add_idletime(after-begin_loop)
            
				#delworkers = []
                                #We look for cleaning workers
				#for id in self.workers:
				#	if self.workers[id].is_killable():
				#		msg=Message(id=0, type='Die')
				#		self.workers[id].send_message(msg)
				#		self.workers[id].set_zombie()
				#		delworkers.append(id)
				#Cleaning the workers
				#for id in delworkers:
				#	self.newzombies.append(id)




#lets go to the party
if __name__ == '__main__':
	broker = Broker()
	broker.main()
