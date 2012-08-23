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
This class is for looking in a apache passwd file
to authenticate a user supplied password.
"""

import os
try:
    import crypt
except ImportError:
    # There is no crypt module on Windows systems
    import fcrypt as crypt

from shinken.log import logger
from shinken.misc.md5crypt import apache_md5_crypt
from shinken.basemodule import BaseModule

properties = {
    'daemons': ['webui', 'skonf'],
    'type': 'passwd_webui'
    }


# called by the plugin manager
def get_instance(plugin):
    logger.info("Instantiate an Apache/Passwd UI module for plugin %s" % plugin.get_name())

    instance = Passwd_Webui(plugin)
    return instance


class Passwd_Webui(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.passwd = modconf.passwd

    # Try to connect if we got true parameter
    def init(self):
        logger.debug("Connection test to the Apache/Passwd file")

    # To load the webui application
    def load(self, app):
        self.app = app

    def check_auth(self, user, password):
        try:
            f = open(self.passwd, 'r')
            for line in f.readlines():
                line = line.strip()
                # By pass bad lines
                if not ':' in line:
                    continue
                if line.startswith('#'):
                    continue
                elts = line.split(':')
                name = elts[0]
                hash = elts[1]
                if hash[:5] == '$apr1':
                    h = hash.split('$')
                    magic = h[1]
                    salt = h[2]
                else:
                    magic = None
                    salt = hash[:2]
                logger.debug("PASSWD: %s %s %s" % (name, hash, salt))
                # If we match the user, look at the crypt
                if name == user:
                    if magic == 'apr1':
                        compute_hash = apache_md5_crypt(password, salt)
                    else:
                        compute_hash = crypt.crypt(password, salt)
                    # print "Computed hash", compute_hash
                    if compute_hash == hash:
                        logger.info("Authentication success")
                        return True
                else:
                    logger.info("Authentication failed" % (name, user))
        except Exception, exp:
            logger.warning("Authentication against apache passwd file failed: %s " % (exp))
            return False
        finally:
            try:
                f.close()
            except:
                pass

        # At the end, we are not happy, so we return False
        logger.debug("Failed to authenticate user, return false")
        return False
