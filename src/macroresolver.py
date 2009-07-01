import re
from borg import Borg
from singleton import Singleton
#from host import Host

from contact import Contact


class MacroResolver(Borg):
#    __metaclass__ = Singleton

    macros = {
        'TOTALHOSTSUP' : '',
        'TOTALHOSTSDOWN' : '',
        'TOTALHOSTSUNREACHABLE' : '',
        'TOTALHOSTSDOWNUNHANDLED' : '',
        'TOTALHOSTSUNREACHABLEUNHANDLED' : '',
        'TOTALHOSTPROBLEMS' : '',
        'TOTALHOSTPROBLEMSUNHANDLED' : '',
        'TOTALSERVICESOK' : '',
        'TOTALSERVICESWARNING' : '',
        'TOTALSERVICESCRITICAL' : '',
        'TOTALSERVICESUNKNOWN' : '',
        'TOTALSERVICESWARNINGUNHANDLED' : '',
        'TOTALSERVICESCRITICALUNHANDLED' : '',
        'TOTALSERVICESUNKNOWNUNHANDLED' : '',
        'TOTALSERVICEPROBLEMS' : '',
        'TOTALSERVICEPROBLEMSUNHANDLED' : '',
        
        'LONGDATETIME' : '',
        'SHORTDATETIME' : '',
        'DATE' : '',
        'TIME' : '',
        'TIMET' : '',
        
        'PROCESSSTARTTIME' : '',
        'EVENTSTARTTIME' : '',

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
            #print elt
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
    

    def resolve_command(self, com, h, s, c):
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
                for elt in [h, s, c]:
                    if type(elt) == macros[macro]['class']:
                        prop = macros[macro]['class'].macros[macro]
                        macros[macro]['val'] = self.get_value_from_element(elt, prop)
        #print "New resolved macros", macros
        for macro in macros:
            #print "Changing", '$'+macro+'$', "by", macros[macro]['val']
            c_line = c_line.replace('$'+macro+'$', macros[macro]['val'])
        #print "Final command:", c_line
        return c_line
        
        
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
            for cls in [Host, Service, Contact]:
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

