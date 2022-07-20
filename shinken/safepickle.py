# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

from __future__ import absolute_import, division, print_function, unicode_literals

import pickle
import sys

# Unpickle but strip and remove all __reduce__ things
# so we don't allow external code to be executed
# Code from Graphite::carbon project
class SafeUnpickler(pickle.Unpickler):
    PICKLE_SAFE = {
        'copy_reg': set(['_reconstructor']),
        '__builtin__': set(['object', 'set']),
        'builtins': set(['object', 'set']),
    }


    @classmethod
    def find_class(cls, module, name):
        if module not in cls.PICKLE_SAFE and not module.startswith('shinken.'):
            raise ValueError('Attempting to unpickle unsafe module %s' % module)
        __import__(module)
        mod = sys.modules[module]
        if not module.startswith('shinken.') and name not in cls.PICKLE_SAFE[module]:
            raise ValueError('Attempting to unpickle unsafe class %s/%s' %
                             (module, name))
        return getattr(mod, name)
