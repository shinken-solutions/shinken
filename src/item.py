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

from util import strip_and_uniq
from command import CommandCall

class Item(object):
    def __init__(self, params={}):
        #We have our own id of My Class type :)
        #use set attr for going into the slots
        #instead of __dict__ :)
        setattr(self, 'id', self.__class__.id)
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
        #[0] = _  -> new custom entry in UPPER case
        for key in params:
            if params[key][0] == '+':
                #Special case : a _MACRO can be a plus. so add to plus
                #but upper the key for the macro name
                if key[0] == "_":
                    self.plus[key.upper()] = params[key][1:] # we remove the +
                else:
                    self.plus[key] = params[key][1:] # we remove the +
            elif key[0] == "_":
                custom_name = key.upper()
                self.customs[custom_name] = params[key]
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

        for prop in properties:
            if not hasattr(self, prop) and 'default' in properties[prop]:
                value = properties[prop]['default']
                setattr(self, prop, value)


    #We load every usefull parameter so no need to access global conf later
    #Must be called after a change in a gloabl conf parameter
    def load_global_conf(cls, conf):
        #print "Load global conf=========================="
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
            #Is this property intended for brokking?
            if 'fill_brok' in cls.properties[prop]:
                if brok_type in cls.properties[prop]['fill_brok']:
                    if hasattr(self, prop):
                        data[prop] = getattr(self, prop)
                    elif 'default' in cls.properties[prop]:
                        data[prop] = cls.properties[prop]['default']
        #We've got prop in running_properties too
        for prop in cls.running_properties:
            if 'fill_brok' in cls.running_properties[prop]:
                if brok_type in cls.running_properties[prop]['fill_brok']:
                    if hasattr(self, prop):
                        data[prop] = getattr(self, prop)
                    elif 'default' in cls.properties[prop]:
                        data[prop] = cls.running_properties[prop]['default']


    #Get a brok with initial status
    def get_initial_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        data = {'id' : self.id}
        
        self.fill_data_brok_from(data, 'full_status')
        b = Brok('initial_'+my_type+'_status', data)
        return b


    #Get a brok with update item status
    def get_update_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        
        data = {'id' : self.id}
        self.fill_data_brok_from(data, 'full_status')
        b = Brok('update_'+my_type+'_status', data)
        return b


    #Get a brok with check_result
    def get_check_result_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        
        data = {}
        self.fill_data_brok_from(data, 'check_result')
        b = Brok(my_type+'_check_result', data)
        return b

    
    #Get brok about the new schedule (next_check)
    def get_next_schedule_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {}
        self.fill_data_brok_from(data, 'next_schedule')
        b = Brok(my_type+'_next_schedule', data)
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
        r = True
        for i in self:
            r &= i.is_correct()
        return r


    #We remove useless properties and templates
    def clean_useless(self):
        #First templates
        tpls = [id for id in self.items if self.items[id].is_tpl()]
        for id in tpls:
            del self.items[id]
        #Ok now delete useless in items
        #TODO : move into item class
        for i in self:
            try:
                del i.templates
                del i.use
                del i.plus
            except AttributeError:
                pass
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



    #We've got a contacts property with , separated contacts names
    #and we want have a list of Contacts
    def linkify_with_contacts(self, contacts):
        for i in self:
            if hasattr(i, 'contacts'):
                contacts_tab = i.contacts.split(',')
                contacts_tab = strip_and_uniq(contacts_tab)
                new_contacts = []
                for c_name in contacts_tab:
                    c = contacts.find_by_name(c_name)
                    if c != None:
                        new_contacts.append(c)
                    else: #TODO: What?
                        pass
                #Get the list, but first make elements uniq
                i.contacts = list(set(new_contacts))


    #Make link between service and it's escalations
    def linkify_with_escalations(self, escalations):
        for i in self:
            if hasattr(i, 'escalations'):
                print i.get_name(), 'going to link escalations', i.escalations
                escalations_tab = i.escalations.split(',')
                escalations_tab = strip_and_uniq(escalations_tab)
                new_escalations = []
                for es_name in escalations_tab:
                    es = escalations.find_by_name(es_name)
                    if es != None:
                        new_escalations.append(es)
                    else: #TODO what?
                        pass
                i.escalations = new_escalations
                print i.get_name(), 'finallygot escalation', i.escalations


    #Make link between item and it's resultmodulations
    def linkify_with_resultmodulations(self, resultmodulations):
        for i in self:
            if hasattr(i, 'resultmodulations'):
                resultmodulations_tab = i.resultmodulations.split(',')
                resultmodulations_tab = strip_and_uniq(resultmodulations_tab)
                new_resultmodulations = []
                for rm_name in resultmodulations_tab:
                    rm = resultmodulations.find_by_name(rm_name)
                    if rm != None:
                        new_resultmodulations.append(rm)
                    else: #TODO WHAT?
                        pass
                i.resultmodulations = new_resultmodulations


    #If we've got a contact_groups properties, we search for all
    #theses groups and ask them their contacts, and then add them
    #all into our contacts property
    def explode_contact_groups_into_contacts(self, contactgroups):
        for i in self:
            if hasattr(i, 'contact_groups'):
                cgnames = i.contact_groups.split(',')
                cgnames = strip_and_uniq(cgnames)
                for cgname in cgnames:
                    cnames = contactgroups.get_members_by_name(cgname)
                    #We add contacts into our contacts
                    if cnames != []:
                        if hasattr(i, 'contacts'):
                            i.contacts += ','+cnames
                        else:
                            i.contacts = cnames

    #Link a timeperiod property (prop)
    def linkify_with_timeperiods(self, timeperiods, prop):
        for i in self:
            if hasattr(i, prop):
                tpname = getattr(i, prop)
                tp = timeperiods.find_by_name(tpname)
                #TODO: catch None?
                setattr(i, prop, tp)


    #Link one command property
    def linkify_one_command_with_commands(self, commands, prop):
        for i in self:
            if hasattr(i, prop):
                command = getattr(i, prop).strip()
                if command != '':
                    cmdCall = CommandCall(commands, command)
                    #TODO: catch None?
                    setattr(i, prop, cmdCall)
                else:
                    setattr(i, prop, None)


    #Link a command list (commands with , between) in real CommandCalls
    def linkify_command_list_with_commands(self, commands, prop):
        for i in self:
            if hasattr(i, prop):
                coms = getattr(i, prop).split(',')
                coms = strip_and_uniq(coms)
                com_list = []
                for com in coms:
                    if com != '':
                        cmdCall = CommandCall(commands, com)
                        #TODO: catch None?
                        com_list.append(cmdCall)
                    else: # TODO: catch?
                        pass
                setattr(i, prop, com_list)


    #If we've got a hostgroup_name property, we search for all
    #theses groups and ask them their hosts, and then add them
    #all into our host_name property
    def explode_host_groups_into_hosts(self, hostgroups):
        for i in self:
            if hasattr(i, 'hostgroup_name'):
                hgnames = i.hostgroup_name.split(',')
                hgnames = strip_and_uniq(hgnames)
                for hgname in hgnames:
                    hnames = hostgroups.get_members_by_name(hgname)
                    #We add hosts into our host_name
                    if hnames != []:
                        if hasattr(i, 'host_name'):
                            i.host_name += ',' + str(hnames)
                        else:
                            i.host_name = str(hnames)

