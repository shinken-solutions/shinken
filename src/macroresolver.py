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


#This class revolv Macro in commands by looking at the macros list
#in Class of elements. It give a propertie that call be callable or not.
#It not callable, it's a simple properties and remplace the macro with the value
#If callable, it's a method that is call for getting the value. for exemple, to 
#get the number of service in a host, you call a method to get the
# len(host.services)

import re
from borg import Borg
#from singleton import Singleton
import time
#from contact import Contact


class MacroResolver(Borg):
    #Global macros
    macros = {
        'TOTALHOSTSUP' : 'get_total_hosts_up',
        'TOTALHOSTSDOWN' : 'get_total_hosts_down',
        'TOTALHOSTSUNREACHABLE' : 'get_total_hosts_unreacheable',
        'TOTALHOSTSDOWNUNHANDLED' : 'get_total_hosts_unhandled',
        'TOTALHOSTSUNREACHABLEUNHANDLED' : 'get_total_hosts_unreacheable_unhandled',
        'TOTALHOSTPROBLEMS' : 'get_total_host_problems',
        'TOTALHOSTPROBLEMSUNHANDLED' : 'get_total_host_problems_unhandled',
        'TOTALSERVICESOK' : 'get_total_service_ok',
        'TOTALSERVICESWARNING' : 'get_total_services_warning',
        'TOTALSERVICESCRITICAL' : 'get_total_services_critical',
        'TOTALSERVICESUNKNOWN' : 'get_total_services_unknown',
        'TOTALSERVICESWARNINGUNHANDLED' : 'get_total_services_warning_unhandled',
        'TOTALSERVICESCRITICALUNHANDLED' : 'get_total_services_critical_unhandled',
        'TOTALSERVICESUNKNOWNUNHANDLED' : 'get_total_services_unknown_unhandled',
        'TOTALSERVICEPROBLEMS' : 'get_total_service_problems',
        'TOTALSERVICEPROBLEMSUNHANDLED' : 'get_total_service_problems_unhandled',
        
        'LONGDATETIME' : 'get_long_date_time',
        'SHORTDATETIME' : 'get_short_date_time',
        'DATE' : 'get_date',
        'TIME' : 'get_time',
        'TIMET' : 'get_timet',
        
        'PROCESSSTARTTIME' : 'get_process_start_time',
        'EVENTSTARTTIME' : 'get_events_start_time',

        }


    #This shall be call ONE TIME. It just put links for elements
    #by scheduler
    def init(self, conf):
        self.hosts = conf.hosts
        self.services = conf.services
        self.contacts = conf.contacts
        self.hostgroups = conf.hostgroups
        self.commands = conf.commands
        self.servicegroups = conf.servicegroups
        self.contactgroups = conf.contactgroups


    #Return all macros of a string, so cut the $
    #And create a dict with it:
    #val : value, not set here
    #type : type of macro, like class one, or ARGN one
    def get_macros(self, s):
        p = re.compile(r'(\$)')
        elts = p.split(s)
        macros = {}
        in_macro = False
        for elt in elts:
            if elt == '$':
                in_macro = not in_macro
            elif in_macro:
                macros[elt] = {'val' : '', 'type' : 'unknown'}
        return macros
                

    #Get a value from a propertie of a element
    #Prop can ba a function or a propertie
    #So we call it or no
    def get_value_from_element(self, elt, prop):
        try:
            value = getattr(elt, prop)
            if callable(value):
                return  value()
            else:
                return value
        except AttributeError as exp:
            return str(exp)


    #Resolve a command with macro by looking at data classes.macros
    #And get macro from item properties.
    def resolve_command(self, com, data):
        c_line = com.command.command_line
        #Ok, we want the macros in the command line
        macros = self.get_macros(c_line)
        #Now we prepare the classes for looking at the class.macros
        data.append(self) #For getting global MACROS
        clss = [d.__class__ for d in data]
        #Put in the macros the type of macro for all macros
        self.get_type_of_macro(macros, clss)
        #Now we get values from elements
        for macro in macros:
            #If type ARGN, look at ARGN cutting
            if macros[macro]['type'] == 'ARGN':
                macros[macro]['val'] = self.resolve_argn(macro, com.args)
                macros[macro]['type'] = 'resolved'
            #If class, get value from properties
            if macros[macro]['type'] == 'class':
                cls = macros[macro]['class']
                for elt in data:
                    if elt is not None and elt.__class__ == cls:
                        prop = cls.macros[macro]
                        macros[macro]['val'] = self.get_value_from_element(elt, prop)
        #We resolved all we can, now replace the macro in the command call
        for macro in macros:
            c_line = c_line.replace('$'+macro+'$', macros[macro]['val'])
        return c_line


    #For all Macros in macros, set the type by looking at the
    #MACRO name (ARGN? -> argn_type,
    #HOSTBLABLA -> class one and set Host in class)
    def get_type_of_macro(self, macros, clss):
        for macro in macros:
            if re.match('ARG\d', macro):
                macros[macro]['type'] = 'ARGN'
                continue
            elif re.match('USER\d', macro):
                macros[macro]['type'] = 'USERN'
                continue
            for cls in clss:
                if macro in cls.macros:
                    macros[macro]['type'] = 'class'
                    macros[macro]['class'] = cls


    #Resolv MACROS for the ARGN
    def resolve_argn(self, macro, args):
        #first, get number of arg
        id = None
        r = re.search('ARG(?P<id>\d+)', macro)
        if r is not None:
            id = int(r.group('id')) - 1
            try:
                return args[id]
            except IndexError:
                return ''


    #Get Fri 15 May 11:42:39 CEST 2009
    def get_long_date_time(self):
        return time.strftime("%a %d %b %H:%M:%S %Z %Y", time.localtime())


    #Get 10-13-2000 00:30:28
    def get_short_date_time(self):
        return time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())


    #Get 10-13-2000
    def get_date(self):
        return time.strftime("%d-%m-%Y", time.localtime())


    #Get 00:30:28
    def get_time(self):
        return time.strftime("%H:%M:%S", time.localtime())


    #Get epoch time
    def get_timet(self):
        return str(int(time.time()))
