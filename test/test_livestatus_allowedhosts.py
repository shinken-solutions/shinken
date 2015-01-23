#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Guillaume Bour/Uperto, guillaume.bour@uperto.com
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
# This file is used to test *allowed_hosts* parameter of Livestatus module
#

import sys
import time
import socket
import threading


from mock_livestatus import mock_livestatus_handle_request

from shinken_test import unittest, time_hacker

from shinken.objects.module import Module
from test_livestatus import LiveStatus_Template


sys.setcheckinterval(10000)


@mock_livestatus_handle_request
class TestConfigAuth_Template(LiveStatus_Template):

    _setup_config_file = 'etc/nagios_1r_1h_1s.cfg'

    def setUp(self, dbmodconf=None, raise_on_bad_config=None):
        super(TestConfigAuth_Template, self).setUp(dbmodconf=dbmodconf, raise_on_bad_config=raise_on_bad_config)

    def tearDown(self):
        # stop thread
        self.livestatus_broker.interrupted = True
        self.lql_thread.join()
        # /
        super(TestConfigAuth_Template, self).tearDown()

    def init_livestatus(self, *a, **kw):
        super(TestConfigAuth_Template, self).init_livestatus(*a, **kw)
        # execute the livestatus by starting a dedicated thread to run the manage_lql_thread function:
        self.lql_thread = threading.Thread(target=self.livestatus_broker.manage_lql_thread, name='lqlthread')
        self.lql_thread.start()
        time_hacker.set_real_time()
        t0 = time.time()
        # give some time for the thread to init and creates its listener socket(s) :
        while True:
            if self.livestatus_broker.listeners:
                break # but as soon as listeners is truth(== non-empty), we can continue,
                # the listening thread has created the input socket so we can connect to it.
            elif time.time() - t0 > 10:
                self.livestatus_broker.interrupted = True
                raise RuntimeError('Livestatus listening thread should have created its input socket(s) quite quickly !!')
            time.sleep(0.5)
        time_hacker.set_my_time()

    def query_livestatus(self, data, ip=None, port=None, timeout=60):
        if ip is None:
            ip = self.modconf.host
        if port is None:
            port = self.modconf.port
        port = int(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(timeout)
            s.connect((ip, port))
            s.send(data)
            try:
                s.shutdown(socket.SHUT_WR)
            except socket.error as err:
                print('query_livestatus: shutdown failed: %s ; that might be normal..' % err)
            ret = []
            while True:
                data = s.recv(1024)
                #print("received: %r" % data)
                if not data:
                    return b''.join(ret)
                ret.append(data)
        except Exception as err:
            print('query_livestatus: got an exception: %s')
        finally:
            s.close()



class TestConfigAuth(TestConfigAuth_Template):

    def test_01_default(self):
        # test livestatus connection
        self.assertTrue(self.query_livestatus("GET hosts\n\n"))

    def test_02_allow_localhost(self):
        # test livestatus connection
        self.assertTrue(self.query_livestatus("GET hosts\n\n"))



class TestConfigAuth_DontAllow(TestConfigAuth_Template):

    def init_livestatus(self, *a, **kw):
        modconf = Module({'module_name': 'LiveStatus',
            'module_type': 'livestatus',
            'port': str(self.get_free_port()),
            'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
            'host': '127.0.0.1',
            'name': 'test',
            'modules': '',
            'allowed_hosts': '127.0.0.2' # must be different than 'host'
        })
        super(TestConfigAuth_DontAllow, self).init_livestatus(*a, modconf=modconf, **kw)

    def test_dont_allow_host(self):
        # test livestatus connection
        self.assertFalse(self.query_livestatus("GET hosts\n\n"))


if __name__ == '__main__':

    command = """unittest.main()"""
    unittest.main()
