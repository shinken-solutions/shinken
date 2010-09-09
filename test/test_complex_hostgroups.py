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


class TestConfig(ShinkenTest):
    #setUp is in shinken_test

    def setUp(self):
        # i am arbiter-like
        Config.fill_usern_macros()
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_complex_hostgroups.cfg']
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

    def find_service(self, name, desc):
        return self.sched.services.find_srv_by_name_and_hostname(name, desc)

    def find_host(self, name):
        return self.sched.hosts.find_by_name(name)

    def find_hostgroup(self, name):
        return self.sched.hostgroups.find_by_name(name)

    def dump_hosts(self, svc):
        for h in svc.host_name:
            print h

    #check if service exist in hst, but NOT in others
    def srv_define_only_on(self, desc, hsts):
        r = True
        #first hsts
        for h in hsts:
            svc = self.find_service(h.host_name, desc)
            if svc == None:
                print "Error : the host %s is missing service %s!!" % (h.host_name, desc)
                r = False

        for h in self.sched.hosts:
            if h not in hsts:
                svc = self.find_service(h.host_name, desc)
                if svc != None:
                    print "Error : the host %s got the service %s!!" % (h.host_name, desc)
                    r = False
        return r


    #Change ME :)
    def test_dummy(self):
        print self.sched.services.items
        svc = self.get_svc()
        print "Service", svc
        #print self.conf.hostgroups

        #All our hosts
        test_linux_web_prod_0 = self.find_host('test_linux_web_prod_0')
        test_linux_web_qual_0 = self.find_host('test_linux_web_qual_0')
        test_win_web_prod_0 = self.find_host('test_win_web_prod_0')
        test_win_web_qual_0 = self.find_host('test_win_web_qual_0')
        test_linux_file_prod_0 = self.find_host('test_linux_file_prod_0')

        

        hg_linux = self.find_hostgroup('linux')
        hg_web = self.find_hostgroup('web')
        hg_win = self.find_hostgroup('win')
        hg_file = self.find_hostgroup('file')
        print "HG Linux", hg_linux
        for h in hg_linux:
            print "H", h.get_name()

        self.assert_(test_linux_web_prod_0 in hg_linux.members)
        self.assert_(test_linux_web_prod_0 not in hg_file.members)
        
        #First the service define for linux only
        svc = self.find_service('test_linux_web_prod_0', 'linux_0')
        print "Service Linux only", svc.get_dbg_name()
        r = self.srv_define_only_on('linux_0', [test_linux_web_prod_0, test_linux_web_qual_0, test_linux_file_prod_0])
        self.assert_(r == True)

        print "Service Linux,web"
        r = self.srv_define_only_on('linux_web_0', [test_linux_web_prod_0, test_linux_web_qual_0, test_linux_file_prod_0,test_win_web_prod_0,test_win_web_qual_0])
        self.assert_(r == True)

        ###Now the real complex things :)
        print "Service Linux&web"
        r = self.srv_define_only_on('linux_AND_web_0', [test_linux_web_prod_0, test_linux_web_qual_0])
        self.assert_(r == True)

        print "Service Linux|web"
        r = self.srv_define_only_on('linux_OR_web_0', [test_linux_web_prod_0, test_linux_web_qual_0, test_win_web_prod_0, test_win_web_qual_0, test_linux_file_prod_0])
        self.assert_(r == True)
        
        print "(linux|web),file"
        r = self.srv_define_only_on('linux_OR_web_PAR_file0', [test_linux_web_prod_0, test_linux_web_qual_0, test_win_web_prod_0, test_win_web_qual_0, test_linux_file_prod_0, test_linux_file_prod_0])
        self.assert_(r == True)

        print "(linux|web)&prod"
        r = self.srv_define_only_on('linux_OR_web_PAR_AND_prod0', [test_linux_web_prod_0,  test_win_web_prod_0, test_linux_file_prod_0])
        self.assert_(r == True)

        print "(linux|web)&!prod"
        r = self.srv_define_only_on('linux_OR_web_PAR_AND_NOT_prod0', [test_linux_web_qual_0, test_win_web_qual_0])
        self.assert_(r == True)

if __name__ == '__main__':
    unittest.main()

