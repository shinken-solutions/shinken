#!/usr/bin/env python
#
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

"""
Test module PasswdUI.
"""

import sys

from shinken_test import unittest, ShinkenTest
try:
    from nose.exc import SkipTest
except ImportError:
    SkipTest = None

if not sys.version_info > (2, 5):
    if SkipTest:
        raise SkipTest("bah, i am 2.4.x")
    else:
        raise SystemExit(0)

from shinken.objects.module import Module
from shinken.modules import passwd_ui
from shinken.modules.passwd_ui import get_instance
from shinken.log import logger


if sys.version_info > (2, 5):
    modconf = Module()
    modconf.module_name = "PasswdUI"
    modconf.module_type = passwd_ui.properties['type']
    modconf.properties = passwd_ui.properties.copy()


class TestPasswdUI(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_check_auth(self):
        # get our modules
        modconf.passwd = 'libexec/htpasswd.users'
        mod = passwd_ui.get_instance(modconf)

        sl = get_instance(mod)
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()

        # Now call the real stuff :)
        r = sl.check_auth('toto', 'titi')
        self.assertFalse(r)

        r = sl.check_auth('admin', 'foobar')
        self.assertTrue(r)

        r = sl.check_auth('apache', 'toto')
        self.assertTrue(r)

        r = sl.check_auth('apachemd5', '0123456789ABCDE')
        self.assertTrue(r)

if __name__ == '__main__':
    if sys.version_info > (2, 5):
        unittest.main()
