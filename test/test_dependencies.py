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
# This file is used to test host- and service-downtimes.
#

from shinken_test import *
sys.setcheckinterval(10000)


class TestConfig(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_dependencies.cfg')

    def test_service_dependencies(self):
        self.print_header()
        now = time.time()
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_host_1 = self.sched.hosts.find_by_name("test_host_1")
        test_host_0.checks_in_progress = []
        test_host_1.checks_in_progress = []
        test_host_0.act_depend_of = []  # ignore the router
        test_host_1.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore other routers
        test_host_0_test_ok_0 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        test_host_0_test_ok_1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_1")
        test_host_1_test_ok_0 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_ok_0")
        test_host_1_test_ok_1 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_ok_1")
        # the most important: test_ok_0 is in the chk_depend_of-list of test_ok_1
        self.assertIn(test_host_0_test_ok_0, [x[0] for x in test_host_0_test_ok_1.chk_depend_of])
        self.assertIn(test_host_1_test_ok_0, [x[0] for x in test_host_1_test_ok_1.chk_depend_of])

        # and not vice versa
        self.assertNotIn(test_host_0_test_ok_1, [x[0] for x in test_host_0_test_ok_0.chk_depend_of])
        self.assertNotIn(test_host_1_test_ok_1, [x[0] for x in test_host_1_test_ok_0.chk_depend_of])

        # test_ok_0 is also in the act_depend_of-list of test_ok_1
        self.assertIn(test_host_0_test_ok_0, [x[0] for x in test_host_0_test_ok_1.chk_depend_of])
        self.assertIn(test_host_1_test_ok_0, [x[0] for x in test_host_1_test_ok_1.chk_depend_of])

        # check the criteria
        # execution_failure_criteria      u,c
        # notification_failure_criteria   u,c,w
        self.assertEqual([x[1] for x in test_host_0_test_ok_1.chk_depend_of if x[0] is test_host_0_test_ok_0], [['u', 'c']] )
        self.assertEqual([x[1] for x in test_host_1_test_ok_1.chk_depend_of if x[0] is test_host_1_test_ok_0], [['u', 'c']] )
        self.assertEqual([x[1] for x in test_host_0_test_ok_1.act_depend_of if x[0] is test_host_0_test_ok_0], [['u', 'c', 'w']] )
        self.assertEqual([x[1] for x in test_host_1_test_ok_1.act_depend_of if x[0] is test_host_1_test_ok_0], [['u', 'c', 'w']] )

        # and every service has the host in it's act_depend_of-list
        self.assertIn(test_host_0, [x[0] for x in test_host_0_test_ok_0.act_depend_of])
        self.assertIn(test_host_0, [x[0] for x in test_host_0_test_ok_1.act_depend_of])
        self.assertIn(test_host_1, [x[0] for x in test_host_1_test_ok_0.act_depend_of])
        self.assertIn(test_host_1, [x[0] for x in test_host_1_test_ok_1.act_depend_of])

        # and final count the masters
        self.assertEqual(0, len(test_host_0_test_ok_0.chk_depend_of))
        self.assertEqual(1, len(test_host_0_test_ok_1.chk_depend_of))
        self.assertEqual(0, len(test_host_1_test_ok_0.chk_depend_of))
        self.assertEqual(1, len(test_host_1_test_ok_1.chk_depend_of))
        self.assertEqual(1, len(test_host_0_test_ok_0.act_depend_of))  # same, plus the host
        self.assertEqual(2, len(test_host_0_test_ok_1.act_depend_of))
        self.assertEqual(1, len(test_host_1_test_ok_0.act_depend_of))
        self.assertEqual(2, len(test_host_1_test_ok_1.act_depend_of))

    def test_host_dependencies(self):
        self.print_header()
        now = time.time()
        #
        #   A  <------  B  <--
        #   ^                 \---  C
        #   |---------------------
        #
        host_A = self.sched.hosts.find_by_name("test_host_A")
        host_B = self.sched.hosts.find_by_name("test_host_B")
        host_C = self.sched.hosts.find_by_name("test_host_C")
        host_D = self.sched.hosts.find_by_name("test_host_D")

        # the most important: test_ok_0 is in the chk_depend_of-list of test_ok_1
        #self.assertTrue(host_A in [x[0] for x in host_C.chk_depend_of])
        print host_C.act_depend_of
        print host_C.chk_depend_of
        print host_C.chk_depend_of_me
        self.assertIn(host_B, [x[0] for x in host_C.act_depend_of])
        self.assertIn(host_A, [x[0] for x in host_C.act_depend_of])
        self.assertIn(host_A, [x[0] for x in host_B.act_depend_of])
        self.assertEqual([], host_A.act_depend_of)
        self.assertIn(host_B, [x[0] for x in host_C.chk_depend_of])
        self.assertIn(host_A, [x[0] for x in host_C.chk_depend_of])
        self.assertIn(host_A, [x[0] for x in host_B.chk_depend_of])
        self.assertEqual([], host_A.act_depend_of)
        self.assertIn(host_B, [x[0] for x in host_A.act_depend_of_me])
        self.assertIn(host_C, [x[0] for x in host_A.act_depend_of_me])
        self.assertIn(host_C, [x[0] for x in host_B.act_depend_of_me])
        #self.assertEqual([], host_C.act_depend_of_me) # D in here
        self.assertIn(host_B, [x[0] for x in host_A.chk_depend_of_me])
        self.assertIn(host_C, [x[0] for x in host_A.chk_depend_of_me])
        self.assertIn(host_C, [x[0] for x in host_B.chk_depend_of_me])
        self.assertIn(host_D, [x[0] for x in host_C.chk_depend_of_me])

        # check the notification/execution criteria
        self.assertEqual([['d', 'u']], [x[1] for x in host_C.act_depend_of if x[0] is host_B])
        self.assertEqual([['d']],       [x[1] for x in host_C.chk_depend_of if x[0] is host_B])
        self.assertEqual([['d', 'u']], [x[1] for x in host_C.act_depend_of if x[0] is host_A])
        self.assertEqual([['d']],       [x[1] for x in host_C.chk_depend_of if x[0] is host_A])
        self.assertEqual([['d', 'u']], [x[1] for x in host_B.act_depend_of if x[0] is host_A])
        self.assertEqual([['n']],       [x[1] for x in host_B.chk_depend_of if x[0] is host_A])

    def test_host_inherits_dependencies(self):
        self.print_header()
        now = time.time()
        #
        #   A  <------  B  <--
        #   ^                 \---  C   <--  D
        #   |---------------------
        #
        host_A = self.sched.hosts.find_by_name("test_host_A")
        host_B = self.sched.hosts.find_by_name("test_host_B")
        host_C = self.sched.hosts.find_by_name("test_host_C")
        host_D = self.sched.hosts.find_by_name("test_host_D")

        print "A depends on", ",".join([x[0].get_name() for x in host_A.chk_depend_of])
        print "B depends on", ",".join([x[0].get_name() for x in host_B.chk_depend_of])
        print "C depends on", ",".join([x[0].get_name() for x in host_C.chk_depend_of])
        print "D depends on", ",".join([x[0].get_name() for x in host_D.chk_depend_of])

        self.assertEqual([], host_A.act_depend_of)
        self.assertIn(host_A, [x[0] for x in host_B.act_depend_of])
        self.assertIn(host_A, [x[0] for x in host_C.act_depend_of])
        self.assertIn(host_B, [x[0] for x in host_C.act_depend_of])
        self.assertIn(host_C, [x[0] for x in host_D.act_depend_of])

        # and through inherits_parent....
        #self.assertTrue(host_A in [x[0] for x in host_D.act_depend_of])
        #self.assertTrue(host_B in [x[0] for x in host_D.act_depend_of])


    # Now test a in service service_dep definition. More easierto use than create a full new object
    def test_in_servicedef_dep(self):
        svc_parent = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_parent_svc")
        svc_son = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_son_svc")

        print "DumP", self.conf.servicedependencies

        # the most important: test_parent is in the chk_depend_of-list of test_son
        print "Dep: ", svc_son.act_depend_of
        self.assertEqual([x[1] for x in svc_son.act_depend_of if x[0] is svc_parent], [['u', 'c', 'w']] )

    def test_host_non_inherits_dependencies(self):
        #
        #   A  <------  B  <--
        #   ^                 \NOT/---  C   <--  D
        #   |---------------------
        #
        host_A = self.sched.hosts.find_by_name("test_host_A")
        host_B = self.sched.hosts.find_by_name("test_host_B")
        host_C = self.sched.hosts.find_by_name("test_host_C")
        host_D = self.sched.hosts.find_by_name("test_host_D")
        host_E = self.sched.hosts.find_by_name("test_host_E")

        print "A depends on", ",".join([x[0].get_name() for x in host_A.chk_depend_of])
        print "B depends on", ",".join([x[0].get_name() for x in host_B.chk_depend_of])
        print "C depends on", ",".join([x[0].get_name() for x in host_C.chk_depend_of])
        print "D depends on", ",".join([x[0].get_name() for x in host_D.chk_depend_of])
        print "E depends on", ",".join([x[0].get_name() for x in host_E.chk_depend_of])

        host_C.state = 'DOWN'
        print "D state", host_D.state
        print "E dep", host_E.chk_depend_of
        print "I raise?", host_D.do_i_raise_dependency('d', inherit_parents=False)
        # If I ask D for dep, he should raise Nothing if we do not want parents.
        self.assertFalse(host_D.do_i_raise_dependency('d', inherit_parents=False) )
        # But he should raise a problem (C here) of we ask for its parents
        self.assertTrue(host_D.do_i_raise_dependency('d', inherit_parents=True) )


    def test_check_dependencies(self):
        self.print_header()
        now = time.time()
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_host_0.checks_in_progress = []
        test_host_0.act_depend_of = []  # ignore the router

        test_host_0_test_ok_0 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        # The pending state is always different. Let assume it OK
        test_host_0.state = 'OK'

        # Create a fake check already done for service
        cs = Check('waitconsume', 'foo', test_host_0_test_ok_0, now)
        cs.exit_status = 2
        cs.output = 'BAD'
        cs.check_time = now
        cs.execution_time = now

        # Create a fake check for the host (so that it is in checking)
        ch = Check('scheduled', 'foo', test_host_0, now)
        test_host_0.checks_in_progress.append(ch)


        # This service should have his host dep
        self.assertNotEqual(0, len(test_host_0_test_ok_0.act_depend_of))

        # Ok we are at attempt 0 (we should have a 1 with the OK state, but nervermind)
        self.assertEqual(0, test_host_0.attempt)

        # Add the check to sched queue
        self.sched.add(cs)
        self.sched.add(ch)
        # This should raise a log entry and schedule the host check now
        self.sched.consume_results()

        # Take the host check. The one generated by dependency not the usual one
        c_dep = test_host_0.actions[1]
        self.assertTrue(bool(c_dep.dependency_check))

        # Hack it to consider it as down and returning critical state
        c_dep.status = 'waitconsume'
        c_dep.exit_status = 2
        c_dep.output = 'BAD'
        c_dep.check_time = now
        c_dep.execution_time = now

        # Add and process result
        self.sched.add(c_dep)
        self.sched.consume_results()

        # We should not have a new attempt as it was a depency check.
        self.assertEqual(0, test_host_0.attempt)


    def test_disabled_host_service_dependencies(self):
        self.print_header()
        now = time.time()
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_host_0.checks_in_progress = []
        test_host_0.act_depend_of = []  # ignore the router
        test_host_0_test_ok_0_d = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0_disbld_hst_dep")
        self.assertEqual(0, len(test_host_0_test_ok_0_d.act_depend_of))
        self.assertNotIn(test_host_0_test_ok_0_d, [x[0] for x in test_host_0.act_depend_of_me])




if __name__ == '__main__':
    import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="Thruk.profile" )
