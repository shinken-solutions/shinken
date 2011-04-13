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

#sudo nmap 192.168.0.1 -T4 -O --traceroute -oX toto.xml

import optparse
import sys
import cPickle
import os
import re
import time

try:
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    if not hasattr(os, "getuid") or os.getuid() != 0:
        imp.load_module('shinken', *imp.find_module('shinken', [".", ".."]))

from shinken.log import logger
from shinken.objects import *
from shinken.macroresolver import MacroResolver


VERSION = '0.1'

parser = optparse.OptionParser(
    "%prog [options] -c discovery_config -o config_output -m list of macros",
    version="%prog " + VERSION)
parser.add_option('-c', '--cfg-input',
                  dest="cfg_input", help=('Discovery configuration file (discovery.cfg)'))
parser.add_option('-o', '--dir-output', dest="output_dir",
                  help="Directory output for results")
parser.add_option('-w', '--overright', dest="overright", action='store_true',
                  help="Allow overwithing xisting file (disabled by default)")
parser.add_option('-r', '--runners', dest="runners",
                  help="List of runners you allow to run, (like nmap,vsphere)")
parser.add_option('-m', '--macros', dest="macros",
                  help="List of macros (like NMAPTARGETS=192.168.0.0/24). Should be the last argument")



opts, args = parser.parse_args()

raw_macros = []
macros=[]

if not opts.cfg_input:
    parser.error("Requires a discovery configuration file, dsicovery.cfg (option -c/--cfg-input")
if not opts.output_dir:
    parser.error("Requires one output directory (option -o/--dir-output")
if not opts.overright:
    overright = False
else:
    overright = opts.overright
if not opts.runners:
    runners = ['*']
else:
    runners = opts.runners.split(',')
if opts.macros:
    raw_macros.append(opts.macros)
if args:
    raw_macros.extend(args)

print "Macros", raw_macros

for m in raw_macros:
    elts = m.split('=')
    if len(elts) < 2:
        print "The macro '%s' is malformed. I bail out" % m
        sys.exit(2)
    macros.append( (elts[0], '='.join(elts[1:])))

print "Got macros", macros

# Says if a host is up or not
def is_up(h):
    status = h.find('status')
    state = status.attrib['state']
    return state == 'up'


class ConfigurationManager:
    def __init__(self, h, path, criticity):
        self.h = h
        self.hosts_path = os.path.join(path, 'hosts')
        self.srvs_path = os.path.join(path, 'services')
        self.templates = ['generic-host']
        self.services = []
        self.criticity = criticity
        self.parents = []

        
    # We search if our potential parent is present in the
    # other detected hosts. If so, set it as my parent
    def look_for_parent(self, all_hosts):
        parent = self.h.parent
        print "Look for my parent", self.h.get_name(), "->", parent
        # Ok, we didn't find any parent
        # we bail out
        if parent == '':
            return
        for h in all_hosts:
            print "Is it you?", h.get_name()
            if h.get_name() == parent:
                print "Houray, we find our parent", self.h.get_name(), "->", h.get_name()
                self.parents.append(h.get_name())
        

        
    def fill_system_conf(self):
        ios = self.h.os
        
        #Ok, unknown os... not good
        if ios == ('', ''):
            return

        map = {('Windows', '2000') : 'windows',
               ('Windows', '2003') : 'windows',
               ('Windows', '7') : 'windows',
               ('Windows', 'XP') : 'windows',
               # ME? you are a stupid moron!
               ('Windows', 'Me') : 'windows',
               ('Windows', '2008') : 'windows',
               # that's a good boy :)
               ('Linux', '2.6.X') : 'linux',
               ('Linux', '2.4.X') : 'linux',
               # HPUX? I think you didn't choose...
               ('HP-UX', '11.X') : 'hpux',
               ('HP-UX', '10.X') : 'hpux',
               }

        if ios not in map:
            print "Unknown OS:", ios
            return

        t = map[ios]
        self.templates.append(t)

        # Look for VMWare VM or hosts
        if self.h.is_vmware_vm():
            self.templates.append('vmware-vm')
        # Now is an host?
        if self.h.is_vmware_esx():
            self.templates.append('vmware-host')


    def get_cfg_for_host(self):
        props = {}
        props['host_name'] = self.h.get_name()
        props['criticity'] = self.criticity

        # Parents if we got some
        if self.parents != []:
            props['parents'] = ','.join(self.parents)

        # Now template
        props['use'] = ','.join(self.templates)            
        
        print "Want to write", props
        s = 'define host {\n'
        for k in props:
            v = props[k]
            s += '  %s    %s\n' % (k, v)
        s += '}\n'
        print s
        return s


    def get_cfg_for_services(self):
        r = {}
        print "And now services:"
        for srv in self.services:
            desc = srv['service_description']
            s = 'define service {\n'
            for k in srv:
                v = srv[k]
                s += '  %s    %s\n' % (k, v)
            s += '}\n'
            print s
            r[desc] = s
        return r

            

    def fill_ports_services(self):
        for p in self.h.open_ports:
            print "The port", p, " is open"
            f = getattr(self, 'gen_srv_'+str(p), None)
            if f:
                f()

    def fill_system_services(self):
        for t in self.templates:
            print "Registering services for the template", t
            # Python functions cannot be -, so we change it by _
            t = t.replace('-','_')
            print "Search for", 'gen_srv_'+str(t)
            f = getattr(self, 'gen_srv_'+str(t), None)
            if f:
                f()


    def generate_service(self, desc, check):
        srv = {'use' : 'generic-service', 'service_description' : desc, 'check_command' : check, 'host_name' : self.h.get_name()}
        self.services.append(srv)


    ######### For network ones

    # HTTP
    def gen_srv_80(self):
        self.generate_service('HTTP', 'check_http')

    # SSH
    def gen_srv_22(self):
        self.generate_service('SSH', 'check_ssh')

    # HTTPS + certificate
    def gen_srv_443(self):
        self.generate_service('HTTPS', 'check_https')
        self.generate_service('HTTPS-CERT', 'check_https_certificate')
        
    # FTP
    def gen_srv_21(self):
        self.generate_service('FTP', 'check_ftp')
        
    # DNS
    def gen_srv_53(self):
        self.generate_service('DNS', 'check_dig!$HOSTADDRESS$')
        
    # Oracle Listener
    def gen_srv_1521(self):
        self.generate_service('Oracle-Listener', 'check_oracle_listener')

    # Now for MSSQL
    def gen_srv_1433(self):
        self.generate_service('MSSQL-Connexion', 'check_mssql_connexion')
        print "I will need check_mssql_health from http://labs.consol.de/nagios/check_mssql_health/"

    # SMTP
    def gen_srv_25(self):
        self.generate_service('SMTP', 'check_smtp')
        
    # And the SMTPS too
    def gen_srv_465(self):
        self.generate_service('SMTPS', 'check_smtps')

    # LDAP
    def gen_srv_389(self):
        self.generate_service('Ldap', 'check_ldap')

    # LDAPS
    def gen_srv_636(self):
        self.generate_service('Ldaps', 'check_ldaps')
    
    #Mysql
    def gen_srv_3306(self):
        self.generate_service('Mysql', 'check_mysql_connexion')


    #### 
    #      For system ones
    ####
    def gen_srv_linux(self):
        print "You want a Linux check, but I don't know what to propose, sorry..."

    def gen_srv_windows(self):
        print "You want a Windows check, but I don't know what to propose, sorry..."

    #For a VM we can add cpu, io, mem and net
    def gen_srv_vmware_vm(self):
        self.generate_service('VM-Cpu', "check_esx_vm!cpu")
        self.generate_service('VM-IO', "check_esx_vm!io")
        self.generate_service('VM-Memory', "check_esx_vm!mem")
        self.generate_service('VM-Network', "check_esx_vm!net")
        print "I will need the check_esx3.pl from http://www.op5.org/community/plugin-inventory/op5-projects/op5-plugins"

    # Quite the same for the host
    def gen_srv_vmware_host(self):
        self.generate_service('ESX-host-Cpu', "check_esx_host!cpu")
        self.generate_service('ESX-host-IO', "check_esx_host!io")
        self.generate_service('ESX-host-Memory', "check_esx_host!mem")
        self.generate_service('ESX-host-Network', "check_esx_host!net")
        print "I will need the check_esx3.pl from http://www.op5.org/community/plugin-inventory/op5-projects/op5-plugins"
        


    # Write the host cfg file
    def write_host_configuration(self):
        name = self.h.get_name()
        # If the host is bad, get out
        if not name:
            return
        
        # Write the directory with the host config
        p = os.path.join(self.hosts_path, name)
        print "I want to create", p
        try:
            os.mkdir(p)
        except OSError, exp:
            # If directory already exists, it's not a problem
            if not exp.errno != '17':
                print "Cannot create the directory '%s' : '%s'" % (p, exp)
                return
        cfg_p = os.path.join(p, name+'.cfg')
        print "I want to write", cfg_p
        s = self.get_cfg_for_host()
        try:
            fd = open(cfg_p, 'w')
        except OSError, exp:
            print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
            return
        fd.write(s)
        fd.close()
        

    def write_services_configuration(self):
        name = self.h.get_name()
        # If the host is bad, get out
        if not name:
            return
        
        # Write the directory with the host config
        p = os.path.join(self.srvs_path, name)
        print "I want to create", p
        try:
            os.mkdir(p)
        except OSError, exp:
            # If directory already exist, it's not a problem
            if not exp.errno != '17':
                print "Cannot create the directory '%s' : '%s'" % (p, exp)
                return
        # Ok now we get the services to create    
        r = c.get_cfg_for_services()
        for s in r:
            cfg_p = os.path.join(p, name+'-'+s+'.cfg')
            print "I want to write", cfg_p
            buf = r[s]
            try:
                fd = open(cfg_p, 'w')
            except OSError, exp:
                print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
                return
            fd.write(buf)
            fd.close()
        
        

class DiscoveryMerger:
    def __init__(self, path, output_dir, macros, overright, runners):
        # i am arbiter-like
        self.log = logger
        self.overright = overright
        self.runners = runners
        self.output_dir = output_dir
        self.log.load_obj(self)
        self.config_files = [path]
        self.conf = Config()
        self.conf.read_config(self.config_files)
        buf = self.conf.read_config(self.config_files)
        
        # Add macros on the end of the buf so they will
        # overright the resource.cfg ones
        for (m, v) in macros:
            buf += '\n$%s$=%s\n' % (m, v)

        raw_objects = self.conf.read_config_buf(buf)
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')
        self.conf.early_arbiter_linking()
        self.conf.create_objects(raw_objects)
        #self.conf.instance_id = 0
        #self.conf.instance_name = ''
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.clean_useless()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependancies()
        #self.conf.explode_global_conf()
        #self.conf.propagate_timezone_option()
        #self.conf.create_business_rules()
        #self.conf.create_business_rules_dependencies()
        self.conf.is_correct()

        self.discoveryrules = self.conf.discoveryrules
        self.discoveryruns = self.conf.discoveryruns
        
        #self.confs = self.conf.cut_into_parts()
        #self.dispatcher = Dispatcher(self.conf, self.me)
        
        #scheddaemon = Shinken(None, False, False, False, None)
        #self.sched = Scheduler(scheddaemon)
        
        #scheddaemon.sched = self.sched
                
        m = MacroResolver()
        m.init(self.conf)
        #self.sched.load_conf(self.conf)
        #e = ExternalCommandManager(self.conf, 'applyer')
        #self.sched.external_command = e
        #e.load_scheduler(self.sched)
        #e2 = ExternalCommandManager(self.conf, 'dispatcher')
        #e2.load_arbiter(self)
        #self.external_command_dispatcher = e2
        #self.sched.schedule()
        
        # Hash = name, and in it (key, value)
        self.disco_data = {}
        # Hash = name, and in it rules that apply
        self.disco_matches = {}


    def add(self, obj):
        pass

    # Look if the name is a IPV4 address or not
    def is_ipv4_addr(self, name):
        p = r"^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$"
        return (re.match(p, name) is not None)


    def read_disco_buf(self):
        buf = self.raw_disco_data
        for l in buf.split('\n'):
            #print ""
            # If it's not a disco line, bypass it
            if not re.search('::', l):
                continue
            #print "line", l
            elts = l.split('::')
            if len(elts) <= 1:
                #print "Bad discovery data"
                continue
            name = elts[0].strip()

            # We can choose to keep only the basename
            # of the nameid, so strip the fqdn
            # But not if it's a plain ipv4 addr
            if self.conf.strip_idname_fqdn:
                if not self.is_ipv4_addr(name):
                    name = name.split('.', 1)[0]

            data = '::'.join(elts[1:])

            #print "Name", name
            #print "data", data
            # Register the name
            if not name in self.disco_data:
                self.disco_data[name] = []
            # Now get key,values
            if not '=' in data:
                #print "Bad discovery data"
                continue
            elts = data.split('=')
            if len(elts) <= 1:
                #print "Bad discovery data"
                continue
            key = elts[0].strip()
            value = elts[1].strip()
            print "-->", name, key, value
            self.disco_data[name].append((key, value))


    def match_rules(self):
        for name in self.disco_data:
            datas = self.disco_data[name]
            for r in self.discoveryrules:
                if r.is_matching_disco_datas(datas):
                    if name not in self.disco_matches:
                        self.disco_matches[name] = []
                    self.disco_matches[name].append(r)
                    print "Generating", name, r.writing_properties


    def is_allowing_runners(self, name):
        name = name.strip()

        # If we got no value, it's * by default
        if '*' in self.runners:
            return True

        #print self.runners
        #If we match the name, ok
        for r in self.runners:
            r_name = r.strip()
            #            print "Look", r_name, name
            if r_name == name:
                return True

        # Not good, so not run this!
        return False

    def allowed_runners(self):
        return [r for r in self.discoveryruns if self.is_allowing_runners(r.get_name())]

    def launch_runners(self):
        for r in self.allowed_runners():
            print "I'm launching", r.get_name()
            print r.discoveryrun_command
            r.launch()


    def wait_for_runners_ends(self):
        all_ok = False
        while not all_ok:
            all_ok = True
            for r in self.allowed_runners():
                if not r.is_finished():
                    #print "Check finished of", r.get_name()
                    r.check_finished()
                b = r.is_finished()
                if not b:
                    #print r.get_name(), "is not finished"
                    all_ok = False
            time.sleep(0.1)


    def get_runners_outputs(self):
        self.raw_disco_data = '\n'.join(r.get_output() for r in self.allowed_runners() if r.is_finished())
        print "Got Raw disco data", self.raw_disco_data


    # Write all configuration we've got
    def write_config(self):
        for name in self.disco_data:
            print "Writing", name, "configuration"
            self.write_host_config(name)
            self.write_service_config(name)


    # We search for all rules of type host, and we merge them
    def write_host_config(self, host):
        host_rules = []
        for (name, rules) in self.disco_matches.items():
            if name != host:
                continue
            rs = [r for r in rules if r.creation_type == 'host']
            host_rules.extend(rs)

        # If no rule, bail out
        if len(host_rules) == 0:
            return
    
        # now merge them
        d = {'host_name' : host}
        for r in host_rules:
            d.update(r.writing_properties)
        print "Will generate", d
        self.write_host_config_to_file(host, d)

        
    # Will wrote all properties/values of d for the host
    # in the file
    def write_host_config_to_file(self, host, d):
        p = os.path.join(self.output_dir, host)
        print "Want to create host path", p
        try:
            os.mkdir(p)
        except OSError, exp:
            # If directory already exist, it's not a problem
            if not exp.errno != '17':
                print "Cannot create the directory '%s' : '%s'" % (p, exp)
                return
        cfg_p = os.path.join(p, host+'.cfg')
        if os.path.exists(cfg_p) and not overright:
            print "The file '%s' already exists" % cfg_p
            return

        buf = self.get_cfg_bufer(d, 'host')

        # Ok, we create it so (or overright)
        try:
            fd = open(cfg_p, 'w')
            fd.write(buf)
            fd.close()
        except OSError, exp:
            print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
            return


    # Generate all service for a host
    def write_service_config(self, host):
        srv_rules = {}
        for (name, rules) in self.disco_matches.items():
            if name != host:
                continue
            rs = [r for r in rules if r.creation_type == 'service']
            print "RS", rs
            for r in rs:
                if 'service_description' in r.writing_properties:
                    desc = r.writing_properties['service_description']
                    if not desc in srv_rules:
                        srv_rules[desc] = []
                    srv_rules[desc].append(r)

        #print "Generate services for", host
        #print srv_rules
        for (desc, rules) in srv_rules.items():
            d = {'service_description' : desc, 'host_name' : host}
            for r in rules:
                d.update(r.writing_properties)
            print "Generating", desc, d
            self.write_service_config_to_file(host, desc, d)


    # Will wrote all properties/values of d for the host
    # in the file
    def write_service_config_to_file(self, host, desc, d):
        p = os.path.join(self.output_dir, host)

        # The host conf should already exist
        cfg_host_p = os.path.join(p, host+'.cfg')
        if not os.path.exists(cfg_host_p):
            print "No host configuration available, I bail out"
            return

        cfg_p = os.path.join(p, desc+'.cfg')
        if os.path.exists(cfg_p) and not overright:
            print "The file '%s' already exists" % cfg_p
            return

        buf = self.get_cfg_bufer(d, 'service')

        # Ok, we create it so (or overright)
        try:
            fd = open(cfg_p, 'w')
            fd.write(buf)
            fd.close()
        except OSError, exp:
            print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
            return

            
    # Create a define t { } with data in d
    def get_cfg_bufer(self, d, t):
        tab = ['define %s {' % t]
        for (key, value) in d.items():
            tab.append('  %s   %s' % (key, value))
        tab.append('}\n')
        return '\n'.join(tab)
        

        


cfg_input = opts.cfg_input
output_dir = opts.output_dir
overright = opts.overright
d = DiscoveryMerger(cfg_input, output_dir, macros, overright, runners)




d.launch_runners()
d.wait_for_runners_ends()
d.get_runners_outputs()

d.read_disco_buf()

# Now look for rules
d.match_rules()
#print d.disco_matches

d.write_config()
