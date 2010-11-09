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


from item import Item, Items
from util import to_split, to_bool, strip_and_uniq

class Contact(Item):
    id = 1#0 is always special in database, so we do not take risk here
    my_type = 'contact'

    properties={
        'contact_name' : {'required' : True, 'fill_brok' : ['full_status']},
        'alias' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'contactgroups' : {'required' : False, 'default' : '', 'fill_brok' : ['full_status']},
        'host_notifications_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'service_notifications_enabled' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'host_notification_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'service_notification_period' : {'required' : True, 'fill_brok' : ['full_status']},
        'host_notification_options' : {'required' : True, 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'service_notification_options' : {'required' : True, 'pythonize' : to_split, 'fill_brok' : ['full_status']},
        'host_notification_commands' : {'required' : True, 'fill_brok' : ['full_status']},
        'service_notification_commands' : {'required' : True, 'fill_brok' : ['full_status']},
        'email' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'pager' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address1' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address2' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address3' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address4' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address5' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'address6' : {'required' : False, 'default' : 'none', 'fill_brok' : ['full_status']},
        'can_submit_commands' : {'required' : False, 'default' : '0', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'retain_status_information' : {'required' : False, 'default' : '1', 'pythonize' : to_bool, 'fill_brok' : ['full_status']},
        'notificationways' : {'required' : False, 'default' : ''},
        }

    running_properties = {
        #All errors and warning raised during the configuration parsing
        #and taht will raised real warning/errors during the is_correct
        'configuration_warnings' : {'default' : []},
        'configuration_errors' : {'default' : []},
        }


    macros = {
        'CONTACTNAME' : 'contact_name',
        'CONTACTALIAS' : 'alias',
        'CONTACTEMAIL' : 'email',
        'CONTACTPAGER' : 'pager',
        'CONTACTADDRESS1' : 'address1',
        'CONTACTADDRESS2' : 'address2',
        'CONTACTADDRESS3' : 'address3',
        'CONTACTADDRESS4' : 'address4',
        'CONTACTADDRESS5' : 'address5',
        'CONTACTADDRESS6' : 'address6',
        'CONTACTGROUPNAME' : 'get_groupname',
        'CONTACTGROUPNAMES' : 'get_groupnames'
        }


    #For debugging purpose only (nice name)
    def get_name(self):
        return self.contact_name


    #Search for notification_options with state and if t is
    #in service_notification_period
    def want_service_notification(self, t, state, type):
        if not self.service_notifications_enabled:
            return False

        #Now the rest is for sub notificationways. If one is OK, we are ok
        for nw in self.notificationways:
            nw_b = nw.want_service_notification(t, state, type)
            if nw_b:
                return True

        #Oh... no one is ok for it? so no, sorry
        return False


    #Search for notification_options with state and if t is in
    #host_notification_period
    def want_host_notification(self, t, state, type):
        if not self.host_notifications_enabled:
            return False

        #Now it's all for sub notificationways. If one is OK, we are OK
        for nw in self.notificationways:
            nw_b = nw.want_host_notification(t, state, type)
            if nw_b:
                return True

        #Oh, nobody..so NO :)
        return False


    #Useless function from now
    def clean(self):
        pass


    #Call to get our commands to launch a Notification
    def get_notification_commands(self, type):
        r = []
        #service_notification_commands for service
        notif_commands_prop = type+'_notification_commands'
        for nw in self.notificationways:
            r.extend(getattr(nw, notif_commands_prop))
        return r



    #Check is required prop are set:
    #contacts OR contactgroups is need
    def is_correct(self):
        state = True #guilty or not? :)
        cls = self.__class__

        #All of the above are checks in the notificationways part
        special_properties = ['service_notification_commands', 'service_notification_commands', \
                                  'service_notification_period', 'host_notification_period', \
                                  'service_notification_options', 'host_notification_options', \
                                  'host_notification_commands', 'contact_name']

        for prop in cls.properties:
            if prop not in special_properties:
                if not hasattr(self, prop) and cls.properties[prop]['required']:
                    print self.get_name(), " : I do not have", prop
                    state = False #Bad boy...

        #There is a case where there is no nw : when there is not special_prop defined
        #at all!!
        if self.notificationways == []:
            for p in special_properties:
                print self.get_name()," : I'm missing the property %s" % p
                state = False

        if hasattr(self, 'contact_name'):
            for c in cls.illegal_object_name_chars:
                if c in self.contact_name:
                    Log().log("%s : My contact_name got the caracter %s that is not allowed." % (self.get_name(), c))
                    state = False
	else:
	    if hasattr(self, 'alias'): #take the alias if we miss the contact_name
		self.contact_name = self.alias
        return state




class Contacts(Items):
    name_property = "contact_name"
    inner_class = Contact

    def linkify(self, timeperiods, commands, notificationways):
        self.linkify_with_timeperiods(timeperiods, 'service_notification_period')
        self.linkify_with_timeperiods(timeperiods, 'host_notification_period')
        self.linkify_command_list_with_commands(commands, 'service_notification_commands')
        self.linkify_command_list_with_commands(commands, 'host_notification_commands')
        self.linkify_with_notificationways(notificationways)

    #We've got a notificationways property with , separated contacts names
    #and we want have a list of NotificationWay
    def linkify_with_notificationways(self, notificationways):
        for i in self:
            if hasattr(i, 'notificationways'):
                notificationways_tab = i.notificationways.split(',')
                notificationways_tab = strip_and_uniq(notificationways_tab)
                new_notificationways = []
                for nw_name in notificationways_tab:
                    nw = notificationways.find_by_name(nw_name)
                    if nw != None:
                        new_notificationways.append(nw)
                    else: #TODO: What?
                        pass
                #Get the list, but first make elements uniq
                i.notificationways = list(set(new_notificationways))



    #We look for contacts property in contacts and
    def explode(self, contactgroups, notificationways):
        #Contactgroups property need to be fullfill for got the informations
        self.apply_partial_inheritance('contactgroups')

        #Register ourself into the contactsgroups we are in
        for c in self:
            if not c.is_tpl():
		if hasattr(c, 'contact_name'):
                	cname = c.contact_name
                	if hasattr(c, 'contactgroups'):
                    		cgs = c.contactgroups.split(',')
                    		for cg in cgs:
                        		contactgroups.add_member(cname, cg.strip())

        #Now create a notification way with the simple parameter of the
        #contacts
        simple_way_parameters = ['service_notification_period', 'host_notification_period', \
                                     'service_notification_options', 'host_notification_options', \
                                     'service_notification_commands', 'host_notification_commands']
        for c in self:
            if not c.is_tpl():
                need_notificationway = False
                params = {}
                for p in simple_way_parameters:
                    if hasattr(c, p):
                        need_notificationway = True
                        params[p] = getattr(c, p)

                if need_notificationway:
                    #print "Create notif way with", params
                    if hasattr(c, 'contact_name'):
                        cname = c.contact_name
                    else: #Will be change with an unique id, but will be an error in the end
			if hasattr(c, 'alias'):
				cname = c.alias
			else:
                        	cname = ''
                    nw_name = cname+'_inner_notificationway'
                    notificationways.new_inner_member(nw_name, params)

                    if not hasattr(c, 'notificationways'):
                        c.notificationways = nw_name
                    else:
                        c.notificationways = c.notificationways + ',' +nw_name


