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
# cluster_discovery_runner.py script simply try to get informations
# from HACMP mib and failback on Safekit mib. SNMP for both product
# need to be activated. For Safekit, add a proxy into snmpd conf to
# include its mib into the master agent netsnmp.
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
parser.add_option("-H", "--hostname", dest="hostname", help="Hostname to scan")
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

clSolution_by_os = { 'aix' : 'hacmp',
       'linux': 'safekit',
     }

if not opts.hostname:
    parser.error("Requires one host and its os to scan (option -H)")

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

oid_safekit_moduleName = ".1.3.6.1.4.1.107.175.10.1.1.2"
oid_hacmp_clusterName = ".1.3.6.1.4.1.2.3.1.2.1.5.1.2"


##############
#  functions #
############## 

### Search for cluster solution, between safekit or hacmp, presents on the target
def get_cluster_discovery(oid):
    name= netsnmp.Varbind(oid)
    result = netsnmp.snmpwalk(name, Version=version, DestHost=hostname, Community=community, SecName=snmpv3_user, SecLevel=snmpv3_level, AuthProto=snmpv3_auth, AuthPass=snmpv3_auth_pass)
    nameList = list(result)
    return nameList

### format the modules list and display them on the standard output
def get_cluster_discovery_output(list):
    names = []
    if list :
        for elt in list:
            names.append(elt)
        print "%s::%s=1"%(hostname, clSolution)# To add tag
        print "%s::_%s_modules=%s"%(hostname, clSolution, ','.join(names))# Host macros by Safekit modules
    else : 
        print "%s::%s=0"%(hostname, clSolution)# No cluster detected

###############
#  execution  #
###############

scan = []
clSolution = clSolution_by_os[os]


scan = get_cluster_discovery(oid_hacmp_clusterName)
if not scan:
    scan = get_cluster_discovery(oid_safekit_moduleName)
    clSolution = 'safekit'

get_cluster_discovery_output(scan)
