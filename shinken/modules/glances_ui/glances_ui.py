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
This module is to allow specific views that are using Glances daemon in the WebUI.
"""

import os

from shinken.basemodule import BaseModule
from shinken.log import logger


class Glances_UI(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)


    # Called by Broker to say 'let's prepare yourself guy'
    def init(self):
        pass


    # Ok We got some plugins for WebUI, so give the info at WebUI :)
    def get_webui_plugins_path(self, webui):
        my_dir = os.path.os.path.dirname(__file__)
        plugins_dir = os.path.join(my_dir, 'plugins')
        return plugins_dir
