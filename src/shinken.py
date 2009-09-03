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


#This class is the app for scheduling
#it create the scheduling object after listen for arbiter
#for a conf. It listen for arbiter even after the scheduler is launch.
#if a new conf is received, the scheduler is stopped
#and a new one is created.
#The scheduler create list of checks and actions for poller
#and reactionner.
import os
import re
import time
import sys
import Pyro.core
import signal
import select
import random

from check import Check
from util import get_sequence
from scheduler import Scheduler
from config import Config
from macroresolver import MacroResolver
from external_command import ExternalCommand


#Interface for Workers
#They connect here and see if they are still OK with
#our running_id, if not, they must drop their checks
#in progress
class IChecks(Pyro.core.ObjBase):
	#we keep sched link
	#and we create a running_id so poller and
	#reactionner know if we restart or not
	def __init__(self, sched):
                Pyro.core.ObjBase.__init__(self)
		self.sched = sched
		self.running_id = random.random()


	#poller or reactionner is asking us our running_id
	def get_running_id(self):
		return self.running_id

		
	#poller or reactionner ask us actions
        def get_checks(self , do_checks=False, do_actions=False):
		print "We ask us checks"
		res = self.sched.get_to_run_checks(do_checks, do_actions)
		print "Sending %d checks" % len(res)
		return res

	
	#poller or reactionner are putting us results
	def put_results(self, results):
		#print "Received %d results" % len(results)
		for c in results:
			self.sched.put_results(c)



#Interface for Brokers
#They connect here and get all broks (data for brokers)
#datas must be ORDERED! (initial status BEFORE uodate...)
class IBroks(Pyro.core.ObjBase):
	#we keep sched link
	def __init__(self, sched):
                Pyro.core.ObjBase.__init__(self)
		self.sched = sched
		#self.running_id = random.random()

		
	#poller or reactionner ask us actions
	def get_broks(self):
		print "We ask us broks"
		res = self.sched.get_broks()
		print "Sending %d broks" % len(res), res
		return res

	#Ping? Pong!
	def ping(self):
		return None


#Interface for Arbiter, our big MASTER
#We ask him a conf and after we listen for him.
#HE got user entry, so we must listen him carefully
#and give information he want, maybe for another scheduler
class IForArbiter(Pyro.core.ObjBase):
	def __init__(self, app):
                Pyro.core.ObjBase.__init__(self)
		self.app = app
		self.running_id = random.random()

	#verry usefull?
	def get_running_id(self):
		return self.running_id


	#use full too?
	def get_info(self, type, ref, prop, other):
		return self.app.sched.get_info(type, ref, prop, other)


	#arbiter is send us a external coomand.
	#it can send us global command, or specific ones
	def run_external_command(self, command):
		self.app.sched.run_external_command(command)


	#Arbiter is sending us a new conf. Ok, we take it, and if
	#app has a scheduler, we ask it to die, so the new conf 
	#will be load, and a new scheduler created
	def put_conf(self, conf):
		self.app.conf = conf
		print "Get conf:", self.app.conf
		self.app.have_conf = True
		print "Have conf?", self.app.have_conf
		
                #if app already have a scheduler, we must say him to DIE Mouahahah
		#So It will quit, and will load a new conf (and create a brand new scheduler)
		if hasattr(self.app, "sched"):
			self.app.sched.die()
			

	#Arbiter want to know if we are alive
	def ping(self):
		return True


#Tha main app class
class Shinken:
	#Create the shinken class:
	#Create a Pyro server (port = arvg 1)
	#then create the interface for arbiter
	#Then, it wait for a first configuration
	def __init__(self):
		#create the server
		Pyro.core.initServer()
		port = int(sys.argv[1])
		print "Port:", port
		self.poller_daemon = Pyro.core.Daemon(port=port)
		if self.poller_daemon.port != port:
			print "Sorry, the port %d is not free" % port
			sys.exit(1)

		#Now the interface
		i_for_arbiter = IForArbiter(self)
		self.uri2 = self.poller_daemon.connect(i_for_arbiter,"ForArbiter")
		print "The daemon runs on port:",self.poller_daemon.port
		print "The arbiter daemon runs on port:",self.poller_daemon.port
		print "The object's uri2 is:",self.uri2
		
		#Ok, now the conf
		self.must_run = True
		self.wait_initial_conf()
		print "Ok we've got conf"
		
		

	#We wait (block) for arbiter to send us conf
	def wait_initial_conf(self):
		self.have_conf = False
		print "Waiting for initial configuration"
		timeout = 1.0
		while not self.have_conf :
			socks = self.poller_daemon.getServerSockets()
			avant = time.time()
			ins,outs,exs=select.select(socks,[],[],timeout)   # 'foreign' event loop
			if ins != []:
				for s in socks:
					if s in ins:
						self.poller_daemon.handleRequests()
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


	#OK, we've got the conf, now we load it
	#and launch scheduler with it
	#we also create interface for poller and reactionner
	def load_conf(self):
		#create scheduler with ref of our daemon
		self.sched = Scheduler(self.poller_daemon)
		#give it an interface
		self.uri = self.poller_daemon.connect(IChecks(self.sched),"Checks")
		print "The object's uri is:",self.uri
		
		self.uri2 = self.poller_daemon.connect(IBroks(self.sched),"Broks")
		print "The object's uri2 is:",self.uri2

		print "Loading configuration"
		self.conf.explode_global_conf()
		self.conf.is_correct()
		self.conf.dump()
		#Creating the Macroresolver Class & unique instance
		m = MacroResolver()
		m.init(self.conf)
		#we give sched it's conf
		self.sched.load_conf(self.conf)
		
		#Now create the external commander
		#it's a applyer : it role is not to dispatch commands,
		#but to apply them
		e = ExternalCommand(self.conf, 'applyer')

		#Scheduler need to know about external command to 
		#activate it if necessery
		self.sched.load_external_command(e)
		
		#External command need the sched because he can raise checks
		e.load_scheduler(self.sched)


	#our main function, launch after the init
	def main(self):
		#ok, if we are here, we've got the conf
		self.load_conf()
		
		print "Configuration Loaded"
		while self.must_run:
			self.sched.run()
			if self.must_run: #Ok, we quit scheduler, but maybe it's just for reloadin our configuration
				self.load_conf()
				

#Here we go!
if __name__ == '__main__':
	p = Shinken()
	p.main()
