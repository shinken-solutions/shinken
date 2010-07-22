#!/usr/bin/env python2.6

#
# This file is used to test acknowledge of problems
#


#It's ugly I know....
from shinken_test import *

class TestConfig(ShinkenTest):
    def setUp(self):
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_1r_1h_1s.cfg']
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



    def test_ack_soft_service(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']])
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assert_(svc.current_notification_number == 0)

        #--------------------------------------------------------------
        # service reaches soft;1
        # there must not be any notification
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_actions()

        #--------------------------------------------------------------
        # someone acknowldeges the problem before a notification goes out
        #--------------------------------------------------------------
        self.assert_(not svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;1;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(svc.problem_has_been_acknowledged)
        self.log_match(0, 'ACKNOWLEDGEMENT \(CRITICAL\)')
        self.show_and_clear_logs()
        self.show_actions()

        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created but blocked
        # log for alert hard and log for eventhandler
        #--------------------------------------------------------------
        print "- 1 x BAD get hard -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(self.count_logs() == 2)
        self.assert_(svc.current_notification_number == 0)

        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created but blocked
        # notification number must be 0
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assert_(svc.current_notification_number == 0)


# service gets hard, notification is sent
# acknowledge
# no repetition of notifications
# ack deleted, notifications again
#    REMOVE_SVC_ACKNOWLEDGEMENT;<host_name>;<service_description>



if __name__ == '__main__':
    unittest.main()
