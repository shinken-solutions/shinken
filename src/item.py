from command import CommandCall
from util import to_int, to_char, to_split, to_bool

class Item(object):
    def __init__(self, params={}):
        self.id = self.__class__.id
        self.__class__.id += 1
        
        self.customs = {} # for custom variables
        self.plus = {} # for value with a +

        #adding running properties like latency
        for prop in self.__class__.running_properties:
            setattr(self, prop, self.__class__.running_properties[prop])

        #[0] = +  -> new key-plus
        #[0] = _  -> new custom entry
        for key in params:
            if params[key][0] == '+':
                self.plus[key] = params[key][1:] # we remove the +
            elif key[0] == "_":
                self.customs[key] = params[key]
            else:
                setattr(self, key, params[key])

    
    def __str__(self):
        return str(self.__dict__)+'\n'


    def is_tpl(self):
        try:
            return self.register == '0'
        except:
            return False


    def has(self, prop):
        return hasattr(self, prop)


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        properties = self.__class__.properties
        for prop in properties:
            if not self.has(prop) and not properties[prop]['required']:
                value = properties[prop]['default']
                setattr(self, prop, value)

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
                print exp


    def get_templates(self):
        if self.has('use'):
            return self.use.split(',')
        else:
            return []


    #We fillfull properties with template ones if need
    def get_property_by_inheritance(self, items, prop):
        if self.has(prop):
            value = getattr(self, prop)
            if self.has_plus(prop):#Manage the additive inheritance for the property, if property is in plus, add or replace it
                value = value+','+self.get_plus_and_delete(prop)
            return value
        tpls = self.get_templates()
        for tpl in tpls:
            i = items.find_tpl_by_name(tpl)
            if i is not None:
                value = i.get_property_by_inheritance(items, prop)
                if value is not None:
                    if self.has_plus(prop):
                        value = value+','+self.get_plus_and_delete(prop)
                    setattr(self, prop, value)
                    return value
        if self.has_plus(prop):
            value = self.get_plus_and_delete(prop)
            setattr(self, prop, value)
            return value
        return None

    
    #We fillfull properties with template ones if need
    def get_customs_properties_by_inheritance(self, items):
        cv = {} # custom variables dict
        tpls = self.get_templates()
        for tpl in tpls:
            i = items.find_tpl_by_name(tpl)
            if i is not None:
                tpl_cv = i.get_customs_properties_by_inheritance(items)
                if tpl_cv is not {}:
                    for prop in tpl_cv:
                        if prop not in self.customs:
                            value = tpl_cv[prop]
                        else:
                            value = self.customs[prop]
                        if self.has_plus(prop):
                            value = value+self.get_plus_and_delete(prop)
                        self.customs[prop]=value
        for prop in self.customs:
            value = self.customs[prop]
            if self.has_plus(prop):
                value = value = value+','+self.get_plus_and_delete(prop)
                self.customs[prop] = value
        #We can get custom properties in plus, we need to get all entires and put
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
        if self.is_tpl:
            return True
        properties = self.__class__.properties
        for prop in properties:
            if not self.has(prop) and properties[prop]['required']:
                return False
        return True


class Items(object):
    def __init__(self, items):
        self.items = {}
        for i in items:
            self.items[i.id] = i

    
    def find_id_by_name(self, name):
        for id in self.items:
            name_property = self.__class__.name_property
            if self.items[id].has(name_property) and getattr(self.items[id], name_property) == name:
                return id
        return None


    def find_by_name(self, name):
        id = self.find_id_by_name(name)
        if id is not None:
            return self.items[id]
        else:
            return None


#    def linkify(self, timeperiods, commands):
#        self.linkify_c_by_tp(timeperiods)
#        self.linkify_c_by_cmd(commands)


    def pythonize(self):
        for id in self.items:
            self.items[id].pythonize()


    def find_tpl_by_name(self, name):
        for id in self.items:
            i = self.items[id]
            if i.is_tpl() and i.name == name:
                return i
        return None


    def is_correct(self):
        for id in self.items:
            i = self.items[id]
            i.is_correct()


    #We remove useless properties
    def clean_useless(self):
        #First templates
        tpls = [id for id in self.items if self.items[id].is_tpl()]
        for id in tpls:
            del self.items[id]

    
#    #We just search for each timeperiod the id of the tp
#    #and replace the name by the id
#    def linkify_c_by_tp(self, timeperiods):
#        for id in self.contacts:
#            c = self.contacts[id]
#            #service notif period
#            sntp_name = c.service_notification_period
#            #host notf period
#            hntp_name = c.host_notification_period
#
#            #The new member list, in id
#            sntp = timeperiods.find_tp_by_name(sntp_name)
#            hntp = timeperiods.find_tp_by_name(hntp_name)
#            
#            c.service_notification_period = sntp
#            c.host_notification_period = hntp


#    #Simplify hosts commands by commands id
#    def linkify_c_by_cmd(self, commands):
#        for id in self.contacts:
#            tmp = []
#            for cmd in self.contacts[id].service_notification_commands:
#                tmp.append(CommandCall(commands,cmd))
#            self.contacts[id].service_notification_commands = tmp
#
#            tmp = []
#            for cmd in self.contacts[id].host_notification_commands:
#                tmp.append(CommandCall(commands,cmd))
#            self.contacts[id].host_notification_commands = tmp


    #If a prop is absent and is not required, put the default value
    def fill_default(self):
        for id in self.items:
            i = self.items[id]
            i.fill_default()

    
    def __str__(self):
        s = ''
        for id in self.items:
            cls = self.items[id].__class__
            s = s + str(cls) + ':' + str(id) + str(self.items[id]) + '\n'
        return s


    #Inheritance forjust a property
    def apply_partial_inheritance(self, prop):
        for id in self.items:
            i = self.items[id]
            i.get_property_by_inheritance(self, prop)


    def apply_inheritance(self):
        #We check for all Host properties if the host has it
        #if not, it check all host templates for a value
        cls = self.inner_class#items[0].__class__
        properties = cls.properties
        for prop in properties:
            self.apply_partial_inheritance(prop)
        for id in self.items:
            i = self.items[id]
            i.get_customs_properties_by_inheritance(self)


#    #We look for contacts property in contacts and
#    def explode(self, contactgroups):
#        #Hostgroups property need to be fullfill for got the informations
#        self.apply_partial_inheritance('contactgroups')
#        for id in self.contacts:
#            c = self.contacts[id]
#            if not c.is_tpl():
#                cname = c.contact_name
#                if c.has('contactgroups'):
#                    cgs = c.contactgroups.split(',')
#                    for cg in cgs:
#                        contactgroups.add_member(cname, cg.strip())
#        #TODO: clean all hostgroups property in hosts
