#!/usr/bin/env python
# Copyright (C) 2009-2012:
#    Romain, FORLOT, romain.forlot@sydel.fr
# 
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################
#
# This script aimed to discover SAN devices in your network.
# Only IBM DS devices are supported for now.
# This use SMcli to manage Array.
#
###############################################################

### modules import
import optparse
import re
import subprocess

##########
#  menu  #
##########

parser = optparse.OptionParser('%prog [options] -t targets') 
cmd = '/opt/IBM_DS/client/SMcli'

# user name and password are defined in /var/lib/net-snmp/snmpd.conf
# default parameters are defined in /usr/local/shinken/etc/resource.cfg
parser.add_option('-t', '--targets', dest='targets', help='comma separated IP list to manage')
parser.add_option('-v', '--verbose', action='store_true', dest='verbose', help='be more verbose')


opts, args = parser.parse_args()

targets = opts.targets
if opts.verbose:
    verbose = True
else:
    verbose = False

def debug(txt):
    if verbose:
        print txt

if not opts.targets:
    parser.error('Requires at least one ip (option -t)')


##############
#  functions #
############## 

### Search for cluster software presents on targets
def iptomanage(targets):
    dict = {}
    addip = [ cmd, '-A', targets ]
    sanname = [cmd, '-d', '-S']
    adding = subprocess.Popen(' '.join(addip), stdout=subprocess.PIPE, shell=True)
#    if adding.returncode != 0:
#        print('Error when adding ip address into client software. Try manual adding to debug.')
#        sys.exit(1)
    debug(adding.communicate()[0])
    adding.wait()
    getmanageddev = subprocess.Popen(sanname,stdout=subprocess.PIPE)
    stdoutdata = getmanageddev.communicate()[0]
    debug(stdoutdata)
    for ip in targets.split(' '):
        getsanname = re.search(r'(?P<sanname>\w+)\t.*'+ip, stdoutdata, flags=re.MULTILINE)
        try:
            sanname = getsanname.group('sanname')
            try:
                dict[sanname].append(ip)
            except KeyError:
                dict[sanname] = [ip]
        except AttributeError:
            print('Can not retrieve San name for '+ip)
            continue
    return dict
    

### converts the listed files systems writing and display them on the standard output
def get_SAN_discovery_output(dict):
    for (sanname, ctrlIP) in dict.items():
        print '%s::_ctrl=%s'%(sanname, ','.join(ctrlIP))

###############
#     main    #
###############

res = iptomanage(targets)
get_SAN_discovery_output(res)
