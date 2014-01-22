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


class TestDiscoveryConf(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_discovery_def.cfg')

    def test_look_for_discorule(self):
        genhttp = self.sched.conf.discoveryrules.find_by_name('GenHttp')
        self.assert_(genhttp != None)
        self.assert_(genhttp.creation_type == 'service')
        self.assert_(genhttp.matches['openports'] == '80,443')
        self.assert_(genhttp.matches['os'] == 'windows')

        key = 'osversion'
        value = '2003'
        # Should not match this
        self.assert_(genhttp.is_matching(key, value) == False)
        # But should match this one
        key = 'openports'
        value = '80'
        self.assert_(genhttp.is_matching(key, value) == True)

        # Low look for a list of matchings
        l = {'openports': '80', 'os': 'windows'}
        # should match this
        self.assert_(genhttp.is_matching_disco_datas(l) == True)
        # Match this one too
        l = {'openports': '80', 'os': 'windows', 'super': 'man'}
        self.assert_(genhttp.is_matching_disco_datas(l) == True)
        # But not this one
        l = {'openports': '80'}
        self.assert_(genhttp.is_matching_disco_datas(l) == False)

        # Now search the NOT rule
        genhttpnowin = self.sched.conf.discoveryrules.find_by_name('GenHttpNotWindows')

        # Should manage this
        l = {'openports': '80', 'os': 'linux'}
        self.assert_(genhttpnowin.is_matching_disco_datas(l) == True)

        # But NOT this one
        l = {'openports': '80', 'os': 'windows'}
        print "Should NOT match"
        self.assert_(genhttpnowin.is_matching_disco_datas(l) == False)

        # Now look for strict rule application
        genhttpstrict = self.sched.conf.discoveryrules.find_by_name('GenHttpStrict')
        self.assert_(genhttpstrict is not None)
        key = 'openports'
        value = '80,443'
        self.assert_(genhttpstrict.is_matching(key, value) == True)

        # But NOT this one
        key = 'openports'
        value = '800'
        self.assert_(genhttpstrict.is_matching(key, value) == False)


    # Look for good definition and call of a discoveryrun
    def test_look_for_discorun(self):
        nmap = self.sched.conf.discoveryruns.find_by_name('nmap')
        self.assert_(nmap != None)
        nmapcmd = self.sched.conf.commands.find_by_name('nmap_runner')
        self.assert_(nmapcmd != None)
        self.assert_(nmap.discoveryrun_command != None)
        # Launch it
        nmap.launch()
        for i in xrange(1, 5):
            nmap.check_finished()
            if nmap.is_finished():
                break
            time.sleep(1)
        print "Exit status", nmap.current_launch.exit_status
        print "Output", nmap.current_launch.output
        print "LongOutput", nmap.current_launch.long_output


    def test_look_for_host_discorule(self):
        genhttp = self.sched.conf.discoveryrules.find_by_name('GenHttpHost')
        self.assert_(genhttp != None)
        self.assert_(genhttp.creation_type == 'host')
        self.assert_(genhttp.matches['openports'] == '^80$')

        key = 'osversion'
        value = '2003'
        # Should not match this
        self.assert_(genhttp.is_matching(key, value) == False)
        # But should match this one
        key = 'openports'
        value = '80'
        self.assert_(genhttp.is_matching(key, value) == True)

        # Low look for a list of matchings
        l = {'openports': '80', 'os': 'windows'}
        # should match this
        self.assert_(genhttp.is_matching_disco_datas(l) == True)
        # Match this one too
        l = {'openports': '80', 'os': 'windows', 'super': 'man'}
        self.assert_(genhttp.is_matching_disco_datas(l) == True)
        # And this last one
        l = {'openports': '80'}
        self.assert_(genhttp.is_matching_disco_datas(l) == True)

        print "Writing properties"
        print genhttp.writing_properties




    def test_look_for_host_discorule_and_delete(self):
        genhttp = self.sched.conf.discoveryrules.find_by_name('GenHttpHostRemoveLinux')
        self.assert_(genhttp != None)
        self.assert_(genhttp.creation_type == 'host')
        self.assert_(genhttp.matches['openports'] == '^80$')

        key = 'os'
        value = 'linux'

        # Should not match this
        self.assert_(genhttp.is_matching(key, value) == False)
        
        # But should match this one
        key = 'openports'
        value = '80'
        self.assert_(genhttp.is_matching(key, value) == True)

        # Low look for a list of matchings
        l = {'openports': '80', 'os': 'linux'}
        # should match this
        self.assert_(genhttp.is_matching_disco_datas(l) == True)
        # Match this one too
        l = {'openports': '80', 'os': 'linux', 'super': 'man'}
        self.assert_(genhttp.is_matching_disco_datas(l) == True)
        # And this last one
        l = {'openports': '80'}
        self.assert_(genhttp.is_matching_disco_datas(l) == True)

        print "Writing properties"
        print genhttp.writing_properties
        
        


    def test_discorun_matches(self):
        linux = self.sched.conf.discoveryruns.find_by_name('linux')
        self.assert_(linux != None)
        print linux.__dict__
        self.assert_(linux.matches == {u'osvendor': u'linux'})

        key = 'osvendor'
        value = 'microsoft'
        # Should not match this
        self.assert_(linux.is_matching(key, value) == False)

        key = 'osvendor'
        value = 'linux'
        # Should match this
        self.assert_(linux.is_matching(key, value) == True)

        # Low look for a list of matchings
        l = {'openports': '80', 'osvendor': 'linux'}
        # should match this
        self.assert_(linux.is_matching_disco_datas(l) == True)


    


if __name__ == '__main__':
    unittest.main()
