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


#This class is an application for launch checks
#The poller listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will
#take checks.
#When already launch and have a conf, poller still listen to arbiter 
#(one a timeout) if arbiter whant it to have a new conf, poller forgot
#old cheduler (and checks into) take new ones and do the (new) job.

import sys, os
import getopt
import ConfigParser

from satellite import Satellite
from util import to_int, to_bool
from plugin import Plugin, Plugins

VERSION = "0.1beta"


#Our main APP class
class Poller (Satellite):
	do_checks = True #I do checks
	do_actions = False #but no actions
	#default_port = 7771
	
	properties = {
		'workdir' : {'default' : '/home/nap/shinken/src/var', 'pythonize' : None},
		'pidfile' : {'default' : '/home/nap/shinken/src/var/pollerd.pid', 'pythonize' : None},
		'port' : {'default' : '7771', 'pythonize' : to_int},
		'host' : {'default' : '0.0.0.0', 'pythonize' : None},
		'user' : {'default' : 'nap', 'pythonize' : None},
		'group' : {'default' : 'nap', 'pythonize' : None},
		'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool}
		}


################### Process launch part
def usage(name):
    print "Shinken Poller Daemon, version %s, from Gabes Jean, naparuba@gmail.com" % VERSION
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

    p = Poller(config_file, is_daemon, do_replace, debug, debug_file)
    import cProfile
    #p.main()
    command = """p.main()"""
    cProfile.runctx( command, globals(), locals(), filename="var/Poller.profile" )

