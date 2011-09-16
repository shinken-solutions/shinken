#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel <h.goebel@goebel-consult.de>
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
import optparse
from subprocess import Popen, PIPE

# Try to load json (2.5 and higer) or simplejson if failed (python2.4)
try:
    import json
except ImportError: 
    # For old Python version, load 
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        sys.exit("Error : you need the json or simplejson module for this script")

VERSION = '0.1'

# Search if we can findthe check_esx3.pl file somewhere
def search_for_check_esx3():
    me = os.path.abspath( __file__ )
    my_dir = os.path.dirname(me)
    possible_paths = [os.path.join(my_dir, 'check_esx3.pl'),
                      '/var/lib/nagios/check_esx3.pl',
                      '/var/lib/plugins/nagios/check_esx3.pl',
                      '/var/lib/shinken/check_esx3.pl',
                      '/usr/local/nagios/libexec/check_esx3.pl',
                      '/usr/local/shinken/libexec/check_esx3.pl',
                      'c:\\shinken\\libexec\\check_esx3.pl']

    for p in possible_paths:
        print "Look for", p
        if os.path.exists(p):
            print "Found a check_esx3.pl at", p
            return p
    return None


# Split and clean the rules from a string to a list
def _split_rules(rules):
    return [r.strip() for r in rules.split('|')]

# Apply all rules on the objects names
def _apply_rules(name, rules):
    if 'nofqdn' in rules:
        name = name.split('.', 1)[0]
    if 'lower' in rules:
        name = name.lower()
    return name

# Get all vmware hosts from a VCenter and return the list
def get_vmware_hosts(check_esx_path, vcenter, user, password):
    list_host_cmd = [check_esx_path, '-D', vcenter, '-u', user, '-p', password,
                     '-l', 'runtime', '-s', 'listhost']

    print "Got host list"
    print ' '.join(list_host_cmd)
    p = Popen(list_host_cmd, stdout=PIPE, stderr=PIPE)
    output = p.communicate()
    
    print "Exit status", p.returncode
    if p.returncode == 2:
        print "Error : the check_esx3.pl return in error :", output
        sys.exit(2)

    parts = output[0].split(':')
    hsts_raw = parts[1].split('|')[0]
    hsts_raw_lst = hsts_raw.split(',')

    hosts = []
    for hst_raw in hsts_raw_lst:
        hst_raw = hst_raw.strip()
        # look as server4.mydomain(UP)
        elts = hst_raw.split('(')
        hst = elts[0]
        hosts.append(hst)
    
    return hosts


# For a specific host, ask all VM on it to the VCenter
def get_vm_of_host(check_esx_path, vcenter, host, user, password):
    print "Listing host", host
    list_vm_cmd = [check_esx_path, '-D', vcenter, '-H', host,
                   '-u', user, '-p', password,
                   '-l', 'runtime', '-s', 'list']
    print ' '.join(list_vm_cmd)
    p = Popen(list_vm_cmd, stdout=PIPE)
    output = p.communicate()

    print "Exit status", p.returncode
    if p.returncode == 2:
        print "Error : the check_esx3.pl return in error :", output
        sys.exit(2)

    parts = output[0].split(':')
    # Maybe we got a 'CRITICAL - There are no VMs.' message,
    # if so, we bypass this host
    if len(parts) < 2:
        return None

    vms_raw = parts[1].split('|')[0]
    vms_raw_lst = vms_raw.split(',')
    
    lst = []
    for vm_raw in vms_raw_lst:
        vm_raw = vm_raw.strip()
        # look as MYVM(UP)
        elts = vm_raw.split('(')
        vm = elts[0]
        lst.append(vm)
    return lst


# Create all tuples of the links for the hosts
def print_all_links(res, rules):
    r = []
    for host in res:
        host_name = _apply_rules(host, rules)
        print "%s::isesxhost=1" % host_name
        for vm in res[host]:
            # First we apply rules on the names
            vm_name = _apply_rules(vm, rules)
            #v = (('host', host_name),('host', vm_name))
            print "%s::isesxvm=1" % vm_name
            print "%s::esxhost=%s" % (vm_name, host_name)
            #r.append(v)
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
        sys.exit("Error writing the file %s : %s" % (path, exp))


def main(check_esx_path, vcenter, user, password, rules):
    rules = _split_rules(rules)
    res = {}
    hosts = get_vmware_hosts(check_esx_path, vcenter, user, password)
    
    for host in hosts:
        lst = get_vm_of_host(check_esx_path, vcenter, host, user, password)
        if lst:
            res[host] = lst


    print_all_links(res, rules)

    #write_output(r, output)
    print "Finished!"


# Here we go!
if __name__ == "__main__":
    # Manage the options
    parser = optparse.OptionParser(
        version="Shinken VMware links dumping script version %s" % VERSION)
    parser.add_option("-x", "--esx3-path", dest='check_esx_path',
                      default='/usr/local/nagios/libexec/check_esx3.pl',
                      help="Full path of the check_esx3.pl script (default: %default)")
    parser.add_option("-V", "--vcenter", '--Vcenter',
                      help="tThe IP/DNS address of your Vcenter host.")
    parser.add_option("-u", "--user",
                      help="User name to connect to this Vcenter")
    parser.add_option("-p", "--password",
                      help="The password of this user")
    parser.add_option('-r', '--rules', default='',
                      help="Rules of name transformation. Valid names are: "
                      "`lower`: to lower names, "
                      "`nofqdn`: keep only the first name (server.mydomain.com -> server)."
                      "You can use several rules like `lower|nofqdn`")

    opts, args = parser.parse_args()
    if args:
        parser.error("does not take any positional arguments")

    if opts.vcenter is None:
        parser.error("missing -V or --Vcenter option for the vcenter IP/DNS address")
    if opts.user is None:
        parser.error("missing -u or --user option for the vcenter username")
    if opts.password is None:
        error = True
        parser.error("missing -p or --password option for the vcenter password")
    if not os.path.exists(opts.check_esx_path):
        parser.error("the path %s for the check_esx3.pl script is wrong, missing file" % opts.check_esx_path)
    else:
        # Not given, try to find one
        p = search_for_check_esx3()
        if p is None:
            parser.error("Sorry, I cannot find check_esx3.pl, please specify it with -x")
        #else set it :)
        opts.check_esx_path = p

    main(**opts.__dict__)
