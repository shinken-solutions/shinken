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


#This class is an interface for reactionner and poller
#The actionner listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will take actions.
#When already launch and have a conf, actionner still listen to arbiter (one a timeout)
#if arbiter whant it to have a new conf, actionner forgot old chedulers (and actions into)
#take new ones and do the (new) job.

from Queue import Empty
from multiprocessing import Process, Queue
import time
import sys
import Pyro.core
import select

from message import Message
from worker import Worker
from util import get_sequence


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

		#self.workers = {} #dict of active workers
		##self.newzombies = [] #list of fresh new zombies, will be join the next loop
		#self.zombies = [] #list of quite old zombies, will be join now
		
		#self.seq_worker = get_sequence()


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


#        #Manage messages from Workers
#	def manage_msg(self, msg):
#		#Ok, a worker whant to die. It's sad, but we must kill him!!!
#		if msg.get_type() == 'IWantToDie':
#			zombie = msg.get_from()
#			print "Got a ding wish from ",zombie
#			self.workers[zombie].join()
#		#Ok, it's a result. We get it, and fill verifs of the good sched_id
#
#		if msg.get_type() == 'Result':
#			id = msg.get_from()
#			self.workers[id].reset_idle()
#			chk = msg.get_data()
#			sched_id = chk.sched_id
#			print "[%d]Get result from worker" % sched_id, chk
#			chk.set_status('waitforhomerun')
#			self.schedulers[sched_id]['verifs'][chk.get_id()] = chk



#        #Return the chk to scheduler and clean them
#	def manage_return(self):
#		#Fot all schedulers, we check for waitforhomerun and we send back results
#		for sched_id in self.schedulers:
#			ret = []
#			verifs = self.schedulers[sched_id]['verifs']
#                        #Get the id to return to pynag, so after make a big array with only them
#			id_to_return = [elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun']
#			for id in id_to_return:
#				v = verifs[id]
#				#We got v without the sched_id prop, so we remove it before resent it.
#				del v.sched_id
#				ret.append(v)
#			#Now ret have all verifs, we can return them
#			print "[%d] Returning %s results" % (sched_id, ret)
#			if ret is not []:
#				try:
#					con = self.schedulers[sched_id]['con']
#					if con is not None:#None = not initialized
#						con.put_results(ret)
#				except Pyro.errors.ProtocolError:
#					self.pynag_con_init(sched_id)
#					return
#				except AttributeError as exp: #the scheduler must  not be initialized
#					print exp
#				except Exception,x:
#					print ''.join(Pyro.util.getPyroTraceback(x))
#					sys.exit(0)
#        
#			#We clean ONLY if the send is OK
#			for id in id_to_return:
#				del verifs[id]


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


#	#Create and launch a new worker, and put it into self.workers
#	#It can be mortal or not
#	def create_and_launch_worker(self, mortal=True):
#		w = Worker(1, self.s, self.m, mortal=mortal)
#		self.workers[w.id] = w#Worker(id, self.s, self.m, mortal=True)
#		print "Allocate : ", w.id
#		self.workers[w.id].start()


#	#Workers are process. We need to clean them some time (see zombie part)
#	#Here we create new workers if the queue load (len of verifs) is too long
#	#here it's > 80% of workers
#	def adjust_worker_number_by_load(self):
#            nb_queue = 0 # Len of actions in queue status, so the "working" queue
#            for sched_id in self.schedulers:
#                verifs = self.schedulers[sched_id]['verifs']
#                tmp_nb_queue = len([elt for elt in verifs.keys() if verifs[elt].get_status() == 'queue'])
#                nb_queue += tmp_nb_queue
#                nb_waitforhomerun = len([elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun'])
#                print '[%d]Stats : Workers:%d Check %d (Queued:%d ReturnWait:%d)' % (sched_id, len(self.workers), len(verifs), tmp_nb_queue, nb_waitforhomerun)            
#		#We add new worker if the queue is > 80% of the worker number
#            while nb_queue > 0.8 * len(self.workers) and len(self.workers) < 20:
#                self.create_and_launch_worker()


	#Create the database connexion
	#TODO : finish error catch
	def connect_database(self):
		import MySQLdb
		self.db = MySQLdb.connect (host = "localhost", user = "root", passwd = "root",db = "merlin")
		self.db_cursor = self.db.cursor ()


	#Just run the query
	#TODO: finish catch
	def execute_query(self, query):
		print "I run query", query
		self.db_cursor.execute (query)
		self.db.commit ()


	#Ok, we are at launch and a scheduler want him only, OK...
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
		query = "INSERT INTO program_status "
		props_str = ' ('
		values_str = ' ('
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
				props_str = props_str + "%s " % prop
				values_str = values_str + "'%s' " % val
			else:
				props_str = props_str + ", %s " % prop
				values_str = values_str + ", '%s' " % val

		#Ok we've got data, let's finish the query
		props_str = props_str + ' )'
		values_str = values_str + ' )'
		query = query + props_str + 'VALUES' + values_str
		return [query]


		#query = "UPDATE program_status SET is_running = %d, \
		#	last_alive = %lu, program_start = %lu, pid = %d, daemon_mode = %d, \
		#	last_command_check = %lu, last_log_rotation = %lu, \
		#	notifications_enabled = %d, \
		#	active_service_checks_enabled = %d, passive_service_checks_enabled = %d, \
		#	active_host_checks_enabled = %d, passive_host_checks_enabled = %d, \
		#	event_handlers_enabled = %d, flap_detection_enabled = %d, \
		#	failure_prediction_enabled = %d, process_performance_data = %d, \
		#	obsess_over_hosts = %d, obsess_over_services = %d, \
		#	modified_host_attributes = %lu, modified_service_attributes = %lu, \
		#	global_host_event_handler = '%s', global_service_event_handler = '%s'\
		#	WHERE instance_id = %d" % (data["is_running"] , data["last_alive"],
		#				   data["program_start"], data["pid"],
		#				   data["daemon_mode"], data["last_command_check"],
		#				   data["last_log_rotation"], data["notifications_enabled"],
		#				   data["active_service_checks_enabled"], 
		#				   data["passive_service_checks_enabled"],
		#				   data["active_host_checks_enabled"],
		#				   data["passive_host_checks_enabled"],
		#				   data["event_handlers_enabled"],
		#				   data["flap_detection_enabled"],
		#				   data["failure_prediction_enabled"],
		#				   data["process_performance_data"],
		#				   data["obsess_over_hosts"],data["obsess_over_services"],
		#				   data["modified_host_attributes"],
		#				   data["modified_service_attributes"],
		#				   data["global_host_event_handler"],
		#				   data['global_service_event_handler'],
		#				   b.instance_id)
		#return [query]
	

	#Get a brok, parse it, and return the query for database
	def manage_initial_service_status_brok(self, b):
		data = b.data

		#It's a initial entry, so we need to clean old entries
		delete_query = "DELETE FROM service WHERE host_name = '%s' AND service_description = '%s'" % (data['host_name'], data['service_description'])

		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "INSERT INTO service "
		props_str = ' ('
		values_str = ' ('
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
				props_str = props_str + "%s " % prop
				values_str = values_str + "'%s' " % val
			else:
				props_str = props_str + ", %s " % prop
				values_str = values_str + ", '%s' " % val

		#Ok we've got data, let's finish the query
		props_str = props_str + ' )'
		values_str = values_str + ' )'
		query = query + props_str + 'VALUES' + values_str
		return [delete_query, query]


	#Get a brok, parse it, and return the query for database
	def manage_service_check_result_brok(self, b):
		data = b.data
		
		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "UPDATE service set "
		i = 0 #for the , problem...

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
				
		query = query + query_folow + " WHERE host_name = '%s' AND service_description = '%s'" % (data['host_name'] , data['service_description'])
		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_update_service_status_brok(self, b):
		data = b.data
		
		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "UPDATE service set "
		i = 0 #for the , problem...

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
				
		query = query + query_folow + " WHERE host_name = '%s' AND service_description = '%s'" % (data['host_name'] , data['service_description'])
		return [query]



	#Get a brok, parse it, and return the query for database
	def manage_initial_host_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		delete_query = "DELETE FROM host WHERE host_name = '%s'" % data['host_name']

		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "INSERT INTO host "
		props_str = ' ('
		values_str = ' ('
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
				props_str = props_str + "%s " % prop
				values_str = values_str + "'%s' " % val
			else:
				props_str = props_str + ", %s " % prop
				values_str = values_str + ", '%s' " % val
		#Ok we've got data, let's finish the query
		props_str = props_str + ' )'
		values_str = values_str + ' )'
		query = query + props_str + 'VALUES' + values_str
		return [delete_query, query]


	#Get a brok, parse it, and return the query for database
	def manage_initial_hostgroup_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		delete_query = "DELETE FROM hostgroup WHERE hostgroup_name = '%s'" % data['hostgroup_name']

		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "INSERT INTO hostgroup "
		props_str = ' ('
		values_str = ' ('
		i = 0 #for the , problem...
		for prop in data:
			if prop != 'members': #members are not in the same table, so do not add them here
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

		res = [delete_query, query]

		for (h_id, h_name) in b.data['members']:
			q_del = "DELETE FROM host_hostgroup WHERE host = '%s' and hostgroup='%s'" % (h_id, b.data['id'])
			res.append(q_del)
			q = "INSERT INTO host_hostgroup (host, hostgroup) VALUES ('%s', '%s')" % (h_id, b.data['id'])
			res.append(q)
		return res


	#Get a brok, parse it, and return the query for database
	def manage_initial_servicegroup_status_brok(self, b):
		data = b.data
		#It's a initial entry, so we need to clean old entries
		delete_query = "DELETE FROM servicegroup WHERE servicegroup_name = '%s'" % data['servicegroup_name']

		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "INSERT INTO servicegroup "
		props_str = ' ('
		values_str = ' ('
		i = 0 #for the , problem...
		for prop in data:
			if prop != 'members': #members are not in the same table, so do not add them here
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

		res = [delete_query, query]

		for (s_id, s_name) in b.data['members']:
			q_del = "DELETE FROM service_servicegroup WHERE service='%s' and servicegroup='%s'" % (s_id, b.data['id'])
			res.append(q_del)
			q = "INSERT INTO service_servicegroup (service, servicegroup) VALUES ('%s', '%s')" % (s_id, b.data['id'])
			res.append(q)
		return res


	#Get a brok, parse it, and return the query for database
	def manage_host_check_result_brok(self, b):
		data = b.data
		
		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "UPDATE host set "
		i = 0 #for the , problem...

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
				
		query = query + query_folow + " WHERE host_name = '%s'" % data['host_name']
		return [query]


	#Get a brok, parse it, and return the query for database
	def manage_update_host_status_brok(self, b):
		data = b.data
		
		#We want a query like :
		#INSERT INTO example (name, age) VALUES('Timmy Mellowman', '23' )
		query = "UPDATE host set "
		i = 0 #for the , problem...

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
				
		query = query + query_folow + " WHERE host_name = '%s'" % data['host_name']
		return [query]



	#Get a brok, parse it, and put in in database
	def manage_brok(self, b):
		if b.type == 'program_status':
			queries = self.manage_program_status_brok(b)
			#print "I run queries :", queries
			for q in queries :
				self.execute_query(q)
			return
		if b.type == 'initial_service_status':
			#print "DATA SERVICE:", b.data
			queries = self.manage_initial_service_status_brok(b)
                        #print "I run queries :", queries
			for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'initial_host_status':
			#print "DATA HOST:", b.data
                        queries = self.manage_initial_host_status_brok(b)
                        #print "I run queries :", queries
                        for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'service_check_result':
			#print "DATA SERVICE:", b.data
                        queries = self.manage_service_check_result_brok(b)
                        #print "I run queries :", queries
	                for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'host_check_result':
			#print "DATA SERVICE:", b.data
                        queries = self.manage_host_check_result_brok(b)
                        #print "I run queries :", queries
	                for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'update_service_status':
			#print "DATA SERVICE:", b.data
                        queries = self.manage_update_service_status_brok(b)
                        #print "I run queries :", queries
	                for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'update_host_status':
			#print "DATA SERVICE:", b.data
                        queries = self.manage_update_host_status_brok(b)
                        #print "I run queries :", queries
	                for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'initial_hostgroup_status':
			print "DATA HOSTGROUP:", b.data
                        queries = self.manage_initial_hostgroup_status_brok(b)
                        print "I run queries :", queries
	                for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'initial_servicegroup_status':
			print "DATA SERVICEGROUP:", b.data
                        queries = self.manage_initial_servicegroup_status_brok(b)
                        print "I run queries :", queries
	                for q in queries :
                                self.execute_query(q)
                        return
		if b.type == 'clean_all_my_instance_id':
                        print "DATA clean_all_my_instance_id:", b.data
                        queries = self.manage_clean_all_my_instance_id_brok(b)
                        print "I run queries :", queries
                        for q in queries :
                                self.execute_query(q)
                        return
		print "Unknown Brok type!!", b

		


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
			#b = new_broks[id]
			#print  "DBG: Brok", b, b.type, b.data
			#Ok, we can get the brok, and doing something with it
			self.manage_brok(b)
			#chk.set_status('queue')
			#verifs = self.schedulers[chk.sched_id]['verifs']
			#id = chk.get_id()
			#verifs[id] = chk
			#msg = Message(id=0, type='Do', data=verifs[id])
			#self.s.put(msg)


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
