#!/usr/bin/env python
# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can memcachetribute it and/or modify
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
import sys

from shinken_test import unittest, ShinkenTest
try:
    from nose.exc import SkipTest as SkipTest
except ImportError:
    SkipTest = None

if not sys.version_info > (2, 5):
    if SkipTest:
        raise SkipTest("bah, i am 2.4.x")
    else:
        sys.exit(0)

from shinken.log import logger
from shinken.objects.module import Module
from shinken.modules import passwd_ui
from shinken.modules.passwd_ui import get_instance


if sys.version_info > (2, 5):
    modconf = Module()
    modconf.module_name = "PasswdUI"
    modconf.module_type = passwd_ui.properties['type']
    modconf.properties = passwd_ui.properties.copy()


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_memcache_retention(self):
        print self.conf.modules
        # get our modules
        modconf.passwd = 'libexec/htpasswd.users'
        mod = passwd_ui.get_instance(modconf)

        sl = get_instance(mod)
        print "Instance", sl
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()
        l = logger

        # Now call the real stuff :)
        r = sl.check_auth('toto', 'titi')
        print "RES", r
        self.assert_(not r)

        r = sl.check_auth('admin', 'foobar')
        print "RES", r
        self.assert_(r)


if __name__ == '__main__':
    if sys.version_info > (2, 5):
        unittest.main()
