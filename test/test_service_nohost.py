#!/usr/bin/env python
# Copyright (C) 2009-2014:
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


class TestServiceNoHost(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_service_nohost.cfg')

    def test_service_with_no_host(self):
        # A service that has no host to be linked to should raise on error.
        self.assertIs(False, self.conf.conf_is_correct)

        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']


        self.assertLess(
            0,
            len( [ log
                        for log in logs
                        if re.search(
                                'a service has been defined without host_name nor hostgroups ',
                                log)
            ])
        )


if __name__ == '__main__':
    unittest.main()
