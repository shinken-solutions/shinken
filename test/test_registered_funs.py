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

from shinken_test import *

import shinken.log as shinken_log

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


class testRegisteredFunctions(unittest.TestCase):
    def create_daemon(self):
        cls = Shinken
        return cls(daemons_config[cls], False, True, False, None, '')


    def test_registered(self):
        print "Testing register funs"

        shinken_log.local_log = None  # otherwise get some "trashs" logs..
        d = self.create_daemon()

        d.load_config_file()

        d.http_backend = 'wsgiref'
        #d.port = HIGH_PORT + run  # random high port, I hope no one is using it :)
        d.do_daemon_init_and_start()
        d.http_daemon.register(d.interface)
        reg_list = d.http_daemon.registered_fun
        expected_list = ['get_external_commands', 'get_running_id', 'got_conf', 'have_conf',
                         'ping', 'push_broks', 'push_host_names', 'put_conf', 'remove_from_conf',
                         'run_external_commands', 'set_log_level', 'wait_new_conf', 'what_i_managed']
        assert( reg_list == expected_list)
        d.do_stop()




if __name__ == '__main__':
    unittest.main()
