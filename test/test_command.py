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

from shinken.commandcall import CommandCall
from shinken.objects import Command, Commands


class TestCommand(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_command(self):
        t = {'command_name': 'check_command_test',
             'command_line': '/tmp/dummy_command.sh $ARG1$ $ARG2$',
             'poller_tag': 'DMZ'
             }
        c = Command(t)
        self.assertEqual('check_command_test', c.command_name)
        b = c.get_initial_status_brok()
        self.assertEqual('initial_command_status', b.type)

        # now create a commands packs
        cs = Commands([c])
        dummy_call = "check_command_test!titi!toto"
        cc = CommandCall(cs, dummy_call)
        self.assertEqual(True, cc.is_valid())
        self.assertEqual(c, cc.command)
        self.assertEqual('DMZ', cc.poller_tag)



if __name__ == '__main__':
    unittest.main()
