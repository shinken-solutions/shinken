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

import sys, os
import getopt


from satellite import Satellite
from daemon import Daemon
from util import to_int, to_bool
from plugin import Plugin, Plugins

VERSION = "0.1beta"


#from message import Message
#from worker import Worker
#from util import get_sequence
from pluginsmanager import PluginsManager


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
		#If we've got something in the schedulers, we do not
		#want it anymore
		#self.schedulers.clear()
		for sched_id in conf['schedulers'] :
			s = conf['schedulers'][sched_id]
			self.schedulers[sched_id] = s
			uri = "PYROLOC://%s:%d/Broks" % (s['address'], s['port'])
			self.schedulers[sched_id]['uri'] = uri
			self.schedulers[sched_id]['broks'] = {}
			self.schedulers[sched_id]['instance_id'] = s['instance_id']
			self.schedulers[sched_id]['running_id'] = 0
			self.schedulers[sched_id]['active'] = s['active']
			#We cannot reinit connexions because this code in
			#in a thread, and
			#pyro do not allow thread to create new connexions...
			#So we do it just after.
		print "We have our schedulers :", self.schedulers
		if not self.app.have_plugins:
			self.app.plugins = conf['global']['plugins']
			self.app.have_plugins = True
			print "We received plugins", self.app.plugins
		

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



#Our main APP class
class Broker(Satellite):
	#default_port = 7772
	properties = {
		'workdir' : {'default' : '/home/nap/shinken/src/var', 'pythonize' : None},
		'pidfile' : {'default' : '/home/nap/shinken/src/var/brokerd.pid', 'pythonize' : None},
		'port' : {'default' : '7772', 'pythonize' : to_int},
		'host' : {'default' : '0.0.0.0', 'pythonize' : None},
		'user' : {'default' : 'nap', 'pythonize' : None},
		'group' : {'default' : 'nap', 'pythonize' : None},
		'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool},
		'pluginspath' : {'default' :'/home/nap/shinken/src/plugins' , 'pythonize' : None}
		}
	

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

		#Bool to know if we have received conf from arbiter
		self.have_conf = False
		self.have_new_conf = False
		#Ours schedulers
		self.schedulers = {}
		self.mods = [] # for brokers from plugins
		
		#Plugins are load one time
		self.have_plugins = False
		self.plugins = []

	#Manage signal function
	#TODO : manage more than just quit
	#Frame is just garbage
	def manage_signal(self, sig, frame):
		print "\nExiting with signal", sig
		self.daemon.shutdown(True)
		sys.exit(0)


	#initialise or re-initialise connexion with scheduler
	def pynag_con_init(self, id):
                #If sched is not active, I do not try to init
		#it is just useless
		is_active = self.schedulers[id]['active']
		if not is_active:
			return

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
		except KeyError , exp:
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
		to_del = []
		#Call all plugins if they catch the call
		for mod in self.mods:
			try:
				mod.manage_brok(b)
			except Exception as exp:
				print "Warning : The mod %s raise an exception: %s, I kill it" % (mod.get_name(),exp)
				to_del.append(mod)
		#Now remove mod that raise an exception
		for mod in to_del:
			self.mods.remove(mod)


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

		Pyro.config.PYRO_STORAGE = self.workdir
                #Daemon init
		Pyro.core.initServer()

		print "Port:", self.port
		self.daemon = Pyro.core.Daemon(host=self.host, port=self.port)
		#If the port is not free, pyro take an other. I don't like that!
		if self.daemon.port != self.port:
			print "Sorry, the port %d was not free" % self.port
			sys.exit(1)
		self.uri2 = self.daemon.connect(IForArbiter(self),"ForArbiter")

                #We wait for initial conf
		self.wait_for_initial_conf()

		#Do the plugins part, we have our plugins in self.plugins
		self.plugins_manager = PluginsManager('broker', self.pluginspath, self.plugins)
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
			self.watch_for_new_conf(1)

			#timeout = 1.0
			#Now we can get new actions from schedulers
			self.get_new_broks()
			#TODO : sleep better...
			#time.sleep(1)



################### Process launch part
def usage(name):
    print "Shinken Broker Daemon, version %s, from Gabes Jean, naparuba@gmail.com" % VERSION
    print "Usage: %s [options] [-c configfile]" % name
    print "Options:"
    print " -c, --config"
    print "\tConfig file."
    print " -d, --daemon"
    print "\tRun in daemon mode"
    print " -r, --replace"
    print "\tReplace previous running scheduler"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print " --debug"
    print "\tDebug File. Default : no use (why debug a bug free program? :) )"


#lets go to the party
if __name__ == "__main__":
    #Manage the options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrdc::w", ["help", "replace", "daemon", "config=", "debug=", "easter"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(sys.argv[0])
        sys.exit(2)
    #Default params
    config_file = None
    is_daemon=False
    do_replace=False
    debug=False
    debug_file=None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.argv[0])
            sys.exit()
	elif o in ("-r", "--replace"):
            do_replace = True
        elif o in ("-c", "--config"):
            config_file = a
        elif o in ("-d", "--daemon"):
            is_daemon = True
	elif o in ("--debug"):
            debug = True
	    debug_file = a
        else:
            print "Sorry, the option",o, a, "is unknown"
	    usage(sys.argv[0])
            sys.exit()

    p = Broker(config_file, is_daemon, do_replace, debug, debug_file)
    #import cProfile
    p.main()
    #command = """p.main()"""
    #cProfile.runctx( command, globals(), locals(), filename="var/Shinken.profile" )


