#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

from shinken.objects.satellitelink import SatelliteLink, SatelliteLinks
from shinken.property import BoolProp, IntegerProp, StringProp
from shinken.log import logger
from shinken.http_client import HTTPExceptions


class SchedulerLink(SatelliteLink):
    """Please Add a Docstring to describe the class here"""

    id = 0

    # Ok we lie a little here because we are a mere link in fact
    my_type = 'scheduler'

    properties = SatelliteLink.properties.copy()
    properties.update({
        'scheduler_name':     StringProp(fill_brok=['full_status']),
        'port':               IntegerProp(default=7768, fill_brok=['full_status']),
        'weight':             IntegerProp(default=1, fill_brok=['full_status']),
        'skip_initial_broks': BoolProp(default=False, fill_brok=['full_status']),
        'accept_passive_unknown_check_results': BoolProp(default=False, fill_brok=['full_status']),
    })

    running_properties = SatelliteLink.running_properties.copy()
    running_properties.update({
        'conf': StringProp(default=None),
        'need_conf': StringProp(default=True),
        'external_commands': StringProp(default=[]),
        'push_flavor': IntegerProp(default=0),
    })

    def get_name(self):
        return self.scheduler_name

    def run_external_commands(self, commands):
        if self.con is None:
            self.create_connection()
        if not self.alive:
            return None
        logger.debug("[SchedulerLink] Sending %d commands", len(commands))
        try:
            self.con.post('run_external_commands', {'cmds': commands})
        except HTTPExceptions, exp:
            self.con = None
            logger.debug(exp)
            return False

    def register_to_my_realm(self):
        self.realm.schedulers.append(self)

    def give_satellite_cfg(self):
        return {'port': self.port, 'address': self.address,
                'name': self.scheduler_name, 'instance_id': self.id,
                'active': self.conf is not None, 'push_flavor': self.push_flavor,
                'timeout': self.timeout, 'data_timeout': self.data_timeout,
                'use_ssl': self.use_ssl, 'hard_ssl_name_check': self.hard_ssl_name_check}

    # Some parameters can give as 'overridden parameters' like use_timezone
    # so they will be mixed (in the scheduler) with the standard conf sent by the arbiter
    def get_override_configuration(self):
        r = {}
        properties = self.__class__.properties
        for prop, entry in properties.items():
            if entry.override:
                r[prop] = getattr(self, prop)
        return r


class SchedulerLinks(SatelliteLinks):
    """Please Add a Docstring to describe the class here"""

    name_property = "scheduler_name"
    inner_class = SchedulerLink
