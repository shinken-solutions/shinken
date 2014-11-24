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

from shinken_test import *
import commands


class TestSystemTimeChange(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def set_time(self, d):
        cmd = 'sudo date -s "%s"' % d
        print "CMD,", cmd
        # NB: disabled for now because we test in a totally direct way
        #a = commands.getstatusoutput(cmd)
        # Check the time is set correctly!
        #self.assertEqual(0, a[0])

    def test_system_time_change(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        host = self.sched.hosts.find_by_name("test_host_0")
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        now = time.time()
        now_str = time.asctime(time.localtime(now))
        print "Now:", now
        print "Now:", time.asctime(time.localtime(now))
        tomorow = time.asctime(time.localtime(now + 86400))
        yesterday = time.asctime(time.localtime(now - 86400))

        # Simulate a change now, because by default the value is 1970
        host.last_state_change = now

        host.schedule()
        host_check = host.actions[0]

        svc.schedule()
        srv_check = svc.actions[0]
        print "Service check", srv_check, time.asctime(time.localtime(srv_check.t_to_go))

        print "Current Host last_state_change", time.asctime(time.localtime(host.last_state_change))

        # Ok, start to check for bad time
        self.set_time(tomorow)
        last_state_change = host.last_state_change
        host.compensate_system_time_change(86400)
        self.assertEqual(86400, host.last_state_change - last_state_change )
        svc.compensate_system_time_change(86400)
        print "Tomorow Host last_state_change", time.asctime(time.localtime(host.last_state_change))

        # And now a huge change: yesterday (so a 2 day move)
        self.set_time(yesterday)
        last_state_change = host.last_state_change
        host.compensate_system_time_change(-86400 * 2)
        self.assertEqual(-86400*2, host.last_state_change - last_state_change )
        svc.compensate_system_time_change(-86400*2)
        print "Yesterday Host last_state_change", time.asctime(time.localtime(host.last_state_change))

        self.set_time(now_str)

        # Ok, now the scheduler and check things
        # Put checks in the scheduler
        self.sched.get_new_actions()

        host_to_go = host_check.t_to_go
        srv_to_go = srv_check.t_to_go
        print "current Host check", time.asctime(time.localtime(host_check.t_to_go))
        print "current Service check", time.asctime(time.localtime(srv_check.t_to_go))
        self.set_time(tomorow)
        self.sched.sched_daemon.compensate_system_time_change(86400)
        print "Tomorow Host check", time.asctime(time.localtime(host_check.t_to_go))
        print "Tomorow Service check", time.asctime(time.localtime(srv_check.t_to_go))
        self.assertEqual(86400, host_check.t_to_go - host_to_go )
        self.assertEqual(86400, srv_check.t_to_go - srv_to_go )

        # and yesterday
        host_to_go = host_check.t_to_go
        srv_to_go = srv_check.t_to_go
        self.set_time(yesterday)
        self.sched.sched_daemon.compensate_system_time_change(-86400*2)
        print "Yesterday Host check", time.asctime(time.localtime(host_check.t_to_go))
        print "Yesterday Service check", time.asctime(time.localtime(srv_check.t_to_go))
        print "New host check", time.asctime(time.localtime(host.next_chk))
        self.assertEqual(host_check.t_to_go, host.next_chk)
        self.assertEqual(srv_check.t_to_go, svc.next_chk)
        self.assertEqual(-86400*2, host_check.t_to_go - host_to_go )
        self.assertEqual(-86400*2, srv_check.t_to_go - srv_to_go )

        self.set_time(now_str)



if __name__ == '__main__':
    unittest.main()
