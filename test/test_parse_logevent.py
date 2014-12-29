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

from shinken_test import *
from shinken.misc.logevent import LogEvent


class TestParseLogEvent(ShinkenTest):

    def test_notification_service(self):
        log = '[1402515279] SERVICE NOTIFICATION: admin;localhost;check-ssh;CRITICAL;notify-service-by-email;Connection refused'
        expected = {
            'hostname': 'localhost',
            'event_type': 'NOTIFICATION',
            'service_desc': 'check-ssh',
            'state': 'CRITICAL',
            'contact': 'admin',
            'time': 1402515279,
            'notification_method': 'notify-service-by-email',
            'notification_type': 'SERVICE',
            'output': 'Connection refused',
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

    def test_notification_host(self):
        log = '[1402515279] HOST NOTIFICATION: admin;localhost;CRITICAL;notify-service-by-email;Connection refused'
        expected = {
            'hostname': 'localhost',
            'event_type': 'NOTIFICATION',
            'service_desc': None,
            'state': 'CRITICAL',
            'contact': 'admin',
            'time': 1402515279,
            'notification_method': 'notify-service-by-email',
            'notification_type': 'HOST',
            'output': 'Connection refused',
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

    def test_alert_service(self):
        log = '[1329144231] SERVICE ALERT: dfw01-is02-006;cpu load maui;WARNING;HARD;4;WARNING - load average: 5.04, 4.67, 5.04'
        expected = {
            'alert_type': 'SERVICE',
            'event_type': 'ALERT',
            'service_desc': 'cpu load maui',
            'attempts': 4,
            'state_type': 'HARD',
            'state': 'WARNING',
            'time': 1329144231,
            'output': 'WARNING - load average: 5.04, 4.67, 5.04',
            'hostname': 'dfw01-is02-006'
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

    def test_alert_host(self):
        log = '[1329144231] HOST ALERT: dfw01-is02-006;WARNING;HARD;4;WARNING - load average: 5.04, 4.67, 5.04'
        expected = {
            'alert_type': 'HOST',
            'event_type': 'ALERT',
            'service_desc': None,
            'attempts': 4,
            'state_type': 'HARD',
            'state': 'WARNING',
            'time': 1329144231,
            'output': 'WARNING - load average: 5.04, 4.67, 5.04',
            'hostname': 'dfw01-is02-006'
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

    def test_downtime_alert_host(self):
        log = '[1279250211] HOST DOWNTIME ALERT: maast64;STARTED; Host has entered a period of scheduled downtime'
        expected = {
            'event_type': 'DOWNTIME',
            'hostname': 'maast64',
            'state': 'STARTED',
            'time': 1279250211,
            'output': ' Host has entered a period of scheduled downtime',
            'downtime_type': 'HOST'
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

    def test_host_flapping(self):
        log = '[1375301662] SERVICE FLAPPING ALERT: testhost;check_ssh;STARTED; Service appears to have started flapping (24.2% change >= 20.0% threshold)'
        expected = {
            'alert_type': 'SERVICE',
            'event_type': 'FLAPPING',
            'hostname': 'testhost',
            'output': ' Service appears to have started flapping (24.2% change >= 20.0% threshold)',
            'service_desc': 'check_ssh',
            'state': 'STARTED',
            'time': 1375301662
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

    def test_service_flapping(self):
        log = '[1375301662] HOST FLAPPING ALERT: hostbw;STARTED; Host appears to have started flapping (20.1% change > 20.0% threshold)'
        expected = {
            'alert_type': 'HOST',
            'event_type': 'FLAPPING',
            'hostname': 'hostbw',
            'output': ' Host appears to have started flapping (20.1% change > 20.0% threshold)',
            'service_desc': None,
            'state': 'STARTED',
            'time': 1375301662
        }
        event = LogEvent(log)
        self.assertEqual(event.data, expected)

if __name__ == '__main__':
    unittest.main()
