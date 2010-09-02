#!/usr/bin/env python2.6

#
# This file is used to test host- and service-downtimes.
#

from shinken_test import *
sys.setcheckinterval(10000)



class TestConfig(ShinkenTest):
    def setUp(self):
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_dependencies.cfg']
        self.conf = Config()
        self.conf.read_config(self.config_files)
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.clean_useless()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependancies()
        self.conf.explode_global_conf()
        self.conf.is_correct()
        self.confs = self.conf.cut_into_parts()
        self.dispatcher = Dispatcher(self.conf, self.me)
        self.sched = Scheduler(None)
        m = MacroResolver()
        m.init(self.conf)
        self.sched.load_conf(self.conf)
        e = ExternalCommand(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        self.sched.schedule()
        self.sched.fill_initial_broks()



    def test_service_dependencies(self):
        self.print_header()
        now = time.time()
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_host_1 = self.sched.hosts.find_by_name("test_host_1")
        test_host_0.checks_in_progress = []
        test_host_1.checks_in_progress = []
        test_host_0.act_depend_of = [] # ignore the router
        test_host_1.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore other routers
        test_host_0_test_ok_0 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        test_host_0_test_ok_1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_1")
        test_host_1_test_ok_0 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_ok_0")
        test_host_1_test_ok_1 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_ok_1")
        # the most important: test_ok_0 is in the chk_depend_of-list of test_ok_1
        self.assert_(test_host_0_test_ok_0 in [x[0] for x in test_host_0_test_ok_1.chk_depend_of])
        self.assert_(test_host_1_test_ok_0 in [x[0] for x in test_host_1_test_ok_1.chk_depend_of])

        # and not vice versa
        self.assert_(test_host_0_test_ok_1 not in [x[0] for x in test_host_0_test_ok_0.chk_depend_of])
        self.assert_(test_host_1_test_ok_1 not in [x[0] for x in test_host_1_test_ok_0.chk_depend_of])

        # test_ok_0 is also in the act_depend_of-list of test_ok_1
        self.assert_(test_host_0_test_ok_0 in [x[0] for x in test_host_0_test_ok_1.chk_depend_of])
        self.assert_(test_host_1_test_ok_0 in [x[0] for x in test_host_1_test_ok_1.chk_depend_of])

        # check the criteria
        # execution_failure_criteria      u,c
        # notification_failure_criteria   u,c,w
        self.assert_([['u', 'c']] == [x[1] for x in test_host_0_test_ok_1.chk_depend_of if x[0] is test_host_0_test_ok_0])
        self.assert_([['u', 'c']] == [x[1] for x in test_host_1_test_ok_1.chk_depend_of if x[0] is test_host_1_test_ok_0])
        self.assert_([['u', 'c', 'w']] == [x[1] for x in test_host_0_test_ok_1.act_depend_of if x[0] is test_host_0_test_ok_0])
        self.assert_([['u', 'c', 'w']] == [x[1] for x in test_host_1_test_ok_1.act_depend_of if x[0] is test_host_1_test_ok_0])

        # and every service has the host in it's act_depend_of-list
        self.assert_(test_host_0 in [x[0] for x in test_host_0_test_ok_0.act_depend_of])
        self.assert_(test_host_0 in [x[0] for x in test_host_0_test_ok_1.act_depend_of])
        self.assert_(test_host_1 in [x[0] for x in test_host_1_test_ok_0.act_depend_of])
        self.assert_(test_host_1 in [x[0] for x in test_host_1_test_ok_1.act_depend_of])

        # and final count the masters
        self.assert_(len(test_host_0_test_ok_0.chk_depend_of) == 0) 
        self.assert_(len(test_host_0_test_ok_1.chk_depend_of) == 1)
        self.assert_(len(test_host_1_test_ok_0.chk_depend_of) == 0)
        self.assert_(len(test_host_1_test_ok_1.chk_depend_of) == 1)
        self.assert_(len(test_host_0_test_ok_0.act_depend_of) == 1) # same, plus the host
        self.assert_(len(test_host_0_test_ok_1.act_depend_of) == 2)
        self.assert_(len(test_host_1_test_ok_0.act_depend_of) == 1)
        self.assert_(len(test_host_1_test_ok_1.act_depend_of) == 2)


if __name__ == '__main__':
    import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="Thruk.profile" )

