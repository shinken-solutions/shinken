from shinken_test import *

class TestConfig(ShinkenTest):
    def update_broker(self, dodeepcopy=False):
        #The brok should be manage in the good order
        ids = self.sched.broks.keys()
        ids.sort()
        for brok_id in ids:
            brok = self.sched.broks[brok_id]
            #print "Managing a brok type", brok.type, "of id", brok_id
            #if brok.type == 'update_service_status':
            #    print "Problem?", brok.data['is_problem']
            if dodeepcopy:
                brok = copy.deepcopy(brok)
            self.livestatus_broker.manage_brok(brok)
        self.sched.broks = {}

    pass

class TestConfigBig(TestConfig):
    def setUp(self):
        start_setUp = time.time()
        self.setup_with_file('etc/nagios_5r_100h_2000s.cfg')
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.fill_initial_broks()
        self.update_broker()
        print "************* Overall Setup:", time.time() - start_setUp
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_000")
        host.__class__.use_aggressive_host_checking = 1

    def tearDown(self):
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs+"-journal"):
            os.remove(self.livelogs+"-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None



    def test_stats(self):
        self.print_header()
        now = time.time()
        objlist = []
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 0, 'OK'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_00")
        print svc1
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_15")
        print svc2
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_16")
        print svc3
        svc4 = self.sched.services.find_srv_by_name_and_hostname("test_host_007", "test_ok_05")
        print svc4
        svc5 = self.sched.services.find_srv_by_name_and_hostname("test_host_007", "test_ok_11")
        svc6 = self.sched.services.find_srv_by_name_and_hostname("test_host_025", "test_ok_01")
        svc7 = self.sched.services.find_srv_by_name_and_hostname("test_host_025", "test_ok_03")

        request = """GET services
Filter: description = test_ok_11
Filter: host_name = test_host_007
Columns: host_name description state state_type"""
        beforeresponse, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "before", beforeresponse

        self.scheduler_loop(1, [[svc1, 1, 'W'], [svc2, 1, 'W'], [svc3, 1, 'W'], [svc4, 2, 'C'], [svc5, 3, 'U'], [svc6, 2, 'C'], [svc7, 2, 'C']])
        self.update_broker()
        # 1993O, 3xW, 3xC, 1xU
        request = """GET services
Filter: contacts >= test_contact
Stats: state != 9999
Stats: state = 0
Stats: state = 1
Stats: state = 2
Stats: state = 3"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print 'query_6_______________\n%s\n%s\n' % (request, response)
        self.assert_(response == '2000;1993;3;3;1\n')

        # Now we play with the cache
        request = """GET services
Filter: description = test_ok_11
Filter: host_name = test_host_007
Columns: host_name description state state_type"""
        afterresponse, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "after", afterresponse
        self.assert_(beforeresponse != afterresponse)
        request = """GET services
Filter: description = test_ok_11
Filter: host_name = test_host_007
Columns: host_name description state state_type"""
        repeatedresponse, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "repeated", repeatedresponse
        self.assert_(afterresponse == repeatedresponse)
        self.scheduler_loop(2, [[svc5, 2, 'C']])
        self.update_broker()
        request = """GET services
Filter: description = test_ok_11
Filter: host_name = test_host_007
Columns: host_name description state state_type"""
        notcachedresponse, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "notcached", notcachedresponse
        self.scheduler_loop(2, [[svc5, 0, 'O']])
        self.update_broker()
        # 1994O, 3xW, 3xC, 0xU
        request = """GET services
Filter: description = test_ok_11
Filter: host_name = test_host_007
Columns: host_name description state state_type"""
        againnotcachedresponse, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "againnotcached", againnotcachedresponse
        self.assert_(notcachedresponse != againnotcachedresponse)
        request = """GET services
Filter: description = test_ok_11
Filter: host_name = test_host_007
Columns: host_name description state state_type"""
        finallycachedresponse, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "finallycached", finallycachedresponse
        self.assert_(againnotcachedresponse == finallycachedresponse)

        request = """GET services
Filter: contacts >= test_contact
Stats: state != 9999
Stats: state = 0
Stats: state = 1
Stats: state = 2
Stats: state = 3"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print 'query_6_______________\n%s\n%s\n' % (request, response)
        self.assert_(response == '2000;1994;3;3;0\n')

if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig)
    #unittest.TextTestRunner(verbosity=2).run(allsuite)


