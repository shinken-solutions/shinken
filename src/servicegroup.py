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


from itemgroup import Itemgroup, Itemgroups
from brok import Brok

class Servicegroup(Itemgroup):
    id = 1 #0 is always a little bit special... like in database
    my_type = 'servicegroup'

    properties={'id': {'required': False, 'default': 0, 'status_broker_name' : None},
                'servicegroup_name': {'required': True, 'status_broker_name' : None},
                'alias': {'required':  True, 'status_broker_name' : None},
                'notes': {'required': False, 'default':'', 'status_broker_name' : None},
                'notes_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'action_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'members' : {'required': True}#No status_broker_name because it put hosts, not host_name
                }


    macros = {
        'SERVICEGROUPALIAS' : 'alias',
        'SERVICEGROUPMEMBERS' : 'members',
        'SERVICEGROUPNOTES' : 'notes',
        'SERVICEGROUPNOTESURL' : 'notes_url',
        'SERVICEGROUPACTIONURL' : 'action_url'
        }
    
    
    def get_services(self):
        return self.members


    def get_name(self):
        return self.servicegroup_name


    def get_servicegroup_members(self):
        if self.has('servicegroup_members'):
            return self.servicegroup_members.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    def get_services_by_explosion(self, servicegroups):
        sg_mbrs = self.get_servicegroup_members()
        for sg_mbr in sg_mbrs:
            sg = servicegroups.find_by_name(sg_mbr)
            if sg is not None:
                value = sg.get_services_by_explosion(servicegroups)
                if value is not None:
                    self.add_string_member(value)
        if self.has('members'):
            return self.members
        else:
            return ''



class Servicegroups(Itemgroups):
    name_property = "servicegroup_name" # is used for finding servicegroup
    inner_class = Servicegroup
    
    def linkify(self, services):
        self.linkify_sg_by_srv(services)
        
        
    #We just search for each host the id of the host
    #and replace the name by the id
    #TODO: very slow for hight services, so search with host list,
    #not service one
    def linkify_sg_by_srv(self, services):
        for id in self.itemgroups:
            mbrs = self.itemgroups[id].get_services().split(',')

            #The new member list, in id
            new_mbrs = []
            seek = 0
            host_name = ''
            for mbr in mbrs:
                if seek % 2 == 0:
                    host_name = mbr
                else:
                    service_desc = mbr
                    find = services.find_srv_by_name_and_hostname(host_name, service_desc)
                    new_mbrs.append(find)
                seek += 1
            #We find the id, we remplace the names
            self.itemgroups[id].replace_members(new_mbrs)


    #Add a service string to a service member
    #if the service group do not exist, create it
    def add_member(self, cname, cgname):
        id = self.find_id_by_name(cgname)
        #if the id do not exist, create the cg
        if id == None:
            cg = Servicegroup({'servicegroup_name' : cgname, 'alias' : cgname, 'members' :  cname})
            self.add(cg)
        else:
            self.itemgroups[id].add_string_member(cname)


    #Use to fill members with contactgroup_members
    def explode(self):
        for id in self.itemgroups:
            sg = self.itemgroups[id]
            if sg.has('servicegroup_members'):
                sg.get_services_by_explosion(self)
