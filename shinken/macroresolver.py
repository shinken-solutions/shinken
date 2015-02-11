#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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


# This class resolve Macro in commands by looking at the macros list
# in Class of elements. It give a property that call be callable or not.
# It not callable, it's a simple property and replace the macro with the value
# If callable, it's a method that is called to get the value. for example, to
# get the number of service in a host, you call a method to get the
# len(host.services)

import re
import time

from shinken.borg import Borg


class MacroResolver(Borg):
    """Please Add a Docstring to describe the class here"""

    my_type = 'macroresolver'
    # Global macros
    macros = {
        'TOTALHOSTSUP':         '_get_total_hosts_up',
        'TOTALHOSTSDOWN':       '_get_total_hosts_down',
        'TOTALHOSTSUNREACHABLE': '_get_total_hosts_unreachable',
        'TOTALHOSTSDOWNUNHANDLED': '_get_total_hosts_unhandled',
        'TOTALHOSTSUNREACHABLEUNHANDLED': '_get_total_hosts_unreachable_unhandled',
        'TOTALHOSTPROBLEMS':    '_get_total_host_problems',
        'TOTALHOSTPROBLEMSUNHANDLED': '_get_total_host_problems_unhandled',
        'TOTALSERVICESOK':      '_get_total_service_ok',
        'TOTALSERVICESWARNING': '_get_total_services_warning',
        'TOTALSERVICESCRITICAL': '_get_total_services_critical',
        'TOTALSERVICESUNKNOWN': '_get_total_services_unknown',
        'TOTALSERVICESWARNINGUNHANDLED': '_get_total_services_warning_unhandled',
        'TOTALSERVICESCRITICALUNHANDLED': '_get_total_services_critical_unhandled',
        'TOTALSERVICESUNKNOWNUNHANDLED': '_get_total_services_unknown_unhandled',
        'TOTALSERVICEPROBLEMS': '_get_total_service_problems',
        'TOTALSERVICEPROBLEMSUNHANDLED': '_get_total_service_problems_unhandled',
        'LONGDATETIME':         '_get_long_date_time',
        'SHORTDATETIME':        '_get_short_date_time',
        'DATE':                 '_get_date',
        'TIME':                 '_get_time',
        'TIMET':                '_get_timet',
        'PROCESSSTARTTIME':     '_get_process_start_time',
        'EVENTSTARTTIME':       '_get_events_start_time',
    }

    output_macros = [
        'HOSTOUTPUT',
        'HOSTPERFDATA',
        'HOSTACKAUTHOR',
        'HOSTACKCOMMENT',
        'SERVICEOUTPUT',
        'SERVICEPERFDATA',
        'SERVICEACKAUTHOR',
        'SERVICEACKCOMMENT'
    ]

    # This must be called ONCE. It just put links for elements
    # by scheduler
    def init(self, conf):
        # For searching class and elements for ondemand
        # we need link to types
        self.conf = conf
        self.lists_on_demand = []
        self.hosts = conf.hosts
        # For special void host_name handling...
        self.host_class = self.hosts.inner_class
        self.lists_on_demand.append(self.hosts)
        self.services = conf.services
        self.contacts = conf.contacts
        self.lists_on_demand.append(self.contacts)
        self.hostgroups = conf.hostgroups
        self.lists_on_demand.append(self.hostgroups)
        self.commands = conf.commands
        self.servicegroups = conf.servicegroups
        self.lists_on_demand.append(self.servicegroups)
        self.contactgroups = conf.contactgroups
        self.lists_on_demand.append(self.contactgroups)
        self.illegal_macro_output_chars = conf.illegal_macro_output_chars

        # Try cache :)
        # self.cache = {}


    # Return all macros of a string, so cut the $
    # And create a dict with it:
    # val: value, not set here
    # type: type of macro, like class one, or ARGN one
    def _get_macros(self, s):
        # if s in self.cache:
        #    return self.cache[s]

        p = re.compile(r'(\$)')
        elts = p.split(s)
        macros = {}
        in_macro = False
        for elt in elts:
            if elt == '$':
                in_macro = not in_macro
            elif in_macro:
                macros[elt] = {'val': '', 'type': 'unknown'}

        # self.cache[s] = macros
        if '' in macros:
            del macros['']
        return macros

    # Get a value from a property of a element
    # Prop can be a function or a property
    # So we call it or not
    def _get_value_from_element(self, elt, prop):
        try:
            value = getattr(elt, prop)
            if callable(value):
                return unicode(value())
            else:
                return unicode(value)
        except AttributeError, exp:
            # Return no value
            return ''
        except UnicodeError, exp:
            if isinstance(value, str):
                return unicode(value, 'utf8', errors='ignore')
            else:
                return ''


    # For some macros, we need to delete unwanted characters
    def _delete_unwanted_caracters(self, s):
        for c in self.illegal_macro_output_chars:
            s = s.replace(c, '')
        return s

    # return a dict with all environment variable came from
    # the macros of the datas object
    def get_env_macros(self, data):
        env = {}

        for o in data:
            cls = o.__class__
            macros = cls.macros
            for macro in macros:
                if macro.startswith("USER"):
                    break

                prop = macros[macro]
                value = self._get_value_from_element(o, prop)
                env['NAGIOS_%s' % macro] = value
            if hasattr(o, 'customs'):
                # make NAGIOS__HOSTMACADDR from _MACADDR
                for cmacro in o.customs:
                    new_env_name = 'NAGIOS__' + o.__class__.__name__.upper() + cmacro[1:].upper()
                    env[new_env_name] = o.customs[cmacro]

        return env

    # This function will look at elements in data (and args if it filled)
    # to replace the macros in c_line with real value.
    def resolve_simple_macros_in_string(self, c_line, data, args=None):
        # Now we prepare the classes for looking at the class.macros
        data.append(self)  # For getting global MACROS
        if hasattr(self, 'conf'):
            data.append(self.conf)  # For USERN macros
        clss = [d.__class__ for d in data]

        # we should do some loops for nested macros
        # like $USER1$ hiding like a ninja in a $ARG2$ Macro. And if
        # $USER1$ is pointing to $USER34$ etc etc, we should loop
        # until we reach the bottom. So the last loop is when we do
        # not still have macros :)
        still_got_macros = True
        nb_loop = 0
        while still_got_macros:
            nb_loop += 1
            # Ok, we want the macros in the command line
            macros = self._get_macros(c_line)

            # We can get out if we do not have macros this loop
            still_got_macros = (len(macros) != 0)
            # print "Still go macros:", still_got_macros

            # Put in the macros the type of macro for all macros
            self._get_type_of_macro(macros, clss)
            # Now we get values from elements
            for macro in macros:
                # If type ARGN, look at ARGN cutting
                if macros[macro]['type'] == 'ARGN' and args is not None:
                    macros[macro]['val'] = self._resolve_argn(macro, args)
                    macros[macro]['type'] = 'resolved'
                # If class, get value from properties
                if macros[macro]['type'] == 'class':
                    cls = macros[macro]['class']
                    for elt in data:
                        if elt is not None and elt.__class__ == cls:
                            prop = cls.macros[macro]
                            macros[macro]['val'] = self._get_value_from_element(elt, prop)
                            # Now check if we do not have a 'output' macro. If so, we must
                            # delete all special characters that can be dangerous
                            if macro in self.output_macros:
                                macros[macro]['val'] = \
                                    self._delete_unwanted_caracters(macros[macro]['val'])
                if macros[macro]['type'] == 'CUSTOM':
                    cls_type = macros[macro]['class']
                    # Beware : only cut the first _HOST value, so the macro name can have it on it..
                    macro_name = re.split('_' + cls_type, macro, 1)[1].upper()
                    # Ok, we've got the macro like MAC_ADDRESS for _HOSTMAC_ADDRESS
                    # Now we get the element in data that have the type HOST
                    # and we check if it got the custom value
                    for elt in data:
                        if elt is not None and elt.__class__.my_type.upper() == cls_type:
                            if '_' + macro_name in elt.customs:
                                macros[macro]['val'] = elt.customs['_' + macro_name]
                            # Then look on the macromodulations, in reserver order, so
                            # the last to set, will be the firt to have. (yes, don't want to play
                            # with break and such things sorry...)
                            mms = getattr(elt, 'macromodulations', [])
                            for mm in mms[::-1]:
                                # Look if the modulation got the value,
                                # but also if it's currently active
                                if '_' + macro_name in mm.customs and mm.is_active():
                                    macros[macro]['val'] = mm.customs['_' + macro_name]
                if macros[macro]['type'] == 'ONDEMAND':
                    macros[macro]['val'] = self._resolve_ondemand(macro, data)

            # We resolved all we can, now replace the macro in the command call
            for macro in macros:
                c_line = c_line.replace('$' + macro + '$', macros[macro]['val'])

            # A $$ means we want a $, it's not a macro!
            # We replace $$ by a big dirty thing to be sure to not misinterpret it
            c_line = c_line.replace("$$", "DOUBLEDOLLAR")

            if nb_loop > 32:  # too much loop, we exit
                still_got_macros = False

        # We now replace the big dirty token we made by only a simple $
        c_line = c_line.replace("DOUBLEDOLLAR", "$")

        # print "Retuning c_line", c_line.strip()
        return c_line.strip()

    # Resolve a command with macro by looking at data classes.macros
    # And get macro from item properties.
    def resolve_command(self, com, data):
        c_line = com.command.command_line
        return self.resolve_simple_macros_in_string(c_line, data, args=com.args)

    # For all Macros in macros, set the type by looking at the
    # MACRO name (ARGN? -> argn_type,
    # HOSTBLABLA -> class one and set Host in class)
    # _HOSTTOTO -> HOST CUSTOM MACRO TOTO
    # $SERVICESTATEID:srv-1:Load$ -> MACRO SERVICESTATEID of
    # the service Load of host srv-1
    def _get_type_of_macro(self, macros, clss):
        for macro in macros:
            # ARGN Macros
            if re.match('ARG\d', macro):
                macros[macro]['type'] = 'ARGN'
                continue
            # USERN macros
            # are managed in the Config class, so no
            # need to look that here
            elif re.match('_HOST\w', macro):
                macros[macro]['type'] = 'CUSTOM'
                macros[macro]['class'] = 'HOST'
                continue
            elif re.match('_SERVICE\w', macro):
                macros[macro]['type'] = 'CUSTOM'
                macros[macro]['class'] = 'SERVICE'
                # value of macro: re.split('_HOST', '_HOSTMAC_ADDRESS')[1]
                continue
            elif re.match('_CONTACT\w', macro):
                macros[macro]['type'] = 'CUSTOM'
                macros[macro]['class'] = 'CONTACT'
                continue
            # On demand macro
            elif len(macro.split(':')) > 1:
                macros[macro]['type'] = 'ONDEMAND'
                continue
            # OK, classical macro...
            for cls in clss:
                if macro in cls.macros:
                    macros[macro]['type'] = 'class'
                    macros[macro]['class'] = cls
                    continue

    # Resolve MACROS for the ARGN
    def _resolve_argn(self, macro, args):
        # first, get the number of args
        id = None
        r = re.search('ARG(?P<id>\d+)', macro)
        if r is not None:
            id = int(r.group('id')) - 1
            try:
                return args[id]
            except IndexError:
                return ''

    # Resolve on-demand macro, quite hard in fact
    def _resolve_ondemand(self, macro, data):
        # print "\nResolving macro", macro
        elts = macro.split(':')
        nb_parts = len(elts)
        macro_name = elts[0]
        # Len 3 == service, 2 = all others types...
        if nb_parts == 3:
            val = ''
            # print "Got a Service on demand asking...", elts
            (host_name, service_description) = (elts[1], elts[2])
            # host_name can be void, so it's the host in data
            # that is important. We use our self.host_class to
            # find the host in the data :)
            if host_name == '':
                for elt in data:
                    if elt is not None and elt.__class__ == self.host_class:
                        host_name = elt.host_name
            # Ok now we get service
            s = self.services.find_srv_by_name_and_hostname(host_name, service_description)
            if s is not None:
                cls = s.__class__
                prop = cls.macros[macro_name]
                val = self._get_value_from_element(s, prop)
                # print "Got val:", val
                return val
        # Ok, service was easy, now hard part
        else:
            val = ''
            elt_name = elts[1]
            # Special case: elt_name can be void
            # so it's the host where it apply
            if elt_name == '':
                for elt in data:
                    if elt is not None and elt.__class__ == self.host_class:
                        elt_name = elt.host_name
            for list in self.lists_on_demand:
                cls = list.inner_class
                # We search our type by looking at the macro
                if macro_name in cls.macros:
                    prop = cls.macros[macro_name]
                    i = list.find_by_name(elt_name)
                    if i is not None:
                        val = self._get_value_from_element(i, prop)
                        # Ok we got our value :)
                        break
            return val
        return ''


    # Get Fri 15 May 11:42:39 CEST 2009
    def _get_long_date_time(self):
        return time.strftime("%a %d %b %H:%M:%S %Z %Y").decode('UTF-8', 'ignore')


    # Get 10-13-2000 00:30:28
    def _get_short_date_time(self):
        return time.strftime("%d-%m-%Y %H:%M:%S")


    # Get 10-13-2000
    def _get_date(self):
        return time.strftime("%d-%m-%Y")


    # Get 00:30:28
    def _get_time(self):
        return time.strftime("%H:%M:%S")


    # Get epoch time
    def _get_timet(self):
        return str(int(time.time()))

    def _get_total_hosts_up(self):
        return len([h for h in self.hosts if h.state == 'UP'])

    def _get_total_hosts_down(self):
        return len([h for h in self.hosts if h.state == 'DOWN'])

    def _get_total_hosts_unreachable(self):
        return len([h for h in self.hosts if h.state == 'UNREACHABLE'])

    # TODO
    def _get_total_hosts_unreachable_unhandled(self):
        return 0

    def _get_total_hosts_problems(self):
        return len([h for h in self.hosts if h.is_problem])

    def _get_total_hosts_problems_unhandled(self):
        return 0

    def _get_total_service_ok(self):
        return len([s for s in self.services if s.state == 'OK'])

    def _get_total_services_warning(self):
        return len([s for s in self.services if s.state == 'WARNING'])

    def _get_total_services_critical(self):
        return len([s for s in self.services if s.state == 'CRITICAL'])

    def _get_total_services_unknown(self):
        return len([s for s in self.services if s.state == 'UNKNOWN'])

    # TODO
    def _get_total_services_warning_unhandled(self):
        return 0

    def _get_total_services_critical_unhandled(self):
        return 0

    def _get_total_services_unknown_unhandled(self):
        return 0

    def _get_total_service_problems(self):
        return len([s for s in self.services if s.is_problem])

    def _get_total_service_problems_unhandled(self):
        return 0

    def _get_process_start_time(self):
        return 0

    def _get_events_start_time(self):
        return 0
