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


#from command import CommandCall
#from util import to_int, to_char, to_split, to_bool
from copy import copy
from brok import Brok

from util import strip_and_uniq
from command import CommandCall
from acknowledge import Acknowledge
from comment import Comment

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
            if len(params[key]) >= 1 and params[key][0]  == '+':
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
            #If we have a class_inherit, and the arbtier really send us it
            if 'class_inherit' in conf.properties[prop] and hasattr(conf, prop):
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
            except AttributeError , exp:
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


    #This function is used by service and hosts
    #to transform Nagios2 parameters to Nagios3
    #ones, like normal_check_interval to
    #check_interval. There is a old_parameters tab
    #in Classes taht give such modifications to do.
    def old_properties_names_to_new(self):
        old_properties = self.__class__.old_properties
        for old_name in old_properties:
            new_name = old_properties[old_name]
            #Ok, if we got old_name and NO new name,
            #we switch the name
            if hasattr(self, old_name) and not hasattr(self, new_name):
                value = getattr(self, old_name)
                setattr(self, new_name, value)


    def add_downtime(self, downtime):
        self.downtimes.append(downtime)


    def del_downtime(self, downtime_id):
        d_to_del = None
        for dt in self.downtimes:
            if dt.id == downtime_id:
                d_to_del = dt
                dt.can_be_deleted = True
        if d_to_del is not None:
            self.downtimes.remove(d_to_del)


    def add_comment(self, comment):
        self.comments.append(comment)


    def del_comment(self, comment_id):
        c_to_del = None
        for c in self.comments:
            if c.id == comment_id:
                c_to_del = c
                c.can_be_deleted = True
        if c_to_del is not None:
            self.comments.remove(c_to_del)


    def acknowledge_problem(self, sticky, notify, persistent, author, comment):
        if self.state != self.ok_up:
            if notify:
                self.create_notifications('ACKNOWLEDGEMENT')
            self.problem_has_been_acknowledged = True
            if sticky == 2:
                sticky = True
            else:
                sticky = False
            a = Acknowledge(self, sticky, notify, persistent, author, comment)
            self.acknowledgement = a
            if self.my_type == 'host':
                comment_type = 1
            else :
                comment_type = 2
            c = Comment(self, persistent, author, comment, comment_type, 4, 0, False, 0)
            self.add_comment(c)
            self.broks.append(self.get_update_status_brok())


    # Delete the acknowledgement object and reset the flag
    # but do not remove the associated comment.
    def unacknowledge_problem(self):
        if self.problem_has_been_acknowledged:
            self.problem_has_been_acknowledged = False
            del self.acknowledgement
            # find comments of non-persistent ack-comments and delete them too
            for c in self.comments:
                if c.entry_type == 4 and not c.persistent:
                    self.del_comment(c.id)
            self.broks.append(self.get_update_status_brok())


    # Check if we have an acknowledgement and if this is marked as sticky.
    # This is needed when a non-ok state changes
    def unacknowledge_problem_if_not_sticky(self):
        if hasattr(self, 'acknowledgement') and self.acknowledgement != None:
            if not self.acknowledgement.sticky:
                self.unacknowledge_problem()


    #Will flatten some parameters taggued by the 'conf_send_preparation'
    #property because they are too "linked" to be send like that (like realms)
    def prepare_for_conf_sending(self):
        cls = self.__class__

        for prop in cls.properties:
            entry = cls.properties[prop]
            #Is this property need preparation for sending?
            if 'conf_send_preparation' in entry:
                f = entry['conf_send_preparation']
                if f != None:
                    val = f(getattr(self, prop))
                    setattr(self, prop, val)

        if hasattr(cls, 'running_properties'):
            for prop in cls.running_properties:
                entry = cls.running_properties[prop]
            #Is this property need preparation for sending?
                if 'conf_send_preparation' in entry:
                    f = entry['conf_send_preparation']
                    if f != None:
                        val = f(getattr(self, prop))
                        setattr(self, prop, val)




    #Get the property for an object, with good value
    #and brok_transformation if need
    def get_property_value_for_brok(self, prop, tab):
        pre_op = None
        entry = tab[prop]
        if 'brok_transformation' in entry:
            pre_op = entry['brok_transformation']

        value = None
        #Get the current value, or the default if need
        if hasattr(self, prop):
            value = getattr(self, prop)
        elif 'default' in entry:
            value = entry['default']

        #Apply brok_transformation if need
        if pre_op != None:
            value = pre_op(value)

        return value


    #Fill data with info of item by looking at brok_type
    #in props of properties or running_propterties
    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        #Now config properties
        for prop in cls.properties:
            #Is this property intended for brokking?
            if 'fill_brok' in cls.properties[prop]:
                if brok_type in cls.properties[prop]['fill_brok']:
                    data[prop] = self.get_property_value_for_brok(prop, cls.properties)
#                    if hasattr(self, prop):
#                        data[prop] = getattr(self, prop)
#                    elif 'default' in cls.properties[prop]:
#                        data[prop] = cls.properties[prop]['default']

        #Maybe the class do not have running_properties
        if hasattr(cls, 'running_properties'):
        #We've got prop in running_properties too
            for prop in cls.running_properties:
                if 'fill_brok' in cls.running_properties[prop]:
                    if brok_type in cls.running_properties[prop]['fill_brok']:
                        data[prop] = self.get_property_value_for_brok(prop, cls.running_properties)
#                        if hasattr(self, prop):
#                            data[prop] = getattr(self, prop)
#                        elif 'default' in cls.properties[prop]:
#                            data[prop] = cls.running_properties[prop]['default']


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


    #Link one command property to a class (for globals like oc*p_command)
    def linkify_one_command_with_commands(self, commands, prop):
        if hasattr(self, prop):
            command = getattr(self, prop).strip()
            if command != '':
                if hasattr(self, 'poller_tag'):
                    cmdCall = CommandCall(commands, command, poller_tag=self.poller_tag)
                else:
                    cmdCall = CommandCall(commands, command)
                    #TODO: catch None?
                    setattr(self, prop, cmdCall)
            else:
                setattr(self, prop, None)



class Items(object):
    def __init__(self, items):
        self.items = {}
        self.configuration_warnings = []
        self.configuration_errors = []
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
        if hasattr(self, 'reversed_list'):
            if name in self.reversed_list:
                return self.reversed_list[name]
            else:
                return None
        else: #ok, an early ask, with no reversed list from now...
            name_property = self.__class__.name_property
            for i in self:
                if hasattr(i, name_property):
                    i_name = getattr(i, name_property)
                    if i_name == name:
                        return i.id
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
        for id in self.templates:
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
                t = self.find_tpl_by_name(tpl.strip())
                if t is not None:
                    new_tpls.append(t)
                else: # not find? not good!
                    err = "ERROR: the template '%s' defined for '%s' is unkown" % (tpl, i.get_name())
                    i.configuration_errors.append(err)
            i.templates = new_tpls



    def is_correct(self):
        #we are ok at the begining. Hope we still ok at the end...
        r = True
        #Some class do not have twins, because they do not have names
        #like servicedependancies
        if hasattr(self, 'twins'):
            #Ok, look at no twins (it's bad!)
            for id in self.twins:
                i = self.items[id]
                print "Error: the", i.__class__.my_type, i.get_name(), "is duplicated"
                r = False
        #Then look if we have some errors in the conf
        #Juts print warnings, but raise errors
        for err in self.configuration_warnings:
            print err            
        for err in self.configuration_errors:
            print err
            r = False

        #Then look for individual ok
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
        #do not remove twins, we should look in it, but just void it
        self.twins = []
        #del self.twins #no more need



    #We've got a contacts property with , separated contacts names
    #and we want have a list of Contacts
    def linkify_with_contacts(self, contacts):
        for i in self:
            if hasattr(i, 'contacts'):
                contacts_tab = i.contacts.split(',')
                contacts_tab = strip_and_uniq(contacts_tab)
                new_contacts = []
                for c_name in contacts_tab:
                    if c_name != '':
                        c = contacts.find_by_name(c_name)
                        if c != None:
                            new_contacts.append(c)
                        else: #Add in the errors tab. will be raised at is_correct
                            err = "ERROR: the contact '%s' defined for '%s' is unkown" % (c_name, i.get_name())
                            i.configuration_errors.append(err)
                #Get the list, but first make elements uniq
                i.contacts = list(set(new_contacts))


    #Make link between service and it's escalations
    def linkify_with_escalations(self, escalations):
        for i in self:
            if hasattr(i, 'escalations'):
                #print i.get_name(), 'going to link escalations', i.escalations
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
                #print i.get_name(), 'finallygot escalation', i.escalations


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
                    cg = contactgroups.find_by_name(cgname)
                    if cg == None:
                        err = "The contact group '%s'defined on the %s '%s' do not exist" % (cgname, i.__class__.my_type, i.get_name())
                        i.configuration_errors.append(err)
                        continue
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
                    if hasattr(i, 'poller_tag'):
                        cmdCall = CommandCall(commands, command, poller_tag=i.poller_tag)
                    else:
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
                        if hasattr(i, 'poller_tag'):
                            cmdCall = CommandCall(commands, com, poller_tag=i.poller_tag)
                        else:
                            cmdCall = CommandCall(commands, com)
                        #TODO: catch None?
                        com_list.append(cmdCall)
                    else: # TODO: catch?
                        pass
                setattr(i, prop, com_list)


    #Return a set with ALL hosts (used in ! expressions)
    def get_all_host_names_set(self, hosts):
        hnames = [h.host_name for h in hosts.items.values() if hasattr(h, 'host_name')]
        return set(hnames)


    def evaluate_hostgroup_expression(self, expr, hosts, hostgroups):
        res = []
        original_expr = expr
        #print "I'm trying to prepare the expression", expr

        #We've got problem with the "-" sign. It can be in a
        #valid name but it's a sign of difference for sets
        #so we change the - now by something, then we reverse after
        if '-' in expr:
            expr = expr.replace('-', 'MINUSSIGN')

        #! (not) should be changed as "ALL-" (all but not...)
        if '!' in expr:
            ALLELEMENTS = self.get_all_host_names_set(hosts)
            #print "Changing ! by ALLELEMENTS- in ", expr
            expr = expr.replace('!', 'ALLELEMENTS-')

        #print "Now finding all token to change in variable"
        #print "So I remove all non want caracters"

        #We change all separaton token by 10 spaces (so names can still have some spaces
        #on them like Europe Servers because we wil cut byy this 10spaces after
        strip_expr = expr
        for c in ['|', '&', '(', ')', ',', '-']:
            strip_expr = strip_expr.replace(c, ' '*10)
        #print "Stripped expression:", strip_expr

        tokens = strip_expr.split(' '*10)
        #Strip and non void token
        tokens = [token.strip() for  token in tokens if token != '']
        #print "Tokens:", tokens

        #Now add in locals() dict (yes, real variables!)
        for token in tokens:
            #ALLELEMENTS is a private group for us
            if token != 'ALLELEMENTS':
                #Maybe the token was with - at the begining,
                #but we change all by "MINUSSIGN". We must change it back now
                #for the search
                if 'MINUSSIGN' in token:
                    tmp_token = token.replace('MINUSSIGN', '-')
                    members = hostgroups.get_members_by_name(tmp_token)
                else:
                    members = hostgroups.get_members_by_name(token)

                if members != []:
                    #print "Get members", members
                    elts = members.split(',')
                    elts = strip_and_uniq(elts)
                    elts = set(elts)
                    #print "Elements:", elts
                    #print "Now set in locals the token new values"
                    locals()[token.upper()] = elts
                #TODO : raise error
                else:
                    if 'MINUSSIGN' in token:
                        token = token.replace('MINUSSIGN', '-')
                    print self.__dict__, type(self)
                    err = "ERROR: the group %s is unknown !" % (token,)
                    print err
                    self.configuration_errors.append(err)
                    return res

            #print "Now changing the exprtoken value with UPPER one (so less risk of problem..."
            expr = expr.replace(token, token.upper())

        #print "Final expression:", expr
        try:
            evaluation = eval(expr)
        except SyntaxError:
            print "The syntax of %s is invalid" % original_expr
            return res
        except NameError:
            print "There is a unknow name in %s" % original_expr
            return res
        #print "Evaluation :", evaluation

        #In evaluation we can have multiples values because of , (so it make a tuple in fact)
        #we must OR them in the result
        if ',' in expr:
            for part in evaluation:
                #print "PART", part
                res.extend(list(part))
        else:#no , so we do not have a tuple but a simple uniq set
            res.extend(list(evaluation))
        res_string = ','.join(res)
        #print "Final resolution is", res_string
        return res_string


    #If we've got a hostgroup_name property, we search for all
    #theses groups and ask them their hosts, and then add them
    #all into our host_name property
    def explode_host_groups_into_hosts(self, hosts, hostgroups):
        for i in self:
            if hasattr(i, 'hostgroup_name'):
                hnames = self.evaluate_hostgroup_expression(i.hostgroup_name, hosts, hostgroups)
                if hnames != []:
                    if hasattr(i, 'host_name'):
                        i.host_name += ',' + str(hnames)
                    else:
                        i.host_name = str(hnames)


