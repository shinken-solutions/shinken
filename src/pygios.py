#!/usr/bin/python

import os
import re
import time
import sys
import Pyro.core, time
import signal
import select
import random
from check import Check
from util import get_sequence
from scheduler import Scheduler
from config import Config
from macroresolver import MacroResolver
from external_command import ExternalCommand

seq_verif = get_sequence()

time_send = time.time()

#global_config
g_config = None


#Interface for Workers
#They connect here and see if they are still OK with
#our running_id, if not, they must ddrop their checks
#in progress
class IChecks(Pyro.core.ObjBase):
	def __init__(self, sched):
                Pyro.core.ObjBase.__init__(self)
		self.sched = sched
		self.running_id = random.random()


	def get_running_id(self):
		return self.running_id

		
        def get_checks(self , do_checks=False, do_actions=False):
		#print "We ask us checks"
		#print "->Asking for scheduler"
		res = self.sched.get_to_run_checks(do_checks, do_actions)
		#print "Sending %d checks" % len(res)
		return res
	
	
	def put_results(self, results):
		#print "Received %d results" % len(results)
		for c in results:
			#print c
			self.sched.put_results(c)



#Interface for Arbiter, our big MASTER
#We ask him a conf and after we listen for him.
#HE got user entry, so we must listen him carefully
#and give information he want, maybe for another scheduler
class IForArbiter(Pyro.core.ObjBase):
	def __init__(self, app):
                Pyro.core.ObjBase.__init__(self)
		self.app = app
		self.running_id = random.random()


	def get_running_id(self):
		return self.running_id


	def get_info(self, type, ref, prop, other):
		return self.app.sched.get_info(type, ref, prop, other)


	def run_external_command(self, command):
		self.app.sched.run_external_command(command)


	def put_conf(self, conf):
		self.app.conf = conf
		print "Get conf:", self.app.conf
		self.app.have_conf = True
		print "Have conf?", self.app.have_conf


	def ping(self):
		return True



class Pygios:
	def __init__(self):
		
		Pyro.core.initServer()
		port = int(sys.argv[1])
		print "Port:", port
		self.poller_daemon = Pyro.core.Daemon(port=7768)
		#self.arbiter_daemon = Pyro.core.Daemon(port=7769)
		self.sched = Scheduler(self.poller_daemon)#, self.arbiter_daemon)
		
		#self.uri2 = self.arbiter_daemon.connect(IForArbiter(self),"ForArbiter")
		self.uri2 = self.poller_daemon.connect(IForArbiter(self),"ForArbiter")
		print "The daemon runs on port:",self.poller_daemon.port
		print "The arbiter daemon runs on port:",self.poller_daemon.port
		print "The object's uri2 is:",self.uri2
		self.wait_conf()
		print "Ok we've got conf"
		self.uri = self.poller_daemon.connect(IChecks(self.sched),"Checks")
		print "The object's uri is:",self.uri


	def wait_conf(self):
		self.have_conf = False
		print "Waiting for a configuration"
		timeout = 1.0
		while not self.have_conf :
			socks = self.poller_daemon.getServerSockets()
			avant = time.time()
			#socks.append(self.fifo)
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
			else:#Timeout
				print "Waiting for a configuration"
				timeout = 1.0

			if timeout < 0:
				timeout = 1.0


#		dummy_conf = Config()
#		self.conf = dummy_conf
#		#initialise or re-initialise connexion with scheduler
#Check if pynag running id is still the same (just a connexion lost) or change
#		# so checks are bad
#		
#		arbiter = Pyro.core.getProxyForURI("PYROLOC://localhost:7767/Arbiter")
#		self.conf = arbiter.get_conf(0)
#		print "Get conf:", self.conf


	def main(self):
		print "Loading configuration"
		#self.get_conf()#Config()
		#g_config = self.conf
		#self.conf.read_config("nagios.cfg")

		#print "****************** Explode ***********************"
		#self.conf.explode()
		
		#print "****************** Inheritance *******************"
		#self.conf.apply_inheritance()
		
		#print "****************** Fill default ******************"
		#self.conf.fill_default()
		
		#print "****************** Clean templates ******************"
		#self.conf.clean_useless()
		
		#print "****************** Pythonize ******************"
		#self.conf.pythonize()
		
		#print "****************** Linkify ******************"
		#self.conf.linkify()
		
		#print "*************** applying dependancies ************"
		#self.conf.apply_dependancies()
		
		#print "************** Exlode global conf ****************"
		self.conf.explode_global_conf()

		#print "****************** Correct ?******************"
		self.conf.is_correct()
		
		self.conf.dump()
		#Creating the Macroresolver Class & unique instance
		m = MacroResolver()
		m.init(self.conf)
		
		self.sched.load_conf(self.conf)

		#Now create the external commander
		e = ExternalCommand(self.conf, 'applyer')

		#Scheduler need to know about external command to activate it if necessery
		self.sched.load_external_command(e)
		
		#External command need the sched because he can raise checks
		e.load_scheduler(self.sched)
		
		print "Configuration Loaded"
		self.sched.run()
	


if __name__ == '__main__':
	p = Pygios()
	p.main()
