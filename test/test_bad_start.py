#!/usr/bin/env python2.6
#Copyright (C) 2009-2010 :
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
# This file is used to test reading and processing of config files
#

import os
import random, time

from shinken_test import unittest

from shinken.daemon import InvalidPidDir, InvalidWorkDir
from shinken.pyro_wrapper import PortNotFree

from shinken.daemons.pollerdaemon import Poller
# all shinken-* services are subclassing Daemon so we only need to test one normally...

# I choose poller.

# and we can use its default/dev config : 
pollerconfig = "../etc/pollerd.ini"

curdir = os.getcwd()

class Test_Daemon_Bad_Start(unittest.TestCase):
           
    def gen_invalid_directory(self, f):
        basedir = "/invalid_directory42/" + str(random.randint(0,100))
        while os.path.exists(basedir):
            basedir = os.path.join(basedir, str(random.randint(0,100)))
        return os.path.join(basedir, f)

    def get_login_and_group(self, p):
        try:
            user = os.getlogin()
        except OSError: # on some rare case, we can have a problem here
            # so bypass it and keep default value
            return
        p.user = p.group = user

    def get_poller_daemon(self):
        os.chdir(curdir)
        p = Poller(pollerconfig, False, True, False, None)
        p.do_load_config()
        p.port = 0  # let's here choose automatic port attribution..
        self.get_login_and_group(p)
        return p
    
    def test_bad_piddir(self):
        print("Testing bad piddir ... mypid=%d" % (os.getpid()))
        p = self.get_poller_daemon()
        p.pidfile = self.gen_invalid_directory(p.pidfile)
        self.assertRaises(InvalidPidDir, p.do_daemon_init_and_start)
        p.do_stop()
    
    def test_bad_workdir(self):
        print("Testing bad workdir ... mypid=%d" % (os.getpid()))
        p = self.get_poller_daemon()
        p.workdir = self.gen_invalid_directory(p.workdir)
        self.assertRaises(InvalidWorkDir, p.do_daemon_init_and_start)
        p.do_stop()

    def test_port_not_free(self):
        time.sleep(1)
        print("Testing port not free ... mypid=%d" % (os.getpid()))
        p1 = self.get_poller_daemon()
        p1.do_daemon_init_and_start()           
        os.unlink(p1.pidfile)  ## so that second poller will not see first started poller
        p2 = self.get_poller_daemon()
        p2.port = p1.daemon.port
        self.assertRaises(PortNotFree, p2.do_daemon_init_and_start)
        
        
if __name__ == '__main__':
    unittest.main()
