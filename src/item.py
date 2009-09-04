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


from command import CommandCall
from util import to_int, to_char, to_split, to_bool
from copy import deepcopy


class Item(object):
    def __init__(self, params={}):
        self.id = self.__class__.id
        self.__class__.id += 1
        
        self.customs = {} # for custom variables
        self.plus = {} # for value with a +

        #adding running properties like latency
        for prop in self.__class__.running_properties:
            setattr(self, prop, deepcopy(self.__class__.running_properties[prop]['default']))#deep copy because we need
            #eatch istance to have his own running prop!

        #[0] = +  -> new key-plus
        #[0] = _  -> new custom entry
        for key in params:
            if params[key][0] == '+':
                self.plus[key] = params[key][1:] # we remove the +
            elif key[0] == "_":
                self.customs[key] = params[key]
            else:
                setattr(self, key, params[key])

    #return a copy of the item, but give him a new id
    def copy(self):
        i = deepcopy(self)
        cls = i.__class__
        i.id = cls.id
        cls.id += 1
        return i


    def clean(self):
        pass
    
    def __str__(self):
        return str(self.__dict__)+'\n'



    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented


    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result


    def is_tpl(self):
        try:
            return self.register == '0'
        except:
            return False


    def has(self, prop):
        return hasattr(self, prop)


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        properties = self.__class__.properties
        for prop in properties:
            if not self.has(prop) and not properties[prop]['required']:
                value = properties[prop]['default']
                setattr(self, prop, value)


    #We load every usefull parameter so no need to access global conf later
    #Must be called after a change in a gloabl conf parameter
    def load_global_conf(cls, conf):
        print "Load global conf=========================="
        #conf have properties, if 'enable_notifications' : { [...] 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]}
        #get the name and put the value if None, put the Name (not None) if not (not clear ?)
        for prop in conf.properties:
            if 'class_inherit' in conf.properties[prop]:
                for (cls_dest, change_name) in conf.properties[prop]['class_inherit']:
                    if cls_dest == cls:#ok, we've got something to get
                        value = getattr(conf, prop)
                        if change_name is None:
                            setattr(cls, prop, value)
                        else:
                            setattr(cls, change_name, value)
        #print "OK, finally, we've got...", str(cls.__dict__)
    #Make this method a classmethod
    load_global_conf = classmethod(load_global_conf)


    #Use to make pyton properties
    def pythonize(self):
        cls = self.__class__
        for prop in cls.properties:
            try:
                tab = cls.properties[prop]
                if 'pythonize' in tab:
                    f = tab['pythonize']
                    old_val = getattr(self, prop)
                    new_val = f(old_val)
                    #print "Changing ", old_val, "by", new_val
                    setattr(self, prop, new_val)
            except AttributeError as exp:
                print exp


    def get_templates(self):
        if self.has('use'):
            return self.use.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    def get_property_by_inheritance(self, items, prop):
        if self.has(prop):
            value = getattr(self, prop)
            if self.has_plus(prop):#Manage the additive inheritance for the property, if property is in plus, add or replace it
                value = value+','+self.get_plus_and_delete(prop)
            return value
        tpls = self.get_templates()
        for tpl in tpls:
            i = items.find_tpl_by_name(tpl)
            if i is not None:
                value = i.get_property_by_inheritance(items, prop)
                if value is not None:
                    if self.has_plus(prop):
                        value = value+','+self.get_plus_and_delete(prop)
                    setattr(self, prop, value)
                    return value
        if self.has_plus(prop):
            value = self.get_plus_and_delete(prop)
            setattr(self, prop, value)
            return value
        return None

    
    #We fillfull properties with template ones if need
    def get_customs_properties_by_inheritance(self, items):
        cv = {} # custom variables dict
        tpls = self.get_templates()
        for tpl in tpls:
            i = items.find_tpl_by_name(tpl)
            if i is not None:
                tpl_cv = i.get_customs_properties_by_inheritance(items)
                if tpl_cv is not {}:
                    for prop in tpl_cv:
                        if prop not in self.customs:
                            value = tpl_cv[prop]
                        else:
                            value = self.customs[prop]
                        if self.has_plus(prop):
                            value = value+self.get_plus_and_delete(prop)
                        self.customs[prop]=value
        for prop in self.customs:
            value = self.customs[prop]
            if self.has_plus(prop):
                value = value = value+','+self.get_plus_and_delete(prop)
                self.customs[prop] = value
        #We can get custom properties in plus, we need to get all entires and put
        #them into customs
        cust_in_plus = self.get_all_plus_and_delete()
        for prop in cust_in_plus:
            self.customs[prop] = cust_in_plus[prop]
        return self.customs

    
    def has_plus(self, prop):
        try:
            self.plus[prop]
        except:
            return False
        return True


    def get_all_plus_and_delete(self):
        res = {}
        props = self.plus.keys() #we delete entries, so no for ... in ...
        for prop in props:
            res[prop] = self.get_plus_and_delete(prop)
        return res


    def get_plus_and_delete(self, prop):
        val = self.plus[prop]
        del self.plus[prop]
        return val


    #Check is required prop are set:
    #template are always correct
    def is_correct(self):
        if self.is_tpl:
            return True
        properties = self.__class__.properties
        for prop in properties:
            if not self.has(prop) and properties[prop]['required']:
                return False
        return True



    def add_downtime(self, downtime):
        self.downtimes.append(downtime)


    def del_downtime(self, downtime_id):
        d_to_del = None
        for dt in self.downtimes:
            if dt.id == downtime_id:
                d_to_del = dt
        if d_to_del is not None:
            self.downtimes.remove(d_to_del)
            

class Items(object):
    def __init__(self, items):
        self.items = {}
        for i in items:
            self.items[i.id] = i
            
            
    def __iter__(self):
        return self.items.itervalues()


    def __len__(self):
        return len(self.items)


    def __delitem__(self, key):
        del self.items[key]


    def __setitem__(self, key, value):
        self.items[key] = value


    def __getitem__(self, key):
        return self.items[key]
    
    
    def find_id_by_name(self, name):
        for id in self.items:
            name_property = self.__class__.name_property
            if self.items[id].has(name_property) and getattr(self.items[id], name_property) == name:
                return id
        return None


    def find_by_name(self, name):
        id = self.find_id_by_name(name)
        if id is not None:
            return self.items[id]
        else:
            return None

    def pythonize(self):
        for id in self.items:
            self.items[id].pythonize()


    def find_tpl_by_name(self, name):
        for id in self.items:
            i = self.items[id]
            if i.is_tpl() and i.name == name:
                return i
        return None


    def is_correct(self):
        for id in self.items:
            i = self.items[id]
            i.is_correct()


    #We remove useless properties
    def clean_useless(self):
        #First templates
        tpls = [id for id in self.items if self.items[id].is_tpl()]
        for id in tpls:
            del self.items[id]


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        for id in self.items:
            i = self.items[id]
            i.fill_default()

    
    def __str__(self):
        s = ''
        for id in self.items:
            cls = self.items[id].__class__
            s = s + str(cls) + ':' + str(id) + str(self.items[id]) + '\n'
        return s


    #Inheritance forjust a property
    def apply_partial_inheritance(self, prop):
        for id in self.items:
            i = self.items[id]
            i.get_property_by_inheritance(self, prop)


    def apply_inheritance(self):
        #We check for all Host properties if the host has it
        #if not, it check all host templates for a value
        cls = self.inner_class#items[0].__class__
        properties = cls.properties
        for prop in properties:
            self.apply_partial_inheritance(prop)
        for id in self.items:
            i = self.items[id]
            i.get_customs_properties_by_inheritance(self)

