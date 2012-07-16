#!/usr/bin/env python
#
# Copyright (C) 2009-2012:
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

import optparse
import subprocess

VERSION = '1.0'

def p_debug(s):
    if debug:
        print "DEBUG:", s

def get_elements(line):
    elts = line.split('|', 2)
    if len(elts) < 2:
        p_debug("Not a good line: %r" % line)
        return None
    return elts


parser = optparse.OptionParser(
    "%prog [options] -H HOSTADRESS -u DOMAIN\\USER -p PASSWORD",
    version="%prog " + VERSION)

parser.add_option('-H', "--hostname",
                  help="Hostname to scan")
parser.add_option('-u', '--user', default='guest',
                  help="Username to scan with. Default to '%default'")
parser.add_option('-p', '--password', default='',
                  help="Password of your user. Default to ''")
parser.add_option('-d', "--debug", action='store_true',
                  help="Debug mode")

opts, args = parser.parse_args()

if not opts.hostname:
    parser.error("Requires one host to scan (option -H)")

hostname = opts.hostname
user = opts.user
debug = opts.debug
password = opts.password

cred = '%s%%%s' % (user, password)

cmd = ["smbclient", '--user', cred, '--grepable', '-L', hostname]
p_debug("Launching command %s" % cmd)
try:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        close_fds=True)
except OSError, exp:
    print "Error in launching command:", cmd, exp
    raise SystemExit(2)

p_debug("Try to communicate with the subprocess")
(stdoutdata, stderrdata) = process.communicate()

if process.returncode != 0:
    print "Error: the share scanner return an error: '%s'" % (stderrdata + stdoutdata)
    raise SystemExit(2)

disks = []
printers = []

p_debug("Good return" + stdoutdata)


for line in stdoutdata.splitlines():
    elts = get_elements(line.strip())
    # Skip strange lines
    if not elts:
        continue
    typ, sharename, desc = elts
    if typ == 'Printer':
        printers.append(sharename)
    if typ == 'Disk' and not sharename.endswith('$'):
        disks.append(sharename)


if len(disks) > 0:
    print "%s::shares_detected=1" % hostname
    print "%s::_shares=%s" % (hostname, ','.join(disks))

if len(printers) > 0:
    print "%s::printers_detected=1" % hostname
    print "%s::_printers=%s" % (hostname, ','.join(printers))
