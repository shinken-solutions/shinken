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


# This Class is an example of an Arbiter module
# Here for the configuration phase AND running one

import socket

from IPy import IP
from shinken.basemodule import BaseModule
from shinken.log import logger


# Just print some stuff
class Ip_Tag_Arbiter(BaseModule):
    def __init__(self, mod_conf, ip_range, prop, value, method):
        BaseModule.__init__(self, mod_conf)
        self.ip_range = IP(ip_range)
        self.property = prop
        self.value = value
        self.method = method

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[IP Tag] Initilisation of the ip range tagguer module")

    def hook_early_configuration(self, arb):
        logger.info("[IpTag] in hook late config")
        for h in arb.conf.hosts:
            if not hasattr(h, 'address') and not hasattr(h, 'host_name'):
                continue
            # The address to resolve
            addr = None

            # By default take the address, if not, take host_name
            if not hasattr(h, 'address'):
                addr = h.host_name
            else:
                addr = h.address

            logger.info("[IP Tag] Looking for h" % h.get_name())
            logger.info("[IP Tag] Address is %s" % str(addr))
            h_ip = None
            try:
                IP(addr)
                # If we reach here, it's it was a real IP :)
                h_ip = addr
            except:
                pass

            # Ok, try again with name resolution
            if not h_ip:
                try:
                    h_ip = socket.gethostbyname(addr)
                except:
                    pass

            # Ok, maybe we succeed :)
            logger.info("[IP Tag] Host ip is: %s" % str(h_ip))
            # If we got an ip that match and the object do not already got
            # the property, tag it!
            if h_ip and h_ip in self.ip_range:
                logger.info("[IP Tag] Is in the range")
                # 2 cases: append or replace.
                # append will join with the value if exist
                # replace will replace it if NOT existing
                if self.method == 'append':
                    orig_v = getattr(h, self.property, '')
                    logger.info("[IP Tag] Orig_v: %s" % str(orig_v))
                    new_v = ','.join([orig_v, self.value])
                    logger.info("[IP Tag] Newv %s" % new_v)
                    setattr(h, self.property, new_v)

                if self.method == 'replace':
                    if not hasattr(h, self.property):
                        # Ok, set the value!
                        setattr(h, self.property, self.value)
