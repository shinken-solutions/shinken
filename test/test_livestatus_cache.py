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
        self.livestatus_broker.query_cache.enabled = True
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

    def test_a_long_history(self):
        #return
        test_host_005 = self.sched.hosts.find_by_name("test_host_005")
        test_host_099 = self.sched.hosts.find_by_name("test_host_099")
        test_ok_00 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_00")
        test_ok_01 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_01")
        test_ok_04 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_04")
        test_ok_16 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_16")
        test_ok_99 = self.sched.services.find_srv_by_name_and_hostname("test_host_099", "test_ok_01")
        time_warp(-1 * 20 * 24 * 3600)
        starttime = time.time()
        numlogs = self.livestatus_broker.db.execute("SELECT COUNT(*) FROM logs")
        if numlogs[0][0] == 0:
            # run silently
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            self.scheduler_loop(2, [
                [test_ok_00, 0, "OK"],
                [test_ok_01, 0, "OK"],
                [test_ok_04, 0, "OK"],
                [test_ok_16, 0, "OK"],
                [test_ok_99, 0, "OK"],
            ])
            self.update_broker()
            should_be = 0
            #for i in xrange(3600 * 24 * 7):
            for i in xrange(10000):
                if i % 10000 == 0:
                    sys.stderr.write(str(i))
                if i % 399 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                        [test_ok_04, 3, "UNKN"],
                        [test_ok_16, 1, "WARN"],
                        [test_ok_99, 2, "CRIT"],
                    ])
                    should_be += 3
                time.sleep(62)
                if i % 399 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                        [test_ok_04, 0, "OK"],
                        [test_ok_16, 0, "OK"],
                        [test_ok_99, 0, "OK"],
                    ])
                    should_be += 1
                time.sleep(2)
                if i % 199 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                    ])
                time.sleep(62)
                if i % 199 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                    ])
                time.sleep(2)
                if i % 299 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 2, "DOWN"],
                    ])
                if i % 19 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 2, "DOWN"],
                    ])
                time.sleep(62)
                if i % 299 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 0, "UP"],
                    ])
                if i % 19 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 0, "UP"],
                    ])
                time.sleep(2)
                self.update_broker()
                if i % 1000 == 0:
                    self.livestatus_broker.db.commit()
            endtime = time.time()
            sys.stdout.close()
            sys.stdout = old_stdout
            self.livestatus_broker.db.commit()
        else:
            should_be = numlogs[0][0]
            xxx = self.livestatus_broker.db.execute("SELECT min(time), max(time) FROM logs")
            print xxx
            starttime, endtime = [self.livestatus_broker.db.execute("SELECT min(time), max(time) FROM logs")][0][0]


        # now we have a lot of events
        # find type = HOST ALERT for test_host_005
        q = int((endtime - starttime) / 8)
        starttime += q
        endtime -= q
        request = """GET log
Columns: class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups
Filter: time >= """ + str(int(starttime)) + """
Filter: time <= """ + str(int(endtime)) + """
Filter: type = SERVICE ALERT
And: 1
Filter: type = HOST ALERT
And: 1
Filter: type = SERVICE FLAPPING ALERT
Filter: type = HOST FLAPPING ALERT
Filter: type = SERVICE DOWNTIME ALERT
Filter: type = HOST DOWNTIME ALERT
Filter: type ~ starting...
Filter: type ~ shutting down...
Or: 8
Filter: host_name = test_host_099
Filter: service_description = test_ok_01
And: 5
OutputFormat: json"""
        # switch back to realtime. we want to know how long it takes
        fake_time_time = time.time
        fake_time_sleep = time.sleep
        time.time = original_time_time
        time.sleep = original_time_sleep
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        print "number of records", len(pyresponse)
        print "should be", should_be
        print "now with cache"
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        print "number of records", len(pyresponse)
        print "should be", should_be
        time.time = fake_time_time
        time.sleep = fake_time_sleep

if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig)
    #unittest.TextTestRunner(verbosity=2).run(allsuite)


