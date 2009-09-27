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


#from command import CommandCall
#from util import to_int, to_char, to_split, to_bool
from copy import copy
from brok import Brok


class Item(object):
    def __init__(self, params={}):
        #We have our own id of My Class type :)
        self.id = self.__class__.id
        self.__class__.id += 1

        
        self.customs = {} # for custom variables
        self.plus = {} # for value with a +

        cls = self.__class__
        #adding running properties like latency, dependency list, etc
        for prop in cls.running_properties:
            #Copy is slow, so we check type
            #Type with __iter__ are list or dict, or tuple.
            #Item need it's own list, so qe copy
            val = cls.running_properties[prop]['default']
            if hasattr(val, '__iter__'): 
                setattr(self, prop, copy(val))
            else:
                setattr(self, prop, val)
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
        cls = self.__class__
        i = cls({})#Dummy item but with it's own running properties
        properties = cls.properties
        for prop in properties:
            if hasattr(self, prop):
                val = getattr(self, prop)
                setattr(i, prop, val)
        return i


    def clean(self):
        pass

    
    def __str__(self):
        return str(self.__dict__)+'\n'


    def is_tpl(self):
        try:
            return self.register == '0'
        except:
            return False


    #has = hasattr
    #def has(self, prop):
    #    return hasattr(self, prop)


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        cls = self.__class__
        properties = cls.properties
        not_required = [prop for prop in properties \
                            if not properties[prop]['required']]
        for prop in not_required:
            if not hasattr(self, prop):
                value = properties[prop]['default']
                setattr(self, prop, value)


    #We load every usefull parameter so no need to access global conf later
    #Must be called after a change in a gloabl conf parameter
    def load_global_conf(cls, conf):
        print "Load global conf=========================="
        #conf have properties, if 'enable_notifications' : 
        #{ [...] 'class_inherit' : [(Host, None), (Service, None),
        # (Contact, None)]}
        #get the name and put the value if None, put the Name 
        #(not None) if not (not clear ?)
        for prop in conf.properties:
            if 'class_inherit' in conf.properties[prop]:
                for (cls_dest, change_name) in conf.properties[prop]['class_inherit']:
                    if cls_dest == cls:#ok, we've got something to get
                        value = getattr(conf, prop)
                        if change_name is None:
                            setattr(cls, prop, value)
                        else:
                            setattr(cls, change_name, value)

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
                #print self.get_name(), ' : ', exp
                pass # Will be catch at the is_correct moment


    def get_templates(self):
        if hasattr(self, 'use'):
            return self.use.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    def get_property_by_inheritance(self, items, prop):
        #If I have the prop, I take mine but I check if I must
        #add a plus porperty
        if hasattr(self, prop):
            value = getattr(self, prop)
            #Manage the additive inheritance for the property,
            #if property is in plus, add or replace it
            if self.has_plus(prop):
                value = value+','+self.get_plus_and_delete(prop)
            return value
        #Ok, I do not have prop, Maybe my templates do?
        #Same story for plus
        for i in self.templates:
            value = i.get_property_by_inheritance(items, prop)
            if value is not None:
                if self.has_plus(prop):
                    value = value+','+self.get_plus_and_delete(prop)
                setattr(self, prop, value)
                return value
        #I do not have prop, my templates too... Maybe a plus?
        if self.has_plus(prop):
            value = self.get_plus_and_delete(prop)
            setattr(self, prop, value)
            return value
        #Not event a plus... so None :)
        return None

    
    #We fillfull properties with template ones if need
    def get_customs_properties_by_inheritance(self, items):
        for i in self.templates:
            tpl_cv = i.get_customs_properties_by_inheritance(items)
            if tpl_cv is not {}:
                for prop in tpl_cv:
                    if prop not in self.customs:
                        value = tpl_cv[prop]
                    else:
                        value = self.customs[prop]
                    if self.has_plus(prop):
                        value = value+self.get_plus_and_delete(prop)
                    self.customs[prop] = value
        for prop in self.customs:
            value = self.customs[prop]
            if self.has_plus(prop):
                value = value = value+','+self.get_plus_and_delete(prop)
                self.customs[prop] = value
        #We can get custom properties in plus, we need to get all 
        #entires and put
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
        #if self.is_tpl:
        #    return True
        state = True
        properties = self.__class__.properties
        for prop in properties:
            if not hasattr(self, prop) and properties[prop]['required']:
                print self.get_name(), "missing property :", prop
                state = False
        return state



    def add_downtime(self, downtime):
        self.downtimes.append(downtime)


    def del_downtime(self, downtime_id):
        d_to_del = None
        for dt in self.downtimes:
            if dt.id == downtime_id:
                d_to_del = dt
        if d_to_del is not None:
            self.downtimes.remove(d_to_del)


    #Fill data with info of item by looking at brok_type
    #in props of properties or running_propterties
    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        #Now config properties
        for prop in cls.properties:
            if brok_type in cls.properties[prop]:
                broker_name = cls.properties[prop][brok_type]
                if broker_name is None:
                    data[prop] = getattr(self, prop)
                else:
                    data[broker_name] = getattr(self, prop)
        #We've got prop in running_properties too
        for prop in cls.running_properties:
            if brok_type in cls.running_properties[prop]:
                broker_name = cls.running_properties[prop][brok_type]
                if broker_name is None:
                    data[prop] = getattr(self, prop)
                else:
                    data[broker_name] = getattr(self, prop)


    #Get a brok with initial status
    def get_initial_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        data = {'id' : self.id}
        
        self.fill_data_brok_from(data, 'status_broker_name')
        b = Brok('initial_'+my_type+'_status', data)
        return b


    #Get a brok with update item status
    def get_update_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        
        data = {'id' : self.id}
        self.fill_data_brok_from(data, 'status_broker_name')
        b = Brok('update_'+my_type+'_status', data)
        return b


    #Get a brok with check_result
    def get_check_result_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {}
        self.fill_data_brok_from(data, 'broker_name')
        b = Brok(my_type+'_check_result', data)
        return b

            

class Items(object):
    def __init__(self, items):
        self.items = {}
        for i in items:
            self.items[i.id] = i
        self.templates = {}
        
    
            
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
    

    #We create the reversed list so search will be faster
    #We also create a twins list with id of twins (not the original
    #just the others, higher twins)
    def create_reversed_list(self):
        self.reversed_list = {}
        self.twins = []
        name_property = self.__class__.name_property
        for id in self.items:
            if hasattr(self.items[id], name_property):
                name = getattr(self.items[id], name_property)
                if name not in self.reversed_list:
                    self.reversed_list[name] = id
                else:
                    self.twins.append(id)

    
    def find_id_by_name(self, name):
        if name in self.reversed_list:
            return self.reversed_list[name]
        else:
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


    def create_tpl_list(self):
        for id in self.items:
            i = self.items[id]
            if i.is_tpl():
                self.templates[id] = i


    def find_tpl_by_name(self, name):
        for id in self.templates:#items:
            i = self.items[id]
            if i.name == name:
                return i
        return None


    def linkify_templates(self):
        #First we create a list of all templates
        self.create_tpl_list() 
        for i in self:
            tpls = i.get_templates()
            new_tpls = []
            for tpl in tpls:
                t = self.find_tpl_by_name(tpl)
                if t is not None:
                    new_tpls.append(t)
            i.templates = new_tpls
            


    def is_correct(self):
        for i in self:#.items:
            #i = self.items[id]
            i.is_correct()
            #if not i.is_correct():
            #    print "An item is not correct:", i.get_name()


    #We remove useless properties and templates
    def clean_useless(self):
        #First templates
        tpls = [id for id in self.items if self.items[id].is_tpl()]
        for id in tpls:
            del self.items[id]
        del self.templates


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        for i in self:
            i.fill_default()

    
    def __str__(self):
        s = ''
        cls = self.__class__
        for id in self.items:
            s = s + str(cls) + ':' + str(id) + str(self.items[id]) + '\n'
        return s


    #Inheritance forjust a property
    def apply_partial_inheritance(self, prop):
        for i in self:
            i.get_property_by_inheritance(self, prop)


    def apply_inheritance(self):
        #We check for all Class properties if the host has it
        #if not, it check all host templates for a value
        cls = self.inner_class
        properties = cls.properties
        for prop in properties:
            self.apply_partial_inheritance(prop)
        for i in self:
            i.get_customs_properties_by_inheritance(self)


    #We remove twins
    #Remember: item id respect the order of conf. So if and item
    # is defined multiple times,
    #we want to keep the first one.
    #Services are also managed here but they are specials:
    #We remove twins services with the same host_name/service_description
    #Remember: host service are take into account first before hostgroup service
    #Id of host service are lower than hostgroups one, so they are 
    #in self.twins_services
    #and we can remove them.
    def remove_twins(self):
        for id in self.twins:
            i = self.items[id]
            type = i.__class__.my_type
            print 'Warning: the', type, i.get_name(), 'is already defined.'
            del self.items[id] #bye bye
        del self.twins #no more need
