#!/usr/bin/env python
# Copyright (C) 2009-2015:
#    Coavoux Sebastien <s.coavoux@free.fr>
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

#
# This file is used to test reading and processing of config files
#

import unittest2 as unittest

import string

from shinken_test import time_hacker
from shinken.log import logger
from shinken.objects.config import Config
from shinken.brok import Brok
from shinken.external_command import ExternalCommand
from shinken.property import UnusedProp, StringProp, IntegerProp, \
    BoolProp, CharProp, DictProp, FloatProp, ListProp, AddrProp, ToGuessProp


class TestEndParsingType(unittest.TestCase):

    def map_type(self, obj):
        # TODO: Replace all str with unicode when done in property.default attribute
        # TODO: Fix ToGuessProp as it may be a list.

        if isinstance(obj, ListProp):
            return list

        if isinstance(obj, StringProp):
            return str

        if isinstance(obj, UnusedProp):
            return str

        if isinstance(obj, BoolProp):
            return bool

        if isinstance(obj, IntegerProp):
            return int

        if isinstance(obj, FloatProp):
            return float

        if isinstance(obj, CharProp):
            return str

        if isinstance(obj, DictProp):
            return dict

        if isinstance(obj, AddrProp):
            return str

        if isinstance(obj, ToGuessProp):
            return str

    def print_header(self):
        print "\n" + "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def add(self, b):
        if isinstance(b, Brok):
            self.broks[b.id] = b
            return
        if isinstance(b, ExternalCommand):
            self.sched.run_external_command(b.cmd_line)

    def test_types(self):
        path = 'etc/shinken_1r_1h_1s.cfg'
        time_hacker.set_my_time()
        self.print_header()
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = logger
        self.log.setLevel("INFO")
        self.log.load_obj(self)
        self.config_files = [path]
        self.conf = Config()
        buf = self.conf.read_config(self.config_files)
        raw_objects = self.conf.read_config_buf(buf)
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')
        self.conf.early_arbiter_linking()
        self.conf.create_objects(raw_objects)
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        # Hack push_flavor, that is set by the dispatcher
        self.conf.push_flavor = 0
        self.conf.load_triggers()
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()

        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.remove_templates()
        self.conf.compute_hash()

        self.conf.override_properties()
        self.conf.linkify()
        self.conf.apply_dependencies()
        self.conf.explode_global_conf()
        self.conf.propagate_timezone_option()
        self.conf.create_business_rules()
        self.conf.create_business_rules_dependencies()
        self.conf.is_correct()

        # Cannot do it for all obj for now. We have to ensure unicode everywhere fist

        for objs in [self.conf.arbiters]:
            for obj in objs:
                #print "=== obj : %s ===" % obj.__class__
                for prop in obj.properties:
                    if hasattr(obj, prop):
                        value = getattr(obj, prop)
                        # We should get ride of None, maybe use the "neutral" value for type
                        if value is not None:
                            #print("TESTING %s with value %s" % (prop, value))
                            self.assertIsInstance(value, self.map_type(obj.properties[prop]))
                        else:
                            print("Skipping %s " % prop)
                #print "==="

        # Manual check of several attr for self.conf.contacts
        # because contacts contains unicode attr
        for contact in self.conf.contacts:
            for prop in ["notificationways", "host_notification_commands", "service_notification_commands"]:
                if hasattr(contact, prop):
                    value = getattr(contact, prop)
                    # We should get ride of None, maybe use the "neutral" value for type
                    if value is not None:
                        print("TESTING %s with value %s" % (prop, value))
                        self.assertIsInstance(value, self.map_type(contact.properties[prop]))
                    else:
                        print("Skipping %s " % prop)

        # Same here
        for notifway in self.conf.notificationways:
            for prop in ["host_notification_commands", "service_notification_commands"]:
                if hasattr(notifway, prop):
                    value = getattr(notifway, prop)
                    # We should get ride of None, maybe use the "neutral" value for type
                    if value is not None:
                        print("TESTING %s with value %s" % (prop, value))
                        self.assertIsInstance(value, self.map_type(notifway.properties[prop]))
                    else:
                        print("Skipping %s " % prop)

if __name__ == '__main__':
    unittest.main()