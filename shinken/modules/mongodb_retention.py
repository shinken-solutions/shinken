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

"""
This is a scheduler module to save host/sevice retention data into a mongodb databse
"""

import cPickle

try:
    from pymongo.connection import Connection
    import gridfs
    from gridfs import GridFS
except ImportError:
    Connection = None

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['scheduler'],
    'type': 'mongodb_retention',
    'external': False,
    }


def get_instance(plugin):
    """
    Called by the plugin manager to get a broker
    """
    logger.debug("Get a Mongodb retention scheduler module for plugin %s" % plugin.get_name())
    if not Connection:
        raise Exception('Cannot find the module python-pymongo or python-gridfs. Please install both.')
    uri = plugin.uri
    database = plugin.database
    instance = Mongodb_retention_scheduler(plugin, uri, database)
    return instance


class Mongodb_retention_scheduler(BaseModule):
    def __init__(self, modconf, uri, database):
        BaseModule.__init__(self, modconf)
        self.uri = uri
        self.database = database

    def init(self):
        """
        Called by Scheduler to say 'let's prepare yourself guy'
        """
        logger.debug("Initilisation of the mongodb  module")
        self.con = Connection(self.uri)
        # Open a gridfs connection
        self.db = getattr(self.con, self.database)
        self.hosts_fs = GridFS(self.db, collection='retention_hosts')
        self.services_fs = GridFS(self.db, collection='retention_services')

    def hook_save_retention(self, daemon):
        """
        main function that is called in the retention creation pass
        """
        logger.debug("[MongodbRetention] asking me to update the retention objects")

        all_data = daemon.get_retention_data()

        hosts = all_data['hosts']
        services = all_data['services']

        # Now the flat file method
        for h_name in hosts:
            h = hosts[h_name]
            key = "HOST-%s" % h_name
            val = cPickle.dumps(h, protocol=cPickle.HIGHEST_PROTOCOL)
            # First delete if a previous one is here, because gridfs is a versionned
            # fs, so we only want the last version...
            self.hosts_fs.delete(key)
            # We save it in the Gridfs for hosts
            fd = self.hosts_fs.put(val, _id=key, filename=key)

        for (h_name, s_desc) in services:
            s = services[(h_name, s_desc)]
            key = "SERVICE-%s,%s" % (h_name, s_desc)
            # space are not allowed in a key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            val = cPickle.dumps(s, protocol=cPickle.HIGHEST_PROTOCOL)

            # We save the binary dumps in a gridfs system
            # First delete if a previous one is here, because gridfs is a versionned
            # fs, so we only want the last version...
            self.services_fs.delete(key)
            fd = self.services_fs.put(val, _id=key, filename=key)

        logger.info("Retention information updated in Mongodb")

    # Should return if it succeed in the retention load or not
    def hook_load_retention(self, daemon):

        # Now the new redis way :)
        logger.debug("MongodbRetention] asking me to load the retention objects")

        # We got list of loaded data from retention uri
        ret_hosts = {}
        ret_services = {}

        # We must load the data and format as the scheduler want :)
        for h in daemon.hosts:
            key = "HOST-%s" % h.host_name
            try:
                fd = self.hosts_fs.get_last_version(key)
            except gridfs.errors.NoFile, exp:
                # Go in the next host object
                continue
            val = fd.read()

            if val is not None:
                val = cPickle.loads(val)
                ret_hosts[h.host_name] = val

        for s in daemon.services:
            key = "SERVICE-%s,%s" % (s.host.host_name, s.service_description)
            # space are not allowed in memcache key.. so change it by SPACE token
            key = key.replace(' ', 'SPACE')
            try:
                fd = self.services_fs.get_last_version(key)
            except gridfs.errors.NoFile, exp:
                # Go in the next host object
                continue
            val = fd.read()

            if val is not None:
                val = cPickle.loads(val)
                ret_services[(s.host.host_name, s.service_description)] = val

        all_data = {'hosts': ret_hosts, 'services': ret_services}

        # Ok, now comme load them scheduler :)
        daemon.restore_retention_data(all_data)

        logger.info("[MongodbRetention] Retention objects loaded successfully.")

        return True
