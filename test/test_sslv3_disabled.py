#!/usr/bin/env python
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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

#
# This test checks that sslv3 is disabled when SSL is used with a cherrypy backend to secure against the Poodle vulnerability (https://poodlebleed.com)

import subprocess
from time import sleep

import httplib
import ssl
try:
    import OpenSSL
except ImportError:
    OpenSSL = None
from shinken_test import *

import shinken.log as shinken_log

from shinken.daemons.schedulerdaemon import Shinken
from shinken.daemons.arbiterdaemon import Arbiter

daemons_config = {
    Shinken:      "etc/test_sslv3_disabled/schedulerd.ini",
    Arbiter:    ["etc/test_sslv3_disabled/shinken.cfg"]
}


class testSchedulerInit(ShinkenTest):
    def setUp(self):
        time_hacker.set_real_time()

    def create_daemon(self):
        cls = Shinken
        return cls(daemons_config[cls], False, True, False, None, '')
    @unittest.skipIf(OpenSSL is None, "Test requires OpenSSL")
    def test_scheduler_init(self):

        shinken_log.local_log = None  # otherwise get some "trashs" logs..
        d = self.create_daemon()

        d.load_config_file()

        d.http_backend = 'cherrypy'
        d.do_daemon_init_and_start(fake=True)
        d.load_modules_manager()

        # Launch an arbiter so that the scheduler get a conf and init
        subprocess.Popen(["../bin/shinken-arbiter.py", "-c", daemons_config[Arbiter][0], "-d"])
        if not hasattr(ssl, 'SSLContext'):
            print 'BAD ssl version for testing, bailing out'
            return
        ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
        ctx.check_hostname=False
        ctx.verify_mode=ssl.CERT_NONE
        self.conn = httplib.HTTPSConnection("localhost:9998",context=ctx)
        self.assertRaises(ssl.SSLError,self.conn.connect)
        try:
            self.conn.connect()
        except ssl.SSLError as e:
            assert e.reason == 'SSLV3_ALERT_HANDSHAKE_FAILURE'
        sleep(2)
        pid = int(file("tmp/arbiterd.pid").read())
        print ("KILLING %d" % pid)*50
        os.kill(int(file("tmp/arbiterd.pid").read()), 2)
        d.do_stop()


if __name__ == '__main__':
    unittest.main()
