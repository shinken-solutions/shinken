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


class TestModuleManager(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    #def setUp(self):
    #    self.setup_with_file('etc/nagios_1r_1h_1s.cfg')

    
    def find_modules_path(self):
        """ Find the absolute path of the shinken module directory and returns it.  """
        import shinken
        
        # BEWARE: this way of finding path is good if we still
        # DO NOT HAVE CHANGE PWD!!!
        # Now get the module path. It's in fact the directory modules
        # inside the shinken directory. So let's find it.

        print "modulemanager file", shinken.modulesmanager.__file__
        modulespath = os.path.abspath(shinken.modulesmanager.__file__)
        print "modulemanager absolute file", modulespath
        # We got one of the files of
        parent_path = os.path.dirname(os.path.dirname(modulespath))
        modulespath = os.path.join(parent_path, 'shinken', 'modules')
        print("Using modules path : %s" % (modulespath))
        
        return modulespath


    # Try to see if the module manager can manage modules :)
    def test_modulemanager(self):
        mod = Module({'module_name' : 'LiveStatus', 'module_type' : 'livestatus'})
        self.modulemanager = ModulesManager('broker', self.find_modules_path(), [])
        self.modulemanager.set_modules([mod])
        self.modulemanager.load_and_init(True)
        print "I correctly loaded the modules : %s " % ([ inst.get_name() for inst in self.modulemanager.instances ])
        #And we clear all now :)
        print "Ask to die"
        self.modulemanager.stop_all()
        print "Died"

        

if __name__ == '__main__':
    unittest.main()

