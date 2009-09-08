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

class Hostgroup(Itemgroup):
    id = 1 #0 is always a little bit special... like in database

    properties={'id': {'required': False, 'default': 0, 'status_broker_name' : None},
                'hostgroup_name': {'required': True, 'status_broker_name' : None},
                'alias': {'required':  True, 'status_broker_name' : None},
                'notes': {'required': False, 'default':'', 'status_broker_name' : None},
                'notes_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'action_url': {'required': False, 'default':'', 'status_broker_name' : None},
                'members' : {'required': True}#No status_broker_name because it put hosts, not host_name
                }

    macros = {
        'HOSTGROUPALIAS' : 'alias',
        'HOSTGROUPMEMBERS' : 'members',
        'HOSTGROUPNOTES' : 'notes',
        'HOSTGROUPNOTESURL' : 'notes_url',
        'HOSTGROUPACTIONURL' : 'action_url'
        }

    def get_hosts(self):
        print "Searching hosts", self.members
        return self.members


    def get_hostgroup_members(self):
        if self.has('hostgroup_members'):
            return self.hostgroup_members.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    def get_hosts_by_explosion(self, hostgroups):
        hg_mbrs = self.get_hostgroup_members()
        for hg_mbr in hg_mbrs:
            hg = hostgroups.find_by_name(hg_mbr)
            if hg is not None:
                value = hg.get_hosts_by_explosion(hostgroups)
                if value is not None:
                    self.add_string_member(value)
            else:
                pass
        if self.has('members'):
            return self.members
        else:
            return ''


    #Get a brok with hostgroup info (like id, name)
    #members is special : list of (id, host_name) for database info
    def get_initial_status_brok(self):
        cls = self.__class__
        data = {}
        #Now config properties
        for prop in cls.properties:
            if 'status_broker_name' in cls.properties[prop]:
                broker_name = cls.properties[prop]['status_broker_name']
                if self.has(prop):
                    if broker_name is None:
                        data[prop] = getattr(self, prop)
                    else:
                        data[broker_name] = getattr(self, prop)
        #Here members is jsut a bunch of host, I need name in place
        data['members'] = []
        for h in self.members:
            data['members'].append( (h.id, h.get_name()) )#it look like lisp! ((( ..))) 
        b = Brok('initial_hostgroup_status', data)
        return b



class Hostgroups(Itemgroups):
    name_property = "hostgroup_name" # is used for finding hostgroups
    

    def get_members_by_name(self, hgname):
        id = self.find_id_by_name(hgname)
        if id == None:
            return []
        return self.itemgroups[id].get_hosts()


    def linkify(self, hosts=None):
        self.linkify_hg_by_hst(hosts)

    
    #We just search for each hostgroup the id of the hosts 
    #and replace the name by the id
    def linkify_hg_by_hst(self, hosts):
        for hg in self.itemgroups.values():
            mbrs = hg.get_hosts()
            #The new member list, in id
            new_mbrs = []
            for mbr in mbrs:
                new_mbrs.append(hosts.find_by_name(mbr))
            #We find the id, we remplace the names
            hg.replace_members(new_mbrs)


    #Add a host string to a hostgroup member
    #if the host group do not exist, create it
    def add_member(self, hname, hgname):
        id = self.find_id_by_name(hgname)
        #if the id do not exist, create the hg
        if id == None:
            hg = Hostgroup({'hostgroup_name' : hgname, 'alias' : hgname, 'members' :  hname})
            self.add(hg)
        else:
            self.itemgroups[id].add_string_member(hname)


    #Use to fill members with hostgroup_members
    def explode(self):
        for hg in self.itemgroups.values():
            if hg.has('hostgroup_members'):
                hg.get_hosts_by_explosion(self)

