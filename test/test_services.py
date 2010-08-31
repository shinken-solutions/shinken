#!/usr/bin/env python2.6

#
# This file is used to test reading and processing of config files
#

import copy
#It's ugly I know....
from shinken_test import *


class TestConfig(ShinkenTest):
    def setUp(self):
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_1r_1h_1s.cfg']
        self.conf = Config()
        self.conf.read_config(self.config_files)
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.clean_useless()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependancies()
        self.conf.explode_global_conf()
        self.conf.is_correct()
        self.confs = self.conf.cut_into_parts()
        self.dispatcher = Dispatcher(self.conf, self.me)
        self.sched = Scheduler(None)
        m = MacroResolver()
        m.init(self.conf)
        self.sched.load_conf(self.conf)
        e = ExternalCommand(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        self.sched.schedule()


    def get_svc(self):
        return self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

    
    #Look if get_*_name return the good result
    def OK_test_get_name(self):
        svc = self.get_svc()
        print svc.get_dbg_name()
        self.assert_(svc.get_name() == 'test_ok_0')
        self.assert_(svc.get_dbg_name() == 'test_host_0/test_ok_0')

    #getstate should be with all properties in dict class + id
    #check also the setstate
    def OK_test___getstate__(self):
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


if __name__ == '__main__':
    unittest.main()

