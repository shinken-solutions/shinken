#!/usr/bin/env python
################################################
#check_shinken.py
################################################

from optparse import OptionParser
try:
    import shinken.pyro_wrapper as pyro
    from shinken.pyro_wrapper import Pyro
except ImportError:
    print 'CRITICAL : check_shinken requires the Python Pyro and the shinken.pyro_wrapper module. Please install it.'
    raise SystemExit, CRITICAL

# Exit statuses recognized by Nagios and thus by Shinken
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2
#Name of the Pyro Object we are searching
PYRO_OBJECT = 'ForArbiter'
daemon_types = ['arbiter', 'broker', 'scheduler', 'poller', 'reactionner']

#The following functions just count the number of deamons with the associated parameters
def count_total(result):
    num = 0
    for cur in result:
	num += 1
    return num

def count_alive(result):
    num = 0
    for cur in result:
	if result[cur]['alive'] == True:
	    num += 1
    return num

def count_total_spare(result):
    num = 0
    for cur in result:
	if result[cur]['spare'] == True:
	    num += 1
    return num

def count_alive_spare(result):
    num = 0
    for cur in result:
	if (result[cur]['spare'] == True and result[cur]['alive'] == True):
	    num += 1
    return num

#this function prints the names of the daemons fallen
def find_dead(result):
    dead_ones = ''
    for cur in result:
	if (result[cur]['alive'] == False):
	    dead_ones = dead_ones+' '+cur
    return dead_ones

def check_deamons_numbers(result, target):
    total_number = count_total(result)
    alive_number = count_alive(result)
    total_spare_number = count_total_spare(result)
    alive_spare_number = count_alive_spare(result)
    dead_number = total_number - alive_number
    dead_list = find_dead(result)
    #TODO : perfdata to graph deamons would be nice (in big HA architectures)
    #if alive_number <= critical, then we have a big problem
    if alive_number <= options.critical:
	print "CRITICAL - %d/%d %s(s) UP" % (alive_number, total_number, target)  
	raise SystemExit, CRITICAL
    #We are not in a case where there is no more daemons, but are there daemons down?
    elif dead_number >= options.warning:
	print "WARNING - %d/%d %s(s) DOWN :%s" % (dead_number, total_number, target, dead_list)
	raise SystemExit, WARNING
        #Everything seems fine. But that's no surprise, is it?
    else :
	print "OK - %d/%d %s(s) UP, with %d/%d spare(s) UP" % (alive_number, total_number, target, alive_spare_number, total_spare_number)
	raise SystemExit, OK

# Adding options. None are required, check_shinken will use shinken defaults
#TODO : Add more control in args problem and usage than the default OptionParser one
parser = OptionParser()
parser.add_option('-a', '--hostname', dest='hostname', default='127.0.0.1')
parser.add_option('-p', '--portnumber', dest='portnum', default=7770)
parser.add_option('-s', '--ssl', dest='ssl', default=False)
#TODO : Add a list of correct values for target and don't authorize anything else
parser.add_option('-t', '--target', dest='target')
parser.add_option('-d', '--daemonname', dest='daemon', default='')
#In HA architectures, a warning should be displayed if there's one daemon down
parser.add_option('-w','--warning', dest='warning', default = 1)
#If no deamon is left, display a critical (but shinken will be probably dead already)
parser.add_option('-c', '--critical', dest='critical', default = 0)

#Retrieving options
options, args = parser.parse_args()
#TODO : for now, helpme doesn't work as desired
options.helpme = False

# Check for required option target
if not getattr(options, 'target'):
    print 'CRITICAL - target is not specified; You must specify which daemons you want to check!'
    raise SystemExit, CRITICAL
elif options.target not in daemon_types:
    print 'CRITICAL - target %s is not a Shinken daemon!' % options.target
    raise SystemExit, CRITICAL

uri = pyro.create_uri(options.hostname, options.portnum, PYRO_OBJECT , options.ssl)
if options.daemon:
    #We just want a check for a single satellite daemon
    #Only OK or CRITICAL here
    daemon_name = options.daemon
    result = Pyro.core.getProxyForURI(uri).get_satellite_status(options.target, daemon_name)
    if result:
        if result['alive']:
            print 'OK - %s alive' % daemon_name
            raise SystemExit, OK
        else:
            print 'CRITICAL - %s down' % daemon_name
            raise SystemExit, CRITICAL
    else:
        print 'UNKNOWN - %s status could not be retrieved' % daemon_name
	raise SystemExit, UNKNOWN
else:
    #If no daemonname is specified, we want a general overview of the "target" daemons
    result = {}
    daemon_list = Pyro.core.getProxyForURI(uri).get_satellite_list(options.target)
    for daemon_name in daemon_list:
	#Getting individual daemon and putting status info in the result dictionnary
	result[daemon_name] = Pyro.core.getProxyForURI(uri).get_satellite_status(options.target, daemon_name)
    #Now we have all data
    if result:
	check_deamons_numbers(result, options.target)
    else :            
	print 'UNKNOWN - Arbiter could not retrieve status for %s' % options.target
	raise SystemExit, UNKNOWN
