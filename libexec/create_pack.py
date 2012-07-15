#!/usr/bin/env python
#
# Copyright (C) 2009-2011:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

import os
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('pack_name')
parser.add_argument('path')
args = parser.parse_args()

pack_name = args.pack_name
pack_path = os.path.join(args.path, pack_name)


def create_file(f_name, content):
    path = os.path.join(pack_path, f_name)
    if not os.path.exists(path):
        print "Writing file", path
        f = open(path, 'w')
        f.write(content)
        f.close()



if not os.path.exists(pack_path):
    print "Creating", pack_path
    os.mkdir(pack_path)
    os.mkdir(os.path.join(pack_path, 'services'))

# Now the templates.cfg creation
templates = """
define host{
   name            %s
   use             generic-host
   check_command   check_ping
   register        0
}
""" % pack_name

create_file('templates.cfg', templates)

# Now the macros
macros = """
#Uncomment the line and change the name and value
#$SAMPLEMACRO$=value
"""

create_file('macros.cfg', macros)

# Now the sample discovery file
discovery = """
# Sample discovery rule. Uncomment it and edit the filter
define discoveryrule {
       discoveryrule_name       %s
       creation_type            host
       # Sample filter for getting port 80
       #openports                ^80$
       FILTER                   VALUE
       +use                     %s
}
""" % (pack_name, pack_name)

create_file('discovery.cfg', discovery)

# Now the commands
commands = """
# EDIT the command with the real one you want
define command {
       command_name  check_%s
       command_line  $PLUGINSDIR$/check_%s -H $HOSTADDRESS$
}
""" % (pack_name, pack_name)

create_file('commands.cfg', commands)

# And a sample service
service = """
# This is a sample service, please change it!
define service{
   service_description    Sample-%s
   use                    generic-service
   register               0
   host_name              %s
   check_command          check_%s
}
""" % (pack_name, pack_name, pack_name)

create_file(os.path.join('services', 'sample.cfg'), service)
