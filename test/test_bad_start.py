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

import os
import tempfile
import shutil

from shinken_test import *

import shinken.log as shinken_log

from shinken.daemon import InvalidPidFile, InvalidWorkDir
from shinken.http_daemon import PortNotFree

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
    Broker:       "etc/core/daemons/brokerd.ini",
    Poller:       "etc/core/daemons/pollerd.ini",
    Reactionner:  "etc/core/daemons/reactionnerd.ini",
    Shinken:      "etc/core/daemons/schedulerd.ini",
    Arbiter:    ["etc/core/shinken.cfg"]
}

import random

HIGH_PORT = random.randint(30000,65000)
run = 0   # We will open some ports but not close them (yes it's not good) and
# so we will open a range from a high port

class template_Daemon_Bad_Start():

    def setUp(self):
        time_hacker.set_real_time()

    def get_login_and_group(self, p):
        try:
            p.user = get_cur_user()
            p.group = get_cur_group()
        except OSError:  # on some rare case, we can have a problem here
            # so bypass it and keep default value
            return

    def create_daemon(self):
        cls = self.daemon_cls
        return cls(daemons_config[cls], False, True, False, None, '')


    def get_daemon(self):
        global run
        os.chdir(curdir)
        shinken_log.local_log = None  # otherwise get some "trashs" logs..
        d = self.create_daemon()

        d.load_config_file()
        d.http_backend = 'wsgiref'
        d.port = HIGH_PORT + run  # random high port, I hope no one is using it :)
        run += 1
        self.get_login_and_group(d)
        return d


    def test_bad_piddir(self):
        print "Testing bad pidfile ..."
        d = self.get_daemon()
        d.workdir = tempfile.mkdtemp()
        d.pidfile = os.path.join('/proc/DONOTEXISTS', "daemon.pid")
        prev_dir = os.getcwd()
        self.assertRaises(InvalidPidFile, d.do_daemon_init_and_start, fake=True)
        shutil.rmtree(d.workdir)
        os.chdir(prev_dir)

    def test_bad_workdir(self):
        print("Testing bad workdir ... mypid=%d" % (os.getpid()))
        d = self.get_daemon()
        d.workdir = '/proc/DONOTEXISTS'
        prev_dir = os.getcwd()
        self.assertRaises(InvalidWorkDir, d.do_daemon_init_and_start, fake=True)
        d.do_stop()
        os.chdir(prev_dir)

    def test_port_not_free(self):
        print("Testing port not free ... mypid=%d" % (os.getpid()))
        d1 = self.get_daemon()
        d1.workdir = tempfile.mkdtemp()
        prev_dir = os.getcwd()  # We have to remember where we are to get back after
        d1.do_daemon_init_and_start(fake=True)
        new_dir = os.getcwd()  # We have to remember this one also
        os.chdir(prev_dir)
        os.unlink(os.path.join(new_dir, d1.pidfile))  ## so that second poller will not see first started poller
        d2 = self.get_daemon()
        d2.workdir = d1.workdir
        # TODO: find a way in Pyro4 to get the port
        if hasattr(d1.http_daemon, 'port'):
            d2.port = d1.http_daemon.port
            self.assertRaises(PortNotFree, d2.do_daemon_init_and_start, fake=True)
            d2.do_stop()
        d1.do_stop()
        try:
            os.unlink(d1.pidfile)
        except Exception:
            pass
        if hasattr(d1, 'local_log'):
            os.unlink(os.path.join(d1.workdir, d1.local_log))
        shutil.rmtree(d1.workdir)
        os.chdir(prev_dir)  # Back to previous dir for next test!


class Test_Broker_Bad_Start(template_Daemon_Bad_Start, ShinkenTest):
    daemon_cls = Broker


class Test_Scheduler_Bad_Start(template_Daemon_Bad_Start, ShinkenTest):
    daemon_cls = Shinken


class Test_Poller_Bad_Start(template_Daemon_Bad_Start, ShinkenTest):
    daemon_cls = Poller


class Test_Reactionner_Bad_Start(template_Daemon_Bad_Start, ShinkenTest):
    daemon_cls = Reactionner


class Test_Arbiter_Bad_Start(template_Daemon_Bad_Start, ShinkenTest):
    daemon_cls = Arbiter

    def create_daemon(self):
        """ arbiter is always a bit special .. """
        cls = self.daemon_cls
        #Arbiter(config_files, is_daemon, do_replace, verify_only, debug, debug_file, profile)
        return cls(daemons_config[cls], False, True, False, False, None, '')


if __name__ == '__main__':
    unittest.main()
