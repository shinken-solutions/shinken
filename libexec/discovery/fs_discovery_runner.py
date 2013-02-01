#!/usr/bin/env python
# Copyright (C) 2009-2012:
#    Camille, VACQUIE
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
# First of all, the fs_discovery_runner.py script get the list 
# of the files systems back from the nmap device list with SNMP 
# protocol. The OID used by SNMP to recover datas is particular
# to each OS type.
# And then it converts the listed files systems writing and
# display it on the standard output.
# For example : / will be translate into _root and /var will be
# translate into _var
#
# For SNMPv3 we created a default user using the command :
# net-snmp-config --create-snmpv3-user -a "mypassword" myuser
# Here the user name is myuser and his password is mypassword
#
###############################################################


### modules import
import netsnmp
import optparse
import re

##########
#  menu  #
##########

parser = optparse.OptionParser('%prog [options] -H HOSTADRESS -C SNMPCOMMUNITYREAD -O ARG1 -V SNMPVERSION -l SNMPSECNAME -L SNMPSECLEVEL -p SNMPAUTHPROTO -x SNMPAUTHPASS')

# user name and password are defined in /var/lib/net-snmp/snmpd.conf
# default parameters are defined in /usr/local/shinken/etc/resource.cfg
parser.add_option("-H", "--hostname", dest="hostname", help="Hostname to scan")
parser.add_option("-m", "--mode", dest="mode", help="Discovery mode : [ macros | tags ]. Macros will creates host macros and tags will add tags for each fs detected.")
parser.add_option("-C", "--community", dest="community", help="Community to scan (default:public)")
parser.add_option("-O", "--os", dest="os", help="OS from scanned host")
parser.add_option("-V", "--version", dest="version", type=int, help="Version number for SNMP (1, 2 or 3; default:1)")
parser.add_option("-l", "--login", dest="snmpv3_user", help="User name for snmpv3(default:admin)")
parser.add_option("-L", "--level", dest="snmpv3_level", help="Security level for snmpv3(default:authNoPriv)")
parser.add_option("-p", "--authproto", dest="snmpv3_auth", help="Authentication protocol for snmpv3(default:MD5)")
parser.add_option("-x", "--authpass", dest="snmpv3_auth_pass", help="Authentication password for snmpv3(default:monpassword)")


opts, args = parser.parse_args()

hostname = opts.hostname
os = opts.os

mode = { 'macros' : '_fs',
         'tags' : 'fs',
}

if not opts.hostname:
    parser.error("Requires one host and its os to scan (option -H)")

if not opts.mode:
    parser.error("Requires mode. Please choose between macros or tags")

if not opts.os:
    parser.error("Requires the os host(option -O)")

if opts.community:
    community = opts.community
else:
    community = 'public'

if opts.version:
    version = opts.version
else:
    version = 1

if opts.snmpv3_user:
    snmpv3_user = opts.snmpv3_user
else:
    snmpv3_user = 'myuser'

if opts.snmpv3_level:
    snmpv3_level = opts.snmpv3_level
else:
    snmpv3_level = 'authNoPriv'

if opts.snmpv3_auth:
    snmpv3_auth = opts.snmpv3_auth
else:
    snmpv3_auth = 'MD5'

if opts.snmpv3_auth_pass:
    snmpv3_auth_pass = opts.snmpv3_auth_pass
else:
    snmpv3_auth_pass = 'mypassword'

oid_aix_linux = ".1.3.6.1.2.1.25.3.8.1.2"# hrFSMountPoint
oid_hpux = ".1.3.6.1.4.1.11.2.3.1.2.2.1.10"# fileSystemName


##############
#  functions #
############## 

### Search for files systems presents on the target
def get_fs_discovery(oid):
    hrFSMountPoint = netsnmp.Varbind(oid)
    result = netsnmp.snmpwalk(hrFSMountPoint, Version=version, DestHost=hostname, Community=community, SecName=snmpv3_user, SecLevel=snmpv3_level, AuthProto=snmpv3_auth, AuthPass=snmpv3_auth_pass)
    #PrivProto=snmpv3_priv, PrivPass=snmpv3_priv_pass
    fsList = list(result)
    return fsList

### converts the listed files systems writing and display them on the standard output
def get_fs_discovery_output(liste):
    fsTbl = []
    for element in liste:
        elt = re.sub(r'\W', '_', element)# conversion from / to _
        if elt == '_':# if _ is the only detected character
            elt = re.sub(r'^_$', '_root', elt)# so we replace _ with _root
        fsTbl.append(elt)
    print "%s::%s=%s"%(hostname, mode[opts.mode], ','.join(fsTbl))# display like in the nmap model

###############
#  execution  #
###############

scan = []

if os == 'aix':
    scan = get_fs_discovery(oid_aix_linux)
elif os == 'linux':
    scan = get_fs_discovery(oid_aix_linux)
elif os == 'hp-ux':
    scan = get_fs_discovery(oid_hpux)

get_fs_discovery_output(scan)
