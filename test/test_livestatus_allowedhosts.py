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

from shinken_test import *
import time
import random
import socket
import threading
import shutil

from mock_livestatus import mock_livestatus_handle_request


from shinken.objects.module import Module
from shinken.comment import Comment
from test_livestatus import TestConfig

sys.setcheckinterval(10000)

@mock_livestatus_handle_request
class TestConfigAuth(TestConfig):
    def setUp(self):
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))

    def tearDown(self):
        # stop thread
        self.livestatus_broker.interrupted = True
        self.lql_thread.join()
        # /

        self.stop_nagios()
        #self.livestatus_broker.db.commit()
        #self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs + "-journal"):
            os.remove(self.livelogs + "-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None

    def init_livestatus(self, conf):
        super(TestConfigAuth, self).init_livestatus(conf)
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_0")
        host.__class__.use_aggressive_host_checking = 1

        # NOTE: function is blocking, so must be launched in a thread
        #self.livestatus_broker.do_main()
        self.lql_thread = threading.Thread(None, self.livestatus_broker.manage_lql_thread, 'lqlthread')
        self.lql_thread.start()
        # wait for thread to init
        original_time_sleep(3)

    def query_livestatus(self, ip, port, data):
        print "Query livestatus on %s:%d" % (ip, port)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ip, port))
            s.send(data)

            res = s.recv(16)
        except Exception, e:
            print "Query livestatus failed: ", e
            return False
        else:
            s.close()

        print "received:", res
        # when connection refused, livestatus server returns empty string
        return len(res) > 0

    def test_01_default(self):
        modconf = Module({'module_name': 'LiveStatus',
            'module_type': 'livestatus',
            'port': str(random.randint(50000, 65534)),
            'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
            'host': '127.0.0.1',
            'name': 'test',
            'modules': ''
        })
        self.init_livestatus(modconf)

        # test livestatus connection
        self.assertTrue(self.query_livestatus(modconf.host, int(modconf.port), "GET hosts\n\n"))

    def test_02_allow_localhost(self):
        modconf = Module({'module_name': 'LiveStatus',
            'module_type': 'livestatus',
            'port': str(random.randint(50000, 65534)),
            'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
            'host': '127.0.0.1',
            'name': 'test',
            'modules': '',
            'allowed_hosts': '127.0.0.1'
        })
        self.init_livestatus(modconf)

        # test livestatus connection
        self.assertTrue(self.query_livestatus(modconf.host, int(modconf.port), "GET hosts\n\n"))

    def test_03_dont_allow_localhost(self):
        modconf = Module({'module_name': 'LiveStatus',
            'module_type': 'livestatus',
            'port': str(random.randint(50000, 65534)),
            'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
            'host': '127.0.0.1',
            'name': 'test',
            'modules': '',
            'allowed_hosts': '192.168.0.1'
        })
        self.init_livestatus(modconf)

        # test livestatus connection
        self.assertFalse(self.query_livestatus(modconf.host, int(modconf.port), "GET hosts\n\n"))

if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig)
    #unittest.TextTestRunner(verbosity=2).run(allsuite)
