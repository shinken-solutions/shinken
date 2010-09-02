#!/usr/bin/env python2.6

#
# This file is used to test reading and processing of config files
#

import os

#It's ugly I know....
from shinken_test import *
from shinken.action import Action

class TestConfig(ShinkenTest):
    #setUp is in shinken_test
    
    #Change ME :)
    def test_action(self):
        a = Action()
        a.timeout = 10
        
        if os.name == 'nt':
            a.command = "./dummy_command.cmd"
        else:
            a.command = "./dummy_command.sh"
        self.assert_(a.got_shell_caracters() == False)
        a.execute()
        self.assert_(a.status == 'launched')
        #Give also the max output we want for the command
        for i in xrange(1, 100):
            if a.status == 'launched':
                a.check_finished(8012)
        self.assert_(a.exit_status == 0)
        self.assert_(a.status == 'done')
        self.assert_(a.output == "Hi, I'm for testing only. Please do not use me directly, really ")
        self.assert_(a.perf_data == " Hip=99% Bob=34mm")
        

if __name__ == '__main__':
    unittest.main()

