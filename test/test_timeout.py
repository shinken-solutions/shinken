#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from shinken_test import *

from shinken.worker import Worker
from multiprocessing import Queue, Manager
from shinken.objects.service import Service
from shinken.objects.host import Host
from shinken.objects.contact import Contact
modconf = Module()


class TestTimeout(ShinkenTest):
    def setUp(self):
        # we have an external process, so we must un-fake time functions
        self.setup_with_file('etc/shinken_check_timeout.cfg')
        time_hacker.set_real_time()

    def test_notification_timeout(self):
        if os.name == 'nt':
            return

        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

        # These queues connect a poller/reactionner with a worker
        to_queue = Queue()
        #manager = Manager()
        from_queue = Queue() #manager.list()
        control_queue = Queue()

        # This testscript plays the role of the reactionner
        # Now "fork" a worker
        w = Worker(1, to_queue, from_queue, 1)
        w.id = 1
        w.i_am_dying = False

        # We prepare a notification in the to_queue
        c = Contact()
        c.contact_name = "mr.schinken"
        n = Notification('PROBLEM', 'scheduled', 'libexec/sleep_command.sh 7', '', svc, '', '', id=1)
        n.status = "queue"
        #n.command = "libexec/sleep_command.sh 7"
        n.t_to_go = time.time()
        n.contact = c
        n.timeout = 2
        n.env = {}
        n.exit_status = 0
        n.module_type = "fork"
        nn = n.copy_shell()

        # Send the job to the worker
        msg = Message(id=0, type='Do', data=nn)
        to_queue.put(msg)

        w.checks = []
        w.returns_queue = from_queue
        w.s = to_queue
        w.c = control_queue
        # Now we simulate the Worker's work() routine. We can't call it
        # as w.work() because it is an endless loop
        for i in xrange(1, 10):
            w.get_new_checks()
            # During the first loop the sleeping command is launched
            w.launch_new_checks()
            w.manage_finished_checks()
            time.sleep(1)

        # The worker should have finished it's job now, either correctly or
        # with a timeout
        o = from_queue.get()

        self.assertEqual('timeout', o.status)
        self.assertEqual(3, o.exit_status)
        self.assertLess(o.execution_time, n.timeout+1)

        # Be a good poller and clean up.
        to_queue.close()
        control_queue.close()

        # Now look what the scheduler says to all this
        self.sched.actions[n.id] = n
        self.sched.put_results(o)
        self.show_logs()
        self.assert_any_log_match("Contact mr.schinken service notification command 'libexec/sleep_command.sh 7 ' timed out after 2 seconds")



    def test_notification_timeout_on_command(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        print svc.checks_in_progress
        cs = svc.checks_in_progress
        self.assertEqual(1, len(cs))
        c = cs.pop()
        print c
        print c.timeout
        self.assertEqual(5, c.timeout)


if __name__ == '__main__':
    unittest.main()
