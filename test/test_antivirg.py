#!/usr/bin/env python
# -*- coding: utf-8 -*

from shinken_test import *

class TestConfig(ShinkenTest):

    def test_hostname_antivirg(self):
        """Check that it is allowed to have a host with the "__ANTI-VIRG__" 
           substring in its hostname

        """
        # load the configuration from file
        self.setup_with_file('etc/nagios_antivirg.cfg')


        # the global configuration must be valid
        self.assert_(
                       True == self.conf.conf_is_correct
                     ,("config is not correct")
                    )

        # try to get the host
        hst = self.conf.hosts.find_by_name('test__ANTI-VIRG___0')
        self.assert_(
                      hst is not None
                     ,("host 'test__ANTI-VIRG___0' not found")
                    )

        # Check that the host has a valid configuration
        self.assert_(
                      True == hst.is_correct()
                     ,("config of host '%s' is not true"
                       % (hst.get_name()))
                    )

    def test_parsing_comment(self):
        """Check that the semicolon is a comment delimiter"""

        # load the configuration from file
        self.setup_with_file('etc/nagios_antivirg.cfg')


        # the global configuration must be valid
        self.assert_(
                       True == self.conf.conf_is_correct
                     ,("config is not correct")
                    )

        # try to get the host
        hst = self.conf.hosts.find_by_name('test_host_1')
        self.assert_(
                      hst is not None
                     ,("host 'test_host_1' not found")
                    )

        # Check that the host has a valid configuration
        self.assert_(
                      True == hst.is_correct()
                     ,("config of host '%s' is not true"
                       % (hst.get_name()))
                    )

    def test_escaped_semicolon(self):
        """Check that it is possible to escape semicolon"""

        # load the configuration from file
        self.setup_with_file('etc/nagios_antivirg.cfg')


        # the global configuration must be valid
        self.assert_(
                       True == self.conf.conf_is_correct
                     ,("config is not correct")
                    )

        # try to get the host
        hst = self.conf.hosts.find_by_name('test_host_2;')
        self.assert_(
                      hst is not None
                     ,("host 'test_host_2;' not found")
                    )

        # Check that the host has a valid configuration
        self.assert_(
                      True == hst.is_correct()
                     ,("config of host '%s' is not true"
                       % (hst.get_name()))
                    )


if '__main__' == __name__:
    unittest.main()

