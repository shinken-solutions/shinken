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


# This Class is a plugin for the Shinken Arbiter. It connect to
# a GLPI with webservice (xmlrpc, SOAP is garbage) and take all
# hosts. Simple way from now

import xmlrpclib

from shinken.basemodule import BaseModule

properties = {
    'daemons': ['arbiter'],
    'type': 'glpi',
    'external': False,
    'phases': ['configuration'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Simple GLPI arbiter for plugin %s" % plugin.get_name()
    uri = plugin.uri
    login_name = plugin.login_name
    login_password = plugin.login_password
    tag = getattr(plugin, 'tag', "")
    instance = Glpi_arbiter(plugin, uri, login_name, login_password, tag)
    return instance


# Just get hostname from a GLPI webservices
class Glpi_arbiter(BaseModule):
    def __init__(self, mod_conf, uri, login_name, login_password, tag):
        BaseModule.__init__(self, mod_conf)
        self.uri = uri
        self.login_name = login_name
        self.login_password = login_password
        self.tag = tag

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "I open the GLPI connection to %s" % self.uri
        self.con = xmlrpclib.ServerProxy(self.uri)
        print "Connection opened"
        print "Authentification in progress"
        arg = {'login_name': self.login_name, 'login_password': self.login_password}
        res = self.con.glpi.doLogin(arg)
        self.session = res['session']
        print "My session number", self.session

    # Ok, main function that will load config from GLPI
    def get_objects(self):
        r = {'commands': [],
             'timeperiods': [],
             'hosts': [],
             'services': [],
             'contacts': []}
        arg = {'session': self.session,
               'tag': self.tag}

        # Get commands
        all_commands = self.con.monitoring.shinkenCommands(arg)
        print "Get all commands", all_commands
        for command_info in all_commands:
            print "\n\n"
            print "Command info in GLPI", command_info
            h = {'command_name': command_info['command_name'],
                 'command_line': command_info['command_line'],
                 }
            r['commands'].append(h)

        # Get timeperiods
        all_timeperiods = self.con.monitoring.shinkenTimeperiods(arg)
        print "Get all timeperiods", all_timeperiods
        attributs = ['timeperiod_name', 'alias', 'sunday',
                     'monday', 'tuesday', 'wednesday',
                     'thursday', 'friday', 'saturday']
        for timeperiod_info in all_timeperiods:
            print "\n\n"
            print "Timeperiod info in GLPI", timeperiod_info
            h = {}
            for attribut in attributs:
                if attribut in timeperiod_info:
                    h[attribut] = timeperiod_info[attribut]

            #print "\nReturning to Arbiter the timeperiods:", h
            r['timeperiods'].append(h)

        # Get hosts
        all_hosts = self.con.monitoring.shinkenHosts(arg)
        print "Get all hosts", all_hosts
        attributs = ['display_name', 'hostgroups', 'initial_state',
                     'active_checks_enabled', 'passive_checks_enabled', 'obsess_over_host',
                     'check_freshness', 'freshness_threshold', 'event_handler',
                     'event_handler_enabled', 'low_flap_threshold ', 'high_flap_threshold',
                     'flap_detection_enabled', 'flap_detection_options', 'retain_status_information',
                     'retain_nonstatus_information', 'contact_groups', 'first_notification_delay',
                     'notifications_enabled', 'stalking_options', 'notes',
                     'notes_url', 'action_url', 'icon_image',
                     'icon_image_alt', 'vrml_image', 'statusmap_image',
                     '2d_coords', '3d_coords', 'realm',
                     'poller_tag', 'business_impact']
        for host_info in all_hosts:
            print "\n\n"
            print "Host info in GLPI", host_info
            h = {'host_name': host_info['host_name'],
                 'alias': host_info['alias'],
                 'address': host_info['address'],
                 'parents': host_info['parents'],
                 'check_command': host_info['check_command'],
                 'check_interval': host_info['check_interval'],
                 'retry_interval': host_info['retry_interval'],
                 'max_check_attempts': host_info['max_check_attempts'],
                 'check_period': host_info['check_period'],
                 'contacts': host_info['contacts'],
                 'process_perf_data': host_info['process_perf_data'],
                 'notification_interval': host_info['notification_interval'],
                 'notification_period': host_info['notification_period'],
                 'notification_options': host_info['notification_options']}
            for attribut in attributs:
                if attribut in host_info:
                    h[attribut] = host_info[attribut]
            r['hosts'].append(h)

        # Get templates
        all_templates = self.con.monitoring.shinkenTemplates(arg)
        print "Get all templates", all_templates
        attributs = ['name', 'check_interval', 'retry_interval',
                     'max_check_attempts', 'check_period', 'notification_interval',
                     'notification_period', 'notification_options', 'active_checks_enabled',
                     'process_perf_data', 'active_checks_enabled', 'passive_checks_enabled',
                     'parallelize_check', 'obsess_over_service', 'check_freshness',
                     'freshness_threshold', 'notifications_enabled', 'event_handler_enabled',
                     'event_handler', 'flap_detection_enabled', 'failure_prediction_enabled',
                     'retain_status_information', 'retain_nonstatus_information', 'is_volatile',
                     '_httpstink']
        for template_info in all_templates:
            print "\n\n"
            print "Template info in GLPI", template_info
            h = {'register': '0'}
            for attribut in attributs:
                if attribut in template_info:
                    h[attribut] = template_info[attribut]

            r['services'].append(h)

        # Get services
        all_services = self.con.monitoring.shinkenServices(arg)
        print "Get all services", all_services
        attributs = ['host_name', 'hostgroup_name', 'service_description',
                     'use', 'check_command', 'check_interval', 'retry_interval',
                     'max_check_attempts', 'check_period', 'contacts',
                     'notification_interval', 'notification_period', 'notification_options',
                     'active_checks_enabled', 'process_perf_data',
                     'passive_checks_enabled', 'parallelize_check', 'obsess_over_service',
                     'check_freshness', 'freshness_threshold', 'notifications_enabled',
                     'event_handler_enabled', 'event_handler', 'flap_detection_enabled',
                     'failure_prediction_enabled', 'retain_status_information', 'retain_nonstatus_information',
                     'is_volatile', '_httpstink',
                     'display_name', 'servicegroups', 'initial_state',
                     'low_flap_threshold', 'high_flap_threshold', 'flap_detection_options',
                     'first_notification_delay', 'notifications_enabled', 'contact_groups',
                     'stalking_options', 'notes', 'notes_url',
                     'action_url', 'icon_image', 'icon_image_alt',
                     'poller_tag', 'service_dependencies', 'business_impact']

        for service_info in all_services:
            print "\n\n"
            print "Service info in GLPI", service_info
            h = {}
            for attribut in attributs:
                if attribut in service_info:
                    h[attribut] = service_info[attribut]

            r['services'].append(h)

        # Get contacts
        all_contacts = self.con.monitoring.shinkenContacts(arg)
        print "Get all contacts", all_contacts
        for contact_info in all_contacts:
            print "\n\n"
            print "Contact info in GLPI", contact_info
            h = {'contact_name': contact_info['contact_name'],
                 'alias': contact_info['alias'],
                 'host_notifications_enabled': contact_info['host_notifications_enabled'],
                 'service_notifications_enabled': contact_info['service_notifications_enabled'],
                 'service_notification_period': contact_info['service_notification_period'],
                 'host_notification_period': contact_info['host_notification_period'],
                 'service_notification_options': contact_info['service_notification_options'],
                 'host_notification_options': contact_info['host_notification_options'],
                 'service_notification_commands': contact_info['service_notification_commands'],
                 'host_notification_commands': contact_info['host_notification_commands'],
                 'email': contact_info['email'],
                 'pager': contact_info['pager'],
                 }
            r['contacts'].append(h)

        #print "Returning to Arbiter the data:", r
        return r
