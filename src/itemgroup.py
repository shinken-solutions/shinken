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


#And itemgroup is like a item, but it's a group if items :)

from brok import Brok

class Itemgroup:
    id = 0

    def __init__(self, params={}):
        self.id = self.__class__.id
        self.__class__.id += 1
        for key in params:
            setattr(self, key, params[key])


    def clean(self):
        pass


    #Copy the groups properties EXCEPT the members
    #members need to be fill after manually
    def copy_shell(self):
        cls = self.__class__
        old_id = cls.id
        new_i = cls() # create a new group
        new_i.id = self.id # with the same id
        cls.id = old_id #Reset the Class counter
        
        #Copy all properties
        for prop in cls.properties:
            if prop is not 'members':
                if self.has(prop):
                    val = getattr(self, prop)
                    setattr(new_i, prop, val)
        #but no members
        new_i.members = []
        return new_i
                    

    #Change the members like item1 ,item2 to ['item1' , 'item2']
    #so a python list :)
    #We also strip elements because spaces Stinks!
    def pythonize(self):
        if hasattr(self, 'members'):
            mbrs = self.members.split(',')
        else:
            mbrs = []
        self.members = []
        for mbr in mbrs:
            self.members.append(mbr.strip())


    def replace_members(self, members):
        self.members = members


    def add_string_member(self, member):
        if hasattr(self, 'members'):
            self.members += ','+member
        else:
            self.members = member


    def __str__(self):
        return str(self.__dict__)+'\n'


    def __iter__(self):
        return self.members.__iter__()


    #a host group is correct if all members actually exists
    def is_correct(self):
        if not None in self.members:
            return True
        else:
            return False


    def has(self, prop):
        return hasattr(self, prop)


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
        for i in self.members:
            #it look like lisp! ((( ..))), sorry....
            data['members'].append( (i.id, i.get_name()) )
        b = Brok('initial_'+cls.my_type+'_status', data)
        return b



class Itemgroups:
    def __init__(self, itemgroups):
        self.itemgroups = {}
        for ig in itemgroups:
            self.itemgroups[ig.id] = ig


    def find_id_by_name(self, name):
        for id in self.itemgroups:
            name_property = self.__class__.name_property
            if getattr(self.itemgroups[id], name_property) == name:
                return id
        return None


    def find_by_name(self, name):
        id = self.find_id_by_name(name)
        if id is not None:
            return self.itemgroups[id]
        else:
            return None


    def __str__(self):
        s = ''
        for id in self.itemgroups:
            s += str(self.itemgroups[id])+'\n'
        return s

    def __iter__(self):
        return self.itemgroups.itervalues()



    def add(self, ig):
        self.itemgroups[ig.id] = ig


    def pythonize(self):
        for ig in self:
            ig.pythonize()


    def is_correct(self):
        for ig in self:
            ig.is_correct()
