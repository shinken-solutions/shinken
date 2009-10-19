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
#When already launch and have a conf, broker still listen to arbiter
# (one a timeout)
#if arbiter whant it to have a new conf, broker forgot old chedulers
#(and broks into)
#take new ones and do the (new) job.

from Queue import Empty
#from multiprocessing import Process, Queue
import time
import sys
import Pyro.core
#import select
#import copy

#from message import Message
#from worker import Worker
#from util import get_sequence
from plugins import Plugins
from satellite import Satellite

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
		#If we've got something in the schedulers, we do not
		#want it anymore
		self.schedulers.clear()
		for sched_id in conf['schedulers'] :
			s = conf['schedulers'][sched_id]
			self.schedulers[sched_id] = s
			uri = "PYROLOC://%s:%d/Broks" % (s['address'], s['port'])
			self.schedulers[sched_id]['uri'] = uri
			self.schedulers[sched_id]['broks'] = {}
			self.schedulers[sched_id]['instance_id'] = s['instance_id']
			self.schedulers[sched_id]['running_id'] = 0
			#We cannot reinit connexions because this code in
			#in a thread, and
			#pyro do not allow thread to create new connexions...
			#So we do it just after.
		print "We have our schedulers :", self.schedulers
		

	#Use for arbiter to know if we are alive
	def ping(self):
		print "We ask us for a ping"
		return True



#Our main APP class
class Broker(Satellite):
	default_port = 7772
	
	def __init__(self):
		#Bool to know if we have received conf from arbiter
		self.have_conf = False

		#Ours schedulers
		self.schedulers = {}
		self.mods = [] # for brokers from plugins


	#initialise or re-initialise connexion with scheduler
	def pynag_con_init(self, id):
		print "init de connexion avec", self.schedulers[id]['uri']
		running_id = self.schedulers[id]['running_id']
		uri = self.schedulers[id]['uri']
		self.schedulers[id]['con'] = Pyro.core.getProxyForURI(uri)
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


	#Get a brok. Our role is to put it in the plugins
	#THEY MUST DO NOT CHANGE data of b !!!
	def manage_brok(self, b):
		#Call all plugins if they catch the call
		for mod in self.mods:
			mod.manage_brok(b)


	#We get new broks from schedulers
	def get_new_broks(self):
		new_broks = {}
		#We check for new check in each schedulers and put
		#the result in new_checks
		for sched_id in self.schedulers:
			try:
				con = self.schedulers[sched_id]['con']
				if con is not None: #None = not initilized
					tmp_broks = con.get_broks()
					for b in tmp_broks.values():
						b.instance_id = self.schedulers[sched_id]['instance_id']
					new_broks.update(tmp_broks)
				else: #no con? make the connexion
					self.pynag_con_init(sched_id)
                        #Ok, con is not know, so we create it
			except KeyError as exp: 
				self.pynag_con_init(sched_id)
			except Pyro.errors.ProtocolError as exp:
				print exp
				#we reinitialise the ccnnexion to pynag
				self.pynag_con_init(sched_id)
                        #scheduler must not #be initialized
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
		#Ok, we've got new broks in new_broks
		#print "New Broks:", new_broks
		for b in new_broks.values():
			#Ok, we can get the brok, and doing something with it
			self.manage_brok(b)


	#Main function, will loop forever
	def main(self):
                #Daemon init
		Pyro.core.initServer()

		if len(sys.argv) == 2:
			self.port = int(sys.argv[1])
		else:
			self.port = self.__class__.default_port
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
		self.mods = self.plugins_manager.get_brokers()
		for mod in self.mods:
			mod.init()


                #Connexion init with PyNag server
		for sched_id in self.schedulers:
			self.pynag_con_init(sched_id)

		#Now main loop
		i = 0
		#timeout = 1.0
		while True:
			i = i + 1
			if not i % 50:
				print "Loop ", i
			#begin_loop = time.time()

			#Now we check if arbiter speek to us in the daemon.
			#If so, we listen for it
			#When it push us conf, we reinit connexions
			self.watch_for_new_conf()

			#timeout = 1.0
			#Now we can get new actions from schedulers
			self.get_new_broks()
			#TODO : sleep better...
			time.sleep(1)



#lets go to the party
if __name__ == '__main__':
	broker = Broker()
	#broker.main()
        import cProfile
        command = """broker.main()"""
        cProfile.runctx( command, globals(), locals(), filename="var/Broker.profile" )
