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

#It's ugly I know....
from shinken_test import *

import os
import sys

import threading
import random

curdir = os.getcwd()

from shinken.daemon import InvalidPidDir, InvalidWorkDir
from shinken.pyro_wrapper import PortNotFree


# all shinken-* services are subclassing Daemon so we only need to test one normally...

# I choose poller.

# and we can use its default/dev config : 
pollerconfig = "../etc/pollerd.ini"


class TestConfig(ShinkenTest):
    
    def gen_invalid_directory(self, f):
        basedir = "/invalid_directory42/" + str(random.randint(0,100))
        while os.path.exists(basedir):
            basedir += os.path.sep + str(random.randint(0,100))
        return basedir + os.path.sep + f 


    def get_login_and_group(self, p):
        try:
            p.user = p.group = os.getlogin()
        except OSError: #on some rare case, we can have a problem here
            # so bypas it with default value
            p.user = p.group = 'shinken'

    
    def test_bad_piddir(self):
        print("Testing bad piddir ..")
        os.chdir(curdir)
        p1 = shinkenpoller.Poller(pollerconfig, False, True, False, None)
        p1.do_load_config()
        self.get_login_and_group(p1)
        p1.pidfile = self.gen_invalid_directory(p1.pidfile)
        self.assertRaises(InvalidPidDir, p1.do_daemon_init_and_start)
    
    def test_bad_workdir(self):
        print("Testing port not free ...")
        os.chdir(curdir)
        p1 = shinkenpoller.Poller(pollerconfig, False, True, False, None)
        p1.do_load_config()
        p1.workdir = self.gen_invalid_directory(p1.workdir)
        self.get_login_and_group(p1)
        self.assertRaises(InvalidWorkDir, p1.do_daemon_init_and_start)

    def test_port_not_free(self):
        print("Testing port not free ...")
        os.chdir(curdir)
        p1 = shinkenpoller.Poller(pollerconfig, False, True, False, None)
        p1.do_load_config()
        self.get_login_and_group(p1)
        p1.do_daemon_init_and_start()
        p1.do_post_daemon_init()
        
        os.chdir(curdir)  ## first one has changed our cwd to its workdir, so reset to good one
        
        p2 = shinkenpoller.Poller(pollerconfig, False, True, False, None)
        p2.do_load_config()
        self.get_login_and_group(p2)
        
        os.unlink(p1.pidfile)  ## so that second poller will not see first started poller
        
        self.assertRaises(PortNotFree, p2.do_daemon_init_and_start)
        
        
if __name__ == '__main__':
    unittest.main()


        
