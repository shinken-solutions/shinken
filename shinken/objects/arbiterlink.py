#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2014:
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

import socket

from shinken.objects.satellitelink import SatelliteLink, SatelliteLinks
from shinken.property import IntegerProp, StringProp
from shinken.http_client import HTTPExceptions
from shinken.log import logger


""" TODO: Add some comment about this class for the doc"""
class ArbiterLink(SatelliteLink):
    id = 0
    my_type = 'arbiter'
    properties = SatelliteLink.properties.copy()
    properties.update({
        'arbiter_name':    StringProp(),
        'host_name':       StringProp(default=socket.gethostname()),
        'port':            IntegerProp(default=7770),
    })

    def get_name(self):
        return self.arbiter_name

    def get_config(self):
        return self.con.get('get_config')


    # Look for ourself as an arbiter. If we search for a specific arbiter name, go forit
    # If not look be our fqdn name, or if not, our hostname
    def is_me(self, lookup_name):
        logger.info("And arbiter is launched with the hostname:%s "
                    "from an arbiter point of view of addr:%s", self.host_name, socket.getfqdn())
        if lookup_name:
            return lookup_name == self.get_name()
        else:
            return self.host_name == socket.getfqdn() or self.host_name == socket.gethostname()

    def give_satellite_cfg(self):
        return {'port': self.port, 'address': self.address, 'name': self.arbiter_name,
                'use_ssl': self.use_ssl, 'hard_ssl_name_check': self.hard_ssl_name_check}

    def do_not_run(self):
        if self.con is None:
            self.create_connection()
        try:
            self.con.get('do_not_run')
            return True
        except HTTPExceptions, exp:
            self.con = None
            return False

    def get_satellite_list(self, daemon_type):
        if self.con is None:
            self.create_connection()
        try:
            r = self.con.get_satellite_list(daemon_type)
            return r
        except HTTPExceptions, exp:
            self.con = None
            return []

    def get_satellite_status(self, daemon_type, name):
        if self.con is None:
            self.create_connection()
        try:
            r = self.con.get_satellite_status(daemon_type, name)
            return r
        except HTTPExceptions, exp:
            self.con = None
            return {}

    def get_all_states(self):
        if self.con is None:
            self.create_connection()
        try:
            r = self.con.get('get_all_states')
            return r
        except HTTPExceptions, exp:
            self.con = None
            return None

    def get_objects_properties(self, table, properties=[]):
        if self.con is None:
            self.create_connection()
        try:
            print properties
            r = self.con.get('get_objects_properties', {'table': table, 'properties': properties})
            return r
        except HTTPExceptions, exp:
            self.con = None
            return None


class ArbiterLinks(SatelliteLinks):
    name_property = "arbiter_name"
    inner_class = ArbiterLink


    # We must have a realm property, so we find our realm
    def linkify(self, modules):
        self.linkify_s_by_plug(modules)
