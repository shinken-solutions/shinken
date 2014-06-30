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

from shinken_test import *


class TestPackHashMemory(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_pack_hash_memory.cfg')

    def setUp2(self):
        self.setup_with_file('etc/shinken_pack_hash_memory2.cfg')

    def test_pack_hash_memory(self):
        packs = {0: set(), 1: set()}
        for h in self.sched.hosts:
            print 'First pass: ', h.get_name(), h.pack_id, '\n'
            packs[h.pack_id].add(h)

        nb_same = 0

        # Reset IDs
        SchedulerLink.id = 0

        self.setUp()
        for h in self.sched.hosts:
            same_pack = h.get_name() in [i.get_name() for i in packs[h.pack_id]]
            print 'Is in the same pack??', h.get_name(), h.pack_id, ':', same_pack
            if same_pack:
                nb_same += 1

        # Should have nearly all in the same pack
        self.assert_(nb_same >= 100)
        print 'Total same', nb_same


if __name__ == '__main__':
    unittest.main()
