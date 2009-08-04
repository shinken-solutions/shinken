#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


from util import to_int, to_char, to_split, to_bool
from item import Item, Items

class Servicedependency(Item):
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
                'dependent_service_description' : {'required':True},
                'host_name' : {'required':True},
                'hostgroup_name' : {'required':False, 'default' : ''},
                'service_description' : {'required':True},
                'inherits_parent' : {'required':False, 'default' : '0', 'pythonize' : to_bool},
                'execution_failure_criteria' : {'required':False, 'default' : 'n', 'pythonize' : to_split},
                'notification_failure_criteria' : {'required':False, 'default' : 'n', 'pythonize' : to_split},
                'dependency_period' : {'required':False, 'default' : ''}
                }
    
    running_properties = {}

#    #return a copy of a service, but give him a new id
#    def copy(self):
#        sd = deepcopy(self)
#        sd.id = Servicedependency.id
#        Servicedependency.id = Servicedependency.id + 1
#        return sd



class Servicedependencies(Items):
    def delete_servicesdep_by_id(self, ids):
        for id in ids:
            del self.items[id]


    #We create new servicedep if necessery (host groups and co)
    def explode(self):
        print "Exploding Service dep"
        #The "old" services will be removed. All services with 
        #more than one host or a host group will be in it
        srvdep_to_remove = []
        
        #Then for every host create a copy of the service with just the host
        servicedeps = self.items.keys() #because we are adding services, we can't just loop in it
        for id in servicedeps:
            sd = self.items[id]
            hnames = sd.dependent_host_name.split(',')
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
        for sd in self:#.items:
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
                
            except AttributeError as exp:
                print exp


    #We just search for each srvdep the id of the srv
    #and replace the name by the id
    def linkify_sd_by_tp(self, timeperiods):
        for sd in self:#.items:
            try:
                tp_name = sd.dependency_period
                tp = timeperiods.find_by_name(tp_name)
                sd.dependency_period = tp
            except AttributeError as exp:
                print exp


    #We backport service dep to service. So SD is not need anymore
    def linkify_s_by_sd(self):
        print self
        for sd in self:#.items:
            s = sd.dependent_service_description
            if s is not None:
                if sd.has('dependency_period'):
                    s.add_service_act_dependancy(sd.service_description, sd.notification_failure_criteria, sd.dependency_period)
                    s.add_service_chk_dependancy(sd.service_description, sd.execution_failure_criteria, sd.dependency_period)
                else:
                    s.add_service_act_dependancy(sd.service_description, sd.notification_failure_criteria, None)
                    s.add_service_chk_dependancy(sd.service_description, sd.execution_failure_criteria, None)
