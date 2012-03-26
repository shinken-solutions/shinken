#!/usr/bin/env python
#Copyright (C) 2009-2012 :
#    Gabes Jean, naparuba@gmail.com
#    Hanesse Olivier, olivier.hanesse@gmail.com
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

import sys
import optparse

try:
    from pynsca import NSCANotifier
    import pynsca
except ImportError:
    sys.exit("Error : you need the pynsca module for this script")

VERSION = '0.1'


def main(hostname, port, encryption, password, to_send):
    notif = NSCANotifier(hostname, port, encryption, password)
    for ts in to_send:
        notif.svc_result(ts[0], ts[1], ts[2], ts[3])

if __name__ == "__main__":
    parser = optparse.OptionParser(
                      version="Python NSCA client version %s" % VERSION)
    parser.add_option("-H", "--hostname", dest='hostname',
                      default='localhost',
                      help="NSCA server IP (default: %default)")
    parser.add_option("-P", "--port", type="int", default='5667',
                      help="NSCA server port (default: %default)")
    parser.add_option("-e", "--encryption", default='1',
                      help="Encryption mode used by NSCA server (default %default)")
    parser.add_option("-p", "--password", default='helloworld',
                      help="Password for encryption, should be the same as NSCA server (default: %default)")
    parser.add_option("-d", "--delimiter", default='\t',
                      help="Argument delimiter (defaults: %default)")

    opts, args = parser.parse_args()

    if args:
        parser.error("does not take any positional arguments")

    notif_to_send = []

    for line in sys.stdin.readlines():
        line = line.rstrip()
        if not len(line) == 0:
            if line.count(opts.delimiter) == 2:
                notif_svc = ''
                notif_host, notif_rc, notif_output = line.split(opts.delimiter)
            else:
                notif_host, notif_svc, notif_rc, notif_output = line.split(opts.delimiter)
            notif_to_send.append([notif_host, notif_svc, notif_rc, notif_output])

#   print notif_to_send
    main(opts.hostname, opts.port, opts.encryption, opts.password, notif_to_send)
