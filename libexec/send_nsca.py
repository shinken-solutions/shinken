#!/usr/bin/env python
#
# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Hanesse Olivier, olivier.hanesse@gmail.com
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

import sys
import optparse

try:
    import pynsca
    from pynsca import NSCANotifier
except ImportError:
    raise SystemExit("Error: you need the pynsca module for this script")

VERSION = '0.1'


def main(hostname, port, encryption, password):
    notif = NSCANotifier(hostname, port, encryption, password)

    for line in sys.stdin.readlines():
        line = line.rstrip()
        if not line:
            continue
        notif = line.split(opts.delimiter)
        if len(notif) == 3:
            # only host, rc, output
            notif.insert(1, '')  # insert service
        # line consists of host, service, rc, output
        assert len(notif) == 4
        notif.svc_result(*notif)


if __name__ == "__main__":
    parser = optparse.OptionParser(
                      version="Python NSCA client version %s" % VERSION)
    parser.add_option("-H", "--hostname", default='localhost',
                      help="NSCA server IP (default: %default)")
    parser.add_option("-P", "--port", type="int", default='5667',
                      help="NSCA server port (default: %default)")
    parser.add_option("-e", "--encryption", default='1',
                      help=("Encryption mode used by NSCA server "
                            "(default: %default)"))
    parser.add_option("-p", "--password", default='helloworld',
                      help=("Password for encryption, should be the same as "
                            "NSCA server (default: %default)"))
    parser.add_option("-d", "--delimiter", default='\t',
                      help="Argument delimiter (defaults to the tab-character)")

    opts, args = parser.parse_args()

    if args:
        parser.error("does not take any positional arguments")

    main(opts.hostname, opts.port, opts.encryption, opts.password)
