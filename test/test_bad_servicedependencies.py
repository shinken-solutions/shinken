#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Sebastien Coavoux, s.coavoux@free.fr
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


class TestBadServiceDependencies(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_bad_servicedependencies.cfg')

    def test_bad_conf(self):
        self.assertFalse(self.conf.conf_is_correct)
        self.assert_any_log_match("hostdependencies conf incorrect!!")
        self.assert_any_log_match("servicedependencies conf incorrect!!")
        self.assert_any_log_match("The host object 'fake host'  is part of a circular parent/child chain!")

if __name__ == '__main__':
    unittest.main()