#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2014 - Savoir-Faire Linux inc.
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

import re

event_type_pattern = \
    re.compile(
        '^\[[0-9]{10}] (?:HOST|SERVICE) (ALERT|NOTIFICATION|FLAPPING|DOWNTIME)(?: ALERT)?:.*'
    )
event_types = {
    'NOTIFICATION': {
        # ex: "[1402515279] SERVICE NOTIFICATION:
        # admin;localhost;check-ssh;CRITICAL;notify-service-by-email;Connection refused"
        'pattern': '\[([0-9]{10})\] (HOST|SERVICE) (NOTIFICATION): '
        '([^\;]*);([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'notification_type',  # 'SERVICE' (or could be 'HOST')
            'event_type',  # 'NOTIFICATION'
            'contact',  # 'admin'
            'hostname',  # 'localhost'
            'service_desc',  # 'check-ssh' (or could be None)
            'state',  # 'CRITICAL'
            'notification_method',  # 'notify-service-by-email'
            'output',  # 'Connection refused'
        ]
    },
    'ALERT': {
        # ex: "[1329144231] SERVICE ALERT:
        #  dfw01-is02-006;cpu load maui;WARNING;HARD;4;WARNING - load average: 5.04, 4.67, 5.04"
        'pattern': '^\[([0-9]{10})] (HOST|SERVICE) (ALERT): '
                   '([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*);([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'alert_type',  # 'SERVICE' (or could be 'HOST')
            'event_type',  # 'ALERT'
            'hostname',  # 'localhost'
            'service_desc',  # 'cpu load maui' (or could be None)
            'state',  # 'WARNING'
            'state_type',  # 'HARD'
            'attempts',  # '4'
            'output',  # 'WARNING - load average: 5.04, 4.67, 5.04'
        ]
    },
    'DOWNTIME': {
        # ex: "[1279250211] HOST DOWNTIME ALERT:
        # maast64;STARTED; Host has entered a period of scheduled downtime"
        'pattern': '^\[([0-9]{10})\] (HOST|SERVICE) (DOWNTIME) ALERT: '
        '([^\;]*);(STARTED|STOPPED|CANCELLED);(.*)',
        'properties': [
            'time',
            'downtime_type',  # '(SERVICE or could be 'HOST')
            'event_type',  # 'DOWNTIME'
            'hostname',  # 'maast64'
            'state',  # 'STARTED'
            'output',  # 'Host has entered a period of scheduled downtime'
        ]
    },
    'FLAPPING': {
        # service flapping ex: "[1375301662] SERVICE FLAPPING ALERT:
        # testhost;check_ssh;STARTED;
        # Service appears to have started flapping (24.2% change >= 20.0% threshold)"

        # host flapping ex: "[1375301662] HOST FLAPPING ALERT:
        # hostbw;STARTED; Host appears to have started flapping (20.1% change > 20.0% threshold)"
        'pattern': '^\[([0-9]{10})] (HOST|SERVICE) (FLAPPING) ALERT: '
        '([^\;]*);(?:([^\;]*);)?([^\;]*);([^\;]*)',
        'properties': [
            'time',
            'alert_type',  # 'SERVICE' or 'HOST'
            'event_type',  # 'FLAPPING'
            'hostname',  # The hostname
            'service_desc',  # The service description or None
            'state',  # 'STOPPED' or 'STARTED'
            'output',  # 'Service appears to have started flapping (24% change >= 20.0% threshold)'
        ]
    }
}


# Class for parsing event logs
# Populates self.data with the log type's properties
class LogEvent:

    def __init__(self, log):
        self.data = {}

        # Find the type of event
        event_type_match = event_type_pattern.match(log)

        if event_type_match:
            # parse it with it's pattern
            event_type = event_types[event_type_match.group(1)]
            properties_match = re.match(event_type['pattern'], log)

            if properties_match:
                # Populate self.data with the event's properties
                for i, p in enumerate(event_type['properties']):
                    self.data[p] = properties_match.group(i + 1)

                # Convert the time to int
                self.data['time'] = int(self.data['time'])

                # Convert attempts to int
                if 'attempts' in self.data:
                    self.data['attempts'] = int(self.data['attempts'])

    def __iter__(self):
        return self.data.iteritems()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

    def __str__(self):
        return str(self.data)
