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
# This file is used to test reading and processing of config files
#

from shinken_test import *
from shinken.objects.trigger import Trigger


class TestTriggers(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_triggers.cfg')

    # Try to catch the perf_datas of self
    def test_function_perf(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "sample_perf_function")
        svc.output = 'I am OK'
        svc.perf_data = 'cpu=95%'
        # Go launch it!
        svc.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        self.assertEqual("not good!", svc.output)
        self.assertEqual("cpu=95%", svc.perf_data)

    # Try to catch the perf_datas of self
    def test_function_perfs(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "AVG-HTTP")

        srvs = []
        for i in xrange(1, 4):
            s = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "HTTP-" + str(i))
            s.output = 'Http ok'
            s.perf_data = 'time=%dms' % i

        # Go launch it!
        svc.eval_triggers()
        self.scheduler_loop(4, [])
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        self.assertEqual("OK all is green", svc.output)
        self.assertEqual("avgtime=2ms", svc.perf_data)

    # Try to catch the perf_datas of self
    def test_function_custom(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "sample_custom_function")
        svc.output = 'Nb users?'
        svc.perf_data = 'users=6'
        # Go launch it!
        svc.eval_triggers()
        self.scheduler_loop(4, [])
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        self.assertEqual("OK all is green", svc.output)
        self.assertEqual("users=12", svc.perf_data)

    def test_in_conf_trigger(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "i_got_trigger")
        print 'will run', svc.trigger
        # Go!
        svc.eval_triggers()
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        self.assertEqual("New output", svc.output)
        self.assertEqual("New perf_data", svc.perf_data)

    # Try to catch the perf_datas of self
    def test_simple_cpu_too_high(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "cpu_too_high")
        svc.output = 'I am OK'
        svc.perf_data = 'cpu=95%'
        # Go launch it!
        svc.eval_triggers()
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        self.assertEqual("not good!", svc.output)
        self.assertEqual("cpu=95%", svc.perf_data)

        # Same with a host
        host = self.sched.hosts.find_by_name("test_host_trigger")
        host.output = 'I am OK'
        host.perf_data = 'cpu=95%'
        # Go launch it!
        host.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", host.output
        print "Perf_Data", host.perf_data
        self.assertEqual("not good!", host.output)
        self.assertEqual("cpu=95", host.perf_data)

    # Try to catch the perf_datas of self
    def test_morecomplex_cpu_too_high(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "cpu_too_high_bis")

        firstlen = len([b for b in self.sched.broks.values() if b.type == 'service_check_result'])
        self.scheduler_loop(1, [(svc, 0, 'I am OK | cpu=95%')])
        seclen = len([b for b in self.sched.broks.values() if b.type == 'service_check_result'])
        self.scheduler_loop(1, [])
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        print firstlen, seclen

        self.assertEqual("not good!", svc.output)
        self.assertEqual("cpu=95", svc.perf_data)
        self.assertEqual(seclen, firstlen)

    # Try to load .trig files
    def test_trig_file_loading(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "cpu_too_high_ter")
        t = self.conf.triggers.find_by_name('simple_cpu')
        self.assertIn(t, svc.triggers)
        svc.output = 'I am OK'
        svc.perf_data = 'cpu=95%'
        svc.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", svc.output
        print "Perf_Data", svc.perf_data
        self.assertEqual("not good!", svc.output)
        self.assertEqual("cpu=95", svc.perf_data)

        # same for host
        host = self.sched.hosts.find_by_name('test_host_trigger2')
        t = self.conf.triggers.find_by_name('simple_cpu')
        self.assertIn(t, host.triggers)
        host.output = 'I am OK'
        host.perf_data = 'cpu=95%'
        host.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", host.output
        print "Perf_Data", host.perf_data
        self.assertEqual("not good!", host.output)
        self.assertEqual("cpu=95", host.perf_data)

    def test_simple_triggers(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        code = '''r = self.get_name()'''.replace(r'\n', '\n').replace(r'\t', '\t')
        t = Trigger({'trigger_name': 'none', 'code_src': code})
        t.compile()
        r = t.eval(svc)
        print r

        code = '''self.output = "Moncul c'est du poulet" '''.replace(r'\n', '\n').replace(r'\t', '\t')
        t = Trigger({'trigger_name': 'none', 'code_src': code})
        t.compile()
        r = t.eval(svc)
        print "Service output", svc.output
        self.assertEqual("Moncul c'est du poulet", svc.output)

        code = '''self.output = "Moncul c'est du poulet2"
self.perf_data = "Moncul c'est du poulet3"
'''.replace(r'\n', '\n').replace(r'\t', '\t')
        t = Trigger({'trigger_name': 'none', 'code_src': code})
        t.compile()
        r = t.eval(svc)
        print "Service output", svc.output
        print "Service perf_data", svc.perf_data
        self.assertEqual("Moncul c'est du poulet2", svc.output)
        self.assertEqual("Moncul c'est du poulet3", svc.perf_data)



if __name__ == '__main__':
    unittest.main()
