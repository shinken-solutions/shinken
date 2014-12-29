#!/usr/bin/env python
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Sebastien Coavoux, s.coavoux@free.fr
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


import time



from shinken_test import ShinkenTest, unittest

from shinken.notification import Notification



class TestMasterNotif(ShinkenTest):

    # For a service, we generate a notification and a event handler.
    # Each one got a specific reactionner_tag that we will look for.
    def test_master_notif(self):
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'BAD | value1=0 value2=0']])

        ### hack Notification.__init__ to save the newly created instances :
        _new_notifs = []
        _old_notif_init = Notification.__init__
        def _mock_notif_init(self, *a, **kw):
            _old_notif_init(self, *a, **kw)
            _new_notifs.append(self) # save it!
        Notification.__init__ = _mock_notif_init
        try:
            # this scheduler_loop will create a new notification:
            self.scheduler_loop(2, [[svc, 2, 'BAD | value1=0 value2=0']])
        finally: # be courteous and always undo what we've mocked once we don't need  it anymore:
            Notification.__init__ =  _old_notif_init
        self.assertNotEqual(0, len(_new_notifs),
                            "A Notification should have been created !")
        guessed_notif = _new_notifs[0] # and we hope that it's the good one..
        self.assertIs(guessed_notif, self.sched.actions.get(guessed_notif.id, None),
                      "Our guessed notification does not match what's in scheduler actions dict !\n"
                      "guessed_notif=[%s] sched.actions=%r" % (guessed_notif, self.sched.actions))

        guessed_notif.t_to_go = time.time()  # Hack to set t_to_go now, so that the notification is processed

        # Try to set master notif status to inpoller
        actions = self.sched.get_to_run_checks(False, True)
        # But no, still scheduled
        self.assertEqual('scheduled', guessed_notif.status)
        # And still no action for our receivers
        self.assertEqual([], actions)



if __name__ == '__main__':
    unittest.main()
