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

VERSION = '0.2'


def main(input_file, output_file, type):
    # Check if input_file is newer than output_file
    if os.path.exists(output_file):
        if os.path.getmtime(output_file) >= os.path.getmtime(input_file):
            print "Nothing to do"
            return True
    r = []
    flatmappingfile = open(input_file)
    try:
        for line in flatmappingfile:
            if line.startswith('#'):
                # this is a comment line, skip it
                continue
            parts = line.split(':')
            if type == 'service' :
                v = (('service', parts[0].strip()), ('service', parts[1].strip()))
            else:
                v = (('host', parts[0].strip()), ('host', parts[1].strip()))
            r.append(v)
    finally:
        flatmappingfile.close()

    jsonmappingfile = open(output_file, 'w')
    try:
        json.dump(r, jsonmappingfile)
    finally:
        jsonmappingfile.close()


if __name__ == "__main__":
    parser = optparse.OptionParser(
        version="Shinken external flat mapping file to json mapping %s" % VERSION)
    parser.add_option("-o", "--output", dest='output_file',
                      default='/tmp/external_mapping_file.json',
                      help="Path of the generated json mapping file.")
    parser.add_option("-i", "--input", dest='input_file',
                      default='/tmp/shinken_flat_mapping',
                      help="Path of the flat mapping input file.")
    parser.add_option("-t", "--type", dest='type',
                      default='host', help='it is a service or host dependency. ( host | service. Default : host)')

    opts, args = parser.parse_args()
    if args:
        parser.error("does not take any positional arguments")

    main(**vars(opts))
