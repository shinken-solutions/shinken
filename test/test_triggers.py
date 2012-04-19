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
from shinken.trigger import Trigger


class TestTriggers(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_triggers.cfg')

    
    # Change ME :)
    def test_simple_triggers(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        code = '''r = self.get_name()'''.replace(r'\n', '\n').replace(r'\t', '\t')
        t = Trigger({'trigger_name' : 'none', 'code_src': code})
        t.compile()
        r = t.eval(svc)
        print r

        code = '''self.output = "Moncul c'est du poulet" '''.replace(r'\n', '\n').replace(r'\t', '\t')
        t = Trigger({'trigger_name' : 'none', 'code_src': code})
        t.compile()
        r = t.eval(svc)
        print "Service output", svc.output
        self.assert_(svc.output == "Moncul c'est du poulet")

        code = '''self.output = "Moncul c'est du poulet2"
self.perfdata = "Moncul c'est du poulet3"
'''.replace(r'\n', '\n').replace(r'\t', '\t')
        t = Trigger({'trigger_name' : 'none', 'code_src': code})
        t.compile()
        r = t.eval(svc)
        print "Service output", svc.output
        print "Service perfdata", svc.perfdata
        self.assert_(svc.output == "Moncul c'est du poulet2")
        self.assert_(svc.perfdata == "Moncul c'est du poulet3")

    # Change ME :)
    def test_in_conf_trigger(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "i_got_trigger")
        print 'will run', svc.trigger
        # Go!
        svc.eval_triggers()
        print "Output", svc.output
        print "Perfdata", svc.perfdata
        self.assert_(svc.output == "New output")
        self.assert_(svc.perfdata == "New perfdata")



    # Try to catch the perfdatas of self
    def test_simple_cpu_too_high(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "cpu_too_high")
        svc.output = 'I am OK'
        svc.perfdata = 'cpu=95%'
        # Go launch it!
        svc.eval_triggers()
        print "Output", svc.output
        print "Perfdata", svc.perfdata
        self.assert_(svc.output == "not good!")
        self.assert_(svc.perfdata == "cpu=95%")

        # Same with an host
        host = self.sched.hosts.find_by_name("test_host_trigger")
        host.output = 'I am OK'
        host.perfdata = 'cpu=95%'
        # Go launch it!
        host.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", host.output
        print "Perfdata", host.perfdata
        self.assert_(host.output == "not good!")
        self.assert_(host.perfdata == "cpu=95%")



    # Try to catch the perfdatas of self
    def test_morecomplex_cpu_too_high(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "cpu_too_high_bis")
        svc.output = 'I am OK'
        svc.perfdata = 'cpu=95%'
        # Go launch it!
        svc.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", svc.output
        print "Perfdata", svc.perfdata
        self.assert_(svc.output == "not good!")
        self.assert_(svc.perfdata == "cpu=95%")


    # Try to load .trig files
    def test_trig_file_loading(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "cpu_too_high_ter")
        t = self.conf.triggers.find_by_name('simple_cpu')
        self.assert_(t in svc.triggers)
        svc.output = 'I am OK'
        svc.perfdata = 'cpu=95%'
        svc.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", svc.output
        print "Perfdata", svc.perfdata
        self.assert_(svc.output == "not good!")
        self.assert_(svc.perfdata == "cpu=95%")
        

        # same for host
        host = self.sched.hosts.find_by_name('test_host_trigger2')
        t = self.conf.triggers.find_by_name('simple_cpu')
        self.assert_(t in host.triggers)
        host.output = 'I am OK'
        host.perfdata = 'cpu=95%'
        host.eval_triggers()
        self.scheduler_loop(2, [])
        print "Output", host.output
        print "Perfdata", host.perfdata
        self.assert_(host.output == "not good!")
        self.assert_(host.perfdata == "cpu=95%")



if __name__ == '__main__':
    unittest.main()

