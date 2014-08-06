#!/usr/bin/env python
# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
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

# sudo nmap 192.168.0.1 --min-rate 1000 --max-retries 0 -sU -sT -T4 -O --traceroute -oX toto.xml

import optparse
import sys
import os
import tempfile
import subprocess

try:
    # xml.etree.ElementTree is new in Python 2.5
    from xml.etree.ElementTree import ElementTree
except ImportError:
    sys.exit("This script needs the Python ElementTree module. Please install it")

VERSION = '0.1.1'
# Fred : command launched depending on os detection
if os.name != 'nt': 
    DEFAULT_CMD = "sudo nmap %s -sU -sT --min-rate %d --max-retries %d -T4 -O -oX %s"
else:
    DEFAULT_CMD = "nmap %s -sU -sT --min-rate %d --max-retries %d -T4 -O -oX %s"
    
parser = optparse.OptionParser(
    "%prog [options] -t nmap scanning targets",
    version="%prog " + VERSION)

parser.add_option('-t', '--targets', dest="targets",
                  help="NMap scanning targets.")
parser.add_option('-v', '--verbose', dest="verbose", action='store_true',
                  help="Verbose output.")
parser.add_option('--min-rate', dest="min_rate",
                  help="Min rate option for nmap (number of parallel packets to launch. By default 1000)")
parser.add_option('--max-retries', dest="max_retries",
                  help="Max retries option for nmap (number of packet send retry). By default 0 - no retry -)")
parser.add_option('-s', '--simulate', dest="simulate",
                  help="Simulate a launch by reading an nmap XML output instead of launching a new one.")

targets = []
opts, args = parser.parse_args()

if not opts.simulate:
    simulate = None
else:
    simulate = opts.simulate


if not opts.simulate and not opts.targets:
    parser.error("Requires at least one nmap target for scanning (option -t/--targets)")
else:
    targets.append(opts.targets)

min_rate = 1000
if opts.min_rate:
    min_rate = int(opts.min_rate)

max_retries = 0
if opts.max_retries:
    max_retries = int(opts.max_retries)


if not opts.verbose:
    verbose = False
else:
    verbose = True

if args:
    targets.extend(args)

print "Got our target", targets


def debug(txt):
    if verbose:
        print txt


# Says if a host is up or not
def is_up(h):
    status = h.find('status')
    state = status.attrib['state']
    return state == 'up'


class DetectedHost:
    def __init__(self):
        self.ip = ''
        self.mac_vendor = ''
        self.host_name = ''

        self.os_possibilities = []
        self.os = ('', '')
        self.open_ports = []

        self.parent = ''

    # Keep the first name we've got
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

    # We look for the host VMWare
    def is_vmware_esx(self):
        # If it's not a virtual machine bail out
        if self.mac_vendor != 'VMware':
            return False
        # If we got all theses ports, we are quite ok for
        # a VMWare host
        needed_ports = [22, 80, 443, 902, 903, 5989]
        for p in needed_ports:
            if p not in self.open_ports:
                # find one missing port, not a VMWare host
                return False
        # Ok all ports are found, we are a ESX :)
        return True

    # Says if we are a virtual machine or not
    def is_vmware_vm(self):
        # special case: the esx host itself
        if self.is_vmware_esx():
            return False
        # Else, look at the mac vendor
        return self.mac_vendor == 'VMware'

    # Fill the different os possibilities
    def add_os_possibility(self, os, osgen, accuracy, os_type, vendor):
        self.os_possibilities.append((os, osgen, accuracy, os_type, vendor))

    # We search if our potential parent is present in the
    # other detected hosts. If so, set it as my parent
    def look_for_parent(self, all_hosts):
        self.parents = []
        parent = self.parent
        debug("Look for my parent %s -> %s" % (self.get_name(), parent))
        # Ok, we didn't find any parent
        # we bail out
        if parent == '':
            return
        for h in all_hosts:
            debug("Is it you? %s" % h.get_name())
            if h.get_name() == parent:
                debug("Houray, we find our parent %s -> %s" % (self.get_name(), h.get_name()))
                self.parents.append(h.get_name())

    # Look at ours oses and see which one is the better
    def compute_os(self):
        self.os_name = 'Unknown OS'
        self.os_version = 'Unknown Version'
        self.os_type = 'Unknown Type'
        self.os_vendor = 'Unknown Vendor'

        # Bailout if we got no os :(
        if len(self.os_possibilities) == 0:
            return

        max_accuracy = 0
        for (os, osgen, accuracy, os_type, vendor) in self.os_possibilities:
            if accuracy > max_accuracy:
                max_accuracy = accuracy

        # now get the entry with the max value, the first one
        for (os, osgen, accuracy, os_type, vendor) in self.os_possibilities:
            print "Can be", (os, osgen, accuracy, os_type, vendor)
            if accuracy == max_accuracy:
                self.os = (os, osgen, os_type, vendor)
                break

        print "Will dump", self.os

        # Ok, unknown os... not good
        if self.os == ('', '', '', ''):
            return

        self.os_name = self.os[0].lower()
        self.os_version = self.os[1].lower()
        self.os_type = self.os[2].lower()
        self.os_vendor = self.os[3].lower()

    # Return the string of the 'discovery' items
    def get_discovery_output(self):
        r = []
        r.append('%s::isup=1' % self.get_name())
        r.append(self.get_discovery_system())
        r.append(self.get_discovery_macvendor())
        op = self.get_discovery_ports()
        if op != '':
            r.append(op)
        par = self.get_discovery_parents()
        if par != '':
            r.append(par)
        fqdn = self.get_dicovery_fqdn()
        if fqdn != '':
            r.append(fqdn)
        ip = self.get_discovery_ip()
        if ip != '':
            r.append(ip)
        return r

    # for system output
    def get_discovery_system(self):
        r = '%s::os=%s' % (self.get_name(), self.os_name) + '\n'
        r += '%s::osversion=%s' % (self.get_name(), self.os_version) + '\n'
        r += '%s::ostype=%s' % (self.get_name(), self.os_type) + '\n'
        r += '%s::osvendor=%s' % (self.get_name(), self.os_vendor)
        return r

    def get_discovery_macvendor(self):
        return '%s::macvendor=%s' % (self.get_name(), self.mac_vendor)

    def get_discovery_ports(self):
        if self.open_ports == []:
            return ''
        return '%s::openports=%s' % (self.get_name(), ','.join([str(p) for p in self.open_ports]))

    def get_discovery_parents(self):
        if self.parents == []:
            return ''
        return '%s::parents=%s' % (self.get_name(), ','.join(self.parents))

    def get_dicovery_fqdn(self):
        if self.host_name == '':
            return ''
        return '%s::fqdn=%s' % (self.get_name(), self.host_name)

    def get_discovery_ip(self):
        if self.ip == '':
            return ''
        return '%s::ip=%s' % (self.get_name(), self.ip)


if not simulate:
    (_, tmppath) = tempfile.mkstemp()

    print "propose a tmppath", tmppath

    # Fred : command launched depending on os detection
    # cmd = "nmap %s -sU -sT --min-rate %d --max-retries %d -T4 -O -oX %s" % (' '.join(targets), min_rate, max_retries, tmppath)
    cmd = DEFAULT_CMD % (' '.join(targets), min_rate, max_retries, tmppath)
    print "Launching command,", cmd
    try:
        nmap_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            close_fds=False, shell=True)
    except OSError, exp:
        print "Debug: Error in launching command:", cmd, exp
        sys.exit(2)

    print "Try to communicate"
    (stdoutdata, stderrdata) = nmap_process.communicate()

    if nmap_process.returncode != 0:
        print "Error: the nmap return an error: '%s'" % stderrdata
        sys.exit(2)

    # Fred : no need to print nmap result catched ...
    # print "Got it", (stdoutdata, stderrdata)
    print "Got it !"

    xml_input = tmppath
else:  # simulate mode
    xml_input = simulate

tree = ElementTree()
try:
    tree.parse(xml_input)
except IOError, exp:
    print "Error opening file '%s': %s" % (xml_input, exp)
    sys.exit(2)

hosts = tree.findall('host')
debug("Number of hosts: %d" % len(hosts))

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
                dh.mac_vendor = addr.attrib['vendor'].lower()

    # Now we've got the hostnames
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
                #We search for the direct father
                if ttl == distance-1:
                    #print ttl
                    #print "Super hop", hop.__dict__
                    # Get the host name if possible, if not
                    # take the IP
                    if 'host' in hop.attrib:
                        dh.parent = hop.attrib['host']
                    else:
                        dh.parent = hop.attrib['ipaddr']

    # Now the OS detection
    ios = h.find('os')
    # Fred : if no OS detected by nmap (localhost on Windows does not detect OS !)
    if ios:
        #print os.__dict__
        cls = ios.findall('osclass')
	# if no osclass found, try bellow the osmatch element (nmap recent versions)
	if len(cls) == 0:
		cls = ios.find('osmatch').findall('osclass')

        for c in cls:
            #print "Class", c.__dict__
            family = c.attrib['osfamily']
            accuracy = c.attrib['accuracy']
            osgen = c.attrib.get('osgen', '')
            os_type = c.attrib.get('type', '')
            vendor = c.attrib.get('vendor', '')
            #print "Type:", family, osgen, accuracy
            dh.add_os_possibility(family, osgen, accuracy, os_type, vendor)
        # Ok we can compute our OS now :)
        dh.compute_os()
    else:
        debug(" No OS detected !")
        family = 'Unknown'
        accuracy = 'Unknown'
        osgen = 'Unknown'
        os_type = 'Unknown'
        vendor = 'Unknown'
        #print "Type:", family, osgen, accuracy
        dh.add_os_possibility(family, osgen, accuracy, os_type, vendor)
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

    #print dh.__dict__
    all_hosts.append(dh)
    #print "\n\n"



for h in all_hosts:
    name = h.get_name()
    if not name:
        continue

    debug("Doing name %s" % name)
    #path = os.path.join(output_dir, name+'.discover')
    #print "Want path", path
    #f = open(path, 'wb')
    #cPickle.dump(h, f)
    #f.close()
    debug(str(h.__dict__))
    # And generate the configuration too
    h.look_for_parent(all_hosts)
    #c.fill_system_conf()
    #c.fill_ports_services()
    #c.fill_system_services()
    #c.write_host_configuration()
    #print "Host config", c.get_cfg_for_host()
    #c.write_services_configuration()
    #print "Service config"
    #print c.get_cfg_for_services()
    #print c.__dict__
    print '\n'.join(h.get_discovery_output())
    #print "\n\n\n"


# Try to remove the temppath
try:
    os.unlink(tmppath)
except Exception:
    pass
