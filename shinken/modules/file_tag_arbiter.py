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

from shinken.log import logger
from shinken.basemodule import BaseModule


properties = {
    'daemons': ['arbiter'],
    'type': 'file_tag',
    }


# called by the plugin manager to get a module
def get_instance(plugin):
    logger.info("[File Tag] Get a FileTag module for plugin %s" % plugin.get_name())

    # Catch errors
    path = plugin.path
    prop = plugin.property
    value = plugin.value
    method = getattr(plugin, 'method', 'replace')
    ignore_hosts = getattr(plugin, 'ignore_hosts', None)

    instance = File_Tag_Arbiter(plugin, path, prop, value, method, ignore_hosts)
    return instance



# Our module class
class File_Tag_Arbiter(BaseModule):
    def __init__(self, mod_conf, path, prop, value, method, ignore_hosts=None):
        BaseModule.__init__(self, mod_conf)
        self.path = path
        self.property = prop
        self.value = value
        self.method = method
        if ignore_hosts:
            self.ignore_hosts = ignore_hosts.split(', ')
            logger.debug("[File Tag] Ignoring hosts : %s" % self.ignore_hosts)
        else:
            self.ignore_hosts = []
        self.hosts = []

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[File Tag] Reading the module file")
        try:
            f = open(self.path, 'r')
            for line in f.readlines():
                host = line.strip()
                self.hosts.append(host)
            f.close()
        except IOError, e:
            logger.error("[File Tag] raised an exception : '%s'" % str(e))
            raise
        logger.info('[File Tag] Load %d hosts from file' % len(self.hosts))
        

    def hook_early_configuration(self, arb):
        logger.info("[FileTag] in hook late config")
        for h in arb.conf.hosts:
            if not hasattr(h, 'host_name'):
                continue

            hname = h.host_name
            
            if hname in self.ignore_hosts:
                logger.debug("[File Tag] Ignoring host %s" % hname)
                continue

            logger.debug("[File Tag] Looking for %s" % hname)

            # If we got an match and the object do not already got
            # the property, tag it!
            if hname in self.hosts:
                logger.debug("[File Tag] Hosts is in the file")
                # 4 cases: append , replace and set
                # append will join with the value if exist
                # replace will replace it if NOT existing
                # set put the value even if the property exists
                if self.method == 'append':
                    orig_v = getattr(h, self.property, '')
                    logger.debug("[File Tag] Orig_v: %s" % str(orig_v))
                    new_v = ','.join([orig_v, self.value])
                    logger.debug("[File Tag] Newv %s" % new_v)
                    setattr(h, self.property, new_v)

                # Same but we put before
                if self.method == 'prepend':
                    orig_v = getattr(h, self.property, '')
                    logger.debug("[File Tag] Orig_v: %s" % str(orig_v))
                    new_v = ','.join([self.value, orig_v])
                    logger.debug("[File Tag] Newv %s" % new_v)
                    setattr(h, self.property, new_v)
                                                                                                                        

                if self.method == 'replace':
                    if not hasattr(h, self.property):
                        # Ok, set the value!
                        setattr(h, self.property, self.value)

                # Ok set is STRONG set, just set it and that's all
                if self.method == 'set':
                    setattr(h, self.property, self.value)
