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
import os
from shinken_test import *
sys.path.append("../shinken/modules")
from status_dat_broker import *
from shinken.brok import Brok

class TestConfig(ShinkenTest):
    #setUp is in shinken_test

    def nb_of_string(self, buf, s):
        nb_s = 0
        for line in buf.splitlines():
            if line == s:
                print "Find string"
                nb_s += 1        
        return nb_s

    
    #Change ME :)
    def test_simplelog(self):
        print self.conf.modules
        #get our modules
        mod = None
        for m in self.conf.modules:
            if m.module_type == 'status_dat':
                mod = m
        self.assert_(mod != None)
        self.assert_(mod.status_file == '/usr/local/shinken/var/status.data')
        self.assert_(mod.module_name == 'Status-Dat')
        self.assert_(mod.object_cache_file == '/usr/local/shinken/var/objects.cache')

        try :
            os.unlink(mod.status_file)
            os.unlink(mod.module_name)
        except :
            pass

        sl = get_instance(mod)
        print sl
        #Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        self.sched.fill_initial_broks()
        print self.sched.broks
        sl.init()
        for b in self.sched.broks.values():
            b.instance_id = 0
            sl.manage_brok(b)

        #Now verify the objects.dat file
        sl.objects_cache.create_or_update()
        obj = open(mod.object_cache_file)
        buf = obj.read()
        obj.close()
        #Check for 1 service and only one
        nb_services = self.nb_of_string(buf, "define service {")
        self.assert_(nb_services == 1)
        #2 hosts : host and a router
        nb_hosts = self.nb_of_string(buf, "define host {")
        self.assert_(nb_hosts == 2)

        #Same for status.dat.
        sl.status.create_or_update()
        status = open(mod.status_file)
        buf = status.read()
        obj.close()

        nb_prog = self.nb_of_string(buf, "programstatus {")
        self.assert_(nb_prog == 1)

        nb_hosts = self.nb_of_string(buf, "hoststatus {")
        self.assert_(nb_hosts == 2)
        
        nb_services = self.nb_of_string(buf, "servicestatus {")
        self.assert_(nb_services  == 1)


        #now check if after a resend we still got the good number
        self.sched.broks.clear()
        self.sched.fill_initial_broks()
        for b in self.sched.broks.values():
            b.instance_id = 0
            sl.manage_brok(b)

        #Now verify the objects.dat file
        sl.objects_cache.create_or_update()
        obj = open(mod.object_cache_file)
        buf = obj.read()
        obj.close()
        #Check for 1 service and only one
        nb_services = self.nb_of_string(buf, "define service {")
        self.assert_(nb_services == 1)
        #2 hosts : host and a router
        nb_hosts = self.nb_of_string(buf, "define host {")
        self.assert_(nb_hosts == 2)

        #Same for status.dat.
        sl.status.create_or_update()
        status = open(mod.status_file)
        buf = status.read()
        obj.close()

        nb_prog = self.nb_of_string(buf, "programstatus {")
        self.assert_(nb_prog == 1)

        nb_hosts = self.nb_of_string(buf, "hoststatus {")
        self.assert_(nb_hosts == 2)

        nb_services = self.nb_of_string(buf, "servicestatus {")
        self.assert_(nb_services  == 1)


        os.unlink(mod.status_file)
        os.unlink(mod.object_cache_file)
        

if __name__ == '__main__':
    unittest.main()

