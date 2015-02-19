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


from shinken.property import StringProp, IntegerProp
from shinken.log import logger

from .itemgroup import Itemgroup, Itemgroups
from .service import Service


class Servicegroup(Itemgroup):
    id = 1  # zero is always a little bit special... like in database
    my_type = 'servicegroup'

    properties = Itemgroup.properties.copy()
    properties.update({
        'id':                IntegerProp(default=0, fill_brok=['full_status']),
        'servicegroup_name': StringProp(fill_brok=['full_status']),
        'alias':             StringProp(fill_brok=['full_status']),
        'notes':             StringProp(default='', fill_brok=['full_status']),
        'notes_url':         StringProp(default='', fill_brok=['full_status']),
        'action_url':        StringProp(default='', fill_brok=['full_status']),
    })

    macros = {
        'SERVICEGROUPALIAS':     'alias',
        'SERVICEGROUPMEMBERS':   'members',
        'SERVICEGROUPNOTES':     'notes',
        'SERVICEGROUPNOTESURL':  'notes_url',
        'SERVICEGROUPACTIONURL': 'action_url'
    }

    def get_services(self):
        if getattr(self, 'members', None) is not None:
            return self.members
        else:
            return []

    def get_name(self):
        return self.servicegroup_name

    def get_servicegroup_members(self):
        if self.has('servicegroup_members'):
            return [m.strip() for m in self.servicegroup_members.split(',')]
        else:
            return []

    # We fillfull properties with template ones if need
    # Because hostgroup we call may not have it's members
    # we call get_hosts_by_explosion on it
    def get_services_by_explosion(self, servicegroups):
        # First we tag the hg so it will not be explode
        # if a son of it already call it
        self.already_explode = True

        # Now the recursive part
        # rec_tag is set to False every HG we explode
        # so if True here, it must be a loop in HG
        # calls... not GOOD!
        if self.rec_tag:
            logger.error("[servicegroup::%s] got a loop in servicegroup definition",
                         self.get_name())
            if self.has('members'):
                return self.members
            else:
                return ''
        # Ok, not a loop, we tag it and continue
        self.rec_tag = True

        sg_mbrs = self.get_servicegroup_members()
        for sg_mbr in sg_mbrs:
            sg = servicegroups.find_by_name(sg_mbr.strip())
            if sg is not None:
                value = sg.get_services_by_explosion(servicegroups)
                if value is not None:
                    self.add_string_member(value)

        if self.has('members'):
            return self.members
        else:
            return ''


class Servicegroups(Itemgroups):
    name_property = "servicegroup_name"  # is used for finding servicegroup
    inner_class = Servicegroup

    def linkify(self, hosts, services):
        self.linkify_sg_by_srv(hosts, services)

    # We just search for each host the id of the host
    # and replace the name by the id
    # TODO: very slow for hight services, so search with host list,
    # not service one
    def linkify_sg_by_srv(self, hosts, services):
        for sg in self:
            mbrs = sg.get_services()
            # The new member list, in id
            new_mbrs = []
            seek = 0
            host_name = ''
            if len(mbrs) == 1 and mbrs[0] != '':
                sg.add_string_unknown_member('%s' % mbrs[0])

            for mbr in mbrs:
                if seek % 2 == 0:
                    host_name = mbr.strip()
                else:
                    service_desc = mbr.strip()
                    find = services.find_srv_by_name_and_hostname(host_name, service_desc)
                    if find is not None:
                        new_mbrs.append(find)
                    else:
                        host = hosts.find_by_name(host_name)
                        if not (host and host.is_excluded_for_sdesc(service_desc)):
                            sg.add_string_unknown_member('%s,%s' % (host_name, service_desc))
                        elif host:
                            self.configuration_warnings.append(
                                'servicegroup %r : %s is excluded from the services of the host %s'
                                % (sg, service_desc, host_name)
                            )
                seek += 1

            # Make members uniq
            new_mbrs = list(set(new_mbrs))

            # We find the id, we replace the names
            sg.replace_members(new_mbrs)
            for s in sg.members:
                s.servicegroups.append(sg)
                # and make this uniq
                s.servicegroups = list(set(s.servicegroups))

    # Add a service string to a service member
    # if the service group do not exist, create it
    def add_member(self, cname, sgname):
        sg = self.find_by_name(sgname)
        # if the id do not exist, create the cg
        if sg is None:
            sg = Servicegroup({'servicegroup_name': sgname, 'alias': sgname, 'members': cname})
            self.add(sg)
        else:
            sg.add_string_member(cname)

    # Use to fill members with contactgroup_members
    def explode(self):
        # We do not want a same hg to be explode again and again
        # so we tag it
        for sg in self:
            sg.already_explode = False

        for sg in self:
            if sg.has('servicegroup_members') and not sg.already_explode:
                # get_services_by_explosion is a recursive
                # function, so we must tag hg so we do not loop
                for sg2 in self:
                    sg2.rec_tag = False
                sg.get_services_by_explosion(self)

        # We clean the tags
        for sg in self:
            try:
                del sg.rec_tag
            except AttributeError:
                pass
            del sg.already_explode
