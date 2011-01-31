#!/usr/bin/env python

import os
import sys
import shlex
import shutil
import getopt
try:
    import json
except ImportError: 
    # For old Python version, load 
    # simple json (it can be hard json?! It's 2 functions guy!)
    import simplejson

from subprocess import Popen, PIPE

check_esx_path = sys.argv[1]#'/home/shinken/check_esx3.pl'
vcenter = sys.argv[2]# Addres o the vcenter
user = sys.argv[3]# user name for vcenter connexion
password = sys.argv[4]# password dumbass
rules = sys.argv[5]# '', or 'lower' or 'nofqdn' or 'lower|nofqdn'

def split_rules(rules):
    t = rules.split('|')
    new_rules = []
    for e in t:
        new_rules.append(e.strip())
    rules = new_rules
    return rules
rules = split_rules(rules)


def _apply_rules(name, rules):
    print 'APPlying rules', rules, 'on name', name
    r = name
    if 'lower' in rules:
        r = r.lower()
    if 'nofqdn' in rules:
        print "APPly nofqdn rule on", r
        r = r.split('.')[0]
    return r


def get_vmware_hosts(check_esx_path, vcenter, user, password):
    list_host_cmd_s = '%s -D %s -u %s -p %s -l runtime -s listhost' % (check_esx_path, vcenter, user, password)
    print "Launching host listing", list_host_cmd_s
    list_host_cmd = shlex.split(list_host_cmd_s)
    
    hosts = []

    
    output = Popen(list_host_cmd, stdout=PIPE).communicate()
    print "Output", output[0]

    parts = output[0].split(':')
    print parts
    hsts_raw = parts[1].split('|')[0]
    print hsts_raw
    hsts_raw_lst = hsts_raw.split(',')
    print hsts_raw_lst 

    for hst_raw in hsts_raw_lst:
        hst_raw = hst_raw.strip()
        # look as server4.mydomain(UP)
        elts = hst_raw.split('(')
        hst = elts[0]
        hosts.append(hst)
    
    return hosts

res = {}
hosts = get_vmware_hosts(check_esx_path, vcenter, user, password)

print "Hosts", hosts


def get_vm_of_host(check_esx_path, vcenter, h, user, password):
    lst = []
    print "Listing host", h
    list_vm_cmd_s = '%s -D %s -H %s -u %s -p %s -l runtime -s list' % (check_esx_path, vcenter, h, user, password)
    print "Launch vm listing", list_vm_cmd_s
    list_vm_cmd = shlex.split(list_vm_cmd_s)
    output = Popen(list_vm_cmd, stdout=PIPE).communicate()
    print "Output", output[0]
    parts = output[0].split(':')
    # Maybe we got a 'CRITICAL - There are no VMs.' message,
    # if so, we bypass this host
    if len(parts) < 2:
        return []
    print parts
    vms_raw = parts[1].split('|')[0]
    print vms_raw
    vms_raw_lst = vms_raw.split(',')
    print vms_raw_lst
    
    for vm_raw in vms_raw_lst:
        vm_raw = vm_raw.strip()
        # look as MYVM(UP)
        elts = vm_raw.split('(')
        vm = elts[0]
        print "GOT A VM", vm
        lst.append(vm)
    return lst


for h in hosts:
    lst = get_vm_of_host(check_esx_path, vcenter, h, user, password)
    if lst != []:
        res[h] = lst



def create_all_links(res, rules):
    r = []
    print "Total res", res
    for host in res:
        print "Doing key", host
        for vm in res[host]:
            # First we apply rules on the names
            host_name = _apply_rules(host, rules)
            vm_name = _apply_rules(vm, rules)
            print "Add", host_name, vm_name
            v = (('host', host_name),('host', vm_name))
            r.append(v)
    return r

r = create_all_links(res, rules)

print "Created %d links" % len(r)

def write_output(r, path):
    f = open(path+'.tmp', 'wb')
    buf = json.dumps(r)
    print "BUF json", buf
    f.write(buf)
    f.close()
    shutil.move(path+'.tmp', path)
    print "File %s wrote" % path

write_output(r, '/tmp/vmware_mapping_file.json')
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



# Here we go!
if __name__ == "__main__":
    # Manage the options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hoxVupr", ["help", "output", "esx3-path", "Vcenter", "user", "password", "rules"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(sys.argv[0])
        sys.exit(2)
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
        elif o in ("o", "--output"):
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
