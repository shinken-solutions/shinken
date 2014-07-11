#!/usr/bin/env python
# Copyright (C) 2009-2010:
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
        self.assert_(self.conf.conf_is_correct == True)
        sgs = []
        for name in ["MYSVCGP", "MYSVCGP2", "MYSVCGP3", "MYSVCGP4"]:
            sg = self.sched.servicegroups.find_by_name(name)
            sgs.append(sg)
            self.assert_(sg is not None)

        svc3 = self.sched.services.find_srv_by_name_and_hostname("fake host", "fake svc3")
        svc4 = self.sched.services.find_srv_by_name_and_hostname("fake host", "fake svc4")
        self.assert_(svc3 in sgs[0].members)
        self.assert_(svc3 in sgs[1].members)
        self.assert_(svc4 in sgs[2].members)
        self.assert_(svc4 in sgs[3].members)

        self.assert_(sgs[0] in svc3.servicegroups)
        self.assert_(sgs[1] in svc3.servicegroups)
        self.assert_(sgs[2] in svc4.servicegroups)
        self.assert_(sgs[3] in svc4.servicegroups)


if __name__ == '__main__':
    unittest.main()
