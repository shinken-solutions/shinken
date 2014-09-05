#!/usr/bin/env python
#  -*- coding: utf-8 -*-
#
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
from shinken.log import logger


class TestConfig(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_1r_1h_1s.cfg')

    # Try to raise an utf8 log message
    def test_utf8log(self):
        sutf = 'h\351h\351'  # Latin Small Letter E with acute in Latin-1
        logger.info(sutf)
        sutf8 = u'I love myself $£¤'  # dollar, pound, currency
        logger.info(sutf8)
        s = unichr(40960) + u'abcd' + unichr(1972)
        logger.info(s)



if __name__ == '__main__':
    unittest.main()
