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

import os, sys, time, platform

from shinken_test import unittest, ShinkenTest

from shinken.log import logger
from shinken.objects.module import Module

from shinken.modules import named_pipe
from shinken.modules.named_pipe import Named_Pipe_arbiter, get_instance

modconf = Module()
modconf.module_name = "NamedPipe"
modconf.module_type = named_pipe.properties['type']
modconf.properties = named_pipe.properties.copy()


class TestModuleNamedPipe(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/nagios_module_hot_dependencies_arbiter.cfg')

    def test_read_named_pipe(self):

        # Ok, windows do not have named pipe, we know...
        # cygwin cannow write from two sides at the same time
        if os.name == 'nt' or platform.system().startswith('CYGWIN'):
            return

        now = int(time.time())
        print self.conf.modules

        host0 = self.sched.conf.hosts.find_by_name('test_host_0')
        self.assert_(host0 is not None)

        # get our modules
        mod = sl = Named_Pipe_arbiter(modconf, 'tmp/nagios.cmd')

        try:
            os.unlink(mod.path)
        except:
            pass

        print "Instance", sl

        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()
        l = logger

        #sl.main()
        sl.open()

        # Now us we wrote in it
        f = open('tmp/nagios.cmd', 'w')
        t = "[%lu] PROCESS_HOST_CHECK_RESULT;dc1;2;yoyo est mort\n" % now

        s = ''
        for i in xrange(1, 1000):
            s += t

        print "Len s", len(s)

        f.write(s)
        f.flush()
        f.close()
        total_cmd = 0
        for i in xrange(1, 100):
            ext_cmds = sl.get()
            print "got ext_cmd", len(ext_cmds)
            total_cmd += len(ext_cmds)
            if len(ext_cmds) == 0:
                sl.open()
            else:
                cmd = ext_cmds.pop()
        print "Total", total_cmd
        self.assert_(total_cmd == 999)
        print cmd.__dict__
        self.assert_(cmd.cmd_line.strip() == t.strip())

        # Ok, we can delete the retention file
        os.unlink('tmp/nagios.cmd')



if __name__ == '__main__':
    unittest.main()
