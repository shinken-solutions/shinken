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
from shinken.misc.regenerator import Regenerator


class TestRegenerator(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_regenerator.cfg')


    def look_for_same_values(self):
        # Look at Regenerator values
        print "Hosts:", self.rg.hosts.__dict__
        for h in self.rg.hosts:
            orig_h = self.sched.hosts.find_by_name(h.host_name)
            print h.state, orig_h.state
            # Look for same states
            self.assert_(h.state == orig_h.state)
            self.assert_(h.state_type == orig_h.state_type)
            # Look for same impacts
            for i in h.impacts:
                print "Got impact", i.get_name()
                same_impacts = i.get_name() in [j.get_name() for j in orig_h.impacts]
                self.assert_(same_impacts)
            # And look for same source problems
            for i in h.source_problems:
                print "Got source pb", i.get_name()
                same_pbs = i.get_name() in [j.get_name() for j in orig_h.source_problems]
                self.assert_(same_pbs)

            
                

        print "Services:", self.rg.services.__dict__
        for s in self.rg.services:
            orig_s = self.sched.services.find_srv_by_name_and_hostname(s.host.host_name, s.service_description)
            print s.state, orig_s.state
            self.assert_(s.state == orig_s.state)
            self.assert_(s.state_type == orig_s.state_type)
            #Look for same impacts too
            for i in s.impacts:
                print "Got impact", i.get_name()
                same_impacts = i.get_name() in [j.get_name() for j in orig_s.impacts]
                self.assert_(same_impacts)
            # And look for same source problems
            for i in s.source_problems:
                print "Got source pb", i.get_name()
                same_pbs = i.get_name() in [j.get_name() for j in orig_s.source_problems]
                self.assert_(same_pbs)
            # Look for same host
            self.assert_(s.host.get_name() == orig_s.host.get_name())
        

    
    #Change ME :)
    def test_regenerator(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        self.sched.fill_initial_broks()
        self.rg = Regenerator()

        # Got the initial creation ones
        ids = self.sched.broks.keys()
        ids.sort()
        for i in ids:
            b = self.sched.broks[i]
            print "Manage b", b.type
            self.rg.manage_brok(b)
        self.sched.broks.clear()

        self.look_for_same_values()

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
        self.scheduler_loop(3, [[host, 2, 'DOWN | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.assert_(host.state == 'DOWN')
        self.assert_(host.state_type == 'HARD')


        ids = self.sched.broks.keys()
        ids.sort()
        for i in ids:
            b = self.sched.broks[i]
            print "Manage b", b.type
            self.rg.manage_brok(b)
        self.sched.broks.clear()

        self.look_for_same_values()

        

        

if __name__ == '__main__':
    unittest.main()

