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
        sys.exit("Error writing the file %s : %s" % (path, exp))


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


# Here we go!
if __name__ == "__main__":
    # Manage the options
    parser = optparse.OptionParser(
        version="Shinken VMware links dumping script version %s" % VERSION)
    parser.add_option("-o", "--output",
                      help="Path of the generated mapping file.")
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
    if opts.output is None:
        parser.error("missing -o or --output option for the output mapping file")

    main(**opts.__dict__)
