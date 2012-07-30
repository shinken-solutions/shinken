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


# This Class is an example of an Scheduler module
# Here for the configuration phase AND running one
try:
    import memcache
except ImportError:
    memcache = None

import cPickle

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['scheduler'],
    'type': 'memcache_retention',
    'external': False,
    }


# called by the plugin manager to get a broker
def get_instance(modconf):
    logger.log("Get a memcache retention scheduler module for plugin %s" % modconf.get_name())
    if not memcache:
        raise Exception('Missing module python-memcache. Please install it.')
    instance = Memcache_retention_scheduler(modconf)
    return instance


# Just print some stuff
class Memcache_retention_scheduler(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.server = mod_conf.server
        self.port = mod_conf.port

    # Called by Scheduler to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the memcache module"
        #self.return_queue = self.properties['from_queue']
        self.mc = memcache.Client(['%s:%s' % (self.server, self.port)], debug=0)

    # Ok, main function that is called in the retention creation pass
    def hook_save_retention(self, daemon):
        log_mgr = logger
        print "[MemcacheRetention] asking me to update the retention objects"

        all_data = daemon.get_retention_data()

        hosts = all_data['hosts']
        services = all_data['services']


        # Now the flat file method
        for h_name in hosts:
            h = hosts[h_name]
            key = "HOST-%s" % h_name
            key = key.encode('utf8', 'ignore')
            val = cPickle.dumps(h)
            self.mc.set(key, val)

        for (h_name, s_desc) in services:
            key = "SERVICE-%s,%s" % (h_name, s_desc)
            s = services[(h_name, s_desc)]
            # space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            key = key.encode('utf8', 'ignore')
            #print "Using key", key
            val = cPickle.dumps(s)
            self.mc.set(key, val)
        log_mgr.log("Retention information updated in Memcache")

    # Should return if it succeed in the retention load or not
    def hook_load_retention(self, daemon):
        log_mgr = logger
        print "[MemcacheRetention] asking me to load the retention objects"

        # Now the old flat file way :(
        log_mgr.log("[MemcacheRetention] asking me to load the retention objects")

        # We got list of loaded data from retention server
        ret_hosts = {}
        ret_services = {}

        # Now the flat file method
        for h in daemon.hosts:
            key = "HOST-%s" % h.host_name
            key = key.encode('utf8', 'ignore')
            val = self.mc.get(key)
            if val is not None:
                val = cPickle.loads(val)
                ret_hosts[h.host_name] = val

        for s in daemon.services:
            key = "SERVICE-%s,%s" % (s.host.host_name, s.service_description)
            # space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            key = key.encode('utf8', 'ignore')
            val = self.mc.get(key)
            if val is not None:
                val = cPickle.loads(val)
                ret_services[(s.host.host_name, s.service_description)] = val

        all_data = {'hosts': ret_hosts, 'services': ret_services}

        # Ok, now comme load them scheduler :)
        daemon.restore_retention_data(all_data)

        log_mgr.log("[MemcacheRetention] OK we've load data from memcache server")

        return True
