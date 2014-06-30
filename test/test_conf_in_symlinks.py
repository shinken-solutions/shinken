#!/usr/bin/env python
# Copyright (C) 2009-2010:
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
import sys
from shinken_test import *


class TestConfigWithSymlinks(ShinkenTest):

    def setUp(self):
        if os.name == 'nt':
            return
        self.setup_with_file('etc/shinken_conf_in_symlinks.cfg')

    def test_symlinks(self):
        if os.name == 'nt':
            return
        if sys.version_info < (2 , 6):
            print "************* WARNING********"*200
            print "On python 2.4 and 2.5, the symlinks following is NOT managed"
            return
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_HIDDEN")
        self.assert_(svc is not None)


if __name__ == '__main__':
    unittest.main()
