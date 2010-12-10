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
        if hasattr(self, 'members') and self.members != '':
            mbrs = self.members.split(',')
        else:
            mbrs = []
        self.members = []
        for mbr in mbrs:
            self.members.append(mbr.strip())


    def replace_members(self, members):
        self.members = members



    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        cls = self.__class__
        properties = cls.properties

        not_required = [prop for prop in properties \
                            if not properties[prop].required]
        for prop in not_required:
            if not hasattr(self, prop):
                value = properties[prop].default
                setattr(self, prop, value)


    def add_string_member(self, member):
        if hasattr(self, 'members'):
            self.members += ','+member
        else:
            self.members = member


    def __str__(self):
        return str(self.__dict__)+'\n'


    def __iter__(self):
        return self.members.__iter__()


    #a item group is correct if all members actually exists,
    #so if unknown_members is still []
    def is_correct(self):
        if self.unknown_members == []:
            return True
        else:
            for m in self.unknown_members:
                print "Error : the", self.__class__.my_type, self.get_name(), "got a unknown member" , m
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
            if cls.properties[prop].fill_brok != []:
                if self.has(prop):
                    data[prop] = getattr(self, prop)
        #Here members is just a bunch of host, I need name in place
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


    def __len__(self):
        return len(self.itemgroups)


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        for i in self:
            i.fill_default()


    def add(self, ig):
        self.itemgroups[ig.id] = ig


    def pythonize(self):
        for ig in self:
            ig.pythonize()


    def is_correct(self):
        #we are ok at the begining. Hope we still ok at the end...
        r = True
        #First look at no twins (it's bad!)
        for id in self.twins:
            i = self.itemgroups[id]
            print "Error : the", i.__class__.my_type, i.get_name(), "is duplicated"
            r = False
        #Then look for individual ok
        for ig in self:
            r &= ig.is_correct()
        return r


    #We create the reversed list so search will be faster
    #We also create a twins list with id of twins (not the original
    #just the others, higher twins)
    def create_reversed_list(self):
        self.reversed_list = {}
        self.twins = []
        name_property = self.__class__.name_property
        for id in self.itemgroups:
            if hasattr(self.itemgroups[id], name_property):
                name = getattr(self.itemgroups[id], name_property)
                if name not in self.reversed_list:
                    self.reversed_list[name] = id
                else:
                    self.twins.append(id)

