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


class TestConfig(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        self.setup_with_file('etc/nagios_triggers.cfg')

    
    #Change ME :)
    def test_dummy(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        code = '''r = self.get_name()'''
        t = Trigger(svc, code)
        r = t.eval()
        print r

        code = '''self.output = "Moncul c'est du poulet" '''
        t = Trigger(svc, code)
        r = t.eval()
        print "Service output", svc.output
        self.assert_(svc.output == "Moncul c'est du poulet")

        code = '''self.output = "Moncul c'est du poulet2"
self.perfdata = "Moncul c'est du poulet3"
'''
        t = Trigger(svc, code)
        r = t.eval()
        print "Service output", svc.output
        print "Service perfdata", svc.perfdata
        self.assert_(svc.output == "Moncul c'est du poulet2")
        self.assert_(svc.perfdata == "Moncul c'est du poulet3")


if __name__ == '__main__':
    unittest.main()

