#!/usr/bin/env python2.6
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class TestConfig(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_business_correlator.cfg')

    
    # We will try a simple bd1 OR db2
    def test_simple_business_correlator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        
        svc_bd1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db1")
        self.assert_(svc_bd1.got_business_rule == False)
        self.assert_(svc_bd1.business_rule == None)
        svc_bd2 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "db2")
        self.assert_(svc_bd2.got_business_rule == False)
        self.assert_(svc_bd2.business_rule == None)
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "Simple_Or")
        self.assert_(svc_cor.got_business_rule == True)
        self.assert_(svc_cor.business_rule != None)
        bp_rule = svc_cor.business_rule
        self.assert_(bp_rule.operand == '|')

        sons = bp_rule.sons
        print "Sons,", sons
        #We(ve got 2 sons, 2 services nodes
        self.assert_(len(sons) == 2)
        self.assert_(sons[0].operand == 'service')
        self.assert_(sons[0].sons[0] == svc_bd1)
        self.assert_(sons[1].operand == 'service')
        self.assert_(sons[1].sons[0] == svc_bd2)
        
        # Now state working on the states
        self.scheduler_loop(1, [[svc_bd2, 0, 'OK | value1=1 value2=2'], [svc_bd1, 0, 'OK | rtt=10']])        
        self.assert_(svc_bd1.state == 'OK')
        self.assert_(svc_bd1.state_type == 'HARD')
        self.assert_(svc_bd2.state == 'OK')
        self.assert_(svc_bd2.state_type == 'HARD')
        
        state = bp_rule.get_state()
        self.assert_(state == 0)
        


if __name__ == '__main__':
    unittest.main()

