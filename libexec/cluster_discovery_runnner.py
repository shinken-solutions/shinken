#!/usr/bin/env python
#First of all, the fs_discovery_runner.py script get the list 
#of the files systems back from the nmap device list with SNMP 
#protocol. The OID used by SNMP to recover datas is particular
#to each OS type.
#And then it converts the listed files systems writing and
#display it on the standard output.
#For example : / will be translate into _root and /var will be
#translate into _var
###############################################################
#For SNMPv3 we created a default user using the command :
#net-snmp-config --create-snmpv3-user -a "mypassword" myuser
#Here the user name is myuser and his password is mypassword


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

### Search for files systems presents on the target
def get_cluster_discovery(oid):
    name= netsnmp.Varbind(oid)
    result = netsnmp.snmpwalk(name, Version=version, DestHost=hostname, Community=community, SecName=snmpv3_user, SecLevel=snmpv3_level, AuthProto=snmpv3_auth, AuthPass=snmpv3_auth_pass)
    nameList = list(result)
    return nameList

### converts the listed files systems writing and display them on the standard output
def get_cluster_discovery_output(list):
    names = []
    for elt in list:
        names.append(elt)
    print "%s::%s=%s"%(hostname, clSolution, ','.join(names))# display like in the nmap model

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
