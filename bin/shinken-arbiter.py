#!/usr/bin/env python
#Copyright (C) 2009-2010 : 
#    Gabes Jean, naparuba@gmail.com 
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#This is the class of the Arbiter. It's role is to read configuration,
#cuts it, and send it to other elements like schedulers, reactionner 
#or pollers. It is responsible for hight avaibility part. If a scheduler
#is dead,
#it send it's conf to another if available.
#It also read order form users (nagios.cmd) and send orders to schedulers.


import os
#import re
import time
import platform
import sys
import select
import getopt
import random


#We know that a Python 2.3 or Python3K will fail.
#We can say why and quit.
python_version = platform.python_version_tuple()

## Make sure people are using Python 2.5 or higher
if int(python_version[0]) == 2 and int(python_version[1]) < 4:
    print "Shinken require as a minimum Python 2.4.x, sorry"
    sys.exit(1)

if int(python_version[0]) == 3:
    print "Shinken is not yet compatible with Python3k, sorry"
    sys.exit(1)


#In fact it's useful for installed daemon
sys.path.insert(0, '.')


#Try to load shinken lib.
#Maybe it's not in our python path, so we detect it
#it so (it's a untar install) we add .. in the path
try :
    from shinken.util import to_bool
    my_path = os.path.abspath(sys.modules['__main__'].__file__)
    elts = os.path.dirname(my_path).split(os.sep)[:-1]
    elts.append('shinken')
    sys.path.append(os.sep.join(elts))
except ImportError:
    #Now add in the python path the shinken lib
    #if we launch it in a direct way and
    #the shinken is not a python lib
    my_path = os.path.abspath(sys.modules['__main__'].__file__)
    elts = os.path.dirname(my_path).split(os.sep)[:-1]
    sys.path.append(os.sep.join(elts))
    elts.append('shinken')
    sys.path.append(os.sep.join(elts))



try:
    import shinken.pyro_wrapper    
except ImportError:
    print "Shinken require the Python Pyro module. Please install it."
    sys.exit(1)

Pyro = shinken.pyro_wrapper.Pyro


from shinken.util import to_bool
#from scheduler import Scheduler
from shinken.config import Config
from shinken.external_command import ExternalCommandManager
from shinken.dispatcher import Dispatcher
from shinken.daemon import Daemon
from shinken.log import Log
from shinken.modulesmanager import ModulesManager


VERSION = "0.2+"



#Interface for the other Arbiter
#It connect, and we manage who is the Master, slave etc. 
#Here is a also a fnction to have a new conf from the master
class IArbiters(Pyro.core.ObjBase):
    #we keep arbiter link
    def __init__(self, arbiter):
        Pyro.core.ObjBase.__init__(self)
        self.arbiter = arbiter
        self.running_id = random.random()


    #Broker need to void it's broks?
    def get_running_id(self):
        return self.running_id


    def have_conf(self, magic_hash):
        #I've got a conf and the good one
        if self.arbiter.have_conf and self.arbiter.conf.magic_hash == magic_hash:
            return True
        else: #No conf or a bad one
            return False


    #The master Arbiter is sending us a new conf. Ok, we take it
    def put_conf(self, conf):
        self.arbiter.conf = conf
        print "Get conf:", self.arbiter.conf
        self.arbiter.have_conf = True
        print "Just after reception"
        self.arbiter.must_run = False


    #Ping? Pong!
    def ping(self):
        return None


    #the master arbiter ask me to do not run!
    def do_not_run(self):
        #If i'm the master, just FUCK YOU!
        if self.arbiter.is_master:
            print "Some fucking idiot ask me to do not run. I'm a proud master, so I'm still running"
        #Else I'm just a spare, so I listen to my master
        else:
            print "Someone ask me to do not run"
            self.arbiter.last_master_speack = time.time()
            self.arbiter.must_run = False


#Main Arbiter Class
class Arbiter(Daemon):


    properties = {
        #'workdir' : {'default' : '/usr/local/shinken/var', 'pythonize' : None},
        #'pidfile' : {'default' : '/usr/local/shinken/var/arbiterd.pid', 'pythonize' : None},
        #'port' : {'default' : '7768', 'pythonize' : to_int},
        #'host' : {'default' : '0.0.0.0', 'pythonize' : None},
        #'user' : {'default' : 'shinken', 'pythonize' : None},
        #'group' : {'default' : 'shinken', 'pythonize' : None},
        #'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool}
        }


    def __init__(self, config_files, is_daemon, do_replace, verify_only, debug, debug_file):
        self.config_file = config_files[0]
        self.config_files = config_files
        self.is_daemon = is_daemon
        self.verify_only = verify_only
        self.do_replace = do_replace
        self.debug = debug
        self.debug_file = debug_file

        #From daemon to manage signal. Call self.manage_signal if
        #exists, a dummy function otherwise
        self.set_exit_handler()
        self.broks = {}
        self.is_master = False
        self.me = None

        self.nb_broks_send = 0

        #Now tab for external_commands
        self.external_commands = []


    #Use for adding broks
    def add(self, b):
        self.broks[b.id] = b


    #We must push our broks to the broker
    #because it's stupid to make a crossing connexion
    #so we find the broker responbile for our broks,
    #and we send him it
    #TODO : better find the broker, here it can be dead?
    #or not the good one?
    def push_broks_to_broker(self):
        for brk in self.conf.brokers:
            #Send only if alive of course
            if brk.manage_arbiters and brk.alive:
                is_send = brk.push_broks(self.broks)
                if is_send:
                    #They are gone, we keep none!
                    self.broks = {}


    #We must take external_commands from all brokers
    def get_external_commands_from_brokers(self):
        for brk in self.conf.brokers:
            #Get only if alive of course
            if brk.alive:
                new_cmds = brk.get_external_commands()
                for new_cmd in new_cmds:
                    self.external_commands.append(new_cmd)

                
    #Our links to satellites can raise broks. We must send them
    def get_broks_from_satellitelinks(self):
        tabs = [self.conf.brokers, self.conf.schedulerlinks, \
                    self.conf.pollers, self.conf.reactionners]
        for tab in tabs:
            for s in tab:
                new_broks = s.get_all_broks()
                for b in new_broks:
                    self.add(b)


    #Our links to satellites can raise broks. We must send them
    def get_initial_broks_from_satellitelinks(self):
        tabs = [self.conf.brokers, self.conf.schedulerlinks, \
                    self.conf.pollers, self.conf.reactionners]
        for tab in tabs:
            for s in tab:
                b  = s.get_initial_status_brok()
                self.add(b)


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        self.fifo = e.open()
        
        
    def main(self):
        #Log will be broks
        self.log = Log()
        self.log.load_obj(self)

        self.print_header()
        for line in self.get_header():
            self.log.log(line)#, format = 'TOTO %s\n')
	    
	#Use to know if we must still be alive or not
        self.must_run = True
        
        print "Loading configuration"
        self.conf = Config()
        #The config Class must have the USERN macro
        #There are 256 of them, so we create online
        Config.fill_usern_macros()
        
        #REF: doc/shinken-conf-dispatching.png (1)
        buf = self.conf.read_config(self.config_files)
        
        raw_objects = self.conf.read_config_buf(buf)

        #### Loading Arbiter module part ####
        
        #first we need to get arbtiers and modules first
        #so we can ask them some objects too
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')
        
        
        self.conf.early_arbiter_linking()

        #Search wich Arbiterlink I am
        for arb in self.conf.arbiterlinks:
            if arb.is_me():
                arb.need_conf = False
                self.me = arb
                print "I am the arbiter :", arb.get_name()
                print "Am I the master?", not self.me.spare
            else: #not me
                arb.need_conf = True

        #If None, there will be huge problems. The conf will be invalid
        #And we will bail out after print all errors
        if self.me != None:
            print "My own modules :"
            for m in self.me.modules:
                print m

            #BEWARE: this way of finding path is good if we still 
            #DO NOT HAVE CHANGE PWD!!!
            #Now get the module path. It's in fact the directory modules
            #inside the shinken directory. So let's find it.
            print "modulemanager file", shinken.modulesmanager.__file__
            modulespath = os.path.abspath(shinken.modulesmanager.__file__)
            print "modulemanager absolute file", modulespath
            #We got one of the files of 
            elts = os.path.dirname(modulespath).split(os.sep)[:-1]
            elts.append('shinken')
            elts.append('modules')
            self.modulespath = os.sep.join(elts)
            Log().log("Using modules path : %s" % os.sep.join(elts))


            self.modules_manager = ModulesManager('arbiter', self.modulespath, self.me.modules)
            self.modules_manager.load()
            self.mod_instances = self.modules_manager.get_instances()

            for inst in self.mod_instances:
                try :
                    r = inst.get_objects()
                    for h in r['hosts']:
                        raw_objects['host'].append(h)
                except Exception, exp:
                    print "The instance %s raise an exception %s. I remove it" % (inst.get_name(), str(exp))


        ### Resume standard operations ###
        self.conf.create_objects(raw_objects)
        
	#Maybe conf is already invalid
        if not self.conf.conf_is_correct:
            print "***> One or more problems was encountered while processing the config files..."
            sys.exit(1)


        #************** Change Nagios2 names to Nagios3 ones ******
        self.conf.old_properties_names_to_new()

	#print "****************** Create Template links **********"
        self.conf.linkify_templates()

        #print "****************** Inheritance *******************"
        self.conf.apply_inheritance()

        #print "****************** Explode ***********************"
        self.conf.explode()

        #print "***************** Create Name reversed list ******"
        self.conf.create_reversed_list()

        #print "***************** Cleaning Twins *****************"
        self.conf.remove_twins()

        #print "****************** Implicit inheritance *******************"
        self.conf.apply_implicit_inheritance()

        #print "****************** Fill default ******************"
        self.conf.fill_default()
        
        #print "****************** Clean templates ******************"
        self.conf.clean_useless()
        
        #print "****************** Pythonize ******************"
        self.conf.pythonize()
        
        #print "****************** Linkify ******************"
        self.conf.linkify()
        
        #print "*************** applying dependancies ************"
        self.conf.apply_dependancies()

        #Hacking some global parameter inherited from Nagios to create
        #on the fly some Broker modules like for status.dat parameters
        #or nagios.log one if there are no already available
        self.conf.hack_old_nagios_parameters()
        
        #print "************** Exlode global conf ****************"
        self.conf.explode_global_conf()

        #************* Print warning about useless parameters in Shinken **************"
        self.conf.notice_about_useless_parameters()
        
        #print "****************** Correct ?******************"
        self.conf.is_correct()

        #If the conf is not correct, we must get out now
        if not self.conf.conf_is_correct:
            print "Configuration is incorrect, sorry, I bail out"
            sys.exit(1)


        #self.conf.dump()

        #from guppy import hpy
        #hp=hpy()
        #print hp.heap()
        #print hp.heapu()

        if self.me == None:
            print "Error : I cannot find my own Arbiter object, I bail out"
            print "To solve it : please change the host_name parameter in the object Arbiter"
            print "in the file shinken-specific.cfg. Thanks."
            sys.exit(1)


	#If I am a spare, I must wait a (true) conf from Arbiter Master
        self.wait_conf = self.me.spare
        
        #print "Dump realms"
        #for r in self.conf.realms:
        #    print r.get_name(), r.__dict__
        print "\n"

        
        #REF: doc/shinken-conf-dispatching.png (2)
        Log().log("Cutting the hosts and services into parts")
        self.confs = self.conf.cut_into_parts()

        #The conf can be incorrect here if the cut into parts see errors like
	#a realm with hosts and not schedulers for it
        if not self.conf.conf_is_correct:
            print "Configuration is incorrect, sorry, I bail out"
            sys.exit(1)

        Log().log('Things look okay - No serious problems were detected during the pre-flight check')

	#Exit if we are just here for config checking
        if self.verify_only:
            sys.exit(0)
	
        #self.conf.debug()

        #Some properties need to be "flatten" (put in strings)
        #before being send, like realms for hosts for example
        #BEWARE: after the cutting part, because we stringify some properties
        self.conf.prepare_for_sending()

	
        #Ok, here we must check if we go on or not.
        #TODO : check OK or not
        self.pidfile = self.conf.lock_file
        self.idontcareaboutsecurity = self.conf.idontcareaboutsecurity
        self.user = self.conf.nagios_user
        self.group = self.conf.nagios_group
        self.workdir = os.path.expanduser('~'+self.user)
        
        #If we go, we must go in daemon or not
        #Check if another Scheduler is not running (with the same conf)
        self.check_parallel_run(do_replace)
                
        #If the admin don't care about security, I allow root running
        insane = not self.idontcareaboutsecurity


        #Try to change the user (not nt for the moment)
        #TODO: change user on nt
        if os.name != 'nt':
            self.change_user(insane)
        else:
            Log().log("Warning : you can't change user on this system")
        
        #Now the daemon part if need
        if is_daemon:
            self.create_daemon(do_debug=debug, debug_file=debug_file)

        Log().log("Opening of the network port")
        #Now open the daemon port for Broks and other Arbiter sends
        Pyro.config.PYRO_STORAGE = self.workdir
        Pyro.config.PYRO_COMPRESSION = 1
        Pyro.config.PYRO_MULTITHREADED = 0
        Log().log("Using working directory : %s" % os.path.abspath(self.workdir))

        self.poller_daemon = shinken.pyro_wrapper.init_daemon(self.me.address, self.me.port)

        Log().log("Listening on %s:%d" % (self.me.address, self.me.port))

        self.iarbiters = IArbiters(self)

        self.uri_arb = shinken.pyro_wrapper.register(self.poller_daemon, self.iarbiters, "ForArbiter")

        Log().log("Configuration Loaded")

        #Main loop
        while True:
	    #If I am a spare, I wait for the master arbiter to send me
	    #true conf. When 
            if self.me.spare:
                self.wait_initial_conf()
            else:#I'm the master, I've got a conf
                self.is_master = True
                self.have_conf = True

            #Ok, now It've got a True conf, Now I wait to get too much
            #time without 
            if self.me.spare:
                print "I must wait now"
                self.wait_for_master_death()

            if self.must_run:
                #Main loop
                self.run()


    #We wait (block) for arbiter to send us conf
    def wait_initial_conf(self):
        self.have_conf = False
        print "Waiting for configuration from master"
        timeout = 1.0
        while not self.have_conf :
            socks = shinken.pyro_wrapper.get_sockets(self.poller_daemon)

            avant = time.time()
            # 'foreign' event loop
            ins, outs, exs = select.select(socks, [], [], timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        shinken.pyro_wrapper.handleRequests(self.poller_daemon, s)
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


    #We wait (block) for arbiter to send us something
    def wait_for_master_death(self):
        print "Waiting for master death"
        timeout = 1.0
        is_master_dead = False
        self.last_master_speack = time.time()
        while not is_master_dead:
            socks = shinken.pyro_wrapper.get_sockets(self.poller_daemon)
            avant = time.time()
            # 'foreign' event loop
            ins, outs, exs = select.select(socks, [], [], timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        shinken.pyro_wrapper.handleRequests(self.poller_daemon, s)
                        self.last_master_speack = time.time()
                        apres = time.time()
                        diff = apres-avant
                        timeout = timeout - diff
            else: #Timeout
                sys.stdout.write(".")
                sys.stdout.flush()
                timeout = 1.0

            if timeout < 0:
                timeout = 1.0
            
            #Now check if master is dead or not
            now = time.time()
            if now - self.last_master_speack > 5:
                print "Master is dead!!!"
                self.must_run = True
                is_master_dead = True


    #Manage signal function
    #Frame is just garbage
    def manage_signal(self, sig, frame):
        print "\nExiting with signal", sig
        print "Stopping all network connexions"
        self.poller_daemon.shutdown(True)
        print "Unlinking pid file"
        try:
            os.unlink(self.pidfile)
        except OSError, exp:
            print "Error un deleting pid file:", exp
        sys.exit(0)


    #Main function
    def run(self):
        #Before running, I must be sure who am I
        #The arbiters change, so we must refound the new self.me
        for arb in self.conf.arbiterlinks:
            if arb.is_me():
                self.me = arb

        Log().log("Begin to dispatch configurations to satellites")
        self.dispatcher = Dispatcher(self.conf, self.me)
        self.dispatcher.check_alive()
        self.dispatcher.check_dispatch()
        #REF: doc/shinken-conf-dispatching.png (3)
        self.dispatcher.dispatch()

        #Now we can get all initial broks for our satellites
        self.get_initial_broks_from_satellitelinks()

	#Now create the external commander
        if os.name != 'nt':
          e = ExternalCommandManager(self.conf, 'dispatcher')
	
	#Scheduler need to know about external command to activate it 
        #if necessary
          self.load_external_command(e)
        else:
          self.fifo = None

        print "Run baby, run..."
        timeout = 1.0
        while self.must_run :
            socks = []
            daemon_sockets = shinken.pyro_wrapper.get_sockets(self.poller_daemon)
            socks.extend(daemon_sockets)
            avant = time.time()
            if self.fifo != None:
                socks.append(self.fifo)
            # 'foreign' event loop
            ins, outs, exs = select.select(socks, [], [], timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        if s in daemon_sockets:
                            shinken.pyro_wrapper.handleRequests(self.poller_daemon, s)
                            apres = time.time()
                            diff = apres-avant
                            timeout = timeout - diff
                            break    # no need to continue with the for loop
                        #If FIFO, read external command
                        if s == self.fifo:
                            ext_cmd = self.external_command.get()
                            if ext_cmd != None:
                                self.external_commands.append(ext_cmd)
                            self.fifo = self.external_command.open()

            else: #Timeout
                self.dispatcher.check_alive()
                self.dispatcher.check_dispatch()
                #REF: doc/shinken-conf-dispatching.png (3)
                self.dispatcher.dispatch()
                self.dispatcher.check_bad_dispatch()

                #Maybe our satellites links raise new broks. Must reap them
                self.get_broks_from_satellitelinks()

                #One broker is responsible for our broks,
                #we must give him our broks
                self.push_broks_to_broker()
                self.get_external_commands_from_brokers()
                #send_conf_to_schedulers()
                timeout = 1.0

                print "Nb Broks send:", self.nb_broks_send
                #Log().log("Nb Broks send: %d" % self.nb_broks_send)
                self.nb_broks_send = 0
                

                #Now send all external commands to schedulers
                for ext_cmd in self.external_commands:
                    self.external_command.resolve_command(ext_cmd)
                #It's send, do not keep them
                #TODO: check if really send. Queue by scheduler?
                self.external_commands = []
						
            if timeout < 0:
                timeout = 1.0



################### Process launch part
def usage(name):
    print "Shinken Arbiter Daemon, version %s, from :" % VERSION
    print "        Gabes Jean, naparuba@gmail.com"
    print "        Gerhard Lausser, Gerhard.Lausser@consol.de"
    print "Usage: %s [options] -c configfile [-c additionnal_config_file]" % name
    print "Options:"
    print " -c, --config"
    print "\tConfig file (your nagios.cfg). Multiple -c can be used, it will be like if all files was just one"
    print " -d, --daemon"
    print "\tRun in daemon mode"
    print " -r, --replace"
    print "\tReplace previous running scheduler"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print " --debug"
    print "\tDebug File. Default : no use (why debug a bug free program? :) )"
    
    


#Here we go!
if __name__ == "__main__":
    #Manage the options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvrdc::w", ["help", "verify-config", "replace", "daemon", "config=", "debug=", "easter"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(sys.argv[0])
        sys.exit(2)
    #Default params
    config_files = []
    verify_only = False
    is_daemon = False
    do_replace = False
    debug = False
    debug_file = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.argv[0])
            sys.exit()
        elif o in ("-v", "--verify-config"):
            verify_only = True
        elif o in ("-r", "--replace"):
            do_replace = True
        elif o in ("-c", "--config"):
            config_files.append(a)
        elif o in ("-d", "--daemon"):
            is_daemon = True
        elif o in ("--debug"):
            debug = True
            debug_file = a
        else:
            print "Sorry, the option", o, a, "is unknown"
            usage(sys.argv[0])
            sys.exit()

    if len(config_files) == 0:
        print "Error : config file is need"
        usage(sys.argv[0])
        sys.exit()

    p = Arbiter(config_files, is_daemon, do_replace, verify_only, debug, debug_file)
    #Ok, now we load the config

    #p = Shinken(conf)
    #import cProfile
    p.main()
    #command = """p.main()"""
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/Arbiter.profile" )

