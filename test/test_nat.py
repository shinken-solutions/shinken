#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2010:
#    Guillaume Bour/Uperto, guillaume.bour@uperto.com
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
# This file test Shinken working in a NATted environment
# Makes use of netkit (www.netkit.org) software
#

import os
import sys
import time
import glob
import shutil
import os.path
import unittest
import subprocess

SVC_CMD = "cd /hostlab && ./bin/shinken-#svc# -d -r -c ./test/etc/netkit/basic/#svc#d.ini\n"

launchers = {
    'arbiter': "cd /hostlab/var && ../bin/shinken-#svc# -r -c ../etc/nagios.cfg -c ../test/etc/netkit/#conf#/shinken-specific.cfg 2>&1 > ./arbiter.debug&\n",
    'broker': SVC_CMD,
    'poller': SVC_CMD,
    'reactionner': SVC_CMD,
    'receiver': SVC_CMD,
    'scheduler': SVC_CMD,
}

LOGBASE = os.path.join("#root#", "var")
LOGFILE = os.path.join(LOGBASE, "#svc#d.log")
logs = {
    'arbiter': os.path.join(LOGBASE, "arbiter.debug"),
    'broker': LOGFILE,
    'poller': LOGFILE,
    'reactionner': LOGFILE,
    'receiver': LOGFILE,
    'scheduler': LOGFILE,
}


def cleanup():
    rootdir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "..")

    subprocess.Popen(["lcrash", "--keep-fs", "-d", rootdir], stdout=open('/dev/null'), stderr=subprocess.STDOUT)
    for prefix in ('pc1', 'pc2', 'nat'):
        for f in glob.glob(os.path.join(rootdir, prefix + '.*')):
            os.remove(f)


class TestNat(unittest.TestCase):
    def setUp(self):
        self.testdir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.files = dict()

        # copying netkit configuration file to project root directory
        root = os.path.join(self.testdir, 'etc', 'netkit')
        for f in os.listdir(root):
            if os.path.isfile(os.path.join(root, f)):
                shutil.copy(os.path.join(root, f), os.path.join(self.testdir, '..'))
                self.files[f] = os.path.join(self.testdir, '..', f)

        for vm in ('pc1', 'pc2', 'nat'):
            lock = os.path.join(self.testdir, '..', vm+'.STARTED')
            if os.path.exists(lock):
                os.remove(lock)

            self.files[vm+'.lock'] = lock

        # cleanup shinken logs
        for f in glob.glob(os.path.join(self.testdir, "..", "var", "*.log")):
            os.remove(f)
        try:
            os.remove(logs['arbiter'].replace('#root#', os.path.join(self.testdir, "..")))
        except:
            pass

    def tearDown(self):
        null = open('/dev/null')
        subprocess.Popen(["lhalt", "-q", "-d", os.path.join(self.testdir, "..")], stdout=null, stderr=subprocess.STDOUT)
        time.sleep(20)
        subprocess.Popen(["lcrash", "--keep-fs", "-d", os.path.join(self.testdir, "..")], stdout=null, stderr=subprocess.STDOUT)
        time.sleep(60)

        for k, f in self.files.iteritems(): # glob.glob(os.path.join(self.testdir, "..", "*.STARTED"));
            if os.path.exists(f):
                os.remove(f)

    def booted(self):
        if not os.path.exists(os.path.join(self.testdir, "..", "pc1.STARTED")):
            return False

        return os.path.exists(os.path.join(self.testdir, "..", "pc2.STARTED"))

    def init_and_start_vms(self, conf, services):
        for vm in ('pc1', 'pc2', 'nat'):
            f = open(self.files[vm+'.startup'], 'a')

            # extend vm startup
            extend = os.path.join(self.testdir, "etc", "netkit", conf, vm+".startup")
            if os.path.exists(extend):
                e = open(extend, 'r')
                for l in e.xreadlines():
                    f.write(l)
                e.close()

            for svc in services.get(vm, []):
                f.write(launchers[svc].replace('#svc#', svc).replace('#conf#', conf))

            f.write("touch /hostlab/"+vm+".STARTED\n")
            f.close()

        subprocess.Popen(["lstart", "-d", os.path.join(self.testdir, ".."), "-f"], stdout=open('/dev/null'), stderr=subprocess.STDOUT)

        # waiting for vms has finished booting
        while not self.booted():
            time.sleep(10)
        print "init_and_start_vms %s done!" % conf

    def found_in_log(self, svc, msg):
        f = open(logs[svc].replace('#root#', os.path.join(self.testdir, "..")).replace('#svc#', svc), 'r')
        for line in f.xreadlines():
            if msg in line:
                f.close()
                return True

        f.close()
        return False

    def test_01_failed_broker(self):
        print "conf-01: init..."
        self.init_and_start_vms('conf-01', {
            'pc1': ['arbiter', 'poller', 'reactionner', 'receiver', 'scheduler'],
            'pc2': ['broker']
        })

        # waiting 5mins to be sure arbiter sent its configuration to other services
        print "waiting..."
        time.sleep(60)

        print "checking..."
        self.assertTrue(self.found_in_log('broker', 'Info: Waiting for initial configuration'))
        self.assertTrue(self.found_in_log('arbiter', 'Warning: Missing satellite broker for configuration 0:'))

        self.assertFalse(self.found_in_log('arbiter', 'Info: [All] Dispatch OK of configuration 0 to broker broker-1'))

    def test_02_broker(self):
        print "conf-02: init..."
        self.init_and_start_vms('conf-02', {
            'pc1': ['arbiter', 'poller', 'reactionner', 'receiver', 'scheduler'],
            'pc2': ['broker']
        })

        # waiting 3mins to be sure arbiter sent its configuration to other services
        print "waiting..."
        time.sleep(210)

        print "checking..."
        self.assertTrue(self.found_in_log('broker', 'Info: Waiting for initial configuration'))
        self.assertTrue(self.found_in_log('arbiter', 'Info: [All] Dispatch OK of configuration 0 to broker broker-1'))

        self.assertTrue(self.found_in_log('broker', 'Info: [broker-1] Connection OK to the scheduler scheduler-1'))
        self.assertTrue(self.found_in_log('broker', 'Info: [broker-1] Connection OK to the poller poller-1'))
        self.assertTrue(self.found_in_log('broker', 'Info: [broker-1] Connection OK to the reactionner reactionner-1'))



if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig)
    #unittest.TextTestRunner(verbosity=2).run(allsuite)

    cleanup()
