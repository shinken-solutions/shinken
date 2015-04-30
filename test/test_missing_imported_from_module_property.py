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

import os
import time

from shinken_test import (
    ShinkenTest, time_hacker, unittest
)

from shinken.modulesmanager import ModulesManager
from shinken.objects.module import Module
from shinken.log import logger

modules_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'module_missing_imported_from_module_property')


class TestMissingimportedFrom(ShinkenTest):

    def setUp(self):
        #logger.setLevel('DEBUG')
        self.setup_with_file('etc/shinken_missing_imported_from_module_property.cfg')

    # we are loading a module (dummy_arbiter) that is givving objects WITHOUT
    # setting imported_from. One host got a warning, and this can crash without the imported_from setting
    # in the arbiterdaemon part.
    def test_missing_imported_from(self):
        self.assertTrue(self.sched.conf.is_correct)
    


if __name__ == '__main__':
    unittest.main()
