#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

""" This class is a base class for nearly all configuration
 elements like service, hosts or contacts.
"""
import time
import cPickle  # for hashing compute

# Try to import md5 function
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from copy import copy

from shinken.graph import Graph
from shinken.commandcall import CommandCall
from shinken.property import StringProp, ListProp, BoolProp, IntegerProp
from shinken.brok import Brok
from shinken.util import strip_and_uniq
from shinken.acknowledge import Acknowledge
from shinken.comment import Comment
from shinken.complexexpression import ComplexExpressionFactory
from shinken.log import logger



class Item(object):

    properties = {
        'imported_from':            StringProp(default='unknown'),
        'use':                      ListProp(default=''),
        'name':                     StringProp(default=''),
        'definition_order':         IntegerProp(default='100'),
        # TODO: find why we can't uncomment this line below.
        #'register':                 BoolProp(default='1'),
    }

    running_properties = {
        # All errors and warning raised during the configuration parsing
        # and that will raised real warning/errors during the is_correct
        'configuration_warnings':   ListProp(default=[]),
        'configuration_errors':     ListProp(default=[]),
        'hash':   StringProp(default=''),
        # We save all template we asked us to load from
        'tags': ListProp(default=set(), fill_brok=['full_status']),
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

        self.customs = {}  # for custom variables
        self.plus = {}  # for value with a +

        self.init_running_properties()

        # [0] = +  -> new key-plus
        # [0] = _  -> new custom entry in UPPER case
        for key in params:
            # delistify attributes if there is only one value
            params[key] = self.compact_unique_attr_value(params[key])
            # checks for attribute value special syntax (+ or _)
            if not isinstance(params[key], list) and \
               len(params[key]) >= 1 and params[key][0] == '+':
                # Special case: a _MACRO can be a plus. so add to plus
                # but upper the key for the macro name
                if key[0] == "_":
                    self.plus[key.upper()] = params[key][1:]  # we remove the +
                else:
                    self.plus[key] = params[key][1:]  # we remove the +
            elif key[0] == "_":
                if isinstance(params[key], list):
                    err = "no support for _ syntax in multiple valued attributes"
                    self.configuration_errors.append(err)
                    continue
                custom_name = key.upper()
                self.customs[custom_name] = params[key]
            else:
                setattr(self, key, params[key])


    # When values to set on attributes are unique (single element list),
    # return the value directly rather than setting list element.
    def compact_unique_attr_value(self, val):
        if isinstance(val, list):
            if len(val) > 1:
                return val
            elif len(val) == 0:
                return ''
            else:
                return val[0]
        else:
            return val

    def init_running_properties(self):
        for prop, entry in self.__class__.running_properties.items():
            # Copy is slow, so we check type
            # Type with __iter__ are list or dict, or tuple.
            # Item need it's own list, so we copy
            val = entry.default
            if hasattr(val, '__iter__'):
                setattr(self, prop, copy(val))
            else:
                setattr(self, prop, val)
            # each instance to have his own running prop!

    def copy(self):
        """ Return a copy of the item, but give him a new id """
        cls = self.__class__
        i = cls({})  # Dummy item but with it's own running properties
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
        for name in ('imported_from', 'use', 'plus', 'templates',):
            try:
                delattr(self, name)
            except AttributeError:
                pass

    def __str__(self):
        return str(self.__dict__) + '\n'

    def is_tpl(self):
        """ Return if the elements is a template """
        try:
            return self.register == '0'
        except Exception, exp:
            return False

    # If a prop is absent and is not required, put the default value
    def fill_default(self):
        """ Fill missing properties if they are missing """
        cls = self.__class__

        for prop, entry in cls.properties.items():
            if not hasattr(self, prop) and entry.has_default:
                setattr(self, prop, entry.default)

    # We load every useful parameter so no need to access global conf later
    # Must be called after a change in a global conf parameter
    def load_global_conf(cls, conf):
        """ Used to put global values in the sub Class like
        hosts or services """
        # conf have properties, if 'enable_notifications':
        # { [...] 'class_inherit': [(Host, None), (Service, None),
        #  (Contact, None)]}
        # get the name and put the value if None, put the Name
        # (not None) if not (not clear?)
        for prop, entry in conf.properties.items():
            # If we have a class_inherit, and the arbiter really send us it
            # if 'class_inherit' in entry and hasattr(conf, prop):
            if hasattr(conf, prop):
                for (cls_dest, change_name) in entry.class_inherit:
                    if cls_dest == cls:  # ok, we've got something to get
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
                new_val = tab.pythonize(getattr(self, prop))
                setattr(self, prop, new_val)
            except AttributeError, exp:
                #print exp
                pass  # Will be catch at the is_correct moment
            except KeyError, exp:
                #print "Missing prop value", exp
                err = "the property '%s' of '%s' do not have value" % (prop, self.get_name())
                self.configuration_errors.append(err)
            except ValueError, exp:
                err = "incorrect type for property '%s' of '%s'" % (prop, self.get_name())
                self.configuration_errors.append(err)

    # Compute a hash of this element values. Should be launched
    # When we got all our values, but not linked with other objects
    def compute_hash(self):
        # ID will always changed between runs, so we remove it
        # for hash compute
        i = self.id
        del self.id
        m = md5()
        tmp = cPickle.dumps(self, cPickle.HIGHEST_PROTOCOL)
        m.update(tmp)
        self.hash = m.digest()
        # and put again our id
        self.id = i

    def get_templates(self):
        if hasattr(self, 'use') and self.use != '':
            if isinstance(self.use, list):
                return self.use
            else:
                return self.use.split(',')
        else:
            return []


    # We fillfull properties with template ones if need
    def get_property_by_inheritance(self, items, prop):

        # If I have the prop, I take mine but I check if I must
        # add a plus property
        if hasattr(self, prop):
            value = getattr(self, prop)
            # Maybe this value is 'null'. If so, we should NOT inherit
            # and just delete this entry, and hope of course.
            # Keep "null" values, because in "inheritance chaining" they must
            # be passed from one level to the next.
            #if value == 'null':
            #    delattr(self, prop)
            #    return None
            # Manage the additive inheritance for the property,
            # if property is in plus, add or replace it
            # Template should keep the '+' at the beginning of the chain
            if self.has_plus(prop):
                value = self.get_plus_and_delete(prop) + ',' + value
                if self.is_tpl():
                    value = '+' + value
            return value
        # Ok, I do not have prop, Maybe my templates do?
        # Same story for plus
        for i in self.templates:
            value = i.get_property_by_inheritance(items, prop)

            if value is not None:
                # If our template give us a '+' value, we should continue to loop
                still_loop = False
                if not isinstance(value, list) and value.startswith('+'):
                    # Templates should keep their + inherited from their parents
                    if not self.is_tpl():
                        value = value[1:]
                    still_loop = True

                # Maybe in the previous loop, we set a value, use it too
                if hasattr(self, prop):
                    # If the current value is strong, it will simplify the problem
                    if not isinstance(value, list) and value.startswith('+'):
                        # In this case we can remove the + from our current
                        # tpl because our value will be final
                        value = ','.join([getattr(self, prop), value[1:]])
                    else: # If not, se should keep the + sign of need
                        value = ','.join([getattr(self, prop), value])


                # Ok, we can set it
                setattr(self, prop, value)

                # If we only got some '+' values, we must still loop
                # for an end value without it
                if not still_loop:
                    # And set my own value in the end if need
                    if self.has_plus(prop):
                        value = ','.join([getattr(self, prop), self.get_plus_and_delete(prop)])
                        # Template should keep their '+'
                        if self.is_tpl() and not value.startswith('+'):
                            value = '+' + value
                        setattr(self, prop, value)
                    return value

        # Maybe templates only give us + values, so we didn't quit, but we already got a
        # self.prop value after all
        template_with_only_plus = hasattr(self, prop)

        # I do not have endingprop, my templates too... Maybe a plus?
        # warning: if all my templates gave me '+' values, do not forgot to
        # add the already set self.prop value
        if self.has_plus(prop):
            if template_with_only_plus:
                value = ','.join([getattr(self, prop), self.get_plus_and_delete(prop)])
            else:
                value = self.get_plus_and_delete(prop)
            # Template should keep their '+' chain
            # We must say it's a '+' value, so our son will now that it must
            # still loop
            if self.is_tpl() and not value.startswith('+'):
                value = '+' + value
            setattr(self, prop, value)
            return value

        # Ok so in the end, we give the value we got if we have one, or None
        # Not even a plus... so None :)
        return getattr(self, prop, None)


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
                        value = self.get_plus_and_delete(prop) + ',' + value
                    self.customs[prop] = value
        for prop in self.customs:
            value = self.customs[prop]
            if self.has_plus(prop):
                value = self.get_plus_and_delete(prop) + ',' + value
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
        props = self.plus.keys()  # we delete entries, so no for ... in ...
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
                logger.error("[item::%s] %s" % (self.get_name(), err))

        for prop, entry in properties.items():
            if not hasattr(self, prop) and entry.required:
                logger.warning("[item::%s] %s property is missing" % (self.get_name(), prop))
                state = False

        return state


    # This function is used by service and hosts
    # to transform Nagios2 parameters to Nagios3
    # ones, like normal_check_interval to
    # check_interval. There is a old_parameters tab
    # in Classes that give such modifications to do.
    def old_properties_names_to_new(self):
        old_properties = self.__class__.old_properties
        for old_name, new_name in old_properties.items():
            # Ok, if we got old_name and NO new name,
            # we switch the name
            if hasattr(self, old_name) and not hasattr(self, new_name):
                value = getattr(self, old_name)
                setattr(self, new_name, value)

    # The arbiter is asking us our raw value before all explode or linking
    def get_raw_import_values(self):
        r = {}
        properties = self.__class__.properties.keys()
        # Register is not by default in the properties
        if not 'register' in properties:
            properties.append('register')

        for prop in properties:
            if hasattr(self, prop):
                v = getattr(self, prop)
                #print prop, ":", v
                r[prop] = v
        return r


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

    def acknowledge_problem(self, sticky, notify, persistent, author, comment, end_time=0):
        if self.state != self.ok_up:
            if notify:
                self.create_notifications('ACKNOWLEDGEMENT')
            self.problem_has_been_acknowledged = True
            if sticky == 2:
                sticky = True
            else:
                sticky = False
            a = Acknowledge(self, sticky, notify, persistent, author, comment, end_time=end_time)
            self.acknowledgement = a
            if self.my_type == 'host':
                comment_type = 1
            else:
                comment_type = 2
            c = Comment(self, persistent, author, comment,
                        comment_type, 4, 0, False, 0)
            self.add_comment(c)
            self.broks.append(self.get_update_status_brok())

    # Look if we got an ack that is too old with an expire date and should
    # be delete
    def check_for_expire_acknowledge(self):
        if self.acknowledgement and self.acknowledgement.end_time != 0 and self.acknowledgement.end_time < time.time():
            self.unacknowledge_problem()

    #  Delete the acknowledgement object and reset the flag
    #  but do not remove the associated comment.
    def unacknowledge_problem(self):
        if self.problem_has_been_acknowledged:
            logger.debug("[item::%s] deleting acknowledge of %s" % (self.get_name(), self.get_dbg_name()))
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

    # Will flatten some parameters tagged by the 'conf_send_preparation'
    # property because they are too "linked" to be send like that (like realms)
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
    # in props of properties or running_properties
    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        # Now config properties
        for prop, entry in cls.properties.items():
            # Is this property intended for broking?
            if brok_type in entry.fill_brok:
                data[prop] = self.get_property_value_for_brok(prop, cls.properties)

        # Maybe the class do not have running_properties
        if hasattr(cls, 'running_properties'):
            # We've got prop in running_properties too
            for prop, entry in cls.running_properties.items():
                #if 'fill_brok' in cls.running_properties[prop]:
                if brok_type in entry.fill_brok:
                    data[prop] = self.get_property_value_for_brok(prop, cls.running_properties)

    # Get a brok with initial status
    def get_initial_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type
        data = {'id': self.id}

        self.fill_data_brok_from(data, 'full_status')
        b = Brok('initial_' + my_type + '_status', data)
        return b

    # Get a brok with update item status
    def get_update_status_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {'id': self.id}
        self.fill_data_brok_from(data, 'full_status')
        b = Brok('update_' + my_type + '_status', data)
        return b

    # Get a brok with check_result
    def get_check_result_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {}
        self.fill_data_brok_from(data, 'check_result')
        b = Brok(my_type + '_check_result', data)
        return b

    # Get brok about the new schedule (next_check)
    def get_next_schedule_brok(self):
        cls = self.__class__
        my_type = cls.my_type

        data = {}
        self.fill_data_brok_from(data, 'next_schedule')
        b = Brok(my_type + '_next_schedule', data)
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



    # We look at the 'trigger' prop and we create a trigger for it
    def explode_trigger_string_into_triggers(self, triggers):
        src = getattr(self, 'trigger', '')
        if src:
            # Change on the fly the characters
            src = src.replace(r'\n', '\n').replace(r'\t', '\t')
            t = triggers.create_trigger(src, 'inner-trigger-' + self.__class__.my_type + '' + str(self.id))
            if t:
                # Maybe the trigger factory give me a already existing trigger,
                # so my name can be dropped
                self.triggers.append(t.get_name())

    # Link with triggers. Can be with a "in source" trigger, or a file name
    def linkify_with_triggers(self, triggers):
        # Get our trigger string and trigger names in the same list
        self.triggers.extend(self.trigger_name)
        #print "I am linking my triggers", self.get_full_name(), self.triggers
        new_triggers = []
        for tname in self.triggers:
            t = triggers.find_by_name(tname)
            if t:
                setattr(t, 'trigger_broker_raise_enabled', self.trigger_broker_raise_enabled)
                new_triggers.append(t)
            else:
                self.configuration_errors.append('the %s %s does have a unknown trigger_name "%s"' % (self.__class__.my_type, self.get_full_name(), tname))
        self.triggers = new_triggers


class Items(object):
    def __init__(self, items):
        self.items = {}
        self.configuration_warnings = []
        self.configuration_errors = []
        for i in items:
            self.items[i.id] = i
        self.templates = {}
        # We should keep a graph of templates relations
        self.templates_graph = Graph()

    def __iter__(self):
        return self.items.itervalues()

    def __len__(self):
        return len(self.items)

    def __delitem__(self, key):
        try:
            del self.items[key]
        except KeyError:  # we don't want it, we do not have it. All is perfect
            pass

    def __setitem__(self, key, value):
        self.items[key] = value

    def __getitem__(self, key):
        return self.items[key]

    def __contains__(self, key):
        return key in self.items

    def compute_hash(self):
        for i in self:
            i.compute_hash()


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
        else:  # ok, an early ask, with no reversed list from now...
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


    # Search items using a list of filter callbacks. Each callback is passed
    # the item instances and should return a boolean value indicating if it
    # matched the filter.
    # Returns a list of items matching all filters.
    def find_by_filter(self, filters):
        items = []
        for i in self:
            failed = False
            for f in filters:
                if not f(i):
                    failed = True
                    break
            if failed is False:
                items.append(i)
        return items


    # prepare_for_conf_sending to flatten some properties
    def prepare_for_sending(self):
        for i in self:
            i.prepare_for_conf_sending()

    
    # It's used to change old Nagios2 names to
    # Nagios3 ones
    def old_properties_names_to_new(self):
        for i in self:
            i.old_properties_names_to_new()

    def pythonize(self):
        for id in self.items:
            self.items[id].pythonize()

    def create_tpl_list(self):
        for id in self.items:
            i = self.items[id]
            if i.is_tpl():
                self.templates[id] = i

    def find_tpl_by_name(self, name):
        for i in self.templates.values():
            if hasattr(i, 'name') and i.name == name:
                return i
        return None

    # We will link all templates, and create the template
    # graph too
    def linkify_templates(self):
        # First we create a list of all templates
        self.create_tpl_list()
        for i in self:
            tpls = i.get_templates()
            new_tpls = []
            for tpl in tpls:
                tpl = tpl.strip()
                # We save this template in the 'tags' set
                i.tags.add(tpl)
                # Then we link it
                t = self.find_tpl_by_name(tpl)
                # If it's ok, add the template and update the
                # template graph too
                if t is not None:
                    # add the template object to us
                    new_tpls.append(t)
                else:  # not find? not good!
                    err = "the template '%s' defined for '%s' is unknown" % (tpl, i.get_name())
                    i.configuration_warnings.append(err)
            i.templates = new_tpls

        # Now we will create the template graph, so
        # we look only for templates here. First we should declare our nodes
        for tpl in self.templates.values():
            self.templates_graph.add_node(tpl)
        # And then really create our edge
        for tpl in self.templates.values():
            for father in tpl.templates:
                self.templates_graph.add_edge(father, tpl)

    def is_correct(self):
        # we are ok at the beginning. Hope we still ok at the end...
        r = True
        # Some class do not have twins, because they do not have names
        # like servicedependencies
        twins = getattr(self, 'twins', None)
        if twins is not None:
            # Ok, look at no twins (it's bad!)
            for id in twins:
                i = self.items[id]
                logger.warning("[items] %s.%s is duplicated from %s" %\
                    (i.__class__.my_type, i.get_name(), getattr(i, 'imported_from', "unknown source")))

        # Then look if we have some errors in the conf
        # Juts print warnings, but raise errors
        for err in self.configuration_warnings:
            logger.warning("[items] %s" % err)

        for err in self.configuration_errors:
            logger.error("[items] %s" % err)
            r = False

        # Then look for individual ok
        for i in self:
            # Alias and display_name hook hook
            prop_name = getattr(self.__class__, 'name_property', None)
            if prop_name and not hasattr(i, 'alias') and hasattr(i, prop_name):
                setattr(i, 'alias', getattr(i, prop_name))
            if prop_name and getattr(i, 'display_name', '') == '' and hasattr(i, prop_name):
                setattr(i, 'display_name', getattr(i, prop_name))

            # Now other checks
            if not i.is_correct():
                n = getattr(i, 'imported_from', "unknown source")
                logger.error("[items] In %s is incorrect ; from %s" % (i.get_name(), n))
                r = False

        return r

    def remove_templates(self):
        """ Remove useless templates (& properties) of our items ; otherwise we could get errors on config.is_correct() """
        tpls = [i for i in self if i.is_tpl()]
        for i in tpls:
            del self[i.id]
        del self.templates
        del self.templates_graph

    def clean(self):
        """ Request to remove the unnecessary attributes/others from our items """
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

    # Inheritance for just a property
    def apply_partial_inheritance(self, prop):
        for i in self:
            i.get_property_by_inheritance(self, prop)
            if not i.is_tpl():
                # If a "null" attribute was inherited, delete it
                try:
                    if getattr(i, prop) == 'null':
                        delattr(i, prop)
                except:
                    pass

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
            logger.warning("[items] %s.%s is already defined '%s'" % (type, i.get_name(), getattr(i, 'imported_from', "unknown source")))
            del self[id]  # bye bye
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
                        # Else: Add in the errors tab.
                        # will be raised at is_correct
                        else:
                            err = "the contact '%s' defined for '%s' is unknown" % (c_name, i.get_name())
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
                    else:  # Escalation not find, not good!
                        err = "the escalation '%s' defined for '%s' is unknown" % (es_name, i.get_name())
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
                    else:
                        err = "the result modulation '%s' defined on the %s '%s' do not exist" % (rm_name, i.__class__.my_type, i.get_name())
                        i.configuration_warnings.append(err)
                        continue
                i.resultmodulations = new_resultmodulations

    # Make link between item and it's business_impact_modulations
    def linkify_with_business_impact_modulations(self, business_impact_modulations):
        for i in self:
            if hasattr(i, 'business_impact_modulations'):
                business_impact_modulations_tab = i.business_impact_modulations.split(',')
                business_impact_modulations_tab = strip_and_uniq(business_impact_modulations_tab)
                new_business_impact_modulations = []
                for rm_name in business_impact_modulations_tab:
                    rm = business_impact_modulations.find_by_name(rm_name)
                    if rm is not None:
                        new_business_impact_modulations.append(rm)
                    else:
                        err = "the business impact modulation '%s' defined on the %s '%s' do not exist" % (rm_name, i.__class__.my_type, i.get_name())
                        i.configuration_errors.append(err)
                        continue
                i.business_impact_modulations = new_business_impact_modulations

    # If we've got a contact_groups properties, we search for all
    # theses groups and ask them their contacts, and then add them
    # all into our contacts property
    def explode_contact_groups_into_contacts(self, contactgroups):
        for i in self:
            if hasattr(i, 'contact_groups'):
                if isinstance(i.contact_groups, list):
                    cgnames = i.contact_groups
                else:
                    cgnames = i.contact_groups.split(',')
                cgnames = strip_and_uniq(cgnames)
                for cgname in cgnames:
                    cg = contactgroups.find_by_name(cgname)
                    if cg is None:
                        err = "The contact group '%s' defined on the %s '%s' do not exist" % (cgname, i.__class__.my_type, i.get_name())
                        i.configuration_errors.append(err)
                        continue
                    cnames = contactgroups.get_members_by_name(cgname)
                    # We add contacts into our contacts
                    if cnames != []:
                        if hasattr(i, 'contacts'):
                            i.contacts += ',' + cnames
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
                # If not found, it's an error
                if tp is None:
                    err = "The %s of the %s '%s' named '%s' is unknown!" % (prop, i.__class__.my_type, i.get_name(), tpname)
                    i.configuration_errors.append(err)
                    continue
                # Got a real one, just set it :)
                setattr(i, prop, tp)

    def create_commandcall(self,prop, commands, command):
        comandcall = dict(commands=commands, call=command)
        if hasattr(prop, 'enable_environment_macros'):
            comandcall['enable_environment_macros'] = prop.enable_environment_macros

        if hasattr(prop, 'poller_tag'):
            comandcall['poller_tag']=prop.poller_tag
        elif hasattr(prop, 'reactionner_tag'):
            comandcall['reactionner_tag']=prop.reactionner_tag

        return CommandCall(**comandcall)

    # Link one command property
    def linkify_one_command_with_commands(self, commands, prop):
        for i in self:
            if hasattr(i, prop):
                command = getattr(i, prop).strip()
                if command != '':
                    cmdCall = self.create_commandcall(i, commands, command)

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
                        cmdCall = self.create_commandcall(i, commands, com)
                        # TODO: catch None?
                        com_list.append(cmdCall)
                    else:  # TODO: catch?
                        pass
                setattr(i, prop, com_list)

    # Link with triggers. Can be with a "in source" trigger, or a file name
    def linkify_with_triggers(self, triggers):
        for i in self:
            i.linkify_with_triggers(triggers)


    # We've got a notificationways property with , separated contacts names
    # and we want have a list of NotificationWay
    def linkify_with_checkmodulations(self, checkmodulations):
        for i in self:
            if not hasattr(i, 'checkmodulations'):
                continue
            new_checkmodulations = []
            for cw_name in i.checkmodulations:
                cw = checkmodulations.find_by_name(cw_name)
                if cw is not None:
                    new_checkmodulations.append(cw)
                else:
                    err = "The checkmodulations of the %s '%s' named '%s' is unknown!" % (i.__class__.my_type, i.get_name(), cw_name)
                    i.configuration_errors.append(err)
            # Get the list, but first make elements uniq
            i.checkmodulations = new_checkmodulations


    # We've got list of macro modulations as list of names, and
    # we want real objects
    def linkify_with_macromodulations(self, macromodulations):
        for i in self:
            if not hasattr(i, 'macromodulations'):
                continue
            new_macromodulations = []
            for cw_name in i.macromodulations:
                cw = macromodulations.find_by_name(cw_name)
                if cw is not None:
                    new_macromodulations.append(cw)
                else:
                    err = "The macromodulations of the %s '%s' named '%s' is unknown!" % (i.__class__.my_type, i.get_name(), cw_name)
                    i.configuration_errors.append(err)
            # Get the list, but first make elements uniq
            i.macromodulations = new_macromodulations


    # Linkify with modules
    def linkify_s_by_plug(self, modules):
        for s in self:
            new_modules = []
            for plug_name in s.modules:
                plug_name = plug_name.strip()
                # don't tread void names
                if plug_name == '':
                    continue

                plug = modules.find_by_name(plug_name)
                print plug
                if plug is not None:
                    new_modules.append(plug)
                else:
                    err = "Error: the module %s is unknown for %s" % (plug_name, s.get_name())
                    s.configuration_errors.append(err)
            s.modules = new_modules


    def evaluate_hostgroup_expression(self, expr, hosts, hostgroups, look_in='hostgroups'):
        #print "\n"*10, "looking for expression", expr
        # Maybe exp is a list, like numerous hostgroups entries in a service, link them
        if isinstance(expr, list):
            expr = '|'.join(expr)
        #print "\n"*10, "looking for expression", expr        
        if look_in=='hostgroups':
            f = ComplexExpressionFactory(look_in, hostgroups, hosts)
        else: # templates
            f = ComplexExpressionFactory(look_in, hosts, hosts)
        expr_tree = f.eval_cor_pattern(expr)

        #print "RES of ComplexExpressionFactory"
        #print expr_tree

        #print "Try to resolve the Tree"
        set_res = expr_tree.resolve_elements()
        #print "R2d2 final is", set_res

        # HOOK DBG
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
                    # If the host start with a !, it's to be removed from
                    # the hostgroup get list
                    if h.startswith('!'):
                        hst_to_remove = h[1:].strip()
                        try:
                            hnames_list.remove(hst_to_remove)
                        # was not in it
                        except ValueError:
                            pass
                    # Else it's an host to add, but maybe it's ALL
                    elif h == '*':
                        for newhost in  set(h.host_name for h in hosts.items.values() \
                                            if getattr(h, 'host_name', '') != '' and not h.is_tpl()):
                            hnames_list.append(newhost)
                            #print "DBG in item.explode_host_groups_into_hosts , added '%s' to group '%s'" % (newhost, i)
                    else:
                        hnames_list.append(h)

            i.host_name = ','.join(list(set(hnames_list)))

            # Ok, even with all of it, there is still no host, put it as a template
            if i.host_name == '':
                i.register = '0'


    # Take our trigger strings and create true objects with it
    def explode_trigger_string_into_triggers(self, triggers):
        for i in self:
            i.explode_trigger_string_into_triggers(triggers)

