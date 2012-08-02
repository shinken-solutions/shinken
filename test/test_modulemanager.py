#!/usr/bin/env python
# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

from shinken_test import *

time.time = original_time_time
time.sleep = original_time_sleep


class TestModuleManager(ShinkenTest):
    # Uncomment this is you want to use a specific configuration
    # for your test
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
        print("Using modules path: %s" % (modulespath))

        return modulespath

    # Try to see if the module manager can manage modules
    def test_modulemanager(self):
        mod = Module({'module_name': 'LiveStatus', 'module_type': 'livestatus'})
        self.modulemanager = ModulesManager('broker', self.find_modules_path(), [])
        self.modulemanager.set_modules([mod])
        self.modulemanager.load_and_init()
        # And start external ones, like our LiveStatus
        self.modulemanager.start_external_instances()
        print "I correctly loaded the modules: %s " % ([inst.get_name() for inst in self.modulemanager.instances])

        print "*** First kill ****"
        # Now I will try to kill the livestatus module
        ls = self.modulemanager.instances[0]
        ls._BaseModule__kill()

        time.sleep(1)
        print "Check alive?"
        print "Is alive?", ls.process.is_alive()
        # Should be dead
        self.assert_(not ls.process.is_alive())
        self.modulemanager.check_alive_instances()
        self.modulemanager.try_to_restart_deads()

        # In fact it's too early, so it won't do it

        # Here the inst should still be dead
        print "Is alive?", ls.process.is_alive()
        self.assert_(not ls.process.is_alive())

        # So we lie
        ls.last_init_try = -5
        self.modulemanager.check_alive_instances()
        self.modulemanager.try_to_restart_deads()

        # In fact it's too early, so it won't do it

        # Here the inst should be alive again
        print "Is alive?", ls.process.is_alive()
        self.assert_(ls.process.is_alive())

        # should be nothing more in to_restart of
        # the module manager
        self.assert_(self.modulemanager.to_restart == [])

        # Now we look for time restart so we kill it again
        ls._BaseModule__kill()
        time.sleep(1)
        self.assert_(not ls.process.is_alive())

        # Should be too early
        self.modulemanager.check_alive_instances()
        self.modulemanager.try_to_restart_deads()
        print "Is alive or not", ls.process.is_alive()
        self.assert_(not ls.process.is_alive())
        # We lie for the test again
        ls.last_init_try = -5
        self.modulemanager.check_alive_instances()
        self.modulemanager.try_to_restart_deads()

        # Here the inst should be alive again
        print "Is alive?", ls.process.is_alive()
        self.assert_(ls.process.is_alive())

        # And we clear all now
        print "Ask to die"
        self.modulemanager.stop_all()
        print "Died"



if __name__ == '__main__':
    unittest.main()
