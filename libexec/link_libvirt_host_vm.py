#!/usr/bin/env python
# Copyright (C) 2012:
#    Thibault Cohen, thibault.cohen@savoirfairelinux.com
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

"""
This program use libvirt to put host parent-child relations in a json one so it
can be loaded in hot_dependencies_arbiter module
"""

import timeit
import os
import sys
import optparse
import signal

import libvirt

class TimeoutException(Exception): 
    pass 

# Try to load json (2.5 and higer) or simplejson if failed (python2.4)
try:
    import json
except ImportError:
    # For old Python version, load simple json
    try:
        import simplejson as json
    except ImportError:
        raise SystemExit("Error: you need the json or simplejson module "
                         "for this script")

VERSION = '0.1'


def main(uris, output_file, ignore):

    def timeout_handler(signum, frame):
        raise TimeoutException()

    ignored_doms = []
    r = []

    if ignore:
        ignored_doms = ignore.split(",")
        
    for uri in uris.split(","):
        signal.signal(signal.SIGALRM, timeout_handler) 
        signal.alarm(10) # triger alarm in 10 seconds
        try:
            conn = libvirt.openReadOnly(uri)
        except libvirt.libvirtError, e:
            print "Libvirt connection error: `%s'" % e.message.replace("\r", "")
            print "Let's try next URI"
            continue
        except TimeoutException:
            print "Libvirt Request timeout"
            print "Let's try next URI"
            continue
        except Exception, e:
            print "Unknown Error: %s" % str(e)
            print "Let's try next URI..."
            continue
            
        hypervisor = conn.getHostname()
        # List all VM (stopped and started)
        for dom in [conn.lookupByName(name) for name in conn.listDefinedDomains()]\
                        + [conn.lookupByID(vmid) for vmid in conn.listDomainsID()]:
            domain_name = dom.name()
            if domain_name in ignored_doms:
                continue
            v = (('host', hypervisor.strip()), ('host', domain_name.strip()))
            r.append(v)

    r = set(r)
    r = list(r)
    jsonmappingfile = open(output_file, 'w')
    try:
        json.dump(r, jsonmappingfile)
    finally:
        jsonmappingfile.close()


if __name__ == "__main__":
    parser = optparse.OptionParser(
        version="Shinken libvirt mapping to json mapping %s" % VERSION)
    parser.add_option("-o", "--output", dest='output_file',
                      default='/tmp/libvirt_mapping_file.json',
                      help="Path of the generated json mapping file.\n"
                      "Default: /tmp/libvirt_mapping_file.json")
    parser.add_option("-u", "--uris", dest='uris',
                      help="Libvirt URIS separated by comma")
    parser.add_option("-i", "--ignore", dest='ignore',
                      default=None,
                      help="Ignore hosts (separated by comma)\n"
                           "Default: None")

    opts, args = parser.parse_args()
    if args:
        parser.error("does not take any positional arguments")

    if opts.uris is None:
        print "At least one URI is mandatory"
        sys.exit(2)

    main(**vars(opts))
