# -*- coding: utf-8 ; mode: python -*-
#
# Copyright (C) 2012:
#    Hartmut Goebel <h.goebel@crazy-compilers.com>
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

"""

Helper module for importing the shinken library from the (uninstalled)
test-suite only, do NOT use the installed one if present.

"""

import imp, os
try:
    imp.load_module('shinken', 
                    *imp.find_module('shinken',
                                     [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]))
except ImportError:
    import shinken
