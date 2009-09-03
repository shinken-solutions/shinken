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


import re
from borg import Borg
from singleton import Singleton
#from host import Host
import time
from contact import Contact


class MacroResolver(Borg):
#    __metaclass__ = Singleton

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


    def init(self, conf):
        self.hosts = conf.hosts
        self.services = conf.services
        self.contacts = conf.contacts
        self.hostgroups = conf.hostgroups
        self.commands = conf.commands
        self.servicegroups = conf.servicegroups
        self.contactgroups = conf.contactgroups


    def get_macros(self, s):
        #print "Checking Macros in", s
        p = re.compile(r'(\$)')
        elts = p.split(s)
        #print "Elts:", elts
        macros = {}
        in_macro = False
        for elt in elts:
            #print 'Debug:', elt, 'in macro?', in_macro
            if elt == '$':
                in_macro = not in_macro
            elif in_macro:
                macros[elt] = {'val' : '', 'type' : 'unknown'}
        #print "Macros", macros
        return macros
                

    def get_value_from_element(self, elt, prop):
        try:
            if callable(getattr(elt, prop)):
                f = getattr(elt, prop)
                #print "Calling ",f, "for", elt
                return  f()
            else:
                #prop = macros[macro]['class'].macros[macro]
                #print "Getting", prop, "for", elt
                return getattr(elt, prop)
        except AttributeError as exp:
            return str(exp)


    #Resolve just a line with data
    def resolve_macro(self, c_line, data):
        macros = self.get_macros(c_line)
        clss = [d.__class__ for d in data]
        self.get_type_of_macro_new(macros, clss)
        print "Got macros:", macros
        for macro in macros:
            if macros[macro]['type'] == 'class':
                #print "Search for type", macros[macro]['class']
                data.append(self)
                for elt in data:
                    if elt is not None and elt.__class__ == macros[macro]['class']:
                        prop = macros[macro]['class'].macros[macro]
                        macros[macro]['val'] = self.get_value_from_element(elt, prop)
        print "New resolved macros", macros
        for macro in macros:
            #print "Changing", '$'+macro+'$', "by", macros[macro]['val']
            c_line = c_line.replace('$'+macro+'$', macros[macro]['val'])
        #print "Final command:", c_line
        return c_line


    def resolve_command(self, com, h, s, c, n):
        #print "Trying to resolve command", com
        #print "Args", com.args
        c_line = com.command.command_line
        #print "Command line:", c_line
        macros = self.get_macros(c_line)
        self.get_type_of_macro(macros)
        #print "Got macros:", macros
        for macro in macros:
            if macros[macro]['type'] == 'ARGN':
                macros[macro]['val'] = self.resolve_argn(macro, com.args)
                macros[macro]['type'] = 'resolved'
            if macros[macro]['type'] == 'class':
                #print "Search for type", macros[macro]['class']
                for elt in [h, s, c, n, self]:
                    #print "Type etl:", type(elt), elt
                    if elt is not None and elt.__class__ == macros[macro]['class']:
                        #print "Elt is a", macros[macro]['class']
                        prop = macros[macro]['class'].macros[macro]
                        macros[macro]['val'] = self.get_value_from_element(elt, prop)
        #print "New resolved macros", macros
        for macro in macros:
            #print "Changing", '$'+macro+'$', "by", macros[macro]['val']
            c_line = c_line.replace('$'+macro+'$', macros[macro]['val'])
        #print "Final command:", c_line
        return c_line


    def get_type_of_macro_new(self, macros, clss):
        for macro in macros:
            if re.match('ARG\d', macro):
                macros[macro]['type'] = 'ARGN'
                continue
            elif re.match('USER\d', macro):
                macros[macro]['type'] = 'USERN'
                continue
            
            for cls in clss:
                if macro in cls.macros:
                    #print "Got a class macro", macro, str(cls)
                    macros[macro]['type'] = 'class'
                    macros[macro]['class'] = cls
            #elif macro['type'] = 'unknown
        
        
    def get_type_of_macro(self, macros):
        for macro in macros:
            if re.match('ARG\d', macro):
                macros[macro]['type'] = 'ARGN'
                continue
            elif re.match('USER\d', macro):
                macros[macro]['type'] = 'USERN'
                continue
            
            from service import Service
            from host import Host
            from contact import Contact
            from notification import Notification
            for cls in [Host, Service, Contact, Notification, MacroResolver]:
                if macro in cls.macros:
                    #print "Got a class macro", macro, str(cls)
                    macros[macro]['type'] = 'class'
                    macros[macro]['class'] = cls
            #elif macro['type'] = 'unknown


    def resolve_argn(self, macro, args):
        #print "Trying to resolve ARGN marco:", macro, "with", args
        #first, get number of arg
        id = None
        r = re.search('ARG(?P<id>\d+)', macro)
        if r is not None:
            id = int(r.group('id')) - 1
            #print "ID:", id
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
