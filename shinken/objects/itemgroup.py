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



# And itemgroup is like a item, but it's a group of items :)

from item import Item, Items

from shinken.brok import Brok
from shinken.property import StringProp, ListProp, ToGuessProp
from shinken.log import logger


# TODO: subclass Item & Items for Itemgroup & Itemgroups?
class Itemgroup(Item):

    id = 0

    properties = Item.properties.copy()
    properties.update({
        'members': ListProp(fill_brok=['full_status'], default=None, split_on_coma=True),
        # Shinken specific
        'unknown_members': ListProp(default=None),
    })

    def __init__(self, params={}):
        self.id = self.__class__.id
        self.__class__.id += 1
        cls = self.__class__
        self.init_running_properties()

        for key in params:

            if key in self.properties:
                val = self.properties[key].pythonize(params[key])
            elif key in self.running_properties:
                warning = "using a the running property %s in a config file" % key
                self.configuration_warnings.append(warning)
                val = self.running_properties[key].pythonize(params[key])
            else:
                warning = "Guessing the property %s type because it is not in %s object properties" % \
                          (key, cls.__name__)
                self.configuration_warnings.append(warning)
                val = ToGuessProp.pythonize(params[key])

            setattr(self, key, val)


    # Copy the groups properties EXCEPT the members
    # members need to be fill after manually
    def copy_shell(self):
        cls = self.__class__
        old_id = cls.id
        new_i = cls()  # create a new group
        new_i.id = self.id  # with the same id
        cls.id = old_id  # Reset the Class counter

        # Copy all properties
        for prop in cls.properties:
            if prop is not 'members':
                if self.has(prop):
                    val = getattr(self, prop)
                    setattr(new_i, prop, val)
        # but no members
        new_i.members = []
        return new_i

    def replace_members(self, members):
        self.members = members

    # If a prop is absent and is not required, put the default value
    def fill_default(self):
        cls = self.__class__
        for prop, entry in cls.properties.items():
            if not hasattr(self, prop) and not entry.required:
                value = entry.default
                setattr(self, prop, value)

    def add_string_member(self, member):
        add_fun = list.extend if isinstance(member, list) else list.append
        if not hasattr(self, "members"):
            self.members = []
        add_fun(self.members, member)

    def add_string_unknown_member(self, member):
        add_fun = list.extend if isinstance(member, list) else list.append
        if not self.unknown_members:
            self.unknown_members = []
        add_fun(self.unknown_members, member)

    def __str__(self):
        return str(self.__dict__) + '\n'

    def __iter__(self):
        return self.members.__iter__()

    def __delitem__(self, i):
        try:
            self.members.remove(i)
        except ValueError:
            pass

    # a item group is correct if all members actually exists,
    # so if unknown_members is still []
    def is_correct(self):
        res = True

        if self.unknown_members:
            for m in self.unknown_members:
                logger.error("[itemgroup::%s] as %s, got unknown member %s",
                             self.get_name(), self.__class__.my_type, m)
            res = False

        if self.configuration_errors != []:
            for err in self.configuration_errors:
                logger.error("[itemgroup] %s", err)
            res = False

        return res


    def has(self, prop):
        return hasattr(self, prop)


    # Get a brok with hostgroup info (like id, name)
    # members is special: list of (id, host_name) for database info
    def get_initial_status_brok(self):
        cls = self.__class__
        data = {}
        # Now config properties
        for prop, entry in cls.properties.items():
            if entry.fill_brok != []:
                if self.has(prop):
                    data[prop] = getattr(self, prop)
        # Here members is just a bunch of host, I need name in place
        data['members'] = []
        for i in self.members:
            # it look like lisp! ((( ..))), sorry....
            data['members'].append((i.id, i.get_name()))
        b = Brok('initial_' + cls.my_type + '_status', data)
        return b


class Itemgroups(Items):

    # If a prop is absent and is not required, put the default value
    def fill_default(self):
        for i in self:
            i.fill_default()


    def add(self, ig):
        self.add_item(ig)


    def get_members_by_name(self, gname):
        g = self.find_by_name(gname)
        if g is None:
            return []
        return getattr(g, 'members', [])
