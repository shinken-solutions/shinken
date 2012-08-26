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
import tempfile

from shinken_test import unittest

import shinken.log as shinken_log

from shinken.daemon import InvalidPidFile, InvalidWorkDir
from shinken.pyro_wrapper import PortNotFree

from shinken.daemons.pollerdaemon import Poller
from shinken.daemons.brokerdaemon import Broker
from shinken.daemons.schedulerdaemon import Shinken
from shinken.daemons.reactionnerdaemon import Reactionner
from shinken.daemons.arbiterdaemon import Arbiter
try:                                                                                                              
    import pwd, grp                                                                                               
    from pwd import getpwnam                                                                                      
    from grp import getgrnam                                                                                      
                                                                                                                  
                                                                                                                  
    def get_cur_user():                                                                                           
        return pwd.getpwuid(os.getuid()).pw_name                                                                  
                                                                                                                  
                                                                                                                  
    def get_cur_group():                                                                                          
        return grp.getgrgid(os.getgid()).gr_name                                                                  
except ImportError, exp:  # Like in nt system or Android                 
                                                                                                                 
                                                                                                                  
    # temporary workaround:                                                                                      
    def get_cur_user():                                                                                           
        return os.getlogin()
                                                                                                                  
                                                                                                                  
    def get_cur_group():                                                                                          
        return os.getlogin()
                  
curdir = os.getcwd()

daemons_config = {
    Broker:       "../etc/brokerd.ini",
    Poller:       "../etc/pollerd.ini",
    Reactionner:  "../etc/reactionnerd.ini",
    Shinken:      "../etc/schedulerd.ini",
    Arbiter:    ["../etc/nagios.cfg", "../etc/shinken-specific.cfg"]
}

HIGH_PORT = 65488
run = 0   # We will open some ports but not close them (yes it's not good) and
# so we will open a range from a high port

class template_Test_Daemon_Bad_Start():

    def get_login_and_group(self, p):
        try:
            #user = os.getlogin()
            user = get_cur_user()
        except OSError:  # on some rare case, we can have a problem here
            # so bypass it and keep default value
            return
        p.user = p.group = user

    def create_daemon(self):
        cls = self.daemon_cls
        return cls(daemons_config[cls], False, True, False, None)

    def get_daemon(self):
        global run
        os.chdir(curdir)
        shinken_log.local_log = None  # otherwise get some "trashs" logs..
        d = self.create_daemon()
        d.load_config_file()
        d.port = HIGH_PORT + run  # random high port, I hope no one is using it :)
        run += 1
        self.get_login_and_group(d)
        return d

    def test_bad_piddir(self):
        print "Testing bad pidfile ..."
        d = self.get_daemon()
        d.workdir = tempfile.mkdtemp()
        d.pidfile = os.path.join(d.workdir, "daemon.pid")
        f = open(d.pidfile, "w")
        f.close()
        os.chmod(d.pidfile, 0)
        self.assertRaises(InvalidPidFile, d.do_daemon_init_and_start)
        os.unlink(d.pidfile)
        os.rmdir(d.workdir)

    def test_bad_workdir(self):
        print("Testing bad workdir ... mypid=%d" % (os.getpid()))
        d = self.get_daemon()
        d.workdir = tempfile.mkdtemp()
        os.chmod(d.workdir, 0)
        self.assertRaises(InvalidWorkDir, d.do_daemon_init_and_start)
        d.do_stop()
        os.rmdir(d.workdir)

    def test_port_not_free(self):
        print("Testing port not free ... mypid=%d" % (os.getpid()))
        d1 = self.get_daemon()
        d1.workdir = tempfile.mkdtemp()
        d1.do_daemon_init_and_start()
        os.unlink(d1.pidfile)  ## so that second poller will not see first started poller
        d2 = self.get_daemon()
        d2.workdir = d1.workdir
        # TODO: find a way in Pyro4 to get the port
        if hasattr(d1.pyro_daemon, 'port'):
            d2.port = d1.pyro_daemon.port
            self.assertRaises(PortNotFree, d2.do_daemon_init_and_start)
            d2.do_stop()
        d1.do_stop()
        try:
            os.unlink(d1.pidfile)
        except:
            pass
        if hasattr(d1, 'local_log'):
            os.unlink(os.path.join(d1.workdir, d1.local_log))
        os.rmdir(d1.workdir)


class Test_Broker_Bad_Start(template_Test_Daemon_Bad_Start, unittest.TestCase):
    daemon_cls = Broker


class Test_Scheduler_Bad_Start(template_Test_Daemon_Bad_Start, unittest.TestCase):
    daemon_cls = Shinken


class Test_Poller_Bad_Start(template_Test_Daemon_Bad_Start, unittest.TestCase):
    daemon_cls = Poller


class Test_Reactionner_Bad_Start(template_Test_Daemon_Bad_Start, unittest.TestCase):
    daemon_cls = Reactionner


class Test_Arbiter_Bad_Start(template_Test_Daemon_Bad_Start, unittest.TestCase):
    daemon_cls = Arbiter

    def create_daemon(self):
        """ arbiter is always a bit special .. """
        cls = self.daemon_cls
        #Arbiter(config_files, is_daemon, do_replace, verify_only, debug, debug_file)
        return cls(daemons_config[cls], False, True, False, False, None)


if __name__ == '__main__':
    unittest.main()
