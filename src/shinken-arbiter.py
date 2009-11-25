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


#This is the class of the Arbiter. It's role is to read configuration,
#cuts it, and send it to other elements like schedulers, reactionner 
#or pollers. It is responsible for hight avaibility part. If a scheduler
#is dead,
#it send it's conf to another if available.
#It also read order form users (nagios.cmd) and send orders to schedulers.

import os
import re
import time
import sys
import Pyro.core
#import signal
import select
import getopt
#import random
#import copy

#from check import Check
from util import scheduler_no_spare_first, to_int, to_bool
from scheduler import Scheduler
from config import Config
#from macroresolver import MacroResolver
from external_command import ExternalCommand
from dispatcher import Dispatcher
from daemon import Daemon
from plugin import Plugin, Plugins

VERSION = "0.1beta"


#Main Arbiter Class
class Arbiter(Daemon):


    properties = {
        'workdir' : {'default' : '/home/nap/shinken/src/var', 'pythonize' : None},
        'pidfile' : {'default' : '/home/nap/shinken/src/var/arbiterd.pid', 'pythonize' : None},
        #'port' : {'default' : '7768', 'pythonize' : to_int},
        #'host' : {'default' : '0.0.0.0', 'pythonize' : None},
        'user' : {'default' : 'nap', 'pythonize' : None},
        'group' : {'default' : 'nap', 'pythonize' : None},
        'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool}
        }


    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        self.config_file = config_file
        self.is_daemon = is_daemon
        self.do_replace = do_replace
        self.debug = debug
        self.debug_file = debug_file


    #Load the external commander
    def load_external_command(self, e):
        self.external_command = e
        self.fifo = e.open()
        
        
    def main(self):
        self.print_header()
        print "Loading configuration"
        self.conf = Config()
        #The config Class must have the USERN macro
        #There are 256 of them, so we create online
        Config.fill_usern_macros()
        self.conf.read_config(self.config_file)

        print "****************** Create Template links **********"
        self.conf.linkify_templates()

        print "****************** Inheritance *******************"
        self.conf.apply_inheritance()

        print "****************** Explode ***********************"
        self.conf.explode()

        print "***************** Create Name reversed list ******"
        self.conf.create_reversed_list()

        print "***************** Cleaning Twins *****************"
        self.conf.remove_twins()

        print "****************** Implicit inheritance *******************"
        self.conf.apply_implicit_inheritance()

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
        
        print "************** Exlode global conf ****************"
        self.conf.explode_global_conf()
        
        print "****************** Correct ?******************"
        self.conf.is_correct()

        #from guppy import hpy
        #hp=hpy()
        #print hp.heap()
        #print hp.heapu()

        print "Dump realms"
        for r in self.conf.realms:
            print r.get_name(), r.__dict__

        print "****************** Cut into parts ******************"
        self.confs = self.conf.cut_into_parts()

        #self.conf.debug()

        #Ok, here we must check if we go on or not.
        #TODO : check OK or not
        self.pidfile = self.conf.lock_file
        self.idontcareaboutsecurity = self.conf.idontcareaboutsecurity
        self.user = self.conf.nagios_user
        self.group = self.conf.nagios_group
        self.workdir = os.path.expanduser('~')
        
        #If we go, we must go in daemon or not
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


        print "****************** Send Configuration to schedulers******************"
        self.dispatcher = Dispatcher(self.conf)
        self.dispatcher.check_alive()
        self.dispatcher.check_dispatch()
        self.dispatcher.dispatch()
        
	#Now create the external commander
	e = ExternalCommand(self.conf, 'dispatcher')

	#Scheduler need to know about external command to activate it 
        #if necessery
	self.load_external_command(e)
	
	print "Configuration Loaded"
        
        #Main loop
	self.run()
	

    #Main function
    def run(self):
        print "Run baby, run..."
        timeout = 1.0
        while True :
            socks = []
            avant = time.time()
            if self.fifo != None:
                socks.append(self.fifo)
            # 'foreign' event loop
            ins,outs,exs = select.select(socks,[],[],timeout)
            if ins != []:
                for s in socks:
                    if s in ins:
                        #If FIFO, read external command
                        if s == self.fifo:
                            self.external_command.read_and_interpret()
                            self.fifo = self.external_command.open()

            else:#Timeout
                print "Timeout"
                #if not self.are_all_conf_assigned:
                self.dispatcher.check_alive()
                self.dispatcher.check_dispatch()
                self.dispatcher.dispatch()
                self.dispatcher.check_bad_dispatch()
                #send_conf_to_schedulers()
                timeout = 1.0
						
            if timeout < 0:
                timeout = 1.0



#if __name__ == '__main__':
#	p = Arbiter()
#        import cProfile
	#p.main()
#        command = """p.main()"""
#        cProfile.runctx( command, globals(), locals(), filename="var/Arbiter.profile" )




################### Process launch part
def usage(name):
    print "Shinken Arbiter Daemon, version %s, from Gabes Jean, naparuba@gmail.com" % VERSION
    print "Usage: %s [options] -c configfile" % name
    print "Options:"
    print " -c, --config"
    print "\tConfig file (your nagios.cfg)."
    print " -d, --daemon"
    print "\tRun in daemon mode"
    print " -r, --replace"
    print "\tReplace previous running scheduler"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print " --debug"
    print "\tDebug File. Default : no use (why debug a bug free program? :) )"



#if __name__ == '__main__':
#	p = Shinken()
#        import cProfile
#	#p.main()
#        command = """p.main()"""
#        cProfile.runctx( command, globals(), locals(), filename="var/Shinken.profile" )







#Here we go!
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

    if config_file == None:
        print "Error : config file is need"
        usage(sys.argv[0])
        sys.exit()

    p = Arbiter(config_file, is_daemon, do_replace, debug, debug_file)
    #Ok, now we load the config

    #p = Shinken(conf)
    #import cProfile
    p.main()
    #command = """p.main()"""
    #cProfile.runctx( command, globals(), locals(), filename="var/Shinken.profile" )

