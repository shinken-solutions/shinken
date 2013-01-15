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
# This module imports hosts and services configuration from a MySQL Database
# Queries for getting hosts and services are pulled from shinken-specific.cfg configuration file.

import os

# Try to import landscape API 
try:
    from landscape_api.base import API, HTTPError
except ImportError:
    API = HTTPError = None

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['arbiter'],
    'type': 'landscape_import',
    'external': False,
    'phases': ['configuration'],
}


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.debug("[Landscape Importer Module]: Get Landscape importer instance for plugin %s" % plugin.get_name())
    if not API:
        raise Exception('Missing module landscape-api. Please install it from https://launchpad.net/~landscape/+archive/landscape-api.')

    # Beware : we must have RAW string here, not unicode!
    key = str(plugin.key.strip())
    secret = str(plugin.secret.strip())
    ca = getattr(plugin, 'ca', None)
    default_template = getattr(plugin, 'default_template', '')
    https_proxy = getattr(plugin, 'https_proxy', '')
    
    instance = Landscape_importer_arbiter(plugin, key, secret, ca, default_template, https_proxy)
    return instance


# Retrieve hosts from landscape API
class Landscape_importer_arbiter(BaseModule):
    def __init__(self, mod_conf, key, secret, ca, default_template, https_proxy):
        BaseModule.__init__(self, mod_conf)
        self.key = key
        self.secret = secret
        self.ca = ca
        self.default_template = default_template
        self.https_proxy   = https_proxy


    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        if self.https_proxy:
            os.environ["https_proxy"] = self.https_proxy
            
        logger.debug("[Landscape Importer Module]: Try to open a Landscape connection")
        uri = "https://landscape.canonical.com/api/"
        try:
            if self.ca:
                self.api = API(uri, self.key, self.secret, self.ca)
            else:
                self.api = API(uri, self.key, self.secret)
        except HTTPError, e:
            logger.debug("Landscape Module: Error %s" % e)
            raise
        logger.info("[Landscape Importer Module]: Connection opened")


    # Main function that is called in the CONFIGURATION phase
    def get_objects(self):
        try:
            computers = self.api.get_computers(with_network=True, limit=30000)
        except HTTPError, e:
            logger.debug("Landscape Module: Error %s" % e)
            raise
        
        # Create variables for result
        r = {'hosts' : []}

        for c in computers:
            hname = c['hostname']
            alias = c["title"]
            tags = c["tags"]
            if tags == [] and self.default_template:
                tags = [self.default_template]
            ips = [net["ip_address"] for net in c["network_devices"]]

            # If there is more than one IP address, use the first
            ip = ''
            if len(ips) > 0:
                ip = ips[0]
            # By default take the IP as teh address
            address = ip
            # But if not available, use the hostname
            if not address:
                address = hname
            h = {'host_name' : hname,
                 'alias'     : alias,
                 'use'       : tags,
                 'use'       : ','.join(tags)
                 }
            r['hosts'].append(h)

        logger.debug("[Landscape Importer Module]: Returning to Arbiter %d hosts" % len(r['hosts']))
        return r
