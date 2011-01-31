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
from hot_dependencies_arbiter import *

try:
    import json
except ImportError: 
    # For old Python version, load 
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error : you need the json or simplejson module for this script"
        sys.exit(0)

class TestModuleHotDep(ShinkenTest):
    #setUp is in shinken_test
    def setUp(self):
        self.setup_with_file('etc/nagios_module_hot_dependencies_arbiter.cfg')

    #Change ME :)
    def test_simple_json_read(self):
        print self.conf.modules

        host0 = self.sched.conf.hosts.find_by_name('test_host_0')
        self.assert_(host0 != None)
        host1 = self.sched.conf.hosts.find_by_name('test_host_1')
        self.assert_(host1 != None)
        host2 = self.sched.conf.hosts.find_by_name('test_host_2')
        self.assert_(host2 != None)

        # From now there is no link between hosts (just parent with the router)
        # but it's not imporant here
        self.assert_(host0.is_linked_with_host(host1) == False)
        self.assert_(host1.is_linked_with_host(host0) == False)
        self.assert_(host0.is_linked_with_host(host2) == False)
        self.assert_(host2.is_linked_with_host(host0) == False)
        self.assert_(host2.is_linked_with_host(host1) == False)
        self.assert_(host1.is_linked_with_host(host2) == False)

    
        #get our modules
        mod = None
        mod = Module({'type' : 'hot_dependencies', 'module_name' : 'VMWare_auto_linking', 'mapping_file' : 'tmp/vmware_mapping_file.json',
                      'mapping_command' : "", 'mapping_command_interval' : '30'})
        
        try :
            os.unlink(mod.mapping_file)
        except :
            pass
        
        sl = get_instance(mod)
        print "Instance", sl

        # Hack here :(
        sl.properties = {}
        sl.properties['to_queue'] = None
        sl.init()
        l = logger

        # We simulate a uniq link, here the vm host1 is on the host host0
        links = [[["host", "test_host_0"], ["host", "test_host_1"]]]
        f = open(mod.mapping_file, 'wb')
        f.write(json.dumps(links))
        f.close()

        # Try the hook for the late config, so it will create
        # the link between host1 and host0
        sl.hook_late_configuration(self)

        # We can look is now the hosts are linked or not :)
        self.assert_(host1.is_linked_with_host(host0) == True)

        if True:
            return


        # updte the hosts and service in the scheduler in the retentino-file
        sl.update_retention_objects(self.sched, l)
        
        #Now we change thing
        svc = self.sched.hosts.find_by_name("test_host_0")
        self.assert_(svc.state == 'PENDING')
        print "State", svc.state
        svc.state = 'UP' #was PENDING in the save time
        
        r = sl.load_retention_objects(self.sched, l)
        self.assert_(r == True)
        
        #search if the host is not changed by the loading thing
        svc2 = self.sched.hosts.find_by_name("test_host_0")
        self.assert_(svc == svc2)
        
        self.assert_(svc.state == 'PENDING')

        #Ok, we can delete the retention file
        os.unlink(mod.path)


        # Now make real loops with notifications
        self.scheduler_loop(10, [[svc, 2, 'CRITICAL | bibi=99%']])
        #updte the hosts and service in the scheduler in the retentino-file
        sl.update_retention_objects(self.sched, l)

        r = sl.load_retention_objects(self.sched, l)
        self.assert_(r == True)



if __name__ == '__main__':
    unittest.main()

