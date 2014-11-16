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
import imp
import traceback
from os.path import abspath, join, exists


from shinken.log import logger
from shinken.misc import importlib


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
        except Exception as err:
            logger.warning('Cannot import %s as a package (%s) ; trying as bare module..',
                           mod_name, err)
            raise


modulesctx = ModulesContext()

