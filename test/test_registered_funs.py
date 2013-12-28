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


import subprocess
from time import sleep

from shinken_test import *

import shinken.log as shinken_log

from shinken.daemons.schedulerdaemon import Shinken
from shinken.daemons.arbiterdaemon import Arbiter

daemons_config = {
    Shinken:      "etc/core/daemons/schedulerd.ini",
    Arbiter:    ["etc/core/shinken.cfg"]
}


class testRegisteredFunctions(unittest.TestCase):
    def create_daemon(self):
        cls = Shinken
        return cls(daemons_config[cls], False, True, False, None, '')

    def test_registered(self):
        logger.info("Testing register funs")

        shinken_log.local_log = None  # otherwise get some "trashs" logs..
        d = self.create_daemon()

        d.load_config_file()

        d.http_backend = 'wsgiref'
        #d.port = HIGH_PORT + run  # random high port, I hope no one is using it :)
        d.do_daemon_init_and_start()
        d.load_modules_manager()
        d.http_daemon.register(d.interface)
        reg_list = d.http_daemon.registered_fun
        expected_list = ['get_external_commands', 'get_running_id', 'got_conf', 'have_conf',
                         'ping', 'push_broks', 'push_host_names', 'put_conf', 'remove_from_conf',
                         'run_external_commands', 'set_log_level', 'wait_new_conf', 'what_i_managed']
        for fun in expected_list:
            assert(fun in reg_list)
        subprocess.Popen(["../bin/shinken-arbiter", "-c", daemons_config[Arbiter][0], "-d"])
        # Ok, now the conf
        d.wait_for_initial_conf()
        if not d.new_conf:
            return
        logger.info("New configuration received")
        d.setup_new_conf()
        reg_list = d.http_daemon.registered_fun
        expected_list = ['get_external_commands', 'get_running_id', 'got_conf', 'have_conf',
                         'ping', 'push_broks', 'push_host_names', 'put_conf', 'remove_from_conf',
                         'run_external_commands', 'set_log_level', 'wait_new_conf', 'what_i_managed',
                         'get_checks', 'put_results', 'fill_initial_broks', 'get_broks']
        for fun in expected_list:
            assert(fun in reg_list)

        sleep(2)
        os.kill(int(file("tmp/arbiterd.pid").read()), 2)
        d.do_stop()


if __name__ == '__main__':
    unittest.main()
