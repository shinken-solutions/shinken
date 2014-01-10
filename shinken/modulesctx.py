#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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
import os
import sys

from shinken.log import logger

class ModulesContext(object):
    def __init__(self):
        pass

    def set_modulesdir(self, modulesdir):
        self.modules_dir = modulesdir

    def get_modulesdir(self):
        return self.modules_dir


    # Useful for a module to load another one, and get a handler to it
    def get_module(self, name):
        mod_dir  = os.path.abspath(os.path.join(self.modules_dir, name))
        if not mod_dir in sys.path:
            sys.path.append(mod_dir)
        mod_path = os.path.join(self.modules_dir, name, 'module.py')
        if not os.path.exists(mod_path):
            mod_path = os.path.join(self.modules_dir, name, 'module.pyc')
        try:
            if mod_path.endswith('.py'):
                r = imp.load_source(name, mod_path)
            else:
                r = imp.load_compiled(name, mod_path)
        except:
            logger.warning('The module %s cannot be founded or load' % mod_path)
            raise
        return r


modulesctx = ModulesContext()

