#!/usr/bin/python

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

import time
import os
import re
try:
    import json
except ImportError:
    json = None

from shinken.objects.item import Item, Items
from shinken.property import StringProp
from shinken.log import logger


class Pack(Item):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'pack'

    properties = Item.properties.copy()
    properties.update({'pack_name': StringProp(fill_brok=['full_status'])})

    running_properties = Item.running_properties.copy()
    running_properties.update({'macros': StringProp(default={})})

    # For debugging purpose only (nice name)
    def get_name(self):
        try:
            return self.pack_name
        except AttributeError:
            return 'UnnamedPack'


class Packs(Items):
    name_property = "pack_name"
    inner_class = Pack

    # We will dig into the path and load all .pack files
    def load_file(self, path):
        # Now walk for it
        for root, dirs, files in os.walk(path):
            for file in files:
                if re.search("\.pack$", file):
                    p = os.path.join(root, file)
                    try:
                        fd = open(p, 'rU')
                        buf = fd.read()
                        fd.close()
                    except IOError, exp:
                        logger.error("Cannot open pack file '%s' for reading: %s", p, exp)
                        # ok, skip this one
                        continue
                    self.create_pack(buf, file[:-5])

    # Create a pack from the string buf, and get a real object from it
    def create_pack(self, buf, name):
        if not json:
            logger.warning("[Pack] cannot load the pack file '%s': missing json lib", name)
            return
        # Ok, go compile the code
        try:
            d = json.loads(buf)
            if 'name' not in d:
                logger.error("[Pack] no name in the pack '%s'", name)
                return
            p = Pack({})
            p.pack_name = d['name']
            p.description = d.get('description', '')
            p.macros = d.get('macros', {})
            p.templates = d.get('templates', [p.pack_name])
            p.path = d.get('path', 'various/')
            p.doc_link = d.get('doc_link', '')
            p.services = d.get('services', {})
            p.commands = d.get('commands', [])
            if not p.path.endswith('/'):
                p.path += '/'
            # Ok, add it
            self[p.id] = p
        except ValueError, exp:
            logger.error("[Pack] error in loading pack file '%s': '%s'", name, exp)
