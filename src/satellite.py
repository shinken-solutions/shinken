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
#The satallite listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will 
#take actions.
#When already launch and have a conf, actionner still listen to arbiter
#(one a timeout)
#if arbiter whant it to have a new conf, satellite forgot old schedulers
#(and actions into)
#take new ones and do the (new) job.

from Queue import Empty
from multiprocessing import Queue, Manager, active_children
import os
import time
import sys
import Pyro.core
import select

from message import Message
from worker import Worker
from load import Load
#from util import get_sequence
from daemon import Daemon


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
	#TODO: catch case where Arbiter send somethign we already have
	#(same id+add+port) -> just do nothing :)
	def put_conf(self, conf):
		self.app.have_conf = True
		self.app.have_new_conf = True
		print "Sending us ", conf
		#If we've got something in the schedulers, we do not want it anymore
		#self.schedulers.clear()
		for sched_id in conf['schedulers'] :
			already_got = False
			if sched_id in self.schedulers:
				print "We already got hte conf", sched_id
				already_got = True
				verifs = self.schedulers[sched_id]['verifs']
			s = conf['schedulers'][sched_id]
			self.schedulers[sched_id] = s
			uri = "PYROLOC://%s:%d/Checks" % (s['address'], s['port'])
			self.schedulers[sched_id]['uri'] = uri
			if already_got:
				self.schedulers[sched_id]['verifs'] = verifs
			else:
				self.schedulers[sched_id]['verifs'] = {}
			self.schedulers[sched_id]['running_id'] = 0
			self.schedulers[sched_id]['active'] = s['active']
			#We cannot reinit connexions because this code in in a thread, and
			#pyro do not allow thread to create new connexions...
			#So we do it just after.
		#Now the limit part
		self.app.max_workers = conf['global']['max_workers']
		self.app.min_workers = conf['global']['min_workers']
		self.app.processes_by_worker = conf['global']['processes_by_worker']
		print "We have our schedulers :", self.schedulers


	#Arbiter ask us to do not manage a scheduler_id anymore
	#I do it and don't ask why
	def remove_from_conf(self, sched_id):
		try:
			del self.schedulers[sched_id]
		except KeyError:
			pass

	#Arbiter ask me which sched_id I manage, If it is not ok with it
	#It will ask me to remove one or more sched_id
	def what_i_managed(self):
		return self.schedulers.keys()

	#Use for arbiter to know if we are alive
	def ping(self):
		print "We ask us for a ping"
		return True


	#Use by arbiter to know if we have a conf or not
	#can be usefull if we must do nothing but 
	#we are not because it can KILL US! 
	def have_conf(self):
		return self.app.have_conf


	#Call by arbiter if it thinks we are running but we must do not (like
	#if I was a spare that take a conf but the master returns, I must die
	#and wait a new conf)
	#Us : No please...
	#Arbiter : I don't care, hasta la vista baby!
	#Us : ... <- Nothing! We are die! you don't follow 
	#anything or what??
	def wait_new_conf(self):
		print "Arbiter want me to wait a new conf"
		self.schedulers.clear()
		self.app.have_conf = False
		self.app.init_stats()


#Our main APP class
class Satellite(Daemon):
	def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
		self.print_header()

		#From daemon to manage signal. Call self.manage_signal if
		#exists, a dummy function otherwise
		self.set_exit_handler()

		#The config reading part
		self.config_file = config_file
		#Read teh config file if exist
		#if not, default properties are used
		self.parse_config_file()

                #Check if another Scheduler is not running (with the same conf)
		self.check_parallele_run(do_replace)
                
                #If the admin don't care about security, I allow root running
		insane = not self.idontcareaboutsecurity

                #Try to change the user (not nt for the moment)
                #TODO: change user on nt
		if os.name != 'nt':
			self.change_user(insane)
		else:
			print "Sorry, you can't change user on this system"


                #Now the daemon part if need
		if is_daemon:
			self.create_daemon(do_debug=debug, debug_file=debug_file)

		#Now the specific stuff
		#Bool to know if we have received conf from arbiter
		self.have_conf = False
		self.have_new_conf = False
		self.s = Queue() #Global Master -> Slave
		#self.m = Queue() #Slave -> Master
		self.manager = Manager()
		self.return_messages = self.manager.list()

		#Ours schedulers
		self.schedulers = {}

		self.workers = {} #dict of active workers
		self.newzombies = [] #list of fresh new zombies, will be join the next loop
		self.zombies = [] #list of quite old zombies, will be join now

		#The actions processing part
		self.nb_actions_max = 1024
		self.nb_actions_in_progress = 0
		self.high_water_mark = 0.9
		
		#Init stats like Load for workers
		self.init_stats()


	def init_stats(self):
		#For calculate the good worker number
                self.nb_actions_procced = 0
                self.total_process_time = 0
                self.wish_workers_load = Load()
                self.avg_dead_workers = Load()

                #For calculate the good timeout to get actions (1s or more)
                self.avg_received_actions = Load()
                self.avg_sent_actions = Load()
                self.wait_ratio = Load(initial_value=1)
		self.load = Load(initial_value=1)
		self.over_load = Load()
		

	#initialise or re-initialise connexion with scheduler
	def pynag_con_init(self, id):
		#If sched is not active, I do not try to init
		#it is just useless
		is_active = self.schedulers[id]['active']
		if not is_active:
			return

		print "init de connexion avec", self.schedulers[id]['uri']
		running_id = self.schedulers[id]['running_id']
		self.schedulers[id]['con'] = Pyro.core.getProxyForURI(self.schedulers[id]['uri'])
		#timeout of 5 s
		try:
			self.schedulers[id]['con']._setTimeout(120)
			new_run_id = self.schedulers[id]['con'].get_running_id()
		except Pyro.errors.ProtocolError, exp:
			print exp
			return
		except Pyro.errors.NamingError, exp:
			print "Scheduler is not initilised", exp
			self.schedulers[id]['con'] = None
			return
		except PicklingError, exp:
			print "Scheduler is not initilised", exp
			self.schedulers[id]['con'] = None
			return
		except KeyError, exp:
                        print "Scheduler is not initilised", exp
                        self.schedulers[id]['con'] = None
                        return

		#The schedulers have been restart : it has a new run_id.
		#So we clear all verifs, they are obsolete now.
		if self.schedulers[id]['running_id'] != 0 and new_run_id != running_id:
			print "The running id of the scheduler changed, we must clear the verifs"
			self.schedulers[id]['verifs'].clear()
		self.schedulers[id]['running_id'] = new_run_id

		print "Connexion OK"


        #Manage messages from Workers
	def manage_msg(self, msg):
		#Ok, a worker whant to die. It's sad, but we must kill him!!!
		if msg.get_type() == 'IWantToDie':
			zombie = msg.get_from()
			print "Got a ding wish from ", zombie
			self.workers[zombie].terminate()
			self.workers[zombie].join()
		#Ok, it's a result. We get it, and fill verifs of the good sched_id

		if msg.get_type() == 'Result':
			id = msg.get_from()
			try:
				self.workers[id].reset_idle()
			except KeyError as exp:
				#message from a zombie, do not care about it
				print exp
				return
			chk = msg.get_data()
			sched_id = chk.sched_id
			chk.set_status('waitforhomerun')
			self.schedulers[sched_id]['verifs'][chk.get_id()] = chk

			#Now update the stat values so we can calculate the good
			#worker number
			self.nb_actions_procced += 1
			self.total_process_time += chk.execution_time


        #Return the chk to scheduler and clean them
	def manage_return(self):
		total_sent = 0
		#Fot all schedulers, we check for waitforhomerun and we send back results
		for sched_id in self.schedulers:
			#If sched is not active, I do not try return
			is_active = self.schedulers[sched_id]['active']
			if not is_active:
				continue
			ret = []
			verifs = self.schedulers[sched_id]['verifs']
                        #Get the id to return to shinken, so after make 
			#a big array with only them
			id_to_return = [elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun']
			for id in id_to_return:
				try:
					v = verifs[id]
				        #We got v without the sched_id prop, so we
				        #remove it before resent it. Maybe it's the second time
					if hasattr(v, 'sched_id'):
						del v.sched_id
					ret.append(v)
				
				except AttributeError as exp:
					print exp
			
			#Now ret have all verifs, we can return them
			send_ok = False
			if ret is not []:
				try:
					con = self.schedulers[sched_id]['con']
					if con is not None:#None = not initialized
						send_ok = con.put_results(ret)
				except Pyro.errors.ProtocolError as exp:
					print exp
					self.pynag_con_init(sched_id)
					return
				except AttributeError as exp: #the scheduler must  not be initialized
					print exp
				except KeyError as exp: # sched is gone
                                        print exp
                                        self.pynag_con_init(sched_id)
                                        return
				except Exception,x:
					print ''.join(Pyro.util.getPyroTraceback(x))
					sys.exit(0)
        
			#We clean ONLY if the send is OK
			if send_ok :
				for id in id_to_return:
					del verifs[id]
				total_sent += len(id_to_return)
			else:
				self.pynag_con_init(sched_id)
				print "Sent failed!"

		#Just update the average sent actions
		self.avg_sent_actions.update_load(total_sent)
		print "AVG SENT:", self.avg_sent_actions.get_load()


	#Use to wait conf from arbiter.
	#It send us conf in our daemon. It put the have_conf prop
	#if he send us something
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
				sys.stdout.write(".")
				sys.stdout.flush()
				timeout = 1.0

			if timeout < 0:
				timeout = 1.0		

				
	#The arbiter can resent us new conf in the daemon port.
	#We do not want to loose time about it, so it's not a bloking 
	#wait, timeout = 0s
	#If it send us a new conf, we reinit the connexions of all schedulers
	def watch_for_new_conf(self, timeout_daemon):
		#timeout_daemon = 0.0
		t0 = time.time()
		#print "Select :", timeout_daemon
		socks = self.daemon.getServerSockets()
		# 'foreign' event loop
		ins,outs,exs = select.select(socks,[],[],timeout_daemon)
		#print "End Select:", time.time() -t0
		if ins != []:
			for sock in socks:
				if sock in ins:
					self.daemon.handleRequests()
					#have_new_conf is set with put_conf
					#so another handle will not make a con_init 
					if self.have_new_conf:
						for sched_id in self.schedulers:
							print "Init watch_for_new_conf"
							self.pynag_con_init(sched_id)
						self.have_new_conf = False


	#Create and launch a new worker, and put it into self.workers
	#It can be mortal or not
	def create_and_launch_worker(self, mortal=True):
		#queue = self.manager.list()
		#self.return_messages.append(queue)
		w = Worker(1, self.s, self.return_messages, self.processes_by_worker, mortal=mortal)
		self.workers[w.id] = w
		print "Allocating new Worker : ", w.id
		self.workers[w.id].start()


	#Manage signal function
	#TODO : manage more than just quit
	#Frame is just garbage
	def manage_signal(self, sig, frame):
		print "\nExiting with signal", sig
		for w in self.workers.values():
			try:
				w.terminate()
				w.join(timeout=1)
				#queue = w.return_queue
				#self.return_messages.remove(queue)
			except AttributeError: #A already die worker
				pass
			except AssertionError: #In a worker
				pass
		self.daemon.disconnect(self.interface)
		self.daemon.shutdown(True)
		sys.exit(0)


	#workers are processes, they can die in a numerous of ways
	#like :
	#*99.99% : bug in code
	#*0.005 % : a mix between a stupid admin (or an admin without coffee),
	#and a kill command
	#*0.005% : alien attack of course
	#So they need to be detected, and restart if need
	def check_and_del_zombie_workers(self):
            #Active children make a join with every one, useful :)
            act = active_children()

	    w_to_del = []
	    for w in self.workers.values():
		    #If a worker go down and we do not ask him, it's not
		    #good : we can think having a worker and it's not True
		    #So we del it
		    if not w.is_alive():
			    print "Warning : the worker %s goes down unexpectly!" % w.id
			    #AIM
			    w.terminate()
			    #PRESS FIRE
			    w.join(timeout=1)
			    w_to_del.append(w.id)
	    #OK, now really del workers
	    for id in w_to_del:
		    #<B>HEAD SHOT!</B>
		    del self.workers[id]
		

	#Here we create new workers if the queue load (len of verifs) is too long
	def adjust_worker_number_by_load(self):
            #TODO : get a real value for a load
            wish_worker = 1
	    #I want at least min_workers or wish_workers (the biggest) but not more than max_workers
	    while len(self.workers) < self.min_workers or (wish_worker > len(self.workers) and len(self.workers) < self.max_workers):
		    self.create_and_launch_worker()
	    #TODO : if len(workers) > 2*wish, maybe we can kill a worker?


	#We get new actions from schedulers, we create a Message ant we 
	#put it in the s queue (from master to slave)
	def get_new_actions(self):
		new_checks = []
		#We check for new check in each schedulers and put the result in new_checks
		for sched_id in self.schedulers:
			#If sched is not active, I do not try return
			is_active = self.schedulers[sched_id]['active']
			if not is_active:
				continue

			try:
				con = self.schedulers[sched_id]['con']
				if con is not None: #None = not initilized
                                        #Here are the differences between a 
					#poller and a reactionner:
                                        #Poller will only do checks,
					#reactionner do actions
                                        do_checks = self.__class__.do_checks
                                        do_actions = self.__class__.do_actions
					tmp_verifs = con.get_checks(do_checks=do_checks, do_actions=do_actions)
					print "Ask actions to", sched_id, "got", len(tmp_verifs)
					#print "We've got new verifs" , tmp_verifs
					for v in tmp_verifs:
						v.sched_id = sched_id
					new_checks.extend(tmp_verifs)
				else: #no con? make the connexion
					print "Init get_new 1"
					self.pynag_con_init(sched_id)
                        #Ok, con is not know, so we create it
			except KeyError as exp:
				print "Init get new 2"
				self.pynag_con_init(sched_id)
			except Pyro.errors.ProtocolError as exp:
				print exp
				print "Init get new 3"
				#we reinitialise the ccnnexion to pynag
				self.pynag_con_init(sched_id)
                        #scheduler must not be initialized
			except AttributeError as exp:
				print exp
                        #scheduler must not have checks
			except Pyro.errors.NamingError as exp:
				print exp
			# What the F**k? We do not know what happenned,
			#so.. bye bye :)
			except Exception,x:
				print ''.join(Pyro.util.getPyroTraceback(x))
				sys.exit(0)
		#Ok, we've got new actions in new_checks
		#so we put them in queue state and we put in in the
		#working queue for workers
		for chk in new_checks:
			chk.set_status('queue')
			verifs = self.schedulers[chk.sched_id]['verifs']
			id = chk.get_id()
			verifs[id] = chk
			msg = Message(id=0, type='Do', data=verifs[id])
			self.s.put(msg)
		#We just update avg new actions
		self.avg_received_actions.update_load(len(new_checks))
		print "AVG received:", self.avg_received_actions.get_load()


	#Main function, will loop forever
	def main(self):
		Pyro.config.PYRO_COMPRESSION = 1
		Pyro.config.PYRO_MULTITHREADED = 0
		Pyro.config.PYRO_STORAGE = self.workdir
                #Daemon init
		Pyro.core.initServer()

		print "Port:", self.port
		self.daemon = Pyro.core.Daemon(host=self.host, port=self.port)

		#If the port is not free, pyro take an other. I don't like that!
		if self.daemon.port != self.port:
			print "Sorry, the port %d was not free" % self.port
			sys.exit(1)
		self.interface = IForArbiter(self)
		self.uri2 = self.daemon.connect(self.interface,"ForArbiter")

                #We wait for initial conf
		self.wait_for_initial_conf()


                #Connexion init with PyNag server
		for sched_id in self.schedulers:
			print "Init main"
			self.pynag_con_init(sched_id)
		self.have_new_conf = False

                #Allocate Mortal Threads
		for i in xrange(1, self.min_workers):
			self.create_and_launch_worker() #create mortal worker

		#Now main loop
		i = 0
		timeout = 1.0
		while True:
			
			#print "Loop"
			#i = i + 1
			#if not i % 50:
			#	print "Loop ", i
			begin_loop = time.time()

			#Maybe the arbiter ask us to wait for a new conf
			#If true, we must restart all...
			if self.have_conf == False:
				print "Begin wait initial"
				self.wait_for_initial_conf()
				print "End wiat initial"
				for sched_id in self.schedulers:
					print "Init main2"
					self.pynag_con_init(sched_id)

			#Now we check if arbiter speek to us in the daemon.
                        #If so, we listen for it
			#When it push us conf, we reinit connexions
			#Sleep in waiting a new conf :)
			self.watch_for_new_conf(timeout)

			try:
				#print "Timeout", timeout
				#msg = self.m.get(timeout=timeout)
				#time.sleep(timeout)
				after = time.time()
				timeout -= after-begin_loop

                                #Manager the msg like check return
				#self.manage_msg(msg)
				
                                #We add the time pass on the workers'idle time
				#for id in self.workers:
				#	self.workers[id].add_idletime(after-begin_loop)

				if timeout < 0: #for go in timeout
					print "Time out", timeout
					raise Empty
					
			except Empty as exp: #Time out Part
				print " ======================== "
				after = time.time()
				timeout = 1.0
				
				#Check if zombies workers are among us :)
				#If so : KILL THEM ALL!!!
				self.check_and_del_zombie_workers()


				#Before return or get new actions, see how we manage
				#old ones : are they still in queue (s)? If True, we 
				#must wait more or at least have more workers
				print "Len Queue", self.s.qsize()
				print "Len return", len(self.return_messages)
				
				wait_ratio = self.wait_ratio.get_load()
				if self.s.qsize() != 0 and wait_ratio < 5:
					print "I decide to up wait ratio"
					self.wait_ratio.update_load(wait_ratio * 2)
				else:
					#Go to 1 on normal run, if wait_ratio was >5, 
					#it make it come near 5 because if < 5, go up :)
					self.wait_ratio.update_load(1)
				wait_ratio = self.wait_ratio.get_load()
				print "Wait ratio:", wait_ratio

				#We can wait more than 1s if need,
				#no more than 5s, but no less than 1
				timeout = timeout * wait_ratio
				#No less than 1
				timeout = max(1, timeout)
				#No more than 5
				timeout = min(5, timeout)

				#Maybe we do not have enouth workers, we check for it
				#and launch new ones if need
				self.adjust_worker_number_by_load()

				#Manage all messages we've got in the last timeout
				#for queue in self.return_messages:
				while(len(self.return_messages) != 0):
					self.manage_msg(self.return_messages.pop())
					
				for sched_id in self.schedulers:
					verifs = self.schedulers[sched_id]['verifs']
					tmp_nb_queue = len([elt for elt in verifs.keys() if verifs[elt].status == 'queue'])
					nb_waitforhomerun = len([elt for elt in verifs.keys() if verifs[elt].status == 'waitforhomerun'])
					print '[%d][%s]Stats : Workers:%d Check %d (Queued:%d In progress:%d ReturnWait:%d)' % (sched_id, self.schedulers[sched_id]['name'],len(self.workers), len(verifs), tmp_nb_queue, self.nb_actions_in_progress, nb_waitforhomerun)            

				#Now we can get new actions from schedulers
				self.get_new_actions()
				
                                #We send all finished checks
				self.manage_return()
				
				
