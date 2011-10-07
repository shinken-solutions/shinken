#!/usr/bin/python
#Copyright (C) 2011 Durieux David, d.durieux@siprossii.com
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


#This Class is a plugin for the Shinken Arbiter. It connect to
#a GLPI with webservice (xmlrpc, SOAP is garbage) and take all
#hosts. Simple way from now


import xmlrpclib

from shinken.basemodule import BaseModule


properties = {
    'daemons' : ['arbiter'],
    'type' : 'glpi',
    'external' : False,
    'phases' : ['configuration'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Simple GLPI arbiter for plugin %s" % plugin.get_name()
    uri = plugin.uri
    login_name = plugin.login_name
    login_password = plugin.login_password
    instance = Glpi_arbiter(plugin, uri, login_name, login_password)
    return instance



#Just get hostname from a GLPI webservices
class Glpi_arbiter(BaseModule):
    def __init__(self, mod_conf, uri, login_name, login_password):
        BaseModule.__init__(self, mod_conf)
        self.uri = uri
        self.login_name = login_name
        self.login_password = login_password

    #Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "I open the GLPI connection to %s" % self.uri
        self.con = xmlrpclib.ServerProxy(self.uri)
        print "Connection opened"
        print "Authentification in progress"
        arg = {'login_name' : self.login_name , 'login_password' : self.login_password}
        res = self.con.glpi.doLogin(arg)
        self.session = res['session']
        print "My session number", self.session


    #Ok, main function that will load config from GLPI
    def get_objects(self):
        r = {'commands' : [],
             'timeperiods' : [],
             'hosts' : [],
             'services' : [],
             'contacts' : []}
        arg = {'session' : self.session}

        # Get commands
        all_commands = self.con.monitoring.shinkenCommands(arg)
        print "Get all commands", all_commands
        for command_info in all_commands:
            print "\n\n"
            print "Command info in GLPI", command_info
            h = {'command_name' : command_info['command_name'],
                 'command_line' : command_info['command_line'],
                 }
            r['commands'].append(h)

        # Get timeperiods
        all_timeperiods = self.con.monitoring.shinkenTimeperiods(arg)
        print "Get all timeperiods", all_timeperiods
        for timeperiod_info in all_timeperiods:
            print "\n\n"
            print "Timeperiod info in GLPI", timeperiod_info
            h = {'timeperiod_name' : timeperiod_info['timeperiod_name']};

            if timeperiod_info['sunday']:
                h['sunday'] = timeperiod_info['sunday']

            if timeperiod_info['monday']:
                h['monday'] = timeperiod_info['monday']

            if timeperiod_info['tuesday']:
                h['tuesday'] = timeperiod_info['tuesday']

            if timeperiod_info['wednesday']:
                h['wednesday'] = timeperiod_info['wednesday']

            if timeperiod_info['thursday']:
                h['thursday'] = timeperiod_info['thursday']

            if timeperiod_info['friday']:
                h['friday'] = timeperiod_info['friday']

            if timeperiod_info['saturday']:
                h['saturday'] = timeperiod_info['saturday']

            r['timeperiods'].append(h)

        # Get hosts
        all_hosts = self.con.monitoring.shinkenHosts(arg)
        print "Get all hosts", all_hosts
        for host_info in all_hosts:
            print "\n\n"
            print "Host info in GLPI", host_info
            h = {'host_name' : host_info['host_name'],
                 'alias' : host_info['alias'],
                 'address' : host_info['address'],
                 'parents' : host_info['parents'],
                 'check_command' : host_info['check_command'],
                 'check_interval' : host_info['check_interval'],
                 'retry_interval' : host_info['retry_interval'],
                 'max_check_attempts' : host_info['max_check_attempts'],
                 'check_period' : host_info['check_period'],
                 'contacts' : host_info['contacts'],
                 'process_perf_data' : host_info['process_perf_data'],
                 'notification_interval' : host_info['notification_interval'],
                 'notification_period' : host_info['notification_period'],
                 'notification_options' : host_info['notification_options']};
            r['hosts'].append(h)

        # Get services
        all_services = self.con.monitoring.shinkenServices(arg)
        print "Get all services", all_services
        for service_info in all_services:
            print "\n\n"
            print "Service info in GLPI", service_info
            h = {'host_name' : service_info['host_name'],
                 'service_description' : service_info['service_description']};
            if service_info['check_command']:
                h['check_command'] = service_info['check_command']

            if service_info['check_interval']:
                h['check_interval'] = service_info['check_interval']

            if service_info['retry_interval']:
                h['retry_interval'] = service_info['retry_interval']

            if service_info['max_check_attempts']:
                h['max_check_attempts'] = service_info['max_check_attempts']

            if service_info['check_period']:
                h['check_period'] = service_info['check_period']

            if service_info['contacts']:
                h['contacts'] = service_info['contacts']

            if service_info['notification_interval']:
                h['notification_interval'] = service_info['notification_interval']

            if service_info['notification_period']:
                h['notification_period'] = service_info['notification_period']

            if service_info['notification_options']:
                h['notification_options'] = service_info['notification_options']

            if service_info['active_checks_enabled']:
                h['active_checks_enabled'] = service_info['active_checks_enabled']

            if service_info['process_perf_data']:
                h['process_perf_data'] = service_info['process_perf_data']

            if service_info['active_checks_enabled']:
                h['active_checks_enabled'] = service_info['active_checks_enabled']

            if service_info['passive_checks_enabled']:
                h['passive_checks_enabled'] = service_info['passive_checks_enabled']

            if service_info['parallelize_check']:
                h['parallelize_check'] = service_info['parallelize_check']

            if service_info['obsess_over_service']:
                h['obsess_over_service'] = service_info['obsess_over_service']

            if service_info['check_freshness']:
                h['check_freshness'] = service_info['check_freshness']

            if service_info['freshness_threshold']:
                h['freshness_threshold'] = service_info['freshness_threshold']

            if service_info['notifications_enabled']:
                h['notifications_enabled'] = service_info['notifications_enabled']

            if service_info['event_handler_enabled']:
                h['event_handler_enabled'] = service_info['event_handler_enabled']

            if service_info['event_handler']:
                h['event_handler'] = service_info['event_handler']

            if service_info['flap_detection_enabled']:
                h['flap_detection_enabled'] = service_info['flap_detection_enabled']

            if service_info['failure_prediction_enabled']:
                h['failure_prediction_enabled'] = service_info['failure_prediction_enabled']

            if service_info['retain_status_information']:
                h['retain_status_information'] = service_info['retain_status_information']

            if service_info['retain_nonstatus_information']:
                h['retain_nonstatus_information'] = service_info['retain_nonstatus_information']

            if service_info['is_volatile']:
                h['is_volatile'] = service_info['is_volatile']

            if service_info['_httpstink']:
                h['_httpstink'] = service_info['_httpstink']

            print "Service TEST : ", h
            r['services'].append(h)

        # Get contacts
        all_contacts = self.con.monitoring.shinkenContacts(arg)
        print "Get all contacts", all_contacts
        for contact_info in all_contacts:
            print "\n\n"
            print "Contact info in GLPI", contact_info
            h = {'contact_name' : contact_info['contact_name'],
                 'alias' : contact_info['alias'],
                 'host_notifications_enabled' : contact_info['host_notifications_enabled'],
                 'service_notifications_enabled' : contact_info['service_notifications_enabled'],
                 'service_notification_period' : contact_info['service_notification_period'],
                 'host_notification_period' : contact_info['host_notification_period'],
                 'service_notification_options' : contact_info['service_notification_options'],
                 'host_notification_options' : contact_info['host_notification_options'],
                 'service_notification_commands' : contact_info['service_notification_commands'],
                 'host_notification_commands' : contact_info['host_notification_commands'],
                 'email' : contact_info['email'],
                 'pager' : contact_info['pager'],
                 }
            r['contacts'].append(h)

        #print "Returning to Arbiter the hosts:", r
        return r
