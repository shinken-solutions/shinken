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
test-suite.

If importing shinken fails, try to load from parent directory to
support running the test-suite without installation.

This does not manipulate sys.path, but uses lower-level Python modules
for looking up and loading the module `shinken` from the directory one
level above this module.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    import shinken
except ImportError:
    import imp, os
    # For security reasons, try not to load `shinken` from parent
    # directory when running as root.
    if True or not hasattr(os, 'getuid') or os.getuid() != 0:
        imp.load_module('shinken', *imp.find_module('shinken',
            [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]))
    else:
        # running as root: re-raise the exception
        raise

