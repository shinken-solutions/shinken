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


import subprocess
from time import sleep

from shinken_test import *

import shinken.log as shinken_log

from shinken.daemons.schedulerdaemon import Shinken
from shinken.daemons.arbiterdaemon import Arbiter

daemons_config = {
    Shinken:      "etc/test_scheduler_init/schedulerd.ini",
    Arbiter:    ["etc/test_scheduler_init/shinken.cfg"]
}


class testSchedulerInit(ShinkenTest):
    def setUp(self):
        time_hacker.set_real_time()

    def create_daemon(self):
        cls = Shinken
        return cls(daemons_config[cls], False, True, False, None, '')

    def test_scheduler_init(self):

        shinken_log.local_log = None  # otherwise get some "trashs" logs..
        d = self.create_daemon()

        d.load_config_file()

        d.http_backend = 'wsgiref'
        d.do_daemon_init_and_start(fake=True)
        d.load_modules_manager()

        # Test registered function list
        d.http_daemon.register(d.interface)
        reg_list = d.http_daemon.registered_fun
        expected_list = ['get_external_commands', 'get_running_id', 'got_conf', 'have_conf',
                         'ping', 'push_broks', 'push_host_names', 'put_conf', 'remove_from_conf',
                         'run_external_commands', 'set_log_level', 'wait_new_conf', 'what_i_managed']
        for fun in expected_list:
            assert(fun in reg_list)

        # Launch an arbiter so that the scheduler get a conf and init
        subprocess.Popen(["../bin/shinken-arbiter.py", "-c", daemons_config[Arbiter][0], "-d"])

        # Ok, now the conf
        d.wait_for_initial_conf(timeout=20)
        if not d.new_conf:
            return

        d.setup_new_conf()

        # Test registered function list again, so that there is no overriden functions
        reg_list = d.http_daemon.registered_fun
        expected_list = ['get_external_commands', 'get_running_id', 'got_conf', 'have_conf',
                         'ping', 'push_broks', 'push_host_names', 'put_conf', 'remove_from_conf',
                         'run_external_commands', 'set_log_level', 'wait_new_conf', 'what_i_managed',
                         'get_checks', 'put_results', 'fill_initial_broks', 'get_broks']
        for fun in expected_list:
            assert(fun in reg_list)


        # Test that use_ssl parameter generates the good uri
        if d.pollers[0]['use_ssl']:
            assert d.pollers[0]['uri'] == 'https://localhost:7771/'
        else:
            assert d.pollers[0]['uri'] == 'http://localhost:7771/'


        # Test receivers are init like pollers
        assert d.reactionners != {}  # Previously this was {} for ever
        assert d.reactionners[0]['uri'] == 'http://localhost:7769/' # Test dummy value

        # I want a simple init
        d.must_run = False
        d.sched.must_run = False
        d.sched.run()

        # Test con key is missing or not. Passive daemon should have one
        assert 'con' not in d.pollers[0] # Ensure con key is not here, deamon is not passive so we did not try to connect
        assert d.reactionners[0]['con'] is None  # Previously only pollers were init (sould be None), here daemon is passive

        # "Clean" shutdown
        sleep(2)
        pid = int(file("tmp/arbiterd.pid").read())
        print ("KILLING %d" % pid)*50
        os.kill(int(file("tmp/arbiterd.pid").read()), 2)
        d.do_stop()


if __name__ == '__main__':
    unittest.main()
