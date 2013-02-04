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
import socket
import fcntl
import struct
 
SIOCGIFNETMASK = 0x891b
eth_dev_name='eth0'

##########
#  menu  #
##########

parser = optparse.OptionParser('%prog [options] -t target') 
cmd = { 'ibm_ds' : '/opt/IBM_DS/client/SMcli',
        'example' : '/path/to/cmd',
      }

# user name and password are defined in /var/lib/net-snmp/snmpd.conf
# default parameters are defined in /usr/local/shinken/etc/resource.cfg
parser.add_option('-t', '--target', dest='target', help='IP to manage. One at a time only')
parser.add_option('-v', '--vendor', dest='vendor', help='specify SAN vendor [ibm_ds|...]')
parser.add_option('-n', '--network', action='store_true', dest='network', help='Take controller IP which are on same network as you are')
parser.add_option('-d', '--debug', action='store_true', dest='debug', help='be more verbose')


opts, args = parser.parse_args()

target = opts.target
vendor = opts.vendor

if opts.debug:
    debug = True
else:
    debug = False

def debuging(txt):
    if debug:
        print txt

if opts.network:
    network = True

if not opts.target:
    parser.error('Require at least one ip (option -t)')
if not opts.vendor:
    parser.error('Require SAN vendor name. [ibm_ds|...]')

SANvendor = { 'ibm_ds' : { 'add_cmd' : [ cmd['ibm_ds'], '-A', target ],
                           'getprofile_cmd' : [ cmd['ibm_ds'], target, '-c', 'show storagesubsystem profile;' ],
                           'sanname_regex' :  re.compile('PROFILE FOR STORAGE SUBSYSTEM:\s(?P<sanname>\w+)\s+.*$', re.S|re.M),
                           'controllers_ip_regex' : re.compile('IP address:\s+((?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))', re.S|re.M),
                         },
              'example' : { 'add_cmd' : [ cmd['example'], 'arg1', 'arg2' ],
                            'getprofile_cmd' : [ cmd['example'], 'arg1', 'arg2' ],
                            'sanname_regex' :  re.compile('(?P<sanname>\w+)', re.S|re.M),
                            'controllers_ip_regex' : re.compile('IP address:\s+((?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))', re.S|re.M),
                          },
}

##############
#  functions #
############## 

### Code snippet to retrieve some system network informations
def get_network_mask(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    netmask = fcntl.ioctl(s, SIOCGIFNETMASK, struct.pack('256s', ifname))[20:24]
    return socket.inet_ntoa(netmask)
 
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def address_in_network(ip,net):
   ipaddr = struct.unpack('L',socket.inet_aton(ip))[0]
   netaddr,bits = net.split('/')
   netmask = struct.unpack('L',socket.inet_aton(netaddr))[0] & struct.unpack('L',socket.inet_aton(bits))[0]
   return ipaddr & netmask == netmask

### Search for cluster software presents on target
def set_ip():
    addip = v['add_cmd']
    adding = subprocess.Popen(' '.join(addip), stdout=subprocess.PIPE, shell=True)
    debuging(adding.communicate()[0])
    adding.wait()
    
def get_SAN_profile():
    sanprofile = v['getprofile_cmd']
    get_managed_dev = subprocess.Popen(sanprofile,stdout=subprocess.PIPE)
    stdoutdata = get_managed_dev.communicate()[0]
    debuging(stdoutdata)
    return stdoutdata

def get_name(san_profile):
    getsanname = v['sanname_regex'].search(san_profile)
    try:
        sanname = getsanname.group('sanname')
    except AttributeError:
        print('Can not retrieve San name')
    return sanname

def get_controllers_ip(san_profile, keep_on_same_network=False):
    ctrl = v['controllers_ip_regex'].findall(san_profile)
    debuging('Find ip : %s' % ctrl)
    if keep_on_same_network:
        my_ip = get_ip_address(eth_dev_name)
        my_netmask = get_network_mask(eth_dev_name)
        my_subnet_unpacked = struct.unpack('L', socket.inet_aton(my_ip))[0] & struct.unpack('L', socket.inet_aton(my_netmask))[0]
        my_subnet = socket.inet_ntoa(struct.pack('L', my_subnet_unpacked))
        n = [ my_subnet, my_netmask ]
        i = 0
        for ip in ctrl:
            if not address_in_network(ip, '/'.join(n)):
               ctrl.pop(i)
            i += 1
    return ctrl
    
### converts the listed files systems writing and display them on the standard output
def get_discovery_output(sanname, ctrlIP):
    i = 1
    for ip in ctrlIP:
        print '%s::_ctrl%d=%s'%(sanname, i, ip)
        i += 1

###############
#     main    #
###############

v = SANvendor[vendor]

# Add ip in client software managing SAN device
set_ip()

# Get SAN profile from client
profile = get_SAN_profile()

# Get SAN device name
sanname = get_name(profile)

# Get List of controllers IP
ctrl_ip = get_controllers_ip(profile, network)

get_discovery_output(sanname,ctrl_ip)
