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


class TestMissingObjectValue(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_missing_object_value.cfg')

    def test_missing_object_value(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #

        print "Get the hosts and services"
        now = time.time()
        host = self.conf.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.conf.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.conf.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        # The service is mising a value for active_check_enabled, it's an error.
        self.assertEqual(False, svc.is_correct())


if __name__ == '__main__':
    unittest.main()
