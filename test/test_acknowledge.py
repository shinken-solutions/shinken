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
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(5, 'SERVICE NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        # clean up
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.clear_logs()
        self.clear_actions()
        
        #--------------------------------------------------------------
        # service reaches soft;1
        # there must not be any notification
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 0)

        #--------------------------------------------------------------
        # someone acknowledges the problem before a notification goes out
        #--------------------------------------------------------------
        self.assert_(not svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;0;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(svc.problem_has_been_acknowledged)
        self.assert_(self.log_match(3, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.show_and_clear_logs()
        self.show_actions()
        self.sched.update_downtimes_and_comments()
        self.assert_(len(svc.comments) == 1)

        
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created but blocked
        # log for alert hard and log for eventhandler
        #--------------------------------------------------------------
        print "- 1 x BAD get hard -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(self.count_logs() == 2)
        self.assert_(self.count_actions() == 2)
        self.assert_(svc.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # recover
        # the acknowledgement must have been removed automatically
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        print "- 1 x OK recover"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3) # alert, eventhndlr, notification
        self.assert_(self.count_actions() == 3) # evt, master notif, contact notif
        self.assert_(not svc.problem_has_been_acknowledged)
        self.assert_(svc.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_ack_hard_service(self):
        self.print_header()
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
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(5, 'SERVICE NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # stay hard and wait for the second notification (notification_interval)
        #--------------------------------------------------------------
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == 2)

        #--------------------------------------------------------------
        # admin wakes up and acknowledges the problem
        # the ACK is the only log message
        # a master notification is still around, but can't be sent
        #--------------------------------------------------------------
        self.assert_(not svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;0;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(svc.problem_has_been_acknowledged)
        self.assert_(self.log_match(1, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.assert_(self.count_logs() == 1) 
        self.assert_(self.count_actions() == 1) 
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # remove acknowledgement
        # now notifications are sent again
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] REMOVE_SVC_ACKNOWLEDGEMENT;test_host_0;test_ok_0" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.show_logs()
        self.show_actions()
        # the contact notification was sent immediately (t_to_go)
        self.assert_(not svc.problem_has_been_acknowledged)
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.show_logs()
        self.show_actions()
        self.assert_(self.log_match(1, 'SERVICE NOTIFICATION'))
        self.assert_(self.log_match(2, 'SERVICE NOTIFICATION'))
        self.assert_(self.count_logs() == 2)
        self.assert_(self.count_actions() == 2) # master sched, contact zombie
        self.assert_(svc.current_notification_number == 4)
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # recover
        # the acknowledgement must have been removed automatically
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        print "- 1 x OK recover"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3) # alert, eventhndlr, notification
        self.assert_(self.count_actions() == 3) # evt, master notif, contact notif
        self.assert_(not svc.problem_has_been_acknowledged)
        self.assert_(svc.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_ack_nonsticky_changing_service(self):
        # acknowledge is not sticky
        # service goes from critical to warning
        # this means, the acknowledge deletes itself
        self.print_header()
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
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(5, 'SERVICE NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # stay hard and wait for the second notification (notification_interval)
        #--------------------------------------------------------------
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == 2)

        #--------------------------------------------------------------
        # admin wakes up and acknowledges the problem
        # the ACK is the only log message
        # a master notification is still around, but can't be sent
        #--------------------------------------------------------------
        self.assert_(not svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;1;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(svc.problem_has_been_acknowledged)
        self.assert_(self.log_match(1, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.assert_(self.count_logs() == 1) 
        self.assert_(self.count_actions() == 1) 
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # now become warning
        # ack is deleted automatically and notifications are sent again
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[svc, 1, 'NOT REALLY BAD']], do_sleep=True)
        self.assert_(not svc.problem_has_been_acknowledged)
        self.show_logs()
        self.show_actions()
        self.assert_(self.log_match(1, 'SERVICE ALERT.*WARNING'))
        self.assert_(self.log_match(2, 'SERVICE NOTIFICATION'))
        self.assert_(self.log_match(3, 'SERVICE NOTIFICATION'))
        self.assert_(self.count_logs() == 3)
        self.assert_(self.count_actions() == 2) # master sched, contact zombie
        self.assert_(svc.current_notification_number == 4)
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # recover
        # the acknowledgement must have been removed automatically
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        print "- 1 x OK recover"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3) # alert, eventhndlr, notification
        self.assert_(self.count_actions() == 3) # evt, master notif, contact notif
        self.assert_(not svc.problem_has_been_acknowledged)
        self.assert_(svc.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_ack_sticky_changing_service(self):
        # acknowledge is sticky
        # service goes from critical to warning
        # still acknowledged
        self.print_header()
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
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(5, 'SERVICE NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # stay hard and wait for the second notification (notification_interval)
        #--------------------------------------------------------------
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == 2)

        #--------------------------------------------------------------
        # admin wakes up and acknowledges the problem
        # the ACK is the only log message
        # a master notification is still around, but can't be sent
        #--------------------------------------------------------------
        self.assert_(not svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;0;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(svc.problem_has_been_acknowledged)
        self.assert_(self.log_match(1, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.assert_(self.count_logs() == 1) 
        self.assert_(self.count_actions() == 1) 
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # now become warning
        # ack remains set
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[svc, 1, 'NOT REALLY BAD']], do_sleep=True)
        self.assert_(svc.problem_has_been_acknowledged)
        self.show_logs()
        self.show_actions()
        self.assert_(self.log_match(1, 'SERVICE ALERT.*WARNING'))
        self.assert_(self.count_logs() == 1) # alert
        self.assert_(svc.current_notification_number == 2)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(len(svc.comments) == 1)
        self.assert_(svc.comments[0].comment == 'blablub')
        
        #--------------------------------------------------------------
        # recover
        # the acknowledgement must have been removed automatically
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        print "- 1 x OK recover"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3) # alert, eventhndlr, notification
        self.assert_(self.count_actions() == 3) # evt, master notif, contact notif
        self.assert_(not svc.problem_has_been_acknowledged)
        self.assert_(svc.current_notification_number == 0)
        self.assert_(len(svc.comments) == 0)
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_ack_soft_host(self):
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
        self.assert_(host.current_notification_number == 0)

        #--------------------------------------------------------------
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 3 x DOWN get hard -------------------------------------"
        self.scheduler_loop(3, [[host, 2, 'DOWN']])
        self.assert_(host.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(7, 'HOST NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        # clean up
        self.scheduler_loop(1, [[host, 0, 'UP']])
        self.clear_logs()
        self.clear_actions()
        
        #--------------------------------------------------------------
        # service reaches soft;1
        # there must not be any notification
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.assert_(host.current_notification_number == 0)

        #--------------------------------------------------------------
        # someone acknowledges the problem before a notification goes out
        #--------------------------------------------------------------
        self.assert_(not host.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_HOST_PROBLEM;test_host_0;1;1;0;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(host.problem_has_been_acknowledged)
        self.assert_(self.log_match(3, 'ACKNOWLEDGEMENT \(DOWN\)'))
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created but blocked
        # log for alert soft2, hard3 and log for eventhandler soft2, hard3
        # eventhandler hard3 (eventhandler soft2 is already zombied when
        # the workerloop is finished
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 4)
        self.assert_(self.count_actions() == 2)
        self.assert_(host.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # recover
        # the acknowledgement must have been removed automatically
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']])
        print "- 1 x OK recover"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3) # alert, eventhndlr, notification
        self.assert_(self.count_actions() == 3) # evt, master notif, contact notif
        self.assert_(not host.problem_has_been_acknowledged)
        self.assert_(host.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_ack_hard_host(self):
        self.print_header()
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
        self.assert_(host.current_notification_number == 0)

        #--------------------------------------------------------------
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(3, [[host, 2, 'DOWN']])
        self.assert_(host.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(7, 'HOST NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # stay hard and wait for the second notification (notification_interval)
        #--------------------------------------------------------------
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[host, 2, 'DOWN']], do_sleep=True)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(host.current_notification_number == 2)

        #--------------------------------------------------------------
        # admin wakes up and acknowledges the problem
        # the ACK is the only log message
        # a master notification is still around, but can't be sent
        #--------------------------------------------------------------
        self.assert_(not host.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_HOST_PROBLEM;test_host_0;1;1;0;lausser;blablub" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(host.problem_has_been_acknowledged)
        self.assert_(self.log_match(1, 'ACKNOWLEDGEMENT \(DOWN\)'))
        self.scheduler_loop(2, [[host, 2, 'DOWN']], do_sleep=True)
        self.assert_(self.count_logs() == 1) 
        self.assert_(self.count_actions() == 1) 
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # remove acknowledgement
        # now notifications are sent again
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] REMOVE_HOST_ACKNOWLEDGEMENT;test_host_0" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        # the contact notification was sent immediately (t_to_go)
        self.assert_(not host.problem_has_been_acknowledged)
        self.scheduler_loop(2, [[host, 2, 'DOWN']], do_sleep=True)
        self.show_logs()
        self.show_actions()
        self.assert_(self.log_match(1, 'HOST NOTIFICATION'))
        self.assert_(self.log_match(2, 'HOST NOTIFICATION'))
        self.assert_(self.count_logs() == 2)
        self.assert_(self.count_actions() == 2) # master sched, contact zombie
        self.assert_(host.current_notification_number == 4)
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # recover
        # the acknowledgement must have been removed automatically
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'GOOD']])
        print "- 1 x OK recover"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3) # alert, eventhndlr, notification
        self.assert_(self.count_actions() == 3) # evt, master notif, contact notif
        self.assert_(not host.problem_has_been_acknowledged)
        self.assert_(host.current_notification_number == 0)
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_unack_removes_comments(self):
# critical
# ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;1;test_contact_alias;ackweb6
# ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;1;test_contact_alias;ackweb6
# ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;0;test_contact_alias;acknull
# now remove the ack
# the first two comments remain. So persistent not only means "survice a reboot"
# but also "stay after the ack has been deleted"
        self.print_header()
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
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard, 
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.assert_(svc.current_notification_number == 1)
        self.assert_(self.count_actions() == 3) 
        self.assert_(self.log_match(5, 'SERVICE NOTIFICATION'))
        self.show_and_clear_logs()
        self.show_actions()
        
        #--------------------------------------------------------------
        # stay hard and wait for the second notification (notification_interval)
        #--------------------------------------------------------------
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == 2)

        #--------------------------------------------------------------
        # admin wakes up and acknowledges the problem
        # the ACK is the only log message
        # a master notification is still around, but can't be sent
        #--------------------------------------------------------------
        self.assert_(not svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;1;lausser;blablub1" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;1;lausser;blablub2" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;2;1;0;lausser;blablub3" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(svc.problem_has_been_acknowledged)
        self.assert_(self.log_match(1, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.assert_(self.log_match(2, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.assert_(self.log_match(3, 'ACKNOWLEDGEMENT \(CRITICAL\)'))
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True)
        self.assert_(self.count_actions() == 1) 
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(len(svc.comments) == 3)
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True)
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == 2)
        
        #--------------------------------------------------------------
        # remove the ack. the 2 persistent comments must remain
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] REMOVE_SVC_ACKNOWLEDGEMENT;test_host_0;test_ok_0" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_(not svc.problem_has_been_acknowledged)
        self.assert_(len(svc.comments) == 2)
        self.assert_(svc.comments[0].comment == 'blablub1')
        self.assert_(svc.comments[1].comment == 'blablub2')


# service is critical, notification is out
# click on ack without setting the sticky checkbox in the webinterface
# EXTERNAL COMMAND: ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;0;test_contact_alias;weback
# now service is acknowledged and has a comment
# silence...
# service is warning
# notification is sent
# acknowledgement and comment have disappeared

# service is critical, notification is out
# send external command through the pipe 3 times
# ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;0;test_contact_alias;weback
# ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;0;test_contact_alias;weback
# ACKNOWLEDGE_SVC_PROBLEM;test_host_0;test_ok_0;1;1;0;test_contact_alias;weback
# now service is acknowledged and has 3 comments
# silence...
# service is warning
# notification is sent
# acknowledgement and comments have disappeared


if __name__ == '__main__':
    unittest.main()
