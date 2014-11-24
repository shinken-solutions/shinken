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
# This file is used to test reading and processing of config files
#

from shinken_test import *


class TestSrvTplOnHostTpl(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_service_tpl_on_host_tpl.cfg')

    # Look is a service template apply on a host one will
    # make hosts that inherit from it got such service
    def test_service_tpl_on_host_tpl(self):
        # In fact the whole thing will be to have the service defined :)
        host = self.sched.hosts.find_by_name("test_host_0")
        print "All the test_host_0 services"
        for s in host.services:
            print s.get_dbg_name()

        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Service_Template_Description")
        self.assertIsNot(svc, None)

    # And look for multy layer template too. Like a service is apply on
    # layer1, that use layer2. And srv is apply on layer2
    def test_service_tpl_on_host_tpl_n_layers(self):

        host = self.sched.hosts.find_by_name("host_multi_layers")
        print "All the test_host_0 services"
        for s in host.services:
            print s.get_dbg_name()

        svc = self.sched.services.find_srv_by_name_and_hostname("host_multi_layers", "srv_multi_layer")
        self.assertIsNot(svc, None)

    # And look for multy layer template too. Like a service is apply on
    # layer1, that use layer2. And srv is apply on layer2
    def test_complex_expr(self):
        h_linux = self.sched.hosts.find_by_name("host_linux_http")
        print "All the host_linux_http services"
        for s in h_linux.services:
            print s.get_dbg_name()

        # The linux and http service should exist on the linux host
        svc = self.sched.services.find_srv_by_name_and_hostname("host_linux_http", "http_AND_linux")
        self.assertIsNot(svc, None)

        # But not on the windows one
        h_windows = self.sched.hosts.find_by_name("host_windows_http")
        print "All the host_windows_http services"
        for s in h_windows.services:
            print s.get_dbg_name()

        # The linux and http service should exist on the linux host
        svc = self.sched.services.find_srv_by_name_and_hostname("host_windows_http", "http_AND_linux")
        self.assertIs(None, svc)

        # The http_OR_linux should be every where
        svc = self.sched.services.find_srv_by_name_and_hostname("host_linux_http", "http_OR_linux")
        self.assertIsNot(svc, None)
        svc = self.sched.services.find_srv_by_name_and_hostname("host_windows_http", "http_OR_linux")
        self.assertIsNot(svc, None)

        # The http_BUT_NOT_linux should be in the windows host only
        svc = self.sched.services.find_srv_by_name_and_hostname("host_linux_http", "http_BUT_NOT_linux")
        self.assertIs(None, svc)
        svc = self.sched.services.find_srv_by_name_and_hostname("host_windows_http", "http_BUT_NOT_linux")
        self.assertIsNot(svc, None)

        # The http_ALL_BUT_NOT_linux should be in the windows host only
        svc = self.sched.services.find_srv_by_name_and_hostname("host_linux_http", "http_ALL_BUT_NOT_linux")
        self.assertIs(None, svc)
        svc = self.sched.services.find_srv_by_name_and_hostname("host_windows_http", "http_ALL_BUT_NOT_linux")
        self.assertIsNot(svc, None)

        # The http_ALL_BUT_NOT_linux_AND_EVEN_LINUX should be every where :)
        # yes, it's a stupid example, but at least it help to test :)
        svc = self.sched.services.find_srv_by_name_and_hostname("host_linux_http", "http_ALL_BUT_NOT_linux_AND_EVEN_LINUX")
        self.assertIsNot(svc, None)
        svc = self.sched.services.find_srv_by_name_and_hostname("host_windows_http", "http_ALL_BUT_NOT_linux_AND_EVEN_LINUX")
        self.assertIsNot(svc, None)





if __name__ == '__main__':
    unittest.main()
