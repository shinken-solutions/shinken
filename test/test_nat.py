#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

#Copyright (C) 2009-2010 :
#    Guillaume Bour/Uperto, guillaume.bour@uperto.com 
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


#
# This file test Shinken working in a NATted environment
# Makes use of netkit (www.netkit.org) software
#

import os
import sys
import time
import shutil
import os.path
import unittest
import subprocess

class TestNat(unittest.TestCase):
    def setUp(self):
        self.testdir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.files   = dict()

        for root, dirs, files in os.walk(os.path.join(self.testdir, 'etc', 'netkit')):
            for f in files:
                if f.endswith('.disk'):
                    continue

                shutil.copy(os.path.join(root, f), os.path.join(self.testdir, '..'))
                self.files[f] = os.path.join(self.testdir, '..', f)

        self.files['pc1s'] = os.path.join(self.testdir, '..', "pc1.STARTED")
        self.files['pc2s'] = os.path.join(self.testdir, '..', "pc2.STARTED")

    def tearDown(self):
        subprocess.Popen(["lhalt" , "-d", os.path.join(self.testdir, "..")])
        subprocess.Popen(["lcrash", "-d", os.path.join(self.testdir, "..")])

        #for f in self.files:
        #    os.remove(os.path.join(self.testdir, '..', f))

    def started(self):
        if not os.path.exists(os.path.join(self.testdir, "..", "pc1.STARTED"))
            return False

        return os.path.exists(os.path.join(self.testdir, "..", "pc2.STARTED"))
        
    def init_and_start_vms(self, services):
        for pc in ('pc1','pc2'):
            f = open(self.files[pc+'startup'], 'a')
            for svc in services[pc]:
                f.write("/hostlab/bin/launch_"+svc+".sh\n")

            f.write("touch /hostlab/"+pc+".STARTED\n")
            f.close()
        
        subprocess.Popen(["lstart","-d",os.path.join(self.testdir, ".."),"-f"])

        while not self.booted():
            time.sleep(10)
        print "done!"

    def test_natted_broker(self):
        init_and_start_vms({
            'pc1': ['arbiter'],
            'pc2': ['broker']
        })


if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig) 
    #unittest.TextTestRunner(verbosity=2).run(allsuite) 
