#!/usr/bin/env python2.6

#
# This file is used to test host- and service-downtimes.
#


from shinken_test import *


class TestConfig(ShinkenTest):
    def setUp(self):
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_problem_impact.cfg']
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
    
    

    def test_problems_impacts(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification

        #First initialize routers 0 and 1
        now = time.time()
        host_router_0 = self.sched.hosts.find_by_name("test_router_0")
        host_router_0.checks_in_progress = []
        host_router_1 = self.sched.hosts.find_by_name("test_router_1")
        host_router_1.checks_in_progress = []

        #Then initialize host under theses routers
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
        self.scheduler_loop(1, [[host_router_0, 1, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        #Max attempt is at 5, should be soft now
        for h in all_routers:
            self.assert_(h.state == 'DOWN')
            self.assert_(h.state_type == 'SOFT')

        print "- routers get DOWN /HARD-------------------------------------"
        #Now put 4 more checks so we get DOWN/HARD
        self.scheduler_loop(1, [[host_router_0, 1, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 1, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 1, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 1, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)

        #Max attempt is reach, should be HARD now
        for h in all_routers:
            self.assert_(h.state == 'DOWN')
            self.assert_(h.state_type == 'HARD')
        
                         
        #--------------------------------------------------------------
        # Routers get HARD/DOWN
        # should be problems now!
        #--------------------------------------------------------------
        #Should be problems and have sub servers as impacts
        for h in all_routers:
            self.assert_(h.is_problem == True)
            for s in all_servers:
                self.assert_(s in h.impacts)
        
        #Now impacts should really be .. impacts :)
        for s in all_servers:
            self.assert_(s.is_impact == True)
            self.assert_(s.state == 'UNREACHABLE')
            for h in all_routers:
                self.assert_(h in s.source_problems)

        #--------------------------------------------------------------
        # One router get UP now
        #--------------------------------------------------------------
        print "- 1 X UP for a router ------------------------------"
        #Ok here the problem/impact propagation is Checked. Now what
        #if one router get back? :)
        self.scheduler_loop(1, [[host_router_0, 0, 'UP']], do_sleep=False)
        
        #should be UP/HARD now
        self.assert_(host_router_0.state == 'UP')
        self.assert_(host_router_0.state_type == 'HARD')

        #And should not be a problem any more!
        self.assert_(host_router_0.is_problem == False)
        self.assert_(host_router_0.impacts == [])

        #And check if it's no more in sources problems of others servers
        for s in all_servers:
            #Still impacted by the other server
            self.assert_(s.is_impact == True)
            self.assert_(s.source_problems == [host_router_1])

        #--------------------------------------------------------------
        # The other router get UP :)
        #--------------------------------------------------------------
        print "- 1 X UP for the last router ------------------------------"
        #What is the last router get back? :)
        self.scheduler_loop(1, [[host_router_1, 0, 'UP']], do_sleep=False)

        #should be UP/HARD now
        self.assert_(host_router_1.state == 'UP')
        self.assert_(host_router_1.state_type == 'HARD')

        #And should not be a problem any more!
        self.assert_(host_router_1.is_problem == False)
        self.assert_(host_router_1.impacts == [])

        #And check if it's no more in sources problems of others servers
        for s in all_servers:
            #Still impacted by the other server
            self.assert_(s.is_impact == False)
            self.assert_(s.state == 'UP')
            self.assert_(s.source_problems == [])
        
        #It's done :)


if __name__ == '__main__':
    unittest.main()
