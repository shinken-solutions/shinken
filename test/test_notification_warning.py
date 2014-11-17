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

from shinken.notification import Notification


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def test_raise_warning_on_notification_errors(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        cmd = "/error/pl"
        # Create a dummy notif
        n = Notification('PROBLEM', 'scheduled', 'BADCOMMAND', cmd, host, None, 0)
        n.execute()
        time.sleep(0.2)
        if n.status is not 'done':
            n.check_finished(8000)
        print n.__dict__
        self.sched.actions[n.id] = n
        self.sched.put_results(n)
        # Should have raised something like "Warning: the notification command 'BADCOMMAND' raised an error (exit code=2): '[Errno 2] No such file or directory'"
        # Ok, in HUDSON, we got a problem here. so always run with a shell run before release please
        if os.environ.get('HUDSON_URL', None):
            return

        self.assert_any_log_match('.*BADCOMMAND.*')
        #self.assert_any_log_match(u'.*BADCOMMAND.*') or self.assert_any_log_match('.*BADCOMMAND.*')


if __name__ == '__main__':
    unittest.main()
