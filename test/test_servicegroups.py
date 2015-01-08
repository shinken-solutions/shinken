#!/usr/bin/env python
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

import copy
from shinken_test import *


class TestServicegroup(ShinkenTest):
    def setUp(self):
        self.setup_with_file("etc/shinken_servicegroups_generated.cfg")


    def test_servicegroup(self):
        self.assertEqual(True, self.conf.conf_is_correct)
        sgs = []
        for name in ["MYSVCGP", "MYSVCGP2", "MYSVCGP3", "MYSVCGP4"]:
            sg = self.sched.servicegroups.find_by_name(name)
            sgs.append(sg)
            self.assertIsNot(sg, None)

        svc3 = self.sched.services.find_srv_by_name_and_hostname("fake host", "fake svc3")
        svc4 = self.sched.services.find_srv_by_name_and_hostname("fake host", "fake svc4")
        self.assertIn(svc3, sgs[0].members)
        self.assertIn(svc3, sgs[1].members)
        self.assertIn(svc4, sgs[2].members)
        self.assertIn(svc4, sgs[3].members)

        self.assertIn(sgs[0].get_name(), [sg.get_name() for sg in svc3.servicegroups])
        self.assertIn(sgs[1].get_name(), [sg.get_name() for sg in svc3.servicegroups])
        self.assertIn(sgs[2].get_name(), [sg.get_name() for sg in svc4.servicegroups])
        self.assertIn(sgs[3].get_name(), [sg.get_name() for sg in svc4.servicegroups])


if __name__ == '__main__':
    unittest.main()
