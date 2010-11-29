#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


from shinken.util import to_split, to_bool
from shinken.item import Item, Items

class Hostdependency(Item):
    id = 0

#F is dep of D
#host_name			Host B
#	service_description		Service D
#	dependent_host_name		Host C
#	dependent_service_description	Service F
#	execution_failure_criteria	o
#	notification_failure_criteria	w,u
#       inherits_parent		1
#       dependency_period       24x7

    properties={'dependent_host_name' : {'required':True},
                'dependent_hostgroup_name' : {'required':False, 'default' : ''},
                'host_name' : {'required':True},
                'hostgroup_name' : {'required':False, 'default' : ''},
                'inherits_parent' : {'required':False, 'default' : '0', 'pythonize' : to_bool},
                'execution_failure_criteria' : {'required':False, 'default' : 'n', 'pythonize' : to_split},
                'notification_failure_criteria' : {'required':False, 'default' : 'n', 'pythonize' : to_split},
                'dependency_period' : {'required':False, 'default' : ''}
                }

    running_properties = {}


    #Give a nice name output, for debbuging purpose
    #(debugging happens more often than expected...)
    def get_name(self):
        return self.dependent_host_name+'/'+self.host_name



class Hostdependencies(Items):
    def delete_hostsdep_by_id(self, ids):
        for id in ids:
            del self.items[id]


    #We create new servicedep if necessery (host groups and co)
    def explode(self):
        #The "old" dependencies will be removed. All dependencies with
        #more than one host or a host group will be in it
        hstdep_to_remove = []

        #Then for every host create a copy of the dependency with just the host
        #because we are adding services, we can't just loop in it
        hostdeps = self.items.keys()
        for id in hostdeps:
            hd = self.items[id]
            if not hd.is_tpl(): #Exploding template is useless
                hnames = hd.dependent_host_name.split(',')
                if len(hnames) >= 1:
                    for hname in hnames:
                        hname = hname.strip()
                        new_hd = hd.copy()
                        new_hd.dependent_host_name = hname
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
                dh = hosts.find_by_name(dh_name)
                hd.host_name = h
                hd.dependent_host_name = dh
            except AttributeError , exp:
                print exp


    #We just search for each hostdep the id of the host
    #and replace the name by the id
    def linkify_hd_by_tp(self, timeperiods):
        for hd in self:
            try:
                tp_name = hd.dependency_period
                tp = timeperiods.find_by_name(tp_name)
                hd.dependency_period = tp
            except AttributeError , exp:
                print exp


    #We backport host dep to host. So HD is not need anymore
    def linkify_h_by_hd(self):
        for hd in self:
            if not hd.is_tpl():
                h = hd.dependent_host_name
                if h is not None:
                    if hasattr(hd, 'dependency_period'):
                        h.add_host_act_dependancy(hd.host_name, hd.notification_failure_criteria, hd.dependency_period, hd.inherits_parent)
                        h.add_host_chk_dependancy(hd.host_name, hd.execution_failure_criteria, hd.dependency_period, hd.inherits_parent)
                    else:
                        h.add_host_act_dependancy(hd.host_name, hd.notification_failure_criteria, None, hd.inherits_parent)
                        h.add_host_chk_dependancy(hd.host_name, hd.execution_failure_criteria, None, hd.inherits_parent)


    #Apply inheritance for all properties
    def apply_inheritance(self):
        #We check for all Host properties if the host has it
        #if not, it check all host templates for a value
        for prop in Hostdependency.properties:
            self.apply_partial_inheritance(prop)

        #Then implicit inheritance
        #self.apply_implicit_inheritance(hosts)
        for h in self:
            h.get_customs_properties_by_inheritance(self)
