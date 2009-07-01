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

seq_verif = get_sequence()

time_send = time.time()

class IChecks(Pyro.core.ObjBase):
	def __init__(self, sched):
                Pyro.core.ObjBase.__init__(self)
		self.sched = sched
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


class Pygios:
	def __init__(self):

		Pyro.core.initServer()
		self.daemon=Pyro.core.Daemon()
		self.sched = Scheduler(self.daemon)
		self.uri=self.daemon.connect(IChecks(self.sched),"Checks")
		print "The daemon runs on port:",self.daemon.port
		print "The object's uri is:",self.uri


	def main(self):
		print "Loading configuration"
		self.conf = Config()
		self.conf.read_config("nagios.cfg")
		
		print "****************** Explode ***********************"
		self.conf.explode()
		
		print "****************** Inheritance *******************"
		self.conf.apply_inheritance()
		
		print "****************** Fill default ******************"
		self.conf.fill_default()
		
		print "****************** Clean templates ******************"
		self.conf.clean_useless()
		
		print "****************** Pythonize ******************"
		self.conf.pythonize()
		
		print "****************** Linkify ******************"
		self.conf.linkify()
		
		print "*************** applying dependancies ************"
		self.conf.apply_dependancies()
		
		print "****************** Correct ?******************"
		self.conf.is_correct()

		#Creating the Macroresolver Class & unique instance
		m = MacroResolver()
		m.init(self.conf)
		
		self.sched.load_conf(self.conf)
		
		print "Configuration Loaded"
		self.sched.run()
	


if __name__ == '__main__':
	p = Pygios()
	p.main()
