#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
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

import os
import sys
import shlex
import shutil
import getopt
# Try to load the json (2.5 and higer) or
# the simplejson if failed (python2.4)
try:
    import json
except ImportError: 
    # For old Python version, load 
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error : you need the json or simplejson module for this script"
        sys.exit(2)
from subprocess import Popen, PIPE


# Split and clean the rules from a string to a list
def split_rules(rules):
    t = rules.split('|')
    new_rules = []
    for e in t:
        new_rules.append(e.strip())
    rules = new_rules
    return rules

# Apply all rules on the objects names
def _apply_rules(name, rules):
    r = name
    if 'lower' in rules:
        r = r.lower()
    if 'nofqdn' in rules:
        r = r.split('.')[0]
    return r

# Get all vmware hosts from a VCenter and return the list
def get_vmware_hosts(check_esx_path, vcenter, user, password):
    list_host_cmd_s = '%s -D %s -u %s -p %s -l runtime -s listhost' % (check_esx_path, vcenter, user, password)
    list_host_cmd = shlex.split(list_host_cmd_s)
    
    hosts = []

    output = Popen(list_host_cmd, stdout=PIPE).communicate()

    parts = output[0].split(':')
    hsts_raw = parts[1].split('|')[0]
    hsts_raw_lst = hsts_raw.split(',')

    for hst_raw in hsts_raw_lst:
        hst_raw = hst_raw.strip()
        # look as server4.mydomain(UP)
        elts = hst_raw.split('(')
        hst = elts[0]
        hosts.append(hst)
    
    return hosts


# For a specific host, ask all VM on it to the VCenter
def get_vm_of_host(check_esx_path, vcenter, h, user, password):
    lst = []
    print "Listing host", h
    list_vm_cmd_s = '%s -D %s -H %s -u %s -p %s -l runtime -s list' % (check_esx_path, vcenter, h, user, password)
    list_vm_cmd = shlex.split(list_vm_cmd_s)
    output = Popen(list_vm_cmd, stdout=PIPE).communicate()
    parts = output[0].split(':')
    # Maybe we got a 'CRITICAL - There are no VMs.' message,
    # if so, we bypass this host
    if len(parts) < 2:
        return []

    vms_raw = parts[1].split('|')[0]
    vms_raw_lst = vms_raw.split(',')
    
    for vm_raw in vms_raw_lst:
        vm_raw = vm_raw.strip()
        # look as MYVM(UP)
        elts = vm_raw.split('(')
        vm = elts[0]
        lst.append(vm)
    return lst


# Create all tuples of the links for the hosts
def create_all_links(res, rules):
    r = []
    for host in res:
        for vm in res[host]:
            # First we apply rules on the names
            host_name = _apply_rules(host, rules)
            vm_name = _apply_rules(vm, rules)
            v = (('host', host_name),('host', vm_name))
            r.append(v)
    return r


def write_output(r, path):
    try:
        f = open(path+'.tmp', 'wb')
        buf = json.dumps(r)
        f.write(buf)
        f.close()
        shutil.move(path+'.tmp', path)
        print "File %s wrote" % path
    except IOError, exp:
        print "Error writing the file %s : %s" % (path, exp)
        sys.exit(2)


def main(check_esx_path, vcenter, user, password, output, rules):
    rules = split_rules(rules)
    res = {}
    hosts = get_vmware_hosts(check_esx_path, vcenter, user, password)
    
    for h in hosts:
        lst = get_vm_of_host(check_esx_path, vcenter, h, user, password)
        if lst != []:
            res[h] = lst

    r = create_all_links(res, rules)
    print "Created %d links" % len(r)

    write_output(r, output)
    print "Finished!"
    sys.exit(0)


VERSION = '0.1'
def usage(name):
    print "Shinken VMware links dumping script version %s from :" % VERSION
    print "        Gabes Jean, naparuba@gmail.com"
    print "        Gerhard Lausser, Gerhard.Lausser@consol.de"
    print "Usage: %s -V vcenter-ip -u USER -p PASSWORD -o /tmp/vmware_link.json [--esx3-path  /full/path/check_esx3.pl --rules RULES" % name
    print "Options:"
    print " -V, --Vcenter"
    print "\tThe IP/DNS address of your Vcenter host."
    print " -u, --user"
    print "\tUser name to connect to this Vcenter"
    print " -p, --password"
    print "\tThe password of this user"
    print " -o, --output"
    print "\tPath of the generated mapping file."
    print " -x, --esx3-path"
    print "\tFull path of the check_esx3.pl script. By default /usr/local/nagios/libexec/check_esx3.pl"
    print " -r, --rules"
    print "\t Rules of name transformation:"
    print "\t\t lower : to lower names"
    print "\t\t nofqdn : keep only the first name (server.mydomain.com -> server)"
    print "\t\t you can use several rules like 'lower|nofqdn'"
    print " -h, --help"
    print "\tPrint detailed help screen"
    print "\n"
    print "Example :"
    print "\t %s -V vcenter.google.com -user MySuperUser -password secret --esx3-path  /usr/local/nagios/libexec/check_esx3.pl --rules 'lower|nofqdn'" % name


def check_args(check_esx_path, vcenter, user, password, output, rules):
    error = False
    if vcenter is None:
        error = True
        print "Error : missing -V or -Vcenter option for the vcenter IP/DNS address"
    if user is None:
        error = True
        print "Error : missing -u or -user option for the vcenter username"
    if password is None:
        error = True
        print "Error : missing -p or -password option for the vcenter password"
    if not os.path.exists(check_esx_path):
        error = True
        print "Error : the path %s for the check_esx3.pl script is wrong, missing file"
    if output is None:
        error = True
        print "Error : missing -o or -output option for the output mapping file"

    if error:
        print "   ^"
        print "   |"
        print "   |"
        print "   |"
        usage(sys.argv[0])
        sys.exit(2)

# Here we go!
if __name__ == "__main__":
    print sys.argv[1:]
    # Manage the options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:x:V:u:p:r:", ["help", "output", "esx3-path", "Vcenter", "user", "password", "rules"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(sys.argv[0])
        sys.exit(2)
    print opts
    # Default params
    check_esx_path = '/usr/local/nagios/libexec/check_esx3.pl'
    vcenter = None
    user = None
    password = None
    rules = ''
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.argv[0])
            sys.exit()
        elif o in ("-o", "--output"):
            print "Got output", a
            output = a
        elif o in ("-x", "--esx3-path"):
            check_esx_path = a
        elif o in ("-V", "--Vcenter"):
            vcenter = a
        elif o in ("-u", "--user"):
            user = a
        elif o in ("-p", "--password"):
            password = a
        elif o in ('-r', '--rules'):
            rules = a
        else:
            print "Sorry, the option", o, a, "is unknown"
            usage(sys.argv[0])
            sys.exit()

    print "Got", check_esx_path, vcenter, user, password, output, rules
    check_args(check_esx_path, vcenter, user, password, output, rules)
    main(check_esx_path, vcenter, user, password, output, rules)
