#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from shinken.objects.satellitelink import SatelliteLink, SatelliteLinks
from shinken.property import IntegerProp, StringProp


class BrokerLink(SatelliteLink):
    """TODO: Add some comment about this class for the doc"""
    id = 0
    my_type = 'broker'
    properties = SatelliteLink.properties.copy()
    properties.update({
        'broker_name': StringProp(fill_brok=['full_status'], to_send=True),
        'port': IntegerProp(default=7772, fill_brok=['full_status']),
    })

    def get_name(self):
        return self.broker_name

    def register_to_my_realm(self):
        self.realm.brokers.append(self)


class BrokerLinks(SatelliteLinks):
    """TODO: Add some comment about this class for the doc"""
    name_property = "broker_name"
    inner_class = BrokerLink
