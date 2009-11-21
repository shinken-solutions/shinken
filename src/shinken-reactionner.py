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


#This class is an application for launch actions 
#like notifications or event handlers
#The actionner listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will take 
#actions.
#When already launch and have a conf, actionner still listen to arbiter (one 
#a timeout) if arbiter wants it to have a new conf, actionner forgot old 
#chedulers (and actions into) take new ones and do the (new) job.

import sys, os
import getopt
import ConfigParser

from satellite import Satellite
from daemon import create_daemon, check_parallele_run, change_user

VERSION = "0.1beta"
default_config_file = "/home/nap/shinken/src/etc/reactionnerd.cfg"


#Our main APP class
class Reactionner(Satellite):
	do_checks = False #I do not do checks
	do_actions = True #just actions like notifications
	default_port = 7769


################### Process launch part
def usage(name):
    print "Shinken Reactionner Daemon, version %s, from Gabes Jean, naparuba@gmail.com" % VERSION
    print "Usage: %s [options] [-c configfile]" % name
    print "Options:"
    print " -c, --config"
    print "\tConfig file. Default : %s " % default_config_file
    print " -d, --daemon"
    print "\tRun in daemon mode"
    print " -r, --replace"
    print "\tReplace previous running scheduler"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print " --debug"
    print "\tDebug File. Default : no use (why debug a bug free program? :) )"



def parse_config(config_file):
    res = {}
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    if config._sections == {}:
        print "Bad or missing config file : %s " % config_file
        sys.exit(2)
    res['workdir'] = config.get('daemon', 'workdir')
    workdir = res['workdir']
    res['port'] = int(config.get('daemon', 'port'))
    res['host'] = config.get('daemon', 'host')
    res['maxfd'] = int(config.get('daemon', 'maxfd'))
    res['pidfile'] = config.get('daemon', 'pidfile')
    res['user'] = config.get('daemon', 'user')
    res['group'] = config.get('daemon', 'group')
    res['idontcareaboutsecurity'] = config.getboolean('daemon', 'idontcareaboutsecurity')
    return res



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
    config_file = default_config_file
    daemon=False
    replace=False
    debug=False
    debug_file=None
    insane = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.argv[0])
            sys.exit()
	elif o in ("-r", "--replace"):
            replace = True
        elif o in ("-c", "--config"):
            config_file = a
        elif o in ("-d", "--daemon"):
            daemon = True
	elif o in ("--debug"):
            debug = True
	    debug_file = a
        else:
            print "Sorry, the option",o, a, "is unknown"
	    usage(sys.argv[0])
            sys.exit()

    
    #Ok, now we load the config
    conf = parse_config(config_file)
    #Check if another Scheduler is not running (with the same conf)
    check_parallele_run(replace=replace, pidfile=conf['pidfile'])
    #If the admin don't care about security, I allow root running
    if 'idontcareaboutsecurity' in conf and conf['idontcareaboutsecurity']:
	    insane = True
    #Try to change the user (not nt for the moment)
    #TODO: change user on nt
    if os.name != 'nt':
	    change_user(conf['user'], conf['group'], insane)
    else:
	    print "Sorry, you can't change user on this system"
    #Now the daemon part if need
    if daemon:
	    create_daemon(maxfd_conf=conf['maxfd'], workdir=conf['workdir'], pidfile=conf['pidfile'], debug=debug, debug_file=debug_file)

    #TODO : signal managment
    #atexit.register(unlink, pidfile=conf['pidfile'])

    p = Reactionner(conf)
    #import cProfile
    p.main()
    #command = """p.main()"""
    #cProfile.runctx( command, globals(), locals(), filename="var/Shinken.profile" )

