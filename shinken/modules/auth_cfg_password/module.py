#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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
This class is for looking in the configuration for auth
"""

import os
#import crypt

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['webui', 'skonf'],
    'type': 'cfg_password_webui'
    }


# called by the plugin manager
def get_instance(plugin):
    logger.info("[Cfg Password UI] Get an CFG/Password UI module for plugin %s" % plugin.get_name())

    instance = Cfg_Password_Webui(plugin)
    return instance


class Cfg_Password_Webui(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)

    # Try to connect if we got true parameter
    def init(self):
        logger.info("[Cfg Password UI] Trying to initialize the CFG/Password auth")

    # To load the webui application
    def load(self, app):
        self.app = app

    def check_auth(self, user, password):
        c = self.app.datamgr.get_contact(user)

        # Ok, if the user is bad, bailout
        if not c:
            return False

        logger.info("[Cfg Password UI] User %s try to init" % user)
        p = None
        # In skonf, it's dummy object
        if isinstance(c, dict):
            p = c.get('password', 'NOPASSWORDSET')
        else:
            p = c.password
        return p == password and p != 'NOPASSWORDSET'
