#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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
import itertools

# Try to import md5 function
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from copy import copy

from shinken.commandcall import CommandCall
from shinken.property import (StringProp, ListProp, BoolProp,
                              IntegerProp, ToGuessProp, PythonizeError)
from shinken.brok import Brok
from shinken.util import strip_and_uniq, is_complex_expr
from shinken.acknowledge import Acknowledge
from shinken.comment import Comment
from shinken.log import logger
from shinken.complexexpression import ComplexExpressionFactory
from shinken.graph import Graph



INHERITANCE_DEEP_LIMIT = 32

class Item(object):

    properties = {
        'imported_from':            StringProp(default='unknown'),
        'use':                      ListProp(default=None, split_on_coma=True),
        'name':                     StringProp(default=''),
        'definition_order':         IntegerProp(default=100),
        # TODO: find why we can't uncomment this line below.
        'register':                 BoolProp(default=True),
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
            # We want to create instance of object with the good type.
            # Here we've just parsed config files so everything is a list.
            # We use the pythonize method to get the good type.
            try:
                if key in self.properties:
                    val = self.properties[key].pythonize(params[key])
                elif key in self.running_properties:
                    warning = "using a the running property %s in a config file" % key
                    self.configuration_warnings.append(warning)
                    val = self.running_properties[key].pythonize(params[key])
                elif hasattr(self, 'old_properties') and key in self.old_properties:
                    val = self.properties[self.old_properties[key]].pythonize(params[key])
                elif key.startswith('_'):  # custom macro, not need to detect something here
                    _t = params[key]
                    # If it's a string, directly use this
                    if isinstance(_t, basestring):
                        val = _t
                    # aa list for a custom macro is not managed (conceptually invalid)
                    # so take the first defined
                    elif isinstance(_t, list) and len(_t) > 0:
                        val = _t[0]
                    # not a list of void? just put void string so
                    else:
                        val = ''
                else:
                    warning = "Guessing the property %s type because it is not in %s object properties" % \
                              (key, cls.__name__)
                    self.configuration_warnings.append(warning)
                    val = ToGuessProp.pythonize(params[key])
            except (PythonizeError, ValueError) as expt:
                err = "Error while pythonizing parameter '%s': %s" % (key, expt)
                self.configuration_errors.append(err)
                continue

            # checks for attribute value special syntax (+ or _)
            # we can have '+param' or ['+template1' , 'template2']
            if isinstance(val, str) and len(val) >= 1 and val[0] == '+':
                err = "A + value for a single string is not handled"
                self.configuration_errors.append(err)
                continue

            if (isinstance(val, list) and
                    len(val) >= 1 and
                    isinstance(val[0], unicode) and
                    len(val[0]) >= 1 and
                    val[0][0] == '+'):
                # Special case: a _MACRO can be a plus. so add to plus
                # but upper the key for the macro name
                val[0] = val[0][1:]
                if key[0] == "_":

                    self.plus[key.upper()] = val  # we remove the +
                else:
                    self.plus[key] = val   # we remove the +
            elif key[0] == "_":
                if isinstance(val, list):
                    err = "no support for _ syntax in multiple valued attributes"
                    self.configuration_errors.append(err)
                    continue
                custom_name = key.upper()
                self.customs[custom_name] = val
            else:
                setattr(self, key, val)


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
        # And tags/templates
        if hasattr(self, "tags"):
            i.tags = copy(self.tags)
        if hasattr(self, "templates"):
            i.templates = copy(self.templates)
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
        return not getattr(self, "register", True)

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
        use = getattr(self, 'use', '')
        if isinstance(use, list):
            return [n.strip() for n in use if n.strip()]
        else:
            return [n.strip() for n in use.split(',') if n.strip()]


    # We fillfull properties with template ones if need
    def get_property_by_inheritance(self, prop, deep_level):
        if prop == 'register':
            return None  # We do not inherit from register

        # Don't allow to loop too much over the inheritance, to avoid infinite
        # recursive calls. This loop will raise an error at global configuration
        # check.
        if deep_level > INHERITANCE_DEEP_LIMIT:
            return None

        # If I have the prop, I take mine but I check if I must
        # add a plus property
        if hasattr(self, prop):
            value = getattr(self, prop)
            # Manage the additive inheritance for the property,
            # if property is in plus, add or replace it
            # Template should keep the '+' at the beginning of the chain
            if self.has_plus(prop):
                value.insert(0, self.get_plus_and_delete(prop))
                if self.is_tpl():
                    value = list(value)
                    value.insert(0, '+')
            return value
        # Ok, I do not have prop, Maybe my templates do?
        # Same story for plus
        # We reverse list, so that when looking for properties by inheritance,
        # the least defined template wins (if property is set).
        for i in self.templates:
            value = i.get_property_by_inheritance(prop, deep_level + 1)

            if value is not None and value != []:
                # If our template give us a '+' value, we should continue to loop
                still_loop = False
                if isinstance(value, list) and value[0] == '+':
                    # Templates should keep their + inherited from their parents
                    if not self.is_tpl():
                        value = list(value)
                        value = [x for x in value if x != '+']
                    still_loop = True

                # Maybe in the previous loop, we set a value, use it too
                if hasattr(self, prop):
                    # If the current value is strong, it will simplify the problem
                    if not isinstance(value, list) and value[0] == '+':
                        # In this case we can remove the + from our current
                        # tpl because our value will be final
                        new_val = list(getattr(self, prop))
                        new_val.extend(value[1:])
                        value = new_val
                    else:  # If not, se should keep the + sign of need
                        new_val = list(getattr(self, prop))
                        new_val.extend(value)
                        value = new_val


                # Ok, we can set it
                setattr(self, prop, value)

                # If we only got some '+' values, we must still loop
                # for an end value without it
                if not still_loop:
                    # And set my own value in the end if need
                    if self.has_plus(prop):
                        value = list(value)
                        value = list(getattr(self, prop))
                        value.extend(self.get_plus_and_delete(prop))
                        # Template should keep their '+'
                        if self.is_tpl() and not value[0] == '+':
                            value.insert(0, '+')
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
                value = list(getattr(self, prop))
                value.extend(self.get_plus_and_delete(prop))
            else:
                value = self.get_plus_and_delete(prop)
            # Template should keep their '+' chain
            # We must say it's a '+' value, so our son will now that it must
            # still loop
            if self.is_tpl() and value != [] and not value[0] == '+':
                value.insert(0, '+')

            setattr(self, prop, value)
            return value

        # Ok so in the end, we give the value we got if we have one, or None
        # Not even a plus... so None :)
        return getattr(self, prop, None)


    # We fillfull properties with template ones if need
    def get_customs_properties_by_inheritance(self, deep_level):
        # protect against infinite recursive loop
        if deep_level > INHERITANCE_DEEP_LIMIT:
            return self.customs

        # We reverse list, so that when looking for properties by inheritance,
        # the least defined template wins (if property is set).
        for i in self.templates:
            tpl_cv = i.get_customs_properties_by_inheritance(deep_level + 1)
            if tpl_cv is not {}:
                for prop in tpl_cv:
                    if prop not in self.customs:
                        value = tpl_cv[prop]
                    else:
                        value = self.customs[prop]
                    if self.has_plus(prop):
                        value.insert(0, self.get_plus_and_delete(prop))
                        # value = self.get_plus_and_delete(prop) + ',' + value
                    self.customs[prop] = value
        for prop in self.customs:
            value = self.customs[prop]
            if self.has_plus(prop):
                value.insert(0, self.get_plus_and_delete(prop))
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
        except KeyError:
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
                logger.error("[item::%s] %s", self.get_name(), err)

        for prop, entry in properties.items():
            if not hasattr(self, prop) and entry.required:
                logger.warning("[item::%s] %s property is missing", self.get_name(), prop)
                state = False

        return state


    # This function is used by service and hosts
    # to transform Nagios2 parameters to Nagios3
    # ones, like normal_check_interval to
    # check_interval. There is a old_parameters tab
    # in Classes that give such modifications to do.
    def old_properties_names_to_new(self):
        old_properties = getattr(self.__class__, "old_properties", {})
        for old_name, new_name in old_properties.items():
            # Ok, if we got old_name and NO new name,
            # we switch the name
            if hasattr(self, old_name) and not hasattr(self, new_name):
                value = getattr(self, old_name)
                setattr(self, new_name, value)
                delattr(self, old_name)

    # The arbiter is asking us our raw value before all explode or linking
    def get_raw_import_values(self):
        r = {}
        properties = self.__class__.properties.keys()
        # Register is not by default in the properties
        if 'register' not in properties:
            properties.append('register')

        for prop in properties:
            if hasattr(self, prop):
                v = getattr(self, prop)
                # print prop, ":", v
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
        if (self.acknowledgement and
                self.acknowledgement.end_time != 0 and
                self.acknowledgement.end_time < time.time()):
            self.unacknowledge_problem()

    #  Delete the acknowledgement object and reset the flag
    #  but do not remove the associated comment.
    def unacknowledge_problem(self):
        if self.problem_has_been_acknowledged:
            logger.debug("[item::%s] deleting acknowledge of %s",
                         self.get_name(),
                         self.get_dbg_name())
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
                # if 'fill_brok' in cls.running_properties[prop]:
                if brok_type in entry.fill_brok:
                    data[prop] = self.get_property_value_for_brok(prop, cls.running_properties)


    # Get a brok with initial status
    def get_initial_status_brok(self):
        data = {'id': self.id}
        self.fill_data_brok_from(data, 'full_status')
        return Brok('initial_' + self.my_type + '_status', data)


    # Get a brok with update item status
    def get_update_status_brok(self):
        data = {'id': self.id}
        self.fill_data_brok_from(data, 'full_status')
        return Brok('update_' + self.my_type + '_status', data)

    # Get a brok with check_result
    def get_check_result_brok(self):
        data = {}
        self.fill_data_brok_from(data, 'check_result')
        return Brok(self.my_type + '_check_result', data)

    # Get brok about the new schedule (next_check)
    def get_next_schedule_brok(self):
        data = {}
        self.fill_data_brok_from(data, 'next_schedule')
        return Brok(self.my_type + '_next_schedule', data)

    # A snapshot brok is alike a check_result, with also a
    # output from the snapshot command
    def get_snapshot_brok(self, snap_output, exit_status):
        data = {
            'snapshot_output':      snap_output,
            'snapshot_time':        int(time.time()),
            'snapshot_exit_status': exit_status,
        }
        self.fill_data_brok_from(data, 'check_result')
        return Brok(self.my_type + '_snapshot', data)

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
            t = triggers.create_trigger(src,
                                        'inner-trigger-' + self.__class__.my_type + str(self.id))
            if t:
                # Maybe the trigger factory give me a already existing trigger,
                # so my name can be dropped
                self.triggers.append(t.get_name())


    # Link with triggers. Can be with a "in source" trigger, or a file name
    def linkify_with_triggers(self, triggers):
        # Get our trigger string and trigger names in the same list
        self.triggers.extend([self.trigger_name])
        # print "I am linking my triggers", self.get_full_name(), self.triggers
        new_triggers = []
        for tname in self.triggers:
            if tname == '':
                continue
            t = triggers.find_by_name(tname)
            if t:
                setattr(t, 'trigger_broker_raise_enabled', self.trigger_broker_raise_enabled)
                new_triggers.append(t)
            else:
                self.configuration_errors.append('the %s %s does have a unknown trigger_name '
                                                 '"%s"' % (self.__class__.my_type,
                                                           self.get_full_name(),
                                                           tname))
        self.triggers = new_triggers

    def dump(self):
        dmp = {}
        for prop in self.properties.keys():
            if not hasattr(self, prop):
                continue
            attr = getattr(self, prop)
            if isinstance(attr, list) and attr and isinstance(attr[0], Item):
                dmp[prop] = [i.dump() for i in attr]
            elif isinstance(attr, Item):
                dmp[prop] = attr.dump()
            elif attr:
                dmp[prop] = getattr(self, prop)
        return dmp

    def _get_name(self):
        if hasattr(self, 'get_name'):
            return self.get_name()
        name = getattr(self, 'name', None)
        host_name = getattr(self, 'host_name', None)
        return '%s(host_name=%s)' % (name or 'no-name', host_name or '')



class Items(object):
    def __init__(self, items, index_items=True):
        self.items = {}
        self.name_to_item = {}
        self.templates = {}
        self.name_to_template = {}
        self.configuration_warnings = []
        self.configuration_errors = []
        self.add_items(items, index_items)

    def get_source(self, item):
        source = getattr(item, 'imported_from', None)
        if source:
            return " in %s" % source
        else:
            return ""

    def add_items(self, items, index_items):
        """
        Add items into the `items` or `templates` container depending on the
        is_tpl method result.

        :param items:       The items list to add.
        :param index_items: Flag indicating if the items should be indexed
                            on the fly.
        """
        for i in items:
            if i.is_tpl():
                self.add_template(i)
            else:
                self.add_item(i, index_items)


    def manage_conflict(self, item, name):
        """
        Cheks if an object holding the same name already exists in the index.

        If so, it compares their definition order: the lowest definition order
        is kept. If definiton order equal, an error is risen.Item

        The method returns the item that should be added after it has decided
        which one should be kept.

        If the new item has precedence over the New existing one, the
        existing is removed for the new to replace it.

        :param item:    The new item to check for confict
        :param name:    The exiting object name
        :return         The retained object
        """
        if item.is_tpl():
            existing = self.name_to_template[name]
        else:
            existing = self.name_to_item[name]
        existing_prio = getattr(
            existing,
            "definition_order",
            existing.properties["definition_order"].default)
        item_prio = getattr(
            item,
            "definition_order",
            item.properties["definition_order"].default)
        if existing_prio < item_prio:
            # Existing item has lower priority, so it has precedence.
            return existing
        elif existing_prio > item_prio:
            # New item has lower priority, so it has precedence.
            # Existing item will be deleted below
            pass
        else:
            # Don't know which one to keep, lastly defined has precedence
            objcls = getattr(self.inner_class, "my_type", "[unknown]")
            mesg = "duplicate %s name %s%s, using lastly defined. You may " \
                   "manually set the definition_order parameter to avoid " \
                   "this message." % \
                   (objcls, name, self.get_source(item))
            item.configuration_warnings.append(mesg)
        if item.is_tpl():
            self.remove_template(existing)
        else:
            self.remove_item(existing)
        return item


    def add_template(self, tpl):
        """
        Adds and index a template into the `templates` container.

        :param tpl: The template to add
        """
        tpl = self.index_template(tpl)
        self.templates[tpl.id] = tpl


    def index_template(self, tpl):
        """
        Indexes a template by `name` into the `name_to_template` dictionnary.

        :param tpl: The template to index
        """
        objcls = self.inner_class.my_type
        name = getattr(tpl, 'name', '')
        if not name:
            mesg = "a %s template has been defined without name%s%s" % \
                   (objcls, tpl.imported_from, self.get_source(tpl))
            tpl.configuration_errors.append(mesg)
        elif name in self.name_to_template:
            tpl = self.manage_conflict(tpl, name)
        self.name_to_template[name] = tpl
        return tpl


    def remove_template(self, tpl):
        """
        Removes and unindex a template from the `templates` container.

        :param tpl: The template to remove
        """
        try:
            del self.templates[tpl.id]
        except KeyError:
            pass
        self.unindex_template(tpl)


    def unindex_template(self, tpl):
        """
        Unindex a template from the `templates` container.

        :param tpl: The template to unindex
        """
        name = getattr(tpl, 'name', '')
        try:
            del self.name_to_template[name]
        except KeyError:
            pass


    def add_item(self, item, index=True):
        """Adds an item into our containers, and index it depending on the `index` flag.

        :param item:    The item to add
        :param index:   Flag indicating if the item should be indexed
        """
        name_property = getattr(self.__class__, "name_property", None)
        if index is True and name_property:
            item = self.index_item(item)
        self.items[item.id] = item


    def remove_item(self, item):
        """Removes (and un-index) an item from our containers.

        :param item: The item to be removed.
        :type item:  Item  # or subclass of
        """
        self.unindex_item(item)
        self.items.pop(item.id, None)


    def index_item(self, item):
        """ Indexes an item into our `name_to_item` dictionary.
        If an object holding the same item's name/key already exists in the index
        then the conflict is managed by the `manage_conflict` method.

        :param item: The item to index
        :param name: The optional name to use to index the item
        """
        # TODO: simplify this function (along with its opposite: unindex_item)
        # it's too complex for what it does.
        # more over:
        # There are cases (in unindex_item) where some item is tried to be removed
        # from name_to_item while it's not present in it !
        # so either it wasn't added or it was added with another key or the item key changed
        # between the index and unindex calls..
        #  -> We should simply not have to call unindex_item() with a non-indexed item !
        name_property = getattr(self.__class__, "name_property", None)
        # if there is no 'name_property' set(it is None), then the following getattr() will
        # "hopefully" evaluates to '',
        # unless some(thing|one) have setattr(item, None, 'with_something'),
        # which would be rather odd :
        name = getattr(item, name_property, '')
        if not name:
            objcls = self.inner_class.my_type
            mesg = "a %s item has been defined without %s%s" % \
                   (objcls, name_property, self.get_source(item))
            item.configuration_errors.append(mesg)
        elif name in self.name_to_item:
            if item.id != self.name_to_item[name].id:
                item = self.manage_conflict(item, name)
        self.name_to_item[name] = item
        return item


    def unindex_item(self, item):
        """ Unindex an item from our name_to_item dict.
        :param item:    The item to unindex
        """
        name_property = getattr(self.__class__, "name_property", None)
        if name_property is None:
            return
        self.name_to_item.pop(getattr(item, name_property, ''), None)


    def __iter__(self):
        return self.items.itervalues()


    def __len__(self):
        return len(self.items)


    def __delitem__(self, key):
        try:
            self.unindex_item(self.items[key])
            del self.items[key]
        except KeyError:  # we don't want it, we do not have it. All is perfect
            pass


    def __setitem__(self, key, value):
        self.items[key] = value
        name_property = getattr(self.__class__, "name_property", None)
        if name_property:
            self.index_item(value)


    def __getitem__(self, key):
        return self.items[key]


    def __contains__(self, key):
        return key in self.items


    def compute_hash(self):
        for i in self:
            i.compute_hash()


    def find_by_name(self, name):
        return self.name_to_item.get(name, None)


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
        for i in itertools.chain(self.items.itervalues(),
                                 self.templates.itervalues()):
            i.old_properties_names_to_new()


    def pythonize(self):
        for id in self.items:
            self.items[id].pythonize()


    def find_tpl_by_name(self, name):
        return self.name_to_template.get(name, None)


    def get_all_tags(self, item):
        all_tags = item.get_templates()

        for t in item.templates:
            all_tags.append(t.name)
            all_tags.extend(self.get_all_tags(t))
        return list(set(all_tags))


    def linkify_item_templates(self, item):
        tpls = []
        tpl_names = item.get_templates()

        for name in tpl_names:
            t = self.find_tpl_by_name(name)
            if t is None:
                # TODO: Check if this should not be better to report as an error ?
                self.configuration_warnings.append("%s %r use/inherit from an unknown template "
                                                   "(%r) ! Imported from: "
                                                   "%s" % (type(item).__name__,
                                                           item._get_name(),
                                                           name,
                                                           item.imported_from))
            else:
                if t is item:
                    self.configuration_errors.append(
                        '%s %r use/inherits from itself ! Imported from: '
                        '%s' % (type(item).__name__,
                                item._get_name(),
                                item.imported_from))
                else:
                    tpls.append(t)
        item.templates = tpls


    # We will link all templates, and create the template
    # graph too
    def linkify_templates(self):
        # First we create a list of all templates
        for i in itertools.chain(self.items.itervalues(),
                                 self.templates.itervalues()):
            self.linkify_item_templates(i)
        for i in self:
            i.tags = self.get_all_tags(i)

        # Look if there are loop in our parents definition
        if not self.no_loop_in_parents("self", "templates", templates=True):
            err = '[items] There are loops in the %s templates definition.' % i.__class__.my_type
            self.configuration_errors.append(err)


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
                logger.warning("[items] %s.%s is duplicated from %s",
                               i.__class__.my_type,
                               i.get_name(),
                               getattr(i, 'imported_from', "unknown source"))


        # Then look if we have some errors in the conf
        # Juts print warnings, but raise errors
        for err in self.configuration_warnings:
            logger.warning("[items] %s", err)

        for err in self.configuration_errors:
            logger.error("[items] %s", err)
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
                logger.error("[items] In %s is incorrect ; from %s", i.get_name(), n)
                r = False

        return r


    def remove_templates(self):
        """ Remove useless templates (& properties) of our items
            otherwise we could get errors on config.is_correct()
        """
        del self.templates


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
        for i in itertools.chain(self.items.itervalues(),
                                 self.templates.itervalues()):
            i.get_property_by_inheritance(prop, 0)
            # If a "null" attribute was inherited, delete it
            try:
                if getattr(i, prop) == 'null':
                    delattr(i, prop)
            except AttributeError:
                pass


    def apply_inheritance(self):
        """ For all items and templates inherite properties and custom
            variables.
        """
        # We check for all Class properties if the host has it
        # if not, it check all host templates for a value
        cls = self.inner_class
        for prop in cls.properties:
            self.apply_partial_inheritance(prop)
        for i in itertools.chain(self.items.itervalues(),
                                 self.templates.itervalues()):
            i.get_customs_properties_by_inheritance(0)


    # We've got a contacts property with , separated contacts names
    # and we want have a list of Contacts
    def linkify_with_contacts(self, contacts):
        for i in self:
            if hasattr(i, 'contacts'):
                contacts_tab = strip_and_uniq(i.contacts)
                new_contacts = []
                for c_name in contacts_tab:
                    if c_name != '':
                        c = contacts.find_by_name(c_name)
                        if c is not None:
                            new_contacts.append(c)
                        # Else: Add in the errors tab.
                        # will be raised at is_correct
                        else:
                            err = "the contact '%s' defined for '%s' is unknown" % (c_name,
                                                                                    i.get_name())
                            i.configuration_errors.append(err)
                # Get the list, but first make elements uniq
                i.contacts = list(set(new_contacts))

    # Make link between an object and its escalations
    def linkify_with_escalations(self, escalations):
        for i in self:
            if hasattr(i, 'escalations'):
                escalations_tab = strip_and_uniq(i.escalations)
                new_escalations = []
                for es_name in [e for e in escalations_tab if e != '']:
                    es = escalations.find_by_name(es_name)
                    if es is not None:
                        new_escalations.append(es)
                    else:  # Escalation not find, not good!
                        err = "the escalation '%s' defined for '%s' is unknown" % (es_name,
                                                                                   i.get_name())
                        i.configuration_errors.append(err)
                i.escalations = new_escalations

    # Make link between item and it's resultmodulations
    def linkify_with_resultmodulations(self, resultmodulations):
        for i in self:
            if hasattr(i, 'resultmodulations'):
                resultmodulations_tab = strip_and_uniq(i.resultmodulations)
                new_resultmodulations = []
                for rm_name in resultmodulations_tab:
                    rm = resultmodulations.find_by_name(rm_name)
                    if rm is not None:
                        new_resultmodulations.append(rm)
                    else:
                        err = ("the result modulation '%s' defined on the %s "
                               "'%s' do not exist" % (rm_name, i.__class__.my_type, i.get_name()))
                        i.configuration_warnings.append(err)
                        continue
                i.resultmodulations = new_resultmodulations

    # Make link between item and it's business_impact_modulations
    def linkify_with_business_impact_modulations(self, business_impact_modulations):
        for i in self:
            if hasattr(i, 'business_impact_modulations'):
                business_impact_modulations_tab = strip_and_uniq(i.business_impact_modulations)
                new_business_impact_modulations = []
                for rm_name in business_impact_modulations_tab:
                    rm = business_impact_modulations.find_by_name(rm_name)
                    if rm is not None:
                        new_business_impact_modulations.append(rm)
                    else:
                        err = ("the business impact modulation '%s' defined on the %s "
                               "'%s' do not exist" % (rm_name, i.__class__.my_type, i.get_name()))
                        i.configuration_errors.append(err)
                        continue
                i.business_impact_modulations = new_business_impact_modulations

    # If we've got a contact_groups properties, we search for all
    # theses groups and ask them their contacts, and then add them
    # all into our contacts property
    def explode_contact_groups_into_contacts(self, item, contactgroups):
        if hasattr(item, 'contact_groups'):
            # TODO : See if we can remove this if
            if isinstance(item.contact_groups, list):
                cgnames = item.contact_groups
            else:
                cgnames = item.contact_groups.split(',')
            cgnames = strip_and_uniq(cgnames)
            for cgname in cgnames:
                cg = contactgroups.find_by_name(cgname)
                if cg is None:
                    err = "The contact group '%s' defined on the %s '%s' do " \
                          "not exist" % (cgname, item.__class__.my_type,
                                         item.get_name())
                    item.configuration_errors.append(err)
                    continue
                cnames = contactgroups.get_members_by_name(cgname)
                # We add contacts into our contacts
                if cnames != []:
                    if hasattr(item, 'contacts'):
                        item.contacts.extend(cnames)
                    else:
                        item.contacts = cnames

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
                    err = ("The %s of the %s '%s' named "
                           "'%s' is unknown!" % (prop, i.__class__.my_type, i.get_name(), tpname))
                    i.configuration_errors.append(err)
                    continue
                # Got a real one, just set it :)
                setattr(i, prop, tp)

    def create_commandcall(self, prop, commands, command):
        comandcall = dict(commands=commands, call=command)
        if hasattr(prop, 'enable_environment_macros'):
            comandcall['enable_environment_macros'] = prop.enable_environment_macros

        if hasattr(prop, 'poller_tag'):
            comandcall['poller_tag'] = prop.poller_tag
        elif hasattr(prop, 'reactionner_tag'):
            comandcall['reactionner_tag'] = prop.reactionner_tag

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
                coms = strip_and_uniq(getattr(i, prop))
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
                    err = ("The checkmodulations of the %s '%s' named "
                           "'%s' is unknown!" % (i.__class__.my_type, i.get_name(), cw_name))
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
                    err = ("The macromodulations of the %s '%s' named "
                           "'%s' is unknown!" % (i.__class__.my_type, i.get_name(), cw_name))
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
                if plug is not None:
                    new_modules.append(plug)
                else:
                    err = "Error: the module %s is unknown for %s" % (plug_name, s.get_name())
                    s.configuration_errors.append(err)
            s.modules = new_modules

    def evaluate_hostgroup_expression(self, expr, hosts, hostgroups, look_in='hostgroups'):
        # print "\n"*10, "looking for expression", expr
        # Maybe exp is a list, like numerous hostgroups entries in a service, link them
        if isinstance(expr, list):
            expr = '|'.join(expr)
        # print "\n"*10, "looking for expression", expr
        if look_in == 'hostgroups':
            f = ComplexExpressionFactory(look_in, hostgroups, hosts)
        else:  # templates
            f = ComplexExpressionFactory(look_in, hosts, hosts)
        expr_tree = f.eval_cor_pattern(expr)

        # print "RES of ComplexExpressionFactory"
        # print expr_tree

        # print "Try to resolve the Tree"
        set_res = expr_tree.resolve_elements()
        # print "R2d2 final is", set_res

        # HOOK DBG
        return list(set_res)

    def get_hosts_from_hostgroups(self, hgname, hostgroups):
        if not isinstance(hgname, list):
            hgname = [e.strip() for e in hgname.split(',') if e.strip()]

        host_names = []

        for name in hgname:
            hg = hostgroups.find_by_name(name)
            if hg is None:
                raise ValueError("the hostgroup '%s' is unknown" % hgname)
            mbrs = [h.strip() for h in hg.get_hosts() if h.strip()]
            host_names.extend(mbrs)
        return host_names

    # If we've got a hostgroup_name property, we search for all
    # theses groups and ask them their hosts, and then add them
    # all into our host_name property
    def explode_host_groups_into_hosts(self, item, hosts, hostgroups):
        hnames_list = []
        # Gets item's hostgroup_name
        hgnames = getattr(item, "hostgroup_name", '')

        # Defines if hostgroup is a complex expression
        # Expands hostgroups
        if is_complex_expr(hgnames):
            hnames_list.extend(self.evaluate_hostgroup_expression(
                item.hostgroup_name, hosts, hostgroups))
        elif hgnames:
            try:
                hnames_list.extend(
                    self.get_hosts_from_hostgroups(hgnames, hostgroups))
            except ValueError, e:
                item.configuration_errors.append(str(e))

        # Expands host names
        hname = getattr(item, "host_name", '')
        hnames_list.extend([n.strip() for n in hname.split(',') if n.strip()])
        hnames = set()

        for h in hnames_list:
            # If the host start with a !, it's to be removed from
            # the hostgroup get list
            if h.startswith('!'):
                hst_to_remove = h[1:].strip()
                try:
                    hnames.remove(hst_to_remove)
                except KeyError:
                    pass
            elif h == '*':
                [hnames.add(h.host_name) for h in hosts.items.itervalues()
                 if getattr(h, 'host_name', '')]
            # Else it's a host to add, but maybe it's ALL
            else:
                hnames.add(h)

        item.host_name = ','.join(hnames)

    # Take our trigger strings and create true objects with it
    def explode_trigger_string_into_triggers(self, triggers):
        for i in self:
            i.explode_trigger_string_into_triggers(triggers)


    # Parent graph: use to find quickly relations between all item, and loop
    # return True if there is a loop
    def no_loop_in_parents(self, attr1, attr2, templates=False):
        """ Find loop in dependencies.
        For now, used with the following attributes :
        :(self, parents):
            host dependencies from host object
        :(host_name, dependent_host_name):\
            host dependencies from hostdependencies object
        :(service_description, dependent_service_description):
            service dependencies from servicedependencies object
        """
        # Ok, we say "from now, no loop :) "
        r = True

        # Create parent graph
        parents = Graph()

        elts_lst = self
        if templates:
            elts_lst = self.templates.values()

        # Start with all items as nodes
        for item in elts_lst:
            # Hack to get self here. Used when looping on host and host parent's
            if attr1 == "self":
                obj = item          # obj is a host/service [list]
            else:
                obj = getattr(item, attr1, None)
            if obj is not None:
                if isinstance(obj, list):
                    for sobj in obj:
                        parents.add_node(sobj)
                else:
                    parents.add_node(obj)

        # And now fill edges
        for item in elts_lst:
            if attr1 == "self":
                obj1 = item
            else:
                obj1 = getattr(item, attr1, None)
            obj2 = getattr(item, attr2, None)
            if obj2 is not None:
                if isinstance(obj2, list):
                    for sobj2 in obj2:
                        if isinstance(obj1, list):
                            for sobj1 in obj1:
                                parents.add_edge(sobj1, sobj2)
                        else:
                            parents.add_edge(obj1, sobj2)
                else:
                    if isinstance(obj1, list):
                        for sobj1 in obj1:
                            parents.add_edge(sobj1, obj2)
                    else:
                        parents.add_edge(obj1, obj2)

        # Now get the list of all item in a loop
        items_in_loops = parents.loop_check()

        # and raise errors about it
        for item in items_in_loops:
            logger.error("The %s object '%s'  is part of a circular parent/child chain!",
                         item.my_type,
                         item.get_name())
            r = False

        return r
