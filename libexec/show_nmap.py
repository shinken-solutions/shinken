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
opts, args = parser.parse_args()

if not opts.xml_input:
    parser.error("Requires one nmap xml output file (option -x/--xml-input")
if not opts.output_dir:
    parser.error("Requires one output directory (option -o/--dir-output")
if args:
    parser.error("Does not accept any argument.")


# Say if a host is up or not
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
        hops = trace.findall('hop')
        #for hop in hops:
        #    print hop.__dict__


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
