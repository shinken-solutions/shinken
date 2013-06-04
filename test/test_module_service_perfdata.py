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
import time

from shinken_test import unittest, ShinkenTest

from shinken.modulesctx import modulesctx
get_instance = modulesctx.get_module('perfdata_service').get_instance


class TestModSRVPErfdata(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_service_perfdata(self):
        print self.conf.modules
        # get our modules
        mod = None
        for m in self.conf.modules:
            if m.module_type == 'service_perfdata':
                mod = m
        self.assert_(mod is not None)
        self.assert_(mod.path == 'tmp/service-perfdata')
        self.assert_(mod.module_name == 'Service-Perfdata')
        self.assert_(mod.mode == 'a')
        # Warning, the r (raw) is important here
        self.assert_(mod.template == r'$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICEOUTPUT$\t$SERVICESTATE$\t$SERVICEPERFDATA$\n')

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
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        t = int(time.time())
        print "T", t
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0']])
        # manage all service check result broks
        for b in self.sched.broks.values():
            if b.type == 'service_check_result':
                sl.manage_brok(b)
        self.sched.broks = {}
        sl.file.close()  # the sl has also an open (writing) file handle
        # Ok, go for writing
        sl.hook_tick(None)

        fd = open(mod.path)
        buf = fd.readline()
        #print "BUF:", buf
        comparison = '%d\t%s\t%s\t%s\t%s\t%s\n' % (t, "test_host_0", "test_ok_0", 'BAD', 'CRITICAL', 'value1=0 value2=0')
        #print "Comparison:", comparison
        self.assert_(buf == comparison)
        fd.close()
        os.unlink(mod.path)

        # Now change with a new template
        # and direct in the instance (do not do this in prod :) )
        mod.template = '$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICEOUTPUT$\t$SERVICEPERFDATA$\t$SERVICESTATE$\n'
        sl2 = get_instance(mod)
        sl2.init()
        print sl2.__dict__
        t = int(time.time())
        print "T", t
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0'u'\xf6']])
        # manage all service check result broks
        for b in self.sched.broks.values():
            if b.type == 'service_check_result':
                sl2.manage_brok(b)
        sl2.file.close()
        # Ok, go for writing
        sl2.hook_tick(None)

        fd = open(mod.path)
        buf = fd.readline().decode('utf8')
        print fd.read()

        comparison = u'%d\t%s\t%s\t%s\t%s\t%s\n' % (t, "test_host_0", "test_ok_0", 'BAD', 'value1=0 value2=0' + u'\xf6', 'CRITICAL')

        self.assert_(buf == comparison)
        fd.close()
        os.unlink(mod.path)

        # Now change with a new template, a CENTREON ONE
        mod.template = '$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$LASTSERVICESTATE$\t$SERVICESTATE$\t$SERVICEPERFDATA$\n'
        sl2 = get_instance(mod)
        sl2.init()
        print sl2.__dict__
        t = int(time.time())
        print "T", t
        self.scheduler_loop(1, [[svc, 2, 'BAD | value1=0 value2=0'u'\xf6']])
        # manage all service check result broks
        for b in self.sched.broks.values():
            if b.type == 'service_check_result':
                sl2.manage_brok(b)
        sl2.file.close()
        # Ok, go for writing
        sl2.hook_tick(None)

        fd = open(mod.path)
        buf = fd.readline().decode('utf8')
        print fd.read()

        comparison = u'%d\t%s\t%s\t%s\t%s\t%s\n' % (t, "test_host_0", "test_ok_0", 'CRITICAL', 'CRITICAL', 'value1=0 value2=0' + u'\xf6')
        #print "BUF", buf
        #print "COM", comparison
        self.assert_(buf == comparison)
        fd.close()
        os.unlink(mod.path)


if __name__ == '__main__':
    unittest.main()
