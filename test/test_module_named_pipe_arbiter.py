#!/usr/bin/env python
#
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

"""
Test the named pipe arbiter module.
"""

import os, time, platform

from shinken_test import unittest, ShinkenTest

from shinken.objects.module import Module

from shinken.modules import named_pipe
from shinken.modules.named_pipe import Named_Pipe_arbiter, get_instance

modconf = Module()
modconf.module_name = "NamedPipe"
modconf.module_type = named_pipe.properties['type']
modconf.properties = named_pipe.properties.copy()


class TestModuleNamedPipe(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_read_named_pipe(self):

        # Ok, windows do not have named pipe, we know...
        # cygwin cannot write from two sides at the same time
        if os.name == 'nt' or platform.system().startswith('CYGWIN'):
            return

        now = int(time.time())

        host0 = self.sched.conf.hosts.find_by_name('test_host_0')
        self.assert_(host0 is not None)

        # get our modules
        mod = sl = Named_Pipe_arbiter(modconf, 'tmp/nagios.cmd')

        try:
            os.unlink(mod.path)
        except:
            pass

        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()

        #sl.main()
        sl.open()

        # Now us we wrote in it
        f = open('tmp/nagios.cmd', 'w')
        t = "[%lu] PROCESS_HOST_CHECK_RESULT;dc1;2;yoyo est mort\n" % now
        for i in xrange(999):
            f.write(t)
        f.flush()
        f.close()

        total_cmd = 0
        for i in xrange(99):
            ext_cmds = sl.get()
            total_cmd += len(ext_cmds)
            if len(ext_cmds) == 0:
                sl.open()
            else:
                cmd = ext_cmds.pop()
        self.assertEqual(total_cmd, 999)
        self.assertEqual(cmd.cmd_line.strip(), t.strip())

        # Ok, we can delete the retention file
        os.unlink('tmp/nagios.cmd')



if __name__ == '__main__':
    unittest.main()
