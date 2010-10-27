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

import os

#It's ugly I know....
from shinken_test import *
from shinken.action import Action

class TestConfig(ShinkenTest):
    #setUp is in shinken_test

    def wait_finished(self, a):
        for i in xrange(1, 10000):
            if a.status == 'launched':
                a.check_finished(8012)

    #Change ME :)
    def test_action(self):
        a = Action()
        a.timeout = 10
        a.env = {}

        if os.name == 'nt':
            a.command = "./dummy_command.cmd"
        else:
            a.command = "./dummy_command.sh"
        self.assert_(a.got_shell_caracters() == False)
        a.execute()
        self.assert_(a.status == 'launched')
        #Give also the max output we want for the command
        self.wait_finished(a)
        self.assert_(a.exit_status == 0)
        self.assert_(a.status == 'done')
        self.assert_(a.output == "Hi, I'm for testing only. Please do not use me directly, really ")
        self.assert_(a.perf_data == " Hip=99% Bob=34mm")


    def test_environnement_variables(self):
        a = Action()
        a.timeout = 10
        if os.name == 'nt':
            return
        else:
            a.command = "/usr/bin/env"
        a.env = {'TITI' : 'est en vacance'}

        self.assert_(a.got_shell_caracters() == False)

        a.execute()

        self.assert_(a.status == 'launched')
        #Give also the max output we want for the command
        self.wait_finished(a)
        print "Output", a.long_output, a.output
        titi_found = False
        for l in a.long_output.splitlines():
            if l == 'TITI=est en vacance':
                titi_found = True

        self.assert_(titi_found == True)


if __name__ == '__main__':
    unittest.main()

