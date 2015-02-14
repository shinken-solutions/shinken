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

from item import Item, Items

from shinken.property import StringProp, ListProp
from shinken.util import strip_and_uniq
from shinken.log import logger


class Module(Item):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'module'

    properties = Item.properties.copy()
    properties.update({
        'module_name': StringProp(),
        'module_type': StringProp(),
        'modules': ListProp(default=[''], split_on_coma=True),
    })

    macros = {}

    # For debugging purpose only (nice name)
    def get_name(self):
        return self.module_name

    def __repr__(self):
        return '<module type=%s name=%s />' % (self.module_type, self.module_name)


class Modules(Items):
    name_property = "module_name"
    inner_class = Module

    def linkify(self):
        self.linkify_s_by_plug()

    def linkify_s_by_plug(self):
        for s in self:
            new_modules = []
            mods = strip_and_uniq(s.modules)
            for plug_name in mods:
                plug_name = plug_name.strip()

                # don't read void names
                if plug_name == '':
                    continue

                # We are the modules, we search them :)
                plug = self.find_by_name(plug_name)
                if plug is not None:
                    new_modules.append(plug)
                else:
                    err = "[module] unknown %s module from %s" % (plug_name, s.get_name())
                    logger.error(err)
                    s.configuration_errors.append(err)
            s.modules = new_modules


    # We look for contacts property in contacts and
    def explode(self):
        pass
