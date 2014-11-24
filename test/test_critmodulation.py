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


class TestCritMod(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_critmodulation.cfg')

    def test_critmodulation_def(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get our criticity modulation"
        cm = self.sched.conf.businessimpactmodulations.find_by_name('CritMod')
        self.assertIsNot(cm, None)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        print svc.business_impact_modulations
        self.assertIn(cm, svc.business_impact_modulations)



if __name__ == '__main__':
    unittest.main()
