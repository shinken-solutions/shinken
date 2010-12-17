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

import copy
#It's ugly I know....
from shinken_test import *


class TestConfig(ShinkenTest):
    #setUp is in shinken_test

    def get_svc(self):
        return self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")


    #Look if get_*_name return the good result
    def test_get_name(self):
        svc = self.get_svc()
        print svc.get_dbg_name()
        self.assert_(svc.get_name() == 'test_ok_0')
        self.assert_(svc.get_dbg_name() == 'test_host_0/test_ok_0')

    #getstate should be with all properties in dict class + id
    #check also the setstate
    def test___getstate__(self):
        svc = self.get_svc()
        cls = svc.__class__
        #We get teh state
        state = svc.__getstate__()
        #Check it's the good lenght
        self.assert_(len(state) == len(cls.properties) + len(cls.running_properties) + 1)
        #we copy the service
        svc_copy = copy.copy(svc)
        #reset the state in the original service
        svc.__setstate__(state)
        #And it should be the same :then before :)
        for p in cls.properties:
#            print getattr(svc_copy, p)
#            print getattr(svc, p)
            self.assert_(getattr(svc_copy, p) == getattr(svc, p))


    #Look if it can detect all incorrect cases
    def test_is_correct(self):
        svc = self.get_svc()

        #first it's ok
        self.assert_(svc.is_correct() == True)

        #Now try to delete a required property
        max_check_attempts = svc.max_check_attempts
        del svc.max_check_attempts
        self.assert_(svc.is_correct() == False)
        svc.max_check_attempts = max_check_attempts

        ###
        ### Now special cases
        ###

        #no contacts with notification enabled is a problem
        svc.notifications_enabled = True
        contacts = svc.contacts
        contact_groups = svc.contact_groups
        del svc.contacts
        del svc.contact_groups
        self.assert_(svc.is_correct() == False)
        #and with disabled it's ok
        svc.notifications_enabled = False
        self.assert_(svc.is_correct() == True)
        svc.contacts = contacts
        svc.contact_groups = contact_groups

        svc.notifications_enabled = True
        self.assert_(svc.is_correct() == True)

        #no check command
        check_command = svc.check_command
        del svc.check_command
        self.assert_(svc.is_correct() == False)
        svc.check_command = check_command
        self.assert_(svc.is_correct() == True)

        #no notification_interval
        notification_interval = svc.notification_interval
        del svc.notification_interval
        self.assert_(svc.is_correct() == False)
        svc.notification_interval = notification_interval
        self.assert_(svc.is_correct() == True)

        #No host
        host = svc.host
        del svc.host
        self.assert_(svc.is_correct() == False)
        svc.host = host
        self.assert_(svc.is_correct() == True)


    #Look for set/unset impacted states (unknown)
    def test_impact_state(self):
        svc = self.get_svc()
        ori_state = svc.state
        ori_state_id = svc.state_id
        svc.set_impact_state()
        self.assert_(svc.state == 'UNKNOWN')
        self.assert_(svc.state_id == 3)
        svc.unset_impact_state()
        self.assert_(svc.state == ori_state)
        self.assert_(svc.state_id == ori_state_id)

    def test_set_state_from_exit_status(self):
        svc = self.get_svc()
        #First OK
        svc.set_state_from_exit_status(0)
        self.assert_(svc.state == 'OK')
        self.assert_(svc.state_id == 0)
        self.assert_(svc.is_state('OK') == True)
        self.assert_(svc.is_state('o') == True)
        #Then warning
        svc.set_state_from_exit_status(1)
        self.assert_(svc.state == 'WARNING')
        self.assert_(svc.state_id == 1)
        self.assert_(svc.is_state('WARNING') == True)
        self.assert_(svc.is_state('w') == True)
        #Then Critical
        svc.set_state_from_exit_status(2)
        self.assert_(svc.state == 'CRITICAL')
        self.assert_(svc.state_id == 2)
        self.assert_(svc.is_state('CRITICAL') == True)
        self.assert_(svc.is_state('c') == True)
        #And unknown
        svc.set_state_from_exit_status(3)
        self.assert_(svc.state == 'UNKNOWN')
        self.assert_(svc.state_id == 3)
        self.assert_(svc.is_state('UNKNOWN') == True)
        self.assert_(svc.is_state('u') == True)

        #And something else :)
        svc.set_state_from_exit_status(99)
        self.assert_(svc.state == 'CRITICAL')
        self.assert_(svc.state_id == 2)
        self.assert_(svc.is_state('CRITICAL') == True)
        self.assert_(svc.is_state('c') == True)

    #Check if the check_freshnes is doing it's job
    def test_check_freshness(self):
        self.print_header()
        #We want an eventhandelr (the perfdata command) to be put in the actions dict
        #after we got a service check
        now = time.time()
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        #We do not want to be just a string but a real command
        print "Additonal freshness latency", svc.__class__.additional_freshness_latency
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "Addi :", svc.last_state_update, svc.freshness_threshold , svc.check_freshness
        #By default check fresh ness is set at false, so no new checks
        self.assert_(len(svc.actions) == 0)
        svc.do_check_freshness()
        self.assert_(len(svc.actions) == 0)

        #We make it 10s less than it was
        svc.last_state_update = svc.last_state_update - 10


        #Now we active it, with a too small value (now - 10s is still higer than now - (1 - 15, the addition time)
        #So still no check
        svc.check_freshness = True
        svc.freshness_threshold = 1
        print "Addi:", svc.last_state_update, svc.freshness_threshold , svc.check_freshness
        svc.do_check_freshness()
        self.assert_(len(svc.actions) == 0)

        #Ok, now, we remove again 10s. Here we will saw the new entry
        svc.last_state_update = svc.last_state_update - 10
        svc.do_check_freshness()
        self.assert_(len(svc.actions) == 1)
        #And we check for the message in the log too
        self.assert_(self.log_match(1, 'Warning: The results of service'))


    def test_criticity_value(self):
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        #This service inherit the improtance value from his father, 5
        self.assert_(svc.criticity == 5)


    #Look if the service is in the servicegroup
    def test_servicegroup(self):
        sg = self.sched.servicegroups.find_by_name("servicegroup_01")
        self.assert_(sg != None)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        self.assert_(svc in sg.members)
        self.assert_(sg in svc.servicegroups)

    #Look at the good of the last_hard_state_change
    def test_service_last_hard_state(self):
        self.print_header()
        #We want an eventhandelr (the perfdata command) to be put in the actions dict
        #after we got a service check
        now = time.time()
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        #We do not want to be just a string but a real command
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "FUCK", svc.last_hard_state_change
        orig = svc.last_hard_state_change
        self.assert_(svc.last_hard_state == 'OK')
        
        #now still ok
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        self.assert_(svc.last_hard_state_change == orig)
        self.assert_(svc.last_hard_state == 'OK')

        #now error but still SOFT
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | bibi=99%']])
        print "FUCK", svc.state_type
        self.assert_(svc.last_hard_state_change == orig)
        self.assert_(svc.last_hard_state == 'OK')

        #now go hard!
        now = int(time.time())
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | bibi=99%']])
        print "FUCK", svc.state_type
        self.assert_(svc.last_hard_state_change == now)
        self.assert_(svc.last_hard_state == 'CRITICAL')


    # Check if the autoslots are fill like it should
    def test_autoslots(self):
        svc = self.get_svc()
        self.assert_("check_period" not in svc.__dict__)


if __name__ == '__main__':
    unittest.main()


