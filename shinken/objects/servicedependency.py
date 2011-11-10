#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


from item import Item, Items
from shinken.property import BoolProp, StringProp, ListProp


class Servicedependency(Item):
    id = 0

#F is dep of D
#host_name                      Host B
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
        'dependent_service_description': StringProp(),
        'host_name':                     StringProp(),
        'hostgroup_name':                StringProp(default=''),
        'service_description':           StringProp(),
        'inherits_parent':               BoolProp  (default='0'),
        'execution_failure_criteria':    ListProp  (default='n'),
        'notification_failure_criteria': ListProp  (default='n'),
        'dependency_period':             StringProp(default='')
    })
    

    #Give a nice name output, for debbuging purpose
    #(Yes, debbuging CAN happen...)
    def get_name(self):
        return self.dependent_host_name+'/'+self.dependent_service_description+'..'+self.host_name+'/'+self.service_description



class Servicedependencies(Items):
    def delete_servicesdep_by_id(self, ids):
        for id in ids:
            del self.items[id]


    #Add a simple service dep from another (dep -> par)
    def add_service_dependency(self, dep_host_name, dep_service_description, par_host_name, par_service_description):
        #We create a "standard" service_dep
        prop = {
            'dependent_host_name':           dep_host_name,
            'dependent_service_description': dep_service_description,
            'host_name':                     par_host_name,
            'service_description':           par_service_description,
            'notification_failure_criteria': 'u,c,w',
            'inherits_parent':               '1',
        }
        sd = Servicedependency(prop)
        self.items[sd.id] = sd


    #We create new servicedep if necessery (host groups and co)
    def explode(self, hostgroups):
        #The "old" services will be removed. All services with
        #more than one host or a host group will be in it
        srvdep_to_remove = []

        #Then for every host create a copy of the service with just the host
        #because we are adding services, we can't just loop in it
        servicedeps = self.items.keys()
        for id in servicedeps:
            sd = self.items[id]
            if sd.is_tpl(): #Exploding template is useless
                continue

            hnames = []
            if hasattr(sd, 'dependent_hostgroup_name'):
                hg_names = sd.dependent_hostgroup_name.split(',')
                hg_names = [hg_name.strip() for hg_name in hg_names]
                for hg_name in hg_names:
                    hg = hostgroups.find_by_name(hg_name)
                    if hg is None:
                        err = "ERROR : the servicedependecy got an unknown dependent_hostgroup_name '%s'" % hg_name
                        hg.configuration_errors.append(err)
                        continue
                    hnames.extend(hg.members.split(','))
            
            if not hasattr(sd, 'dependent_host_name'):
                sd.dependent_host_name = sd.host_name
            
            hnames.extend(sd.dependent_host_name.split(','))
            snames = sd.dependent_service_description.split(',')
            couples = []
            for hname in hnames:
                for sname in snames:
                    couples.append((hname, sname))
            if len(couples) >= 2:
                for (hname, sname) in couples:
                    hname = hname.strip()
                    sname = sname.strip()
                    new_sd = sd.copy()
                    new_sd.dependent_host_name = hname
                    new_sd.dependent_service_description = sname
                    self.items[new_sd.id] = new_sd
                srvdep_to_remove.append(id)
        self.delete_servicesdep_by_id(srvdep_to_remove)


    def linkify(self, hosts, services, timeperiods):
        self.linkify_sd_by_s(hosts, services)
        self.linkify_sd_by_tp(timeperiods)
        self.linkify_s_by_sd()


    #We just search for each srvdep the id of the srv
    #and replace the name by the id
    def linkify_sd_by_s(self, hosts, services):
        for sd in self:
            try:
                s_name = sd.dependent_service_description
                hst_name = sd.dependent_host_name

                #The new member list, in id
                s = services.find_srv_by_name_and_hostname(hst_name, s_name)
                sd.dependent_service_description = s

                s_name = sd.service_description
                hst_name = sd.host_name

                #The new member list, in id
                s = services.find_srv_by_name_and_hostname(hst_name, s_name)
                sd.service_description = s

            except AttributeError , exp:
                print exp


    #We just search for each srvdep the id of the srv
    #and replace the name by the id
    def linkify_sd_by_tp(self, timeperiods):
        for sd in self:
            try:
                tp_name = sd.dependency_period
                tp = timeperiods.find_by_name(tp_name)
                sd.dependency_period = tp
            except AttributeError , exp:
                print exp


    #We backport service dep to service. So SD is not need anymore
    def linkify_s_by_sd(self):
        for sd in self:
            if sd.is_tpl(): continue
            dsc = sd.dependent_service_description
            sdval = sd.service_description
            if dsc is not None and sdval is not None:
                dp = getattr(sd, 'dependency_period', None)
                dsc.add_service_act_dependency(sdval, sd.notification_failure_criteria, dp, sd.inherits_parent)
                dsc.add_service_chk_dependency(sdval, sd.execution_failure_criteria, dp, sd.inherits_parent)


    #Apply inheritance for all properties
    def apply_inheritance(self, hosts):
        #We check for all Host properties if the host has it
        #if not, it check all host templates for a value
        for prop in Servicedependency.properties:
            self.apply_partial_inheritance(prop)

        #Then implicit inheritance
        #self.apply_implicit_inheritance(hosts)
        for s in self:
            s.get_customs_properties_by_inheritance(self)
