#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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

from shinken.property import BoolProp, StringProp, ListProp
from shinken.log import logger


class Hostdependency(Item):
    id = 0
    my_type = 'hostdependency'

    # F is dep of D
    # host_name                      Host B
    #       service_description             Service D
    #       dependent_host_name             Host C
    #       dependent_service_description   Service F
    #       execution_failure_criteria      o
    #       notification_failure_criteria   w,u
    #       inherits_parent         1
    #       dependency_period       24x7

    properties = Item.properties.copy()
    properties.update({
        'dependent_host_name':           StringProp(),
        'dependent_hostgroup_name':      StringProp(default=''),
        'host_name':                     StringProp(),
        'hostgroup_name':                StringProp(default=''),
        'inherits_parent':               BoolProp(default='0'),
        'execution_failure_criteria':    ListProp(default='n'),
        'notification_failure_criteria': ListProp(default='n'),
        'dependency_period':             StringProp(default='')
    })

    # Give a nice name output, for debugging purpose
    # (debugging happens more often than expected...)
    def get_name(self):
        dependent_host_name = 'unknown'
        if getattr(self, 'dependent_host_name', None):
            dependent_host_name = getattr(getattr(self, 'dependent_host_name'), 'host_name', 'unknown')
        host_name = 'unknown'
        if getattr(self, 'host_name', None):
            host_name = getattr(getattr(self, 'host_name'), 'host_name', 'unknown')
        return dependent_host_name + '/' + host_name


class Hostdependencies(Items):
    def delete_hostsdep_by_id(self, ids):
        for id in ids:
            del self[id]

    # We create new hostdep if necessary (host groups and co)
    def explode(self, hostgroups):
        # The "old" dependencies will be removed. All dependencies with
        # more than one host or a host group will be in it
        hstdep_to_remove = []

        # Then for every host create a copy of the dependency with just the host
        # because we are adding services, we can't just loop in it
        hostdeps = self.items.keys()
        for id in hostdeps:
            hd = self.items[id]
            if hd.is_tpl():  # Exploding template is useless
                continue

            # We explode first the dependent (son) part
            dephnames = []
            if hasattr(hd, 'dependent_hostgroup_name'):
                dephg_names = hd.dependent_hostgroup_name.split(',')
                dephg_names = [hg_name.strip() for hg_name in dephg_names]
                for dephg_name in dephg_names:
                    dephg = hostgroups.find_by_name(dephg_name)
                    if dephg is None:
                        err = "ERROR: the hostdependency got an unknown dependent_hostgroup_name '%s'" % dephg_name
                        hd.configuration_errors.append(err)
                        continue
                    dephnames.extend(dephg.members.split(','))

            if hasattr(hd, 'dependent_host_name'):
                dephnames.extend(hd.dependent_host_name.split(','))

            # Ok, and now the father part :)
            hnames = []
            if hasattr(hd, 'hostgroup_name'):
                hg_names = hd.hostgroup_name.split(',')
                hg_names = [hg_name.strip() for hg_name in hg_names]
                for hg_name in hg_names:
                    hg = hostgroups.find_by_name(hg_name)
                    if hg is None:
                        err = "ERROR: the hostdependency got an unknown hostgroup_name '%s'" % hg_name
                        hd.configuration_errors.append(err)
                        continue
                    hnames.extend(hg.members.split(','))

            if hasattr(hd, 'host_name'):
                hnames.extend(hd.host_name.split(','))

            # Loop over all sons and fathers to get S*F host deps
            for dephname in dephnames:
                dephname = dephname.strip()
                for hname in hnames:
                    new_hd = hd.copy()
                    new_hd.dependent_host_name = dephname
                    new_hd.host_name = hname
                    self.items[new_hd.id] = new_hd
            hstdep_to_remove.append(id)

        self.delete_hostsdep_by_id(hstdep_to_remove)

    def linkify(self, hosts, timeperiods):
        self.linkify_hd_by_h(hosts)
        self.linkify_hd_by_tp(timeperiods)
        self.linkify_h_by_hd()

    def linkify_hd_by_h(self, hosts):
        for hd in self:
            try:
                h_name = hd.host_name
                dh_name = hd.dependent_host_name
                h = hosts.find_by_name(h_name)
                if h is None:
                    err = "Error: the host dependency got a bad host_name definition '%s'" % h_name
                    hd.configuration_errors.append(err)
                dh = hosts.find_by_name(dh_name)
                if dh is None:
                    err = "Error: the host dependency got a bad dependent_host_name definition '%s'" % dh_name
                    hd.configuration_errors.append(err)
                hd.host_name = h
                hd.dependent_host_name = dh
            except AttributeError, exp:
                err = "Error: the host dependency miss a property '%s'" % exp
                hd.configuration_errors.append(err)

    # We just search for each hostdep the id of the host
    # and replace the name by the id
    def linkify_hd_by_tp(self, timeperiods):
        for hd in self:
            try:
                tp_name = hd.dependency_period
                tp = timeperiods.find_by_name(tp_name)
                hd.dependency_period = tp
            except AttributeError, exp:
                logger.error("[hostdependency] fail to linkify by timeperiod: %s" % exp)

    # We backport host dep to host. So HD is not need anymore
    def linkify_h_by_hd(self):
        for hd in self:
            # Link template is useless
            if hd.is_tpl():
                continue
            # if the host dep conf is bad, pass this one
            if getattr(hd, 'host_name', None) is None or getattr(hd, 'dependent_host_name', None) is None:
                continue
            # Ok, link!
            depdt_hname = hd.dependent_host_name
            dp = getattr(hd, 'dependency_period', None)
            depdt_hname.add_host_act_dependency(hd.host_name, hd.notification_failure_criteria, dp, hd.inherits_parent)
            depdt_hname.add_host_chk_dependency(hd.host_name, hd.execution_failure_criteria, dp, hd.inherits_parent)

    # Apply inheritance for all properties
    def apply_inheritance(self):
        # We check for all Host properties if the host has it
        # if not, it check all host templates for a value
        for prop in Hostdependency.properties:
            self.apply_partial_inheritance(prop)

        # Then implicit inheritance
        # self.apply_implicit_inheritance(hosts)
        for h in self:
            h.get_customs_properties_by_inheritance(self)
