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


""" This class is a base class for nearly all configuration
 elements like service, hosts or contacts.
"""

from copy import copy

from shinken.commandcall import CommandCall
from shinken.property import StringProp, ListProp
from shinken.brok import Brok
from shinken.util import strip_and_uniq
from shinken.acknowledge import Acknowledge
from shinken.comment import Comment
from shinken.log import logger



class Item(object):
    
    properties = {
        'imported_from':            StringProp(default='unknown')
    }
    
    running_properties = {
        # All errors and warning raised during the configuration parsing
        # and that will raised real warning/errors during the is_correct
        'configuration_warnings':   ListProp(default=[]),
        'configuration_errors':     ListProp(default=[]),              
    }
    
    macros = {
    }
    
    def __init__(self, params={}):
        # We have our own id of My Class type :)
        # use set attr for going into the slots
        # instead of __dict__ :)
        cls = self.__class__
        self.id = cls.id
        cls.id += 1

        self.customs = {} # for custom variables
        self.plus = {} # for value with a +

        self.init_running_properties()
        
        # [0] = +  -> new key-plus
        # [0] = _  -> new custom entry in UPPER case
        for key in params:
            if len(params[key]) >= 1 and params[key][0]  == '+':
                # Special case : a _MACRO can be a plus. so add to plus
                # but upper the key for the macro name
                if key[0] == "_":
                    self.plus[key.upper()] = params[key][1:] # we remove the +
                else:
                    self.plus[key] = params[key][1:] # we remove the +
            elif key[0] == "_":
                custom_name = key.upper()
                self.customs[custom_name] = params[key]
            else:
                setattr(self, key, params[key])

    
    def init_running_properties(self):
        for prop, entry in self.__class__.running_properties.items():
            # Copy is slow, so we check type
            # Type with __iter__ are list or dict, or tuple.
            # Item need it's own list, so qe copy
            val = entry.default
            if hasattr(val, '__iter__'):
                setattr(self, prop, copy(val))
            else:
                setattr(self, prop, val)
            # each instance to have his own running prop!


    def copy(self):
        """ Return a copy of the item, but give him a new id """
        cls = self.__class__
        i = cls({})# Dummy item but with it's own running properties
        for prop in cls.properties:
            if hasattr(self, prop):
                val = getattr(self, prop)
                setattr(i, prop, val)
        # Also copy the customs tab
        i.customs = copy(self.customs)
        return i


    def clean(self):
        """ Clean useless things not requested once item has been fully initialized&configured.
Like temporary attributes such as "imported_from", etc.. """
        for name in ( 'imported_from', 'use', 'plus', 'templates', ): 
            try:
                delattr(self, name)
            except AttributeError:
                pass


    def __str__(self):
        return str(self.__dict__)+'\n'


    def is_tpl(self):
        """ Return if the elements is a template """
        try:
            return self.register == '0'
        except:
            return False


    # If a prop is absent and is not required, put the default value
    def fill_default(self):
        """ Fill missing properties if they are missing """
        cls = self.__class__

        for prop, entry in cls.properties.items():
            if not hasattr(self, prop) and entry.has_default:
                setattr(self, prop, entry.default)


    # We load every usefull parameter so no need to access global conf later
    # Must be called after a change in a gloabl conf parameter
    def load_global_conf(cls, conf):
        """ Used to put global values in the sub Class like
        hosts ro services """
        # conf have properties, if 'enable_notifications' :
        # { [...] 'class_inherit' : [(Host, None), (Service, None),
        #  (Contact, None)]}
        # get the name and put the value if None, put the Name
        # (not None) if not (not clear ?)
        for prop, entry in conf.properties.items():
            # If we have a class_inherit, and the arbtier really send us it
            # if 'class_inherit' in entry and hasattr(conf, prop):
            if hasattr(conf, prop):
                for (cls_dest, change_name) in entry.class_inherit:
                    if cls_dest == cls:# ok, we've got something to get
                        value = getattr(conf, prop)
                        if change_name is None:
                            setattr(cls, prop, value)
                        else:
                            setattr(cls, change_name, value)

    # Make this method a classmethod
    load_global_conf = classmethod(load_global_conf)


    # Use to make python properties
    def pythonize(self):
        cls = self.__class__
        for prop, tab in cls.properties.items():
            try:
#                if isinstance(tab, dict):
#                    if 'pythonize' in tab:
#                        f = tab['pythonize']
#                        old_val = getattr(self, prop)
#                        new_val = f(old_val)
#                        #print "Changing ", old_val, "by", new_val
#                        setattr(self, prop, new_val)
#                else: #new style for service
                new_val = tab.pythonize(getattr(self, prop))
                setattr(self, prop, new_val)
            except AttributeError , exp:
                # print self.get_name(), ' : ', exp
                pass # Will be catch at the is_correct moment


    def get_templates(self):
        if hasattr(self, 'use') and self.use != '':
            return self.use.split(',')
        else:
            return []


    # We fillfull properties with template ones if need
    def get_property_by_inheritance(self, items, prop):
        # If I have the prop, I take mine but I check if I must
        # add a plus porperty
        if hasattr(self, prop):
            value = getattr(self, prop)
            # Maybe this value is 'null'. If so, we should NOT inherit
            # and just delete this entry, and hope of course.
            if value == 'null':
                delattr(self, prop)
                return None
            # Manage the additive inheritance for the property,
            # if property is in plus, add or replace it
            if self.has_plus(prop):
                value += ',' + self.get_plus_and_delete(prop)
            return value
        #Ok, I do not have prop, Maybe my templates do?
        # Same story for plus
        for i in self.templates:
            value = i.get_property_by_inheritance(items, prop)
            if value is not None:
                if self.has_plus(prop):
                    value += ','+self.get_plus_and_delete(prop)
                setattr(self, prop, value)
                return value
        # I do not have prop, my templates too... Maybe a plus?
        if self.has_plus(prop):
            value = self.get_plus_and_delete(prop)
            setattr(self, prop, value)
            return value
        # Not event a plus... so None :)
        return None


    # We fillfull properties with template ones if need
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
        # We can get custom properties in plus, we need to get all
        # entires and put
        # them into customs
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
        props = self.plus.keys() # we delete entries, so no for ... in ...
        for prop in props:
            res[prop] = self.get_plus_and_delete(prop)
        return res


    def get_plus_and_delete(self, prop):
        val = self.plus[prop]
        del self.plus[prop]
        return val


    # Check is required prop are set:
    # template are always correct
    def is_correct(self):
        state = True
        properties = self.__class__.properties
        
        # Raised all previously saw errors like unknown contacts and co
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                logger.log(err)

        for prop, entry in properties.items():
            if not hasattr(self, prop) and entry.required:
                print self.get_name(), "missing property :", prop
                state = False
                
        return state


    # This function is used by service and hosts
    # to transform Nagios2 parameters to Nagios3
    # ones, like normal_check_interval to
    # check_interval. There is a old_parameters tab
    # in Classes taht give such modifications to do.
    def old_properties_names_to_new(self):
        old_properties = self.__class__.old_properties
        for old_name, new_name in old_properties.items():
            # Ok, if we got old_name and NO new name,
            # we switch the name
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
            c = Comment(self, persistent, author, comment,
                        comment_type, 4, 0, False, 0)
            self.add_comment(c)
            self.broks.append(self.get_update_status_brok())


    #  Delete the acknowledgement object and reset the flag
    #  but do not remove the associated comment.
    def unacknowledge_problem(self):
        if self.problem_has_been_acknowledged:
            print "Deleting acknowledged of", self.get_dbg_name()
            self.problem_has_been_acknowledged = False
            # Should not be deleted, a None is Good
            self.acknowledgement = None
            # del self.acknowledgement
            # find comments of non-persistent ack-comments and delete them too
            for c in self.comments:
                if c.entry_type == 4 and not c.persistent:
                    self.del_comment(c.id)
            self.broks.append(self.get_update_status_brok())


    # Check if we have an acknowledgement and if this is marked as sticky.
    # This is needed when a non-ok state changes
    def unacknowledge_problem_if_not_sticky(self):
        if hasattr(self, 'acknowledgement') and self.acknowledgement is not None:
            if not self.acknowledgement.sticky:
                self.unacknowledge_problem()


    # Will flatten some parameters taggued by the 'conf_send_preparation'
    #property because they are too "linked" to be send like that (like realms)
    def prepare_for_conf_sending(self):
        cls = self.__class__

        for prop, entry in cls.properties.items():
            # Is this property need preparation for sending?
            if entry.conf_send_preparation is not None:
                f = entry.conf_send_preparation
                if f is not None:
                    val = f(getattr(self, prop))
                    setattr(self, prop, val)

        if hasattr(cls, 'running_properties'):
            for prop, entry in cls.running_properties.items():
            # Is this property need preparation for sending?
                if entry.conf_send_preparation is not None:
                    f = entry.conf_send_preparation
                    if f is not None:
                        val = f(getattr(self, prop))
                        setattr(self, prop, val)




    # Get the property for an object, with good value
    # and brok_transformation if need
    def get_property_value_for_brok(self, prop, tab):
        entry = tab[prop]
        # Get the current value, or the default if need
        value = getattr(self, prop, entry.default)

        # Apply brok_transformation if need
        # Look if we must preprocess the value first
        pre_op = entry.brok_transformation
        if pre_op is not None:
            value = pre_op(self, value)

        return value


    # Fill data with info of item by looking at brok_type
    # in props of properties or running_propterties
    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        # Now config properties
        for prop, entry in cls.properties.items():
            # Is this property intended for brokking?
#            if 'fill_brok' in cls.properties[prop]:
            if brok_type in entry.fill_brok:
                data[prop] = self.get_property_value_for_brok(prop, cls.properties)

        # Maybe the class do not have running_properties
        if hasattr(cls, 'running_properties'):
            # We've got prop in running_properties too
            for prop, entry in cls.running_properties.items():
#                if 'fill_brok' in cls.running_properties[prop]:
                if brok_type in entry.fill_brok:
                    data[prop] = self.get_property_value_for_brok(prop, cls.running_properties)


    # Get a brok with initial status
    def get_initial_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        data = {'id' : self.id}

        self.fill_data_brok_from(data, 'full_status')
        b = Brok('initial_'+my_type+'_status', data)
        return b


    # Get a brok with update item status
    def get_update_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {'id' : self.id}
        self.fill_data_brok_from(data, 'full_status')
        b = Brok('update_'+my_type+'_status', data)
        return b


    # Get a brok with check_result
    def get_check_result_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {}
        self.fill_data_brok_from(data, 'check_result')
        b = Brok(my_type+'_check_result', data)
        return b


    # Get brok about the new schedule (next_check)
    def get_next_schedule_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {}
        self.fill_data_brok_from(data, 'next_schedule')
        b = Brok(my_type+'_next_schedule', data)
        return b


    # Link one command property to a class (for globals like oc*p_command)
    def linkify_one_command_with_commands(self, commands, prop):
        if hasattr(self, prop):
            command = getattr(self, prop).strip()
            if command != '':
                if hasattr(self, 'poller_tag'):
                    cmdCall = CommandCall(commands, command,
                                          poller_tag=self.poller_tag)
                elif hasattr(self, 'reactionner_tag'):
                    cmdCall = CommandCall(commands, command,
                                          reactionner_tag=self.reactionner_tag)
                else:
                    cmdCall = CommandCall(commands, command)
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


    # We create the reversed list so search will be faster
    # We also create a twins list with id of twins (not the original
    # just the others, higher twins)
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
        else: # ok, an early ask, with no reversed list from now...
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
            if hasattr(i, 'name') and i.name == name:
                return i
        return None


    def linkify_templates(self):
        # First we create a list of all templates
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
        # we are ok at the begining. Hope we still ok at the end...
        r = True
        # Some class do not have twins, because they do not have names
        # like servicedependancies
        twins = getattr(self, 'twins', None)
        if twins is not None:
            # Ok, look at no twins (it's bad!)
            for id in twins:
                i = self.items[id]
                print "Error: the", i.__class__.my_type, i.get_name(), "is duplicated from", i.imported_from
                r = False
        # Then look if we have some errors in the conf
        # Juts print warnings, but raise errors
        for err in self.configuration_warnings:
            print err
        for err in self.configuration_errors:
            print err
            r = False

        # Then look for individual ok
        for i in self:
            if not i.is_correct():
                n = getattr(i, 'imported_from', "unknown")
                print "Error: In ", i.get_name(), "is incorrect ; from", n
                r = False        
        
        return r


    def remove_templates(self):
        """ Remove useless templates (& properties) of our items ; otherwise we could get errors on config.is_correct() """
        tpls = [ i for i in self if i.is_tpl() ]
        for i in tpls:
            del self.items[i.id]
        del self.templates


    def clean(self):
        """ Request to remove the unecessary attributes/others from our items """
        for i in self:
            i.clean()
        Item.clean(self)

    # If a prop is absent and is not required, put the default value
    def fill_default(self):
        for i in self:
            i.fill_default()


    def __str__(self):
        s = ''
        cls = self.__class__
        for id in self.items:
            s = s + str(cls) + ':' + str(id) + str(self.items[id]) + '\n'
        return s


    # Inheritance forjust a property
    def apply_partial_inheritance(self, prop):
        for i in self:
            i.get_property_by_inheritance(self, prop)


    def apply_inheritance(self):
        # We check for all Class properties if the host has it
        # if not, it check all host templates for a value
        cls = self.inner_class
        for prop in cls.properties:
            self.apply_partial_inheritance(prop)
        for i in self:
            i.get_customs_properties_by_inheritance(self)


    # We remove twins
    # Remember: item id respect the order of conf. So if and item
    #  is defined multiple times,
    # we want to keep the first one.
    # Services are also managed here but they are specials:
    # We remove twins services with the same host_name/service_description
    # Remember: host service are take into account first before hostgroup service
    # Id of host service are lower than hostgroups one, so they are
    # in self.twins_services
    # and we can remove them.
    def remove_twins(self):
        for id in self.twins:
            i = self.items[id]
            type = i.__class__.my_type
            print 'Warning: the', type, i.get_name(), 'is already defined.'
            del self.items[id] # bye bye
        # do not remove twins, we should look in it, but just void it
        self.twins = []
        #del self.twins #no more need



    # We've got a contacts property with , separated contacts names
    # and we want have a list of Contacts
    def linkify_with_contacts(self, contacts):
        for i in self:
            if hasattr(i, 'contacts'):
                contacts_tab = i.contacts.split(',')
                contacts_tab = strip_and_uniq(contacts_tab)
                new_contacts = []
                for c_name in contacts_tab:
                    if c_name != '':
                        c = contacts.find_by_name(c_name)
                        if c is not None:
                            new_contacts.append(c)
                        # Else : Add in the errors tab.
                        # will be raised at is_correct
                        else:
                            err = "ERROR: the contact '%s' defined for '%s' is unkown" % (c_name, i.get_name())
                            i.configuration_errors.append(err)
                # Get the list, but first make elements uniq
                i.contacts = list(set(new_contacts))


    # Make link between an object and its escalations
    def linkify_with_escalations(self, escalations):
        for i in self:
            if hasattr(i, 'escalations'):
                escalations_tab = i.escalations.split(',')
                escalations_tab = strip_and_uniq(escalations_tab)
                new_escalations = []
                for es_name in [e for e in escalations_tab if e != '']:
                    es = escalations.find_by_name(es_name)
                    if es is not None:
                        new_escalations.append(es)
                    else: # Escalation not find, not good!
                        err = "ERROR : the escalation '%s' defined for '%s' is unknown" % (es_name, i.get_name())
                        i.configuration_errors.append(err)
                i.escalations = new_escalations


    # Make link between item and it's resultmodulations
    def linkify_with_resultmodulations(self, resultmodulations):
        for i in self:
            if hasattr(i, 'resultmodulations'):
                resultmodulations_tab = i.resultmodulations.split(',')
                resultmodulations_tab = strip_and_uniq(resultmodulations_tab)
                new_resultmodulations = []
                for rm_name in resultmodulations_tab:
                    rm = resultmodulations.find_by_name(rm_name)
                    if rm is not None:
                        new_resultmodulations.append(rm)
                    else: # TODO WHAT?
                        pass
                i.resultmodulations = new_resultmodulations


    # If we've got a contact_groups properties, we search for all
    # theses groups and ask them their contacts, and then add them
    # all into our contacts property
    def explode_contact_groups_into_contacts(self, contactgroups):
        for i in self:
            if hasattr(i, 'contact_groups'):
                cgnames = i.contact_groups.split(',')
                cgnames = strip_and_uniq(cgnames)
                for cgname in cgnames:
                    cg = contactgroups.find_by_name(cgname)
                    if cg is None:
                        err = "The contact group '%s'defined on the %s '%s' do not exist" % (cgname, i.__class__.my_type, i.get_name())
                        i.configuration_errors.append(err)
                        continue
                    cnames = contactgroups.get_members_by_name(cgname)
                    # We add contacts into our contacts
                    if cnames != []:
                        if hasattr(i, 'contacts'):
                            i.contacts += ','+cnames
                        else:
                            i.contacts = cnames

    # Link a timeperiod property (prop)
    def linkify_with_timeperiods(self, timeperiods, prop):
        for i in self:
            if hasattr(i, prop):
                tpname = getattr(i, prop).strip()
                # some default values are '', so set None
                if tpname == '':
                    setattr(i, prop, None)
                    continue

                # Ok, get a real name, search for it
                tp = timeperiods.find_by_name(tpname)
                # If nto fidn, it's an error
                if tp is None:
                    err = "The %s of the %s '%s' named '%s' is unknown!" % (prop, i.__class__.my_type, i.get_name(), tpname)
                    i.configuration_errors.append(err)
                    continue
                # Got a real one, just set it :)
                setattr(i, prop, tp)


    # Link one command property
    def linkify_one_command_with_commands(self, commands, prop):
        for i in self:
            if hasattr(i, prop):
                command = getattr(i, prop).strip()
                if command != '':
                    if hasattr(i, 'poller_tag'):
                        cmdCall = CommandCall(commands, command,
                                              poller_tag=i.poller_tag)
                    elif hasattr(i, 'reactionner_tag'):
                        cmdCall = CommandCall(commands, command,
                                              reactionner_tag=i.reactionner_tag)
                    else:
                        cmdCall = CommandCall(commands, command)
                    # TODO: catch None?
                    setattr(i, prop, cmdCall)
                else:
                    
                    setattr(i, prop, None)


    # Link a command list (commands with , between) in real CommandCalls
    def linkify_command_list_with_commands(self, commands, prop):
        for i in self:
            if hasattr(i, prop):
                coms = getattr(i, prop).split(',')
                coms = strip_and_uniq(coms)
                com_list = []
                for com in coms:
                    if com != '':
                        if hasattr(i, 'poller_tag'):
                            cmdCall = CommandCall(commands, com,
                                                  poller_tag=i.poller_tag)
                        elif hasattr(i, 'reactionner_tag'):
                            cmdCall = CommandCall(commands, com,
                                                  reactionner_tag=i.reactionner_tag)
                        else:
                            cmdCall = CommandCall(commands, com)
                        # TODO: catch None?
                        com_list.append(cmdCall)
                    else: # TODO: catch?
                        pass
                setattr(i, prop, com_list)
    
    hgn_chars_separator = ( '|', ',', '&', '^', )
    specials_hostgroup_name_chars = ( '*', '(', ')', '!', ) + hgn_chars_separator
    
    space_chars = ( ' ', '\t', )
    # no group should be named like that :
    catch_all_name = "__ALLELEMENTS__"
    minus_sign_in_name = "__MINUSSIGN_IN_NAME__"   


    def evaluate_hostgroup_expression(self, expr, hosts, hostgroups):
        ctxres = hg_name_parse_EXPR(expr) 
        if ctxres.rc:
            err = "The syntax of %s is invalid : %s" % (expr, ctxres.reason)
            self.configuration_errors.append(err)
            print err
            return []
        print "DBG, in evaluate_hg_expr, expr=%s ; pos=%s, neg=%s" % (expr, ctxres.pos_res, ctxres.neg_res)
        allres = []
        allres.extend(ctxres.pos_res)
        allres.extend(ctxres.neg_res)
        groupsname2hostsnames = hg_name_get_groupnames(ctxres.full_res, hosts, hostgroups)
        print "DBG, in eval: dict= \n" + "\n".join( "%s=%s" % (gn, val) for gn, val in groupsname2hostsnames.items() )
        str_setexpr = hg_name_rebuild_str(ctxres.full_res)
        newgroupname2hostnames = {}
        for gn, val in groupsname2hostsnames.items():
            gn = gn.replace('-', Items.minus_sign_in_name)
            newgroupname2hostnames[gn] = val
        set_res = []
        try:
            set_res = set(eval(str_setexpr, newgroupname2hostnames, {})) 
        except SyntaxError, e:
            err = "The syntax of %s is invalid (%s)" % (expr, e)
            self.configuration_errors.append(err)
            print err
        except NameError, e:
            err = "There is a unknow name in %s (names=%s)" % (expr, groupsname2hostsnames)
            self.configuration_errors.append(err)
            print err
        
        return list(set_res) 


    # If we've got a hostgroup_name property, we search for all
    # theses groups and ask them their hosts, and then add them
    # all into our host_name property
    def explode_host_groups_into_hosts(self, hosts, hostgroups):
        for i in self:
            hnames_list = []
            if hasattr(i, 'hostgroup_name'):
                hnames_list.extend(self.evaluate_hostgroup_expression(i.hostgroup_name, hosts, hostgroups))

                # Maybe there is no host in the groups, and do not have any
                # host_name too, so tag is as template to do not look at
                if hnames_list == [] and not hasattr(i, 'host_name'):
                    i.register = '0'

            if hasattr(i, 'host_name'):
                hst = i.host_name.split(',')
                for h in hst:
                    h = h.strip()
                    # If the host start with a !, it's to be remvoed from
                    # the hostgroup get list
                    if h.startswith('!'):
                        hst_to_remove = h[1:].strip()
                        try:
                            hnames_list.remove(hst_to_remove)
                        # was not in it
                        except ValueError:
                            pass
                    # Else it's an host to add
                    elif h == '*':
                        for newhost in get_all_host_names_set(hosts):
                            hnames_list.append(newhost)
                            print "DBG in item.explode_host_groups_into_hosts , added '%s' to group '%s'" % (newhost, i)
                    else:
                        hnames_list.append(h)
            
            i.host_name = ','.join(list(set(hnames_list)))



class HostGroup_Name_Parse_Ctx(object):       
    
    # flags:
    empty_item_ok = 0
     
    def __init__(self, expr, flags=None):
        if flags is None:
            flags = []
        self.expr = expr
        self.len = len(expr)
        self.flags = flags
        self.last_is_expr = False
        self.prev_res = None
        self.res_i = 0 
        self.rc = 0
        self.reason = ""
        self.pos_res = []
        self.neg_res = []

    def __str__(self):
        return "< prev_item='%s' last_is_expr=%s res_i=%d rc=%d >" % (self.prev_res, self.last_is_expr, self.res_i, self.rc)

    __repr__ = __str__



def skip_space(expr):
    i = 0
    try:
        while expr[i] in Items.space_chars:
            i += 1
    except IndexError:
        pass
    return i


def find_matching_closing(expr):
    # special case, need to find matching closing parenthese for this opening one..
    n_opening = 0
    lenexpr = len(expr)
    i = 0
    while i < lenexpr:
        c = expr[i]
        if c == '(':
            n_opening += 1
        elif c == ')':
            n_opening -= 1
            if n_opening < 0:
                return i
        i += 1
    # ouch..
    # (An unmatched left parenthesis creates an unresolved tension that will stay with you all day.
    #
    return None


def hg_name_parse_item(ctx, expr):
    if ctx.last_is_expr:
        ctx.rc = -1
        ctx.reason = "2 consecutive items without valid separator : '%s' and '%s ..'" % (ctx.prev_res, expr[:10])
        return None
    i = s = skip_space(expr)
    lenexpr = len(expr)
    while i < lenexpr:
        c = expr[i]
        if c in Items.specials_hostgroup_name_chars:
            break
        i += 1
    if i == s:
        if HostGroup_Name_Parse_Ctx.empty_item_ok in ctx.flags:
            ctx.res_i = i
            return "set([])"
            
        ctx.rc = -1
        ctx.reason = "Invalid item: size is zero, near '%s'." % (expr[i:i+10])
        return None
    ctx.res_i = i
    # returns the stripped version of the item :
    res = expr[s:i].strip()
    ctx.prev_res = res
    ctx.last_is_expr = True
    return res


def hg_name_parse_single_expr(ctx, expr):
    """ Parse a "single" expression: either an item, or a "subexpression" """
    i = skip_space(expr)
    expr = expr[i:]
    if len(expr) > 0 and expr[0] == '(':
        res = hg_name_parse_subexpr(ctx, expr)
    else:
        res = hg_name_parse_item(ctx, expr)
    #elif expr[i] == '!':
        #i_end = 
        #subctx = 
    #    pass

    ctx.res_i += i
    return res
    
def hg_name_parse_all(ctx, expr):
    if ctx.last_is_expr:
        ctx.rc = -1
        ctx.reason = "* must be on its own, near '%s'" % (expr[:10])
        return
    ctx.pos_res.append("*")
    ctx.last_is_expr = True
    ctx.res_i = 1 # just skip the '*'
    

def hg_name_parse_and(ctx, expr):
    if not ctx.last_is_expr:
        ctx.rc = -1
        ctx.reason = "& must follow a valid expression, near '%s'" % (expr[:10])
    ctx.pos_res.append("&")
    ctx.last_is_expr = False
    ctx.res_i = 1 # just skip the '&'


def hg_name_parse_or(ctx, expr): # '|' or ','
    if not ctx.last_is_expr:
        ctx.rc = -1
        ctx.reason = "'%s' must follow a valid expression, near '%s'" % (expr[0], expr[0:10])
        return
    if len(ctx.pos_res) > 0:
        ctx.pos_res.append("|")
    ctx.last_is_expr = False
    ctx.res_i = 1


def hg_name_parse_xor(ctx, expr):
    if not ctx.last_is_expr:
        ctx.rc = -1
        ctx.reason = "^ must follow a valid expression, near '%s'" % (expr[:10])
    ctx.pos_res.append("^")
    ctx.last_is_expr = False
    ctx.res_i = 1 # just skip the '^'


def hg_name_parse_not(ctx, expr):
    i = s = skip_space(expr)
    try:
        c = expr[s]
    except IndexError:
        ctx.rc = -1
        return
    
    if c not in tabs_hg_name_list_operators:
        while True:
            try:
                c = expr[i]
            except IndexError:
                break
            if c in tabs_hg_name_list_operators:
                break
            i += 1

        if i == s: # bad
            ctx.rc = -1
            ctx.reason = "Invalid item after '!', near '%'" % (expr[:10])
            return
        
        res = hg_name_parse_item(ctx, expr[s:i])
    else:
        if c != '(':
            ctx.rc = -1
            return
        s += 1
        n = find_matching_closing(expr[s:])
        if n is None:
            ctx.rc = -1
            ctx.reason = "Near '%s' : ( An unmatched left parenthesis creates an unresolved tension that will stay with you all day." % (expr[i:10])
            return
        n += s
        subctx = hg_name_parse_EXPR(expr[s:n], ctx.flags)
        if subctx.rc:
            ctx.rc = subctx.rc
            ctx.reason = subctx.reason
            return
        res = subctx.full_res
        i = n + 1

    ctx.res_i = i
    ctx.neg_res.append(res)
    ctx.last_is_expr = True
    return


def parse_neg_or_not__(ctx, expr):
    expr = expr[1:]
    if not ctx.last_is_expr:
        # ( ... ,) ! X case :
        res = hg_name_parse_not(ctx, expr)
    else:
        # A ! B case :
        ctx.pos_res.append("-")
        ctx.last_is_expr = False
        res = hg_name_parse_single_expr(ctx, expr)
    ctx.res_i += 1
    return res
    

def hg_name_parse_subexpr(ctx, expr):
    if ctx.last_is_expr:
        ctx.rc = -1
        ctx.reason = "'(' following directly an expression, prev_item='%s', near '%s'" % (ctx.prev_res, expr[:10])
    i2s = 1 + skip_space(expr[1:])
    i2e = find_matching_closing(expr[i2s:])
    if i2e is None:
        ctx.rc = -1
        ctx.reason = "Near '%s' : ( An unmatched left parenthesis creates an unresolved tension that will stay with you all day." % (expr[:10])        
        return
    i2e += i2s
    subctx = hg_name_parse_EXPR(expr[i2s:i2e], ctx.flags)
    if subctx.rc:
        ctx.rc = subctx.rc
        ctx.reason = subctx.reason
        return
    ctx.res_i = i2e + 1
    ctx.last_is_expr = True
    ctx.prev_res = subctx.prev_res
    return subctx.full_res


tabs_hg_name_list_operators = {
    '*': hg_name_parse_all,
    ',': hg_name_parse_or,
    '|': hg_name_parse_or,
    '!': parse_neg_or_not__,
    '&': hg_name_parse_and,
    '^': hg_name_parse_xor,
    '(': hg_name_parse_subexpr,
}


def hg_name_parse_expr(ctx, expr):
    """ Parse a hostgroup_name expression, 
Returns a "parse_expr_result" :
    a tuple of 2 item. each one is a list.
    first list is a list of "sub-parse_expr_result" to include.
    second list is a list of "sub-parse_expr_result" to exclude.
A "sub-parse_expr_result" is either:
 - a "parse_expr_result" (== tuple)
 - or a string.
"""

    end = ctx.len
    i = skip_space(expr)

    while i < end:

        c = expr[i]
        
        handler = tabs_hg_name_list_operators.get(c, hg_name_parse_item)
        res = handler(ctx, expr[i:])
        if ctx.rc:
            break
        
        if res is not None:
            ctx.pos_res.append(res)

        i += ctx.res_i
        while i < end:
            if expr[i] not in Items.space_chars:
                break
            i += 1

# Return a set with ALL hosts (used in ! expressions)
def get_all_host_names_set(hosts):
    return set(
        h.host_name
        for h in hosts.items.values()
        if getattr(h, 'host_name', '') != ''
    )


def hg_name_get_groupnames(all_res, hosts, hostgroups, res=None):
    if res is None:
        res = {}
    for tok in all_res:
        if isinstance(tok, tuple):
            hg_name_get_groupnames(tok[0], hosts, hostgroups, res)
            hg_name_get_groupnames(tok[1], hosts, hostgroups, res)
            continue
        if isinstance(tok, list):
            hg_name_get_groupnames(tok, hosts, hostgroups, res)
            continue
        if tok in res: # we already got it, good.
            continue
        print "DBG: in hg_name_get_groupnames: tok='%s'" % (tok)
        if tok == '*':
            print "DBG in get_groupnames: [%s]" % (Items.catch_all_name)
            res[Items.catch_all_name] = get_all_host_names_set(hosts)
            print "DBG in get_groupnames:", res
            continue
        if tok in Items.specials_hostgroup_name_chars + ( '-', ):
            continue
        
        # we got a group name :
        members = hostgroups.get_members_by_name(tok)
        print "DBG: in hg_name_get_groupnames: members='%s'" % (members)
        if isinstance(members, list):
            elts = members
        else:
            elts = members.split(',')
        elts = strip_and_uniq(elts)
        # the "host_name" members of a hostgroup can also be '*' :
        if '*' in elts:
            if '*' not in res:
                elts = get_all_host_names_set(hosts)
        elts = set(elts)
        res[tok] = elts

    return res

def hg_name_rebuild_str(parse_res):
    """ rebuild the expression based on the input 'input' """
    
    print "DBG in rebuild: '%s' %s" % (parse_res, type(parse_res))
    
    if isinstance(parse_res, (str, unicode)):
        if parse_res != "-":
            parse_res = parse_res.replace('-', Items.minus_sign_in_name)
        if parse_res == '*':
            parse_res = Items.catch_all_name
        return parse_res
    
    if isinstance(parse_res, list):
        if len(parse_res) == 0:
            return "set([])"
        return " ".join( hg_name_rebuild_str(i) for i in parse_res )
    
    print "DBG in rebuild parse_res='%s'" % (str(parse_res))
    
    posres = " ".join( hg_name_rebuild_str(i) for i in parse_res[0] )
    negres = " ".join( hg_name_rebuild_str(i) for i in parse_res[1] )
    
    posres.strip()
    negres.strip()
    
    res = ""
    lenpos = len(posres)
    lenneg = len(negres)
    if lenpos == 0 and lenneg == 0:
        res += "set([])"
    else:
        res += "( "
        if lenpos == 0:
            res += "set([])"
        else:
            res += " ( " + posres + " ) "
        if lenneg > 0:
            res += " - ( " + negres + " )"
            
        res += " )"
    
    return res


def hg_name_parse_EXPR(expr, flags=None):
    ctx = HostGroup_Name_Parse_Ctx(expr, flags)
    hg_name_parse_expr(ctx, expr)
    for g in ctx.pos_res, ctx.neg_res:
        if len(g) and g[-1] == '|':
            del g[-1]
    ctx.full_res = ( ctx.pos_res, ctx.neg_res, )
    return ctx
