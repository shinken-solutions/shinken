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
from shinken.modules.webui_broker.helper import helper

class TestUIHelper(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    def setUp(self):
        pass
        #self.setup_with_file('etc/nagios_1r_1h_1s.cfg')

    
    #Change ME :)
    def test_duration_print(self):
        now = time.time()

        # Got bogus return
        s = helper.print_duration(None)
        print "Res", s
        self.assert_(s == 'N/A')
        s = helper.print_duration(0)
        print "Res", s
        self.assert_(s == 'N/A')



        # Get the Now
        s = helper.print_duration(now)
        print "Res", s
        self.assert_(s == 'Now')

        # Go PAST
        # Get the 2s ago
        s = helper.print_duration(now - 2)
        print "Res", s
        self.assert_(s == '2s ago')

        # Ask only the furation string
        s = helper.print_duration(now - 2, just_duration=True)
        print "Res", s
        self.assert_(s == '2s')


        #Got 2minutes
        s = helper.print_duration(now - 120)
        print "Res", s
        self.assert_(s == '2m ago')

        # Go 2hours ago
        s = helper.print_duration(now - 3600*2)
        print "Res", s
        self.assert_(s == '2h ago')

        #Go 2 days ago
        s = helper.print_duration(now - 3600*24*2)
        print "Res", s
        self.assert_(s == '2d ago')

        # Go 2 weeks ago
        s = helper.print_duration(now - 86400*14)
        print "Res", s
        self.assert_(s == '2w ago')

        # Go 2 months ago
        s = helper.print_duration(now - 86400*56)
        print "Res", s
        self.assert_(s == '2M ago')

        # Go 1 year ago
        s = helper.print_duration(now - 86400*365*2)
        print "Res", s
        self.assert_(s == '2y ago')

        # Now a mix of all of this :)
        s = helper.print_duration(now - 2 - 120 - 3600*2 - 3600*24*2 - 86400*14 - 86400*56)
        print "Res", s
        self.assert_(s == '2M 2w 2d 2h 2m 2s ago')

        # Now with a limit, because here it's just a nightmare to read
        s = helper.print_duration(now - 2 - 120 - 3600*2 - 3600*24*2 - 86400*14 - 86400*56, x_elts=2)
        print "Res", s
        self.assert_(s == '2M 2w ago')

        # Return to the future
        # Get the 2s ago
        s = helper.print_duration(now + 2)
        print "Res", s
        self.assert_(s == 'in 2s')

        #Got 2minutes
        s = helper.print_duration(now + 120)
        print "Res", s
        self.assert_(s == 'in 2m')

        # Go 2hours ago
        s = helper.print_duration(now + 3600*2)
        print "Res", s
        self.assert_(s == 'in 2h')

        #Go 2 days ago
        s = helper.print_duration(now + 3600*24*2)
        print "Res", s
        self.assert_(s == 'in 2d')

        # Go 2 weeks ago
        s = helper.print_duration(now + 86400*14)
        print "Res", s
        self.assert_(s == 'in 2w')

        # Go 2 months ago
        s = helper.print_duration(now + 86400*56)
        print "Res", s
        self.assert_(s == 'in 2M')

        # Go 1 year ago
        s = helper.print_duration(now + 86400*365*2)
        print "Res", s
        self.assert_(s == 'in 2y')

        # Now a mix of all of this :)
        s = helper.print_duration(now + 2 + 120 + 3600*2 + 3600*24*2 + 86400*14 + 86400*56)
        print "Res", s
        self.assert_(s == 'in 2M 2w 2d 2h 2m 2s')

        # Now with a limit, because here it's just a nightmare to read
        s = helper.print_duration(now + 2 - 120 + 3600*2 + 3600*24*2 + 86400*14 + 86400*56, x_elts=2)
        print "Res", s
        self.assert_(s == 'in 2M 2w')





        

if __name__ == '__main__':
    unittest.main()

