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
# This file is used to test host- and service-downtimes.
#

from shinken_test import *


class TestProblemImpact(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_problem_impact.cfg')

    def test_problems_impacts(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification

        # First initialize routers 0 and 1
        now = time.time()

        # The problem_impact_state change should be enabled in the configuration
        self.assert_(self.conf.enable_problem_impacts_states_change == True)

        host_router_0 = self.sched.hosts.find_by_name("test_router_0")
        host_router_0.checks_in_progress = []
        self.assert_(host_router_0.business_impact == 2)
        host_router_1 = self.sched.hosts.find_by_name("test_router_1")
        host_router_1.checks_in_progress = []
        self.assert_(host_router_1.business_impact == 2)

        # Then initialize host under theses routers
        host_0 = self.sched.hosts.find_by_name("test_host_0")
        host_0.checks_in_progress = []
        host_1 = self.sched.hosts.find_by_name("test_host_1")
        host_1.checks_in_progress = []

        all_hosts = [host_router_0, host_router_1, host_0, host_1]
        all_routers = [host_router_0, host_router_1]
        all_servers = [host_0, host_1]

        #--------------------------------------------------------------
        # initialize host states as UP
        #--------------------------------------------------------------
        print "- 4 x UP -------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 0, 'UP'], [host_router_1, 0, 'UP'], [host_0, 0, 'UP'], [host_1, 0, 'UP']], do_sleep=False)

        for h in all_hosts:
            self.assert_(h.state == 'UP')
            self.assert_(h.state_type == 'HARD')

        #--------------------------------------------------------------
        # Now we add some problems to routers
        #--------------------------------------------------------------
        print "- routers get DOWN /SOFT-------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        # Max attempt is at 5, should be soft now
        for h in all_routers:
            self.assert_(h.state == 'DOWN')
            self.assert_(h.state_type == 'SOFT')

        print "- routers get DOWN /HARD-------------------------------------"
        # Now put 4 more checks so we get DOWN/HARD
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)

        # Max attempt is reach, should be HARD now
        for h in all_routers:
            self.assert_(h.state == 'DOWN')
            self.assert_(h.state_type == 'HARD')

        #--------------------------------------------------------------
        # Routers get HARD/DOWN
        # should be problems now!
        #--------------------------------------------------------------
        # Now check in the brok generation too
        host_router_0_brok = host_router_0.get_update_status_brok()
        host_router_0_brok.prepare()
        host_router_1_brok = host_router_1.get_update_status_brok()
        host_router_1_brok.prepare()

        # Should be problems and have sub servers as impacts
        for h in all_routers:
            self.assert_(h.is_problem == True)
            # Now routers are problems, they should have take the max
            # business_impact value ofthe impacts, so here 5
            self.assert_(h.business_impact == 5)
            for s in all_servers:
                self.assert_(s in h.impacts)
                self.assert_(s.get_dbg_name() in host_router_0_brok.data['impacts']['hosts'])
                self.assert_(s.get_dbg_name() in host_router_1_brok.data['impacts']['hosts'])

        # Should have host notification, but it's not so simple:
        # our contact say: not under 5, and our hosts are 2. But
        # the impacts have huge business_impact, so the hosts gain such business_impact
        self.assert_(self.any_log_match('HOST NOTIFICATION.*;'))
        self.show_and_clear_logs()


        # Now impacts should really be .. impacts :)
        for s in all_servers:
            self.assert_(s.is_impact == True)
            self.assert_(s.state == 'UNREACHABLE')
            # And check the services are impacted too
            for svc in s.services:
                print "Service state", svc.state
                self.assert_(svc.state == 'UNKNOWN')
                self.assert_(svc.get_dbg_name() in host_router_0_brok.data['impacts']['services'])
                self.assert_(svc.get_dbg_name() in host_router_1_brok.data['impacts']['services'])
                brk_svc = svc.get_update_status_brok()
                brk_svc.prepare()
                self.assert_(brk_svc.data['source_problems']['hosts'] == ['test_router_0', 'test_router_1'])
            for h in all_routers:
                self.assert_(h in s.source_problems)
                brk_hst = s.get_update_status_brok()
                brk_hst.prepare()
                self.assert_(h.get_dbg_name() in brk_hst.data['source_problems']['hosts'])

        #--------------------------------------------------------------
        # One router get UP now
        #--------------------------------------------------------------
        print "- 1 X UP for a router ------------------------------"
        # Ok here the problem/impact propagation is Checked. Now what
        # if one router get back? :)
        self.scheduler_loop(1, [[host_router_0, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assert_(host_router_0.state == 'UP')
        self.assert_(host_router_0.state_type == 'HARD')

        # And should not be a problem any more!
        self.assert_(host_router_0.is_problem == False)
        self.assert_(host_router_0.impacts == [])

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assert_(s.is_impact == True)
            self.assert_(s.source_problems == [host_router_1])

        #--------------------------------------------------------------
        # The other router get UP :)
        #--------------------------------------------------------------
        print "- 1 X UP for the last router ------------------------------"
        # What is the last router get back? :)
        self.scheduler_loop(1, [[host_router_1, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assert_(host_router_1.state == 'UP')
        self.assert_(host_router_1.state_type == 'HARD')

        # And should not be a problem any more!
        self.assert_(host_router_1.is_problem == False)
        self.assert_(host_router_1.impacts == [])

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assert_(s.is_impact == False)
            self.assert_(s.state == 'UP')
            self.assert_(s.source_problems == [])

        # And our "business_impact" should have failed back to our
        # conf value, so 2
        self.assert_(host_router_0.business_impact == 2)
        self.assert_(host_router_1.business_impact == 2)
        # It's done :)

    def test_problems_impacts_with_crit_mod(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification

        # First initialize routers 0 and 1
        now = time.time()

        # The problem_impact_state change should be enabled in the configuration
        self.assert_(self.conf.enable_problem_impacts_states_change == True)

        host_router_0 = self.sched.hosts.find_by_name("test_router_0")
        host_router_0.checks_in_progress = []
        self.assert_(host_router_0.business_impact == 2)
        host_router_1 = self.sched.hosts.find_by_name("test_router_1")
        host_router_1.checks_in_progress = []
        self.assert_(host_router_1.business_impact == 2)

        # Then initialize host under theses routers
        host_0 = self.sched.hosts.find_by_name("test_host_0")
        host_0.checks_in_progress = []
        host_1 = self.sched.hosts.find_by_name("test_host_1")
        host_1.checks_in_progress = []

        all_hosts = [host_router_0, host_router_1, host_0, host_1]
        all_routers = [host_router_0, host_router_1]
        all_servers = [host_0, host_1]

        # Our crit mod that will allow us to play with on the fly
        # business_impact modulation
        critmod = self.sched.conf.businessimpactmodulations.find_by_name('Raise')
        self.assert_(critmod is not None)

        # We lie here, from now we do not want criticities
        for h in all_hosts:
            for s in h.services:
                s.business_impact = 2

        #--------------------------------------------------------------
        # initialize host states as UP
        #--------------------------------------------------------------
        print "- 4 x UP -------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 0, 'UP'], [host_router_1, 0, 'UP'], [host_0, 0, 'UP'], [host_1, 0, 'UP']], do_sleep=False)

        for h in all_hosts:
            self.assert_(h.state == 'UP')
            self.assert_(h.state_type == 'HARD')

        #--------------------------------------------------------------
        # Now we add some problems to routers
        #--------------------------------------------------------------
        print "- routers get DOWN /SOFT-------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        # Max attempt is at 5, should be soft now
        for h in all_routers:
            self.assert_(h.state == 'DOWN')
            self.assert_(h.state_type == 'SOFT')

        print "- routers get DOWN /HARD-------------------------------------"
        # Now put 4 more checks so we get DOWN/HARD
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)

        # Max attempt is reach, should be HARD now
        for h in all_routers:
            self.assert_(h.state == 'DOWN')
            self.assert_(h.state_type == 'HARD')

        #--------------------------------------------------------------
        # Routers get HARD/DOWN
        # should be problems now!
        #--------------------------------------------------------------
        # Now check in the brok generation too
        host_router_0_brok = host_router_0.get_update_status_brok()
        host_router_0_brok.prepare()
        host_router_1_brok = host_router_1.get_update_status_brok()
        host_router_1_brok.prepare()

        # Should be problems and have sub servers as impacts
        for h in all_routers:
            self.assert_(h.is_problem == True)
            # Now routers are problems, they should have take the max
            # business_impact value ofthe impacts, so here 2 because we lower all critcity for our test
            self.assert_(h.business_impact == 2)
            for s in all_servers:
                self.assert_(s in h.impacts)
                self.assert_(s.get_dbg_name() in host_router_0_brok.data['impacts']['hosts'])
                self.assert_(s.get_dbg_name() in host_router_1_brok.data['impacts']['hosts'])

        # Should have host notification, but it's not so simple:
        # our contact say: not under 5, and our hosts are 2. And here
        # the business_impact was still low for our test
        self.assert_(not self.any_log_match('HOST NOTIFICATION.*;'))
        self.show_and_clear_logs()


        # Now impacts should really be .. impacts :)
        for s in all_servers:
            self.assert_(s.is_impact == True)
            self.assert_(s.state == 'UNREACHABLE')
            # And check the services are impacted too
            for svc in s.services:
                print "Service state", svc.state
                self.assert_(svc.state == 'UNKNOWN')
                self.assert_(svc.get_dbg_name() in host_router_0_brok.data['impacts']['services'])
                self.assert_(svc.get_dbg_name() in host_router_1_brok.data['impacts']['services'])
                brk_svc = svc.get_update_status_brok()
                brk_svc.prepare()
                self.assert_(brk_svc.data['source_problems']['hosts'] == ['test_router_0', 'test_router_1'])
            for h in all_routers:
                self.assert_(h in s.source_problems)
                brk_hst = s.get_update_status_brok()
                brk_hst.prepare()
                self.assert_(h.get_dbg_name() in brk_hst.data['source_problems']['hosts'])


        for h in all_hosts:
            for s in h.services:
                s.update_business_impact_value()
                self.assert_(s.business_impact == 2)

        # Now we play with modulation!
        # We put modulation period as None so it will be right all time :)
        critmod.modulation_period = None

        crit_srv = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_ok_1")
        self.assert_(critmod in crit_srv.business_impact_modulations)

        # Now we set the modulation period as always good, we check that the service
        # really update it's business_impact value
        self.sched.update_business_values()
        # So the service with the modulation should got it's business_impact raised
        self.assert_(crit_srv.business_impact == 5)
        # And the routers too (problems)
        self.assert_(host_router_0.business_impact == 5)
        self.assert_(host_router_1.business_impact == 5)

        #--------------------------------------------------------------
        # One router get UP now
        #--------------------------------------------------------------
        print "- 1 X UP for a router ------------------------------"
        # Ok here the problem/impact propagation is Checked. Now what
        # if one router get back? :)
        self.scheduler_loop(1, [[host_router_0, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assert_(host_router_0.state == 'UP')
        self.assert_(host_router_0.state_type == 'HARD')

        # And should not be a problem any more!
        self.assert_(host_router_0.is_problem == False)
        self.assert_(host_router_0.impacts == [])

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assert_(s.is_impact == True)
            self.assert_(s.source_problems == [host_router_1])

        #--------------------------------------------------------------
        # The other router get UP :)
        #--------------------------------------------------------------
        print "- 1 X UP for the last router ------------------------------"
        # What is the last router get back? :)
        self.scheduler_loop(1, [[host_router_1, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assert_(host_router_1.state == 'UP')
        self.assert_(host_router_1.state_type == 'HARD')

        # And should not be a problem any more!
        self.assert_(host_router_1.is_problem == False)
        self.assert_(host_router_1.impacts == [])

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assert_(s.is_impact == False)
            self.assert_(s.state == 'UP')
            self.assert_(s.source_problems == [])

        # And our "business_impact" should have failed back to our
        # conf value, so 2
        self.assert_(host_router_0.business_impact == 2)
        self.assert_(host_router_1.business_impact == 2)
        # It's done :)



if __name__ == '__main__':
    unittest.main()
