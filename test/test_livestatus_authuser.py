#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

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
# This file is used to test host- and service-downtimes.
#

from shinken_test import *
import os
import re
import subprocess
import shutil
import time
import random
import copy

from shinken.brok import Brok
from shinken.objects.timeperiod import Timeperiod
from shinken.objects.module import Module
from shinken.comment import Comment
from shinken.util import from_bool_to_int
from test_livestatus import TestConfig

sys.setcheckinterval(10000)


class TestConfigAuth(TestConfig):
    def setUp(self):
        self.setup_with_file('etc/nagios_livestatus_authuser.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.conf.skip_initial_broks = False
        self.sched.fill_initial_broks()
        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("dbsrv1")
        host.__class__.use_aggressive_host_checking = 1



    def tearDown(self):
        self.stop_nagios()
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs+"-journal"):
            os.remove(self.livelogs+"-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None



    """
dbsrv1  adm(adm1,adm2,adm3) oradba(oradba1,oradba2)
    app_db_oracle_check_connect    oradba(oradba1,oradba2) cc(cc1,cc2,cc3)
    app_db_oracle_check_alertlog   oradba(oradba1,oradba2)

dbsrv2  adm(adm1,adm2,adm3) oradba(oradba1,oradba2)
    app_db_oracle_check_connect    oradba(oradba1,oradba2) cc(cc1,cc2,cc3)
    app_db_oracle_check_alertlog   oradba(oradba1,oradba2)

dbsrv3  adm(adm1,adm2,adm3) oradba(oradba1,oradba2)
    app_db_oracle_check_connect    oradba(oradba1,oradba2) cc(cc1,cc2,cc3)
    app_db_oracle_check_alertlog   oradba(oradba1,oradba2)

dbsrv4  adm(adm1,adm2,adm3) mydba(mydba1,mydba2)
    app_db_mysql_check_connect     mydba(mydba1,mydba2) cc(cc1,cc2,cc3)
    app_db_mysql_check_alertlog    mydba(mydba1,mydba2)

dbsrv5  adm(adm1,adm2,adm3) mydba(mydba1,mydba2)
    app_db_mysql_check_connect     mydba(mydba1,mydba2) cc(cc1,cc2,cc3)
    app_db_mysql_check_alertlog    mydba(mydba1,mydba2)

www1    adm(adm1,adm2,adm3) web(web1,web2)
    app_web_apache_check_http      web(web1,web2) cc(cc1,cc2,cc3)
    app_web_apache_check_errorlog  web(web1,web2)
    """

    def test_host_authorization(self):
        self.print_header()
        now = time.time()
        objlist = []
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 0, 'OK'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        request = """GET hosts
AuthUser: oradba1
Columns: name
OutputFormat: python
KeepAlive: on
"""
        # test_host_0/1
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response 
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 3)
        self.assert_("dbsrv1" in [h[0] for h in pyresponse])
        self.assert_("dbsrv2" in [h[0] for h in pyresponse])
        self.assert_("dbsrv3" in [h[0] for h in pyresponse])

    def test_service_authorization_loose(self):
        self.print_header()
        now = time.time()
        objlist = []
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 0, 'OK'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        request = """GET hosts
AuthUser: adm1
Columns: name services
Filter: name = dbsrv1
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
"""
        # app_db_oracle_* because adm1 is host contact
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response 



if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig) 
    #unittest.TextTestRunner(verbosity=2).run(allsuite) 

