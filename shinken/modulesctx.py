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


import imp
import importlib
import os
import sys
from os.path import abspath, join, exists
import traceback

from shinken.log import logger

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
        try:
            return importlib.import_module('.module', mod_name)
        except ImportError as err:
            logger.warning('Cannot import %s as a package (%s) ; trying as bare module..',
                           mod_name, err)
        mod_dir = abspath(join(self.modules_dir, mod_name))
        mod_file = join(mod_dir, 'module.py')
        if os.path.exists(mod_file):
            # important, equivalent to import fname from module.py:
            load_it = lambda: imp.load_source(mod_name, mod_file)
        else:
            load_it = lambda: imp.load_compiled(mod_name, mod_file+'c')
        # We add this dir to sys.path so the module can load local files too
        if mod_dir not in sys.path:
            sys.path.append(mod_dir)
        try:
            return load_it()
        except Exception as err:
            logger.warning("Importing module %s failed: %s ; backtrace=%s",
                           mod_name, err, traceback.format_exc())
            sys.path.remove(mod_dir)
            raise


modulesctx = ModulesContext()

