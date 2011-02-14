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


try:
    from xml.etree.ElementTree import ElementTree
except ImportError:
    print "This script need the python ElementTree module. Please install it"
    sys.exit(2)

VERSION = '0.1'

parser = optparse.OptionParser(
    "%prog [options] -x nmap.xml -o directory_output",
    version="%prog " + VERSION)
parser.add_option('-x', '--xml-input',
                  dest="xml_input", help=('Output of nmap'))
parser.add_option('-o', '--dir-output', dest="output_dir",
                  help="Directory output for results")
parser.add_option('-d', '--cfg-dir-output', dest="cfg_output_dir",
                  help="Directory output for host/services generated configurations")
opts, args = parser.parse_args()

if not opts.xml_input:
    parser.error("Requires one nmap xml output file (option -x/--xml-input")
if not opts.output_dir:
    parser.error("Requires one output directory (option -o/--dir-output")
if not opts.cfg_output_dir:
    parser.error("Requires one configuration output directory (option -d/--cfg-dir-output")
if args:
    parser.error("Does not accept any argument.")


# Say if a host is up or not
def is_up(h):
    status = h.find('status')
    state = status.attrib['state']
    return state == 'up'


class ConfigurationManager:
    def __init__(self, h, path):
        self.h = h
        self.hosts_path = os.path.join(path, 'hosts')
        self.srvs_path = os.path.join(path, 'services')
        self.templates = ['generic-host']
        self.services = []
        
        
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


    def get_cfg_for_host(self):
        props = {}
        props['host_name'] = self.h.get_name()
        props['use'] = ','.join(self.templates)
        
        if self.h.is_vmware_vm():
            props['_VMWARE_VM'] = '1'
        
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


    def generate_service(self, desc, check):
        srv = {'use' : 'generic-service', 'service_description' : desc, 'check_command' : check, 'host_name' : self.h.get_name()}
        self.services.append(srv)


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
        print "Will need check_mssql_health from http://labs.consol.de/nagios/check_mssql_health/"

    # SMTP
    def gen_srv_25(self):
        self.generate_service('SMTP', 'check_smtp')
        

    # LDAP
    def gen_srv_389(self):
        self.generate_service('Ldap', 'check_ldap')

    # LDAPS
    def gen_srv_636(self):
        self.generate_service('Ldaps', 'check_ldaps')
    

    # Write the host cfg file
    def write_host_configuration(self):
        name = self.h.get_name()
        # If the host is bad, get out
        if not name:
            return
        
        # Write the directory with the host config
        p = os.path.join(self.hosts_path, name)
        print "Want to create", p
        try:
            os.mkdir(p)
        except OSError, exp:
            # If directory already exist, it's not a problem
            if not exp.errno != '17':
                print "Cannot create the directory '%s' : '%s'" % (p, exp)
                return
        cfg_p = os.path.join(p, name+'.cfg')
        print "Want to wrote", cfg_p
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
        print "Want to create", p
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
            print "Want to wrote", cfg_p
            buf = r[s]
            try:
                fd = open(cfg_p, 'w')
            except OSError, exp:
                print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
                return
            fd.write(buf)
            fd.close()
        
        


class DetectedHost:
    def __init__(self):
        self.ip = ''
        self.mac_vendor = ''
        self.host_name = ''

        self.os_possibilities = []
        self.os = ('', '')
        self.open_ports = []

        self.parent = ''


    # Keep the first name we got
    def set_host_name(self, name):
        if self.host_name == '':
            self.host_name = name


    # Get a identifier for this host
    def get_name(self):
        if self.host_name != '':
            return self.host_name
        if self.ip != '':
            return self.ip
        return None


    # Say if we are a virtual machine or not
    def is_vmware_vm(self):
        return self.mac_vendor == 'VMware'


    # Fill the different os possibilities
    def add_os_possibility(self, os, osgen, accuracy):
        self.os_possibilities.append( (os, osgen, accuracy) )

    # Look at ours oses and see which one is the better
    def compute_os(self):
        # bailout if we got no os :(
        if len(self.os_possibilities) == 0:
            return

        max_accuracy = 0
        for (os, osgen, accuracy) in self.os_possibilities:
            if accuracy > max_accuracy:
                max_accuracy = accuracy

        # now get the entry with the max value
        for (os, osgen, accuracy) in self.os_possibilities:
            if accuracy == max_accuracy:
                self.os = (os, osgen)


xml_input = opts.xml_input
output_dir = opts.output_dir
cfg_output_dir = opts.cfg_output_dir

tree = ElementTree()
try:
    tree.parse(xml_input)
except IOError, exp:
    print "Error opening file '%s' : %s" % (xml_input, exp)
    sys.exit(2)

hosts = tree.findall('host')
print "Number of host", len(hosts)


all_hosts = []

for h in hosts:
    # Bypass non up hosts
    if not is_up(h):
        continue
    
    dh = DetectedHost()

    # Now we get the ipaddr and the mac vendor
    # for future VMWare matching
    #print h.__dict__
    addrs = h.findall('address')
    for addr in addrs:
        #print "Address", addr.__dict__
        addrtype = addr.attrib['addrtype']
        if addrtype == 'ipv4':
            dh.ip = addr.attrib['addr']
        if addrtype == "mac":
            if 'vendor' in addr.attrib:
                dh.mac_vendor = addr.attrib['vendor']


    # Now we got the hostnames
    host_names = h.findall('hostnames')
    for h_name in host_names:
        h_names = h_name.findall('hostname')
        for h_n in h_names:
            #print 'hname', h_n.__dict__
            #print 'Host name', h_n.attrib['name']
            dh.set_host_name(h_n.attrib['name'])


    # Now print the traceroute
    traces = h.findall('trace')
    for trace in traces:
        #print trace.__dict__
        hops = trace.findall('hop')
        #print "Number of hops", len(hops)
        distance = len(hops)
        if distance >= 2:
            for hop in hops:
                ttl = int(hop.attrib['ttl'])
                #We search the direct father
                if ttl == distance-1:
                    #print ttl
                    #print hop.__dict__
                    dh.parent = hop.attrib['ipaddr']


    # Now the OS detection
    ios = h.find('os')
    #print os.__dict__
    cls = ios.findall('osclass')
    for c in cls:
        #print "Class", c.__dict__
        family = c.attrib['osfamily']
        accuracy = c.attrib['accuracy']
        if 'osgen' in c.attrib:
            osgen = c.attrib['osgen']
        else:
            osgen = None
        #print "Type:", family, osgen, accuracy
        dh.add_os_possibility(family, osgen, accuracy)
    # Ok we can compute our OS now :)
    dh.compute_os()


    # Now the ports :)
    allports = h.findall('ports')
    for ap in allports:
        ports = ap.findall('port')
        for p in ports:
            #print "Port", p.__dict__
            p_id = p.attrib['portid']
            s = p.find('state')
            #print s.__dict__
            state = s.attrib['state']
            if state == 'open':
                dh.open_ports.append(int(p_id))

    print dh.__dict__
    all_hosts.append(dh)
    print "\n\n"
    


for h in all_hosts:
    name = h.get_name()
    if not name:
        continue
    
    print "Doing name", name
    path = os.path.join(output_dir, name+'.discover')
    print "Want path", path
    f = open(path, 'wb')
    cPickle.dump(h, f)
    f.close()

    # And generate the configuration too
    c = ConfigurationManager(h, cfg_output_dir)
    c.fill_system_conf()
    c.fill_ports_services()
    c.write_host_configuration()
    c.write_services_configuration()
    print c.__dict__
    
