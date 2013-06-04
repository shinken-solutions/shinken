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
from shinken_test import *
sys.path.append("../shinken/modules")
from shinken.modules.perfdata_host import module as host_perfdata_broker
from shinken.modules.perfdata_host.module import get_instance
from shinken.brok import Brok


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_host_perfdata(self):
        print self.conf.modules
        # get our modules
        mod = None
        for m in self.conf.modules:
            if m.module_type == 'host_perfdata':
                mod = m
        self.assert_(mod is not None)
        self.assert_(mod.path == 'tmp/host-perfdata')
        self.assert_(mod.module_name == 'Host-Perfdata')
        self.assert_(mod.mode == 'a')
        # Warning, the r (raw) is important here
        print "Tempalte%stoto" % mod.template
#        self.assert_(mod.template == r'$LASTHOSTCHECK\t$HOSTNAME$\t$HOSTOUTPUT$\t$HOSTSTATE$\t$HOSTPERFDATA$\n')

        try:
            os.unlink(mod.path)
        except:
            pass

        sl = get_instance(mod)
        print sl
        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()
        svc = self.sched.hosts.find_by_name("test_host_0")
        t = int(time.time())
        print "T", t
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0']])
        # manage all host check result broks
        for b in self.sched.broks.values():
            if b.type == 'host_check_result':
                sl.manage_brok(b)
        self.sched.broks = {}
        sl.file.close()  # the sl also has an open file handle

        fd = open(mod.path)
        buf = fd.readline()
        print "BUF:", buf
        comparison = '%d\t%s\t%s\t%s\t%s\n' % (t, "test_host_0", 'BAD', 'DOWN', 'value1=0 value2=0')
        print "Comparison:", comparison
        self.assert_(buf == comparison)
        fd.close()
        os.unlink(mod.path)

        # Now change with a new template
        # and direct in the instance (do not do this in prod :) )
        mod.template = '$LASTHOSTCHECK$\t$HOSTNAME$\t$HOSTOUTPUT$\t$HOSTPERFDATA$\t$HOSTSTATE$\n'
        sl2 = get_instance(mod)
        sl2.init()
        print sl2.__dict__
        t = int(time.time())
        print "T", t
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0' + u'\xf6']])
        # manage all host check result broks
        for b in self.sched.broks.values():
            if b.type == 'host_check_result':
                sl2.manage_brok(b)
        sl2.file.close()

        fd = open(mod.path)
        buf = fd.readline().decode('utf8')

        #print "BUF:", buf
        comparison = u'%d\t%s\t%s\t%s\t%s\n' % (t, "test_host_0", 'BAD', 'value1=0 value2=0' + u'\xf6', 'DOWN')
        #print "Comparison:", comparison
        self.assert_(buf == comparison)
        fd.close()
        os.unlink(mod.path)


if __name__ == '__main__':
    unittest.main()
