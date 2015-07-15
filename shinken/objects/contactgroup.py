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



# Contactgroups are groups for contacts
# They are just used for the config read and explode by elements

from itemgroup import Itemgroup, Itemgroups

from shinken.property import IntegerProp, StringProp
from shinken.log import logger


class Contactgroup(Itemgroup):
    id = 1
    my_type = 'contactgroup'

    properties = Itemgroup.properties.copy()
    properties.update({
        'id':                   IntegerProp(default=0, fill_brok=['full_status']),
        'contactgroup_name':    StringProp(fill_brok=['full_status']),
        'alias':                StringProp(fill_brok=['full_status']),
    })

    macros = {
        'CONTACTGROUPALIAS': 'alias',
        'CONTACTGROUPMEMBERS': 'get_members'
    }

    def get_contacts(self):
        if getattr(self, 'members', None) is not None:
            return [m for m in self.members]
        else:
            return []

    def get_name(self):
        return getattr(self, 'contactgroup_name', 'UNNAMED-CONTACTGROUP')

    def get_contactgroup_members(self):
        if self.has('contactgroup_members'):
            return [m.strip() for m in self.contactgroup_members.split(',')]
        else:
            return []

    # We fillfull properties with template ones if need
    # Because hostgroup we call may not have it's members
    # we call get_hosts_by_explosion on it
    def get_contacts_by_explosion(self, contactgroups):
        # First we tag the hg so it will not be explode
        # if a son of it already call it
        self.already_explode = True

        # Now the recursive part
        # rec_tag is set to False every CG we explode
        # so if True here, it must be a loop in HG
        # calls... not GOOD!
        if self.rec_tag:
            logger.error("[contactgroup::%s] got a loop in contactgroup definition",
                         self.get_name())
            if self.has('members'):
                return self.members
            else:
                return ''
        # Ok, not a loop, we tag it and continue
        self.rec_tag = True

        cg_mbrs = self.get_contactgroup_members()
        for cg_mbr in cg_mbrs:
            cg = contactgroups.find_by_name(cg_mbr.strip())
            if cg is not None:
                value = cg.get_contacts_by_explosion(contactgroups)
                if value is not None:
                    self.add_string_member(value)
        if self.has('members'):
            return self.members
        else:
            return ''


class Contactgroups(Itemgroups):
    name_property = "contactgroup_name"  # is used for finding contactgroup
    inner_class = Contactgroup

    def get_members_by_name(self, cgname):
        cg = self.find_by_name(cgname)
        if cg is None:
            return []
        return cg.get_contacts()

    def add_contactgroup(self, cg):
        self.add_item(cg)

    def linkify(self, contacts):
        self.linkify_cg_by_cont(contacts)

    # We just search for each host the id of the host
    # and replace the name by the id
    def linkify_cg_by_cont(self, contacts):
        for cg in self:
            mbrs = cg.get_contacts()

            # The new member list, in id
            new_mbrs = []
            for mbr in mbrs:
                mbr = mbr.strip()  # protect with strip at the begining so don't care about spaces
                if mbr == '':  # void entry, skip this
                    continue
                m = contacts.find_by_name(mbr)
                # Maybe the contact is missing, if so, must be put in unknown_members
                if m is not None:
                    new_mbrs.append(m)
                else:
                    cg.add_string_unknown_member(mbr)

            # Make members uniq
            new_mbrs = list(set(new_mbrs))

            # We find the id, we replace the names
            cg.replace_members(new_mbrs)

    # Add a contact string to a contact member
    # if the contact group do not exist, create it
    def add_member(self, cname, cgname):
        cg = self.find_by_name(cgname)
        # if the id do not exist, create the cg
        if cg is None:
            cg = Contactgroup({'contactgroup_name': cgname, 'alias': cgname, 'members': cname})
            self.add_contactgroup(cg)
        else:
            cg.add_string_member(cname)

    # Use to fill members with contactgroup_members
    def explode(self):
        # We do not want a same hg to be explode again and again
        # so we tag it
        for tmp_cg in self.items.values():
            tmp_cg.already_explode = False

        for cg in self.items.values():
            if cg.has('contactgroup_members') and not cg.already_explode:
                # get_contacts_by_explosion is a recursive
                # function, so we must tag hg so we do not loop
                for tmp_cg in self.items.values():
                    tmp_cg.rec_tag = False
                cg.get_contacts_by_explosion(self)

        # We clean the tags
        for tmp_cg in self.items.values():
            if hasattr(tmp_cg, 'rec_tag'):
                del tmp_cg.rec_tag
            del tmp_cg.already_explode
