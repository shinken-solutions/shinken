#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
    import redis
except ImportError:
    redis = None
import cPickle

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['scheduler'],
    'type': 'redis_retention',
    'external': False,
    }


def get_instance(plugin):
    """
    Called by the plugin manager to get a broker
    """
    logger.debug("Get a redis retention scheduler module for plugin %s" % plugin.get_name())
    if not redis:
        raise Exception('Missing the module python-redis. Please install it.')
    server = plugin.server
    instance = Redis_retention_scheduler(plugin, server)
    return instance


class Redis_retention_scheduler(BaseModule):
    def __init__(self, modconf, server):
        BaseModule.__init__(self, modconf)
        self.server = server

    def init(self):
        """
        Called by Scheduler to say 'let's prepare yourself guy'
        """
        print "Initilisation of the redis module"
        #self.return_queue = self.properties['from_queue']
        self.mc = redis.Redis(self.server)

    def hook_save_retention(self, daemon):
        """
        main function that is called in the retention creation pass
        """
        log_mgr = logger
        print "[RedisRetention] asking me to update the retention objects"

        all_data = daemon.get_retention_data()

        hosts = all_data['hosts']
        services = all_data['services']

        # Now the flat file method
        for h_name in hosts:
            h = hosts[h_name]
            key = "HOST-%s" % h_name
            val = cPickle.dumps(h)
            self.mc.set(key, val)

        for (h_name, s_desc) in services:
            s = services[(h_name, s_desc)]
            key = "SERVICE-%s,%s" % (h_name, s_desc)
            # space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            #print "Using key", key
            val = cPickle.dumps(s)
            self.mc.set(key, val)
        log_mgr.log("Retention information updated in Redis")

    # Should return if it succeed in the retention load or not
    def hook_load_retention(self, daemon):
        log_mgr = logger

        # Now the new redis way :)
        log_mgr.log("[RedisRetention] asking me to load the retention objects")

        # We got list of loaded data from retention server
        ret_hosts = {}
        ret_services = {}

        # We must load the data and format as the scheduler want :)
        for h in daemon.hosts:
            key = "HOST-%s" % h.host_name
            val = self.mc.get(key)
            if val is not None:
                # redis get unicode, but we send string, so we are ok
                #val = str(unicode(val))
                val = cPickle.loads(val)
                ret_hosts[h.host_name] = val

        for s in daemon.services:
            key = "SERVICE-%s,%s" % (s.host.host_name, s.service_description)
            # space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            #print "Using key", key
            val = self.mc.get(key)
            if val is not None:
                #val = str(unicode(val))
                val = cPickle.loads(val)
                ret_services[(s.host.host_name, s.service_description)] = val

        all_data = {'hosts': ret_hosts, 'services': ret_services}

        # Ok, now comme load them scheduler :)
        daemon.restore_retention_data(all_data)

        log_mgr.log("[RedisRetention] OK we've load data from redis server")

        return True
