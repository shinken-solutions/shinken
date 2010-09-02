#!/usr/bin/env python2.6

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *
from shinken.command import CommandCall, Command, Commands

class TestConfig(ShinkenTest):
    #setUp is in shinken_test
    
    #Change ME :)
    def test_command(self):
        t = {'command_name' : 'check_command_test',
             'command_line' : '/tmp/dummy_command.sh $ARG1$ $ARG2$',
             'poller_tag' : 'DMZ'
             }
        c = Command(t)
        self.assert_(c.command_name == 'check_command_test')
        b = c.get_initial_status_brok()
        self.assert_(b.type == 'initial_command_status')
        
        #now create a commands packs
        cs = Commands([c])
        dummy_call = "check_command_test!titi!toto"
        cc = CommandCall(cs, dummy_call)
        self.assert_(cc.is_valid() == True)
        self.assert_(cc.command == c)
        self.assert_(cc.poller_tag == 'DMZ')

if __name__ == '__main__':
    unittest.main()

