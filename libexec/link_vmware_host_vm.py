#!/usr/bin/env python

import os
import sys
import shlex
import shutil
import json
from subprocess import Popen, PIPE

check_esx_path = sys.argv[1]#'/home/shinken/check_esx3.pl'
vcenter = sys.argv[2]# Addres o the vcenter
user = sys.argv[3]# user name for vcenter connexion
password = sys.argv[4]# password dumbass
rules = sys.argv[5]# '', or 'lower' or 'nofqdn' or 'lower|nofqdn'
list_host_cmd_s = '%s -D %s -u %s -p %s -l runtime -s listhost' % (check_esx_path, vcenter, user, password)
print "Launching host listing", list_host_cmd_s
list_host_cmd = shlex.split(list_host_cmd_s)

hosts = []
res = {}

t = rules.split('|')
new_rules = []
for e in t:
    new_rules.append(e.strip())
rules = new_rules

def apply_rules(name, rules):
    print 'APPlying rules', rules, 'on name', name
    r = name
    if 'lower' in rules:
        r = r.lower()
    if 'nofqdn' in rules:
        print "APPly nofqdn rule on", r
        r = r.split('.')[0]
    return r


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

print "Hosts", hosts
for h in hosts:
    res[h] = []
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
        continue
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
        res[h].append(vm)


r = []
print "Total res", res
for host in res:
    print "Doing key", host
    for vm in res[host]:
        # First we apply rules on the names
        host_name = apply_rules(host, rules)
        vm_name = apply_rules(vm, rules)
        print "Add", host_name, vm_name
        v = (('host', host_name),('host', vm_name))
        r.append(v)


f = open('/tmp/vmware_mapping_file.json'+'.tmp', 'wb')
buf = json.dumps(r)
print "BUF json", buf
f.write(buf)
f.close()
shutil.move('/tmp/vmware_mapping_file.json'+'.tmp', '/tmp/vmware_mapping_file.json')
print "Finished!"
