#!/usr/bin/env python
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
This program transforms a flat dependency file into a json one so it
can be loaded in hot_dependencies_arbiter module

The input file format is:
  host1 ":" vm1
  host2 ":" vm2
  ...

Spaces around host- and vm-names will be stripped. Lines starting with
a `#` will be ignored.

You can now get a live update of your dependency tree in shinken for
your xen/virtualbox/qemu. All you have to do is finding a way to
modify this flat file when you do a live migration.

For example, you can use a script like this in your crontab::

  dsh -Mc -g mydom0group 'xm list' | \
      awk "/vm-/ { print \$1 }"' > /tmp/shinken_flat_mapping

"""


import os
import sys
import optparse
import shinken.daemons.arbiterdaemon

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

from shinken.arbiterlink import ArbiterLink
from shinken.http_client import HTTPExceptions 
from shinken.log import logger

sat_types = ['arbiter', 'scheduler', 'poller', 'reactionner',
             'receiver', 'broker']

VERSION = '0.2'

class ShinkenAdmin():

    def __init__(self):
        self.arb = None 

    def do_connect(self):
        '''
        Connect to an arbiter daemon
        Syntax: connect [host]:[port]
        Ex: for Connecting to server, port 7770
        > connect server:7770
        Ex: connect to localhost, port 7770
        > connect
        '''
        addr = 'localhost'
        port = '7770'
    
        print "Connection to %s:%s" % (addr, port)
        ArbiterLink.use_ssl = False
        self.arb = ArbiterLink({'arbiter_name': 'arbiter-master', 'address': addr, 'port': port})
        self.arb.fill_default()
        self.arb.pythonize()
        self.arb.update_infos()
        if self.arb.reachable:
            print "Connection OK"
        else:
            sys.exit("Connection to the arbiter get a problem")
        return self.arb
    
    def do_getconf(self, arb):
        '''
        Get the data in the arbiter for a table and some properties
        like hosts  host_name realm
        '''
    
        data = self.arb.get_objects_properties('hosts', ['host_name'])
        print data
        
    #    if data != None:
    #        for l in data:
    #            print ' '.join(['%s' % i for i in l])

    
    def main(self, output_file):
        self.arb = self.do_connect()
        self.do_getconf(self.arb)
    #    jsonmappingfile = open(output_file, 'w')
    #    try:
    #        json.dump(r, jsonmappingfile)
    #    finally:
    #        jsonmappingfile.close()


if __name__ == "__main__":
    parser = optparse.OptionParser(
        version="Shinken service hot dependency according to packs (or custom) definition to json mapping %s" % VERSION)
    parser.add_option("-o", "--output", dest='output_file',
                      default='/tmp/shinken_service_dependency:mapping.json',
                      help="Path of the generated json mapping file.")

    opts, args = parser.parse_args()
    if args:
        parser.error("does not take any positional arguments")

    ShinkenAdmin().main(**vars(opts))
