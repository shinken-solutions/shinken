#!/usr/bin/env python

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


import os
import sys


from shinken.modulesmanager import ModulesManager


class ModulesContext(object):
    def __init__(self):
        self.modules_dir = None

    def set_modulesdir(self, modulesdir):
        self.modules_dir = modulesdir

    def get_modulesdir(self):
        return self.modules_dir

    # Useful for a module to load another one, and get a handler to it
    def get_module(self, mod_name):
        if self.modules_dir and self.modules_dir not in sys.path:
            sys.path.append(self.modules_dir)
        if self.modules_dir:
            mod_dir = os.path.join(self.modules_dir, mod_name)
        else:
            mod_dir = None
        # to keep it back-compatible with previous Shinken module way,
        # we first try with "import `mod_name`.module" and if we succeed
        # then that's the one to actually use:
        mod = ModulesManager.try_best_load('.module', mod_name)
        if mod:
            return mod
        # otherwise simply try new and old style:
        return ModulesManager.try_load(mod_name, mod_dir)


modulesctx = ModulesContext()
