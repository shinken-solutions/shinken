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
import sys
import subprocess

##########
#  menu  #
##########

parser = optparse.OptionParser('%prog [options] -t targets') 
cmd = "/opt/IBM_DS/client/SMcli"

# user name and password are defined in /var/lib/net-snmp/snmpd.conf
# default parameters are defined in /usr/local/shinken/etc/resource.cfg
parser.add_option("-t", "--targets", dest="targets", help="IP to manage")


opts, args = parser.parse_args()

targets = opts.targets

if not opts.targets:
    parser.error("Requires at least one ip (option -t)")


##############
#  functions #
############## 

### Search for cluster software presents on targets
def iptomanage(ip):
    addip = [ cmd, '-A', ip ]
    sanname = [cmd, '-d', '-S']
    adding = subprocess.Popen(addip, stdout=subprocess.PIPE)
#    if adding.returncode != 0:
#        print('Error when adding ip address into client software. Try manual adding to debug.')
#        sys.exit(1)
    adding.wait()
    getmanageddev = subprocess.Popen(sanname,stdout=subprocess.PIPE)
    stdoutdata = getmanageddev.communicate()[0]
    getsanname = re.match(r'(?P<sanname>\w+)\t.*'+ip, stdoutdata)
    try:
        name = getsanname.group('sanname')
    except AttributeError:
        print('Can not retrieve San name')
        sys.exit(2)
    return name
    

### converts the listed files systems writing and display them on the standard output
def get_SAN_discovery_output(ip):
    print "%s::_ctrl=%s"%(sanname, ip)# display like in the nmap model

###############
#     main    #
###############

targets = targets.split(' ')
for target in targets:
    sanname = iptomanage(target)
    get_SAN_discovery_output(target)

