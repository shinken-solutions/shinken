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
    logger.info("[GLPI Arbiter] Get a Simple GLPI arbiter for plugin %s" % plugin.get_name())
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
        logger.info("[GLPI Arbiter] I open the GLPI connection to %s" % self.uri)
        self.con = xmlrpclib.ServerProxy(self.uri)
        logger.info("[GLPI Arbiter] Connection opened")
        logger.info("[GLPI Arbiter] Authentification in progress")
        arg = {'login_name': self.login_name, 'login_password': self.login_password}
        res = self.con.glpi.doLogin(arg)
        self.session = res['session']
        logger.info("[GLPI Arbiter] My session number %s" % str(self.session))

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
         logger.info("[GLPI Arbiter] Get all commands: %s" % str(all_commands))
         for command_info in all_commands:
            logger.info("[GLPI Arbiter] Command info in GLPI: " % str(command_info))
            h = {'command_name': command_info['command_name'],
                 'command_line': command_info['command_line'],
                 }
            r['commands'].append(h)

        # Get timeperiods
        all_timeperiods = self.con.monitoring.shinkenTimeperiods(arg)
        logger.info("[GLPI Arbiter] Get all timeperiods: %s" % str(all_timeperiods))
        attributs = ['timeperiod_name', 'alias', 'sunday',
                     'monday', 'tuesday', 'wednesday',
                     'thursday', 'friday', 'saturday']
        for timeperiod_info in all_timeperiods:
            logger.info("[GLPI Arbiter] Timeperiod info in GLPI: %s" % str(timeperiod_info))
            h = {}
            for attribut in attributs:
                if attribut in timeperiod_info:
                    h[attribut] = timeperiod_info[attribut]

            logger.debug("[GLPI Arbiter] Returning to Arbiter the timeperiods: %s " % str(h))
            r['timeperiods'].append(h)

        # Get hosts
        all_hosts = self.con.monitoring.shinkenHosts(arg)
        logger.info("[GLPI Arbiter] Get all hosts" % str(all_hosts))
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
            logger.info("[GLPI Arbiter] Host info in GLPI: %s " % str(host_info))
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
        logger.info("[GLPI Arbiter] Get all templates: %s" % str(all_templates))
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
            logger("[GLPI Arbiter] Template info in GLPI: %s" % template_info)
            h = {'register': '0'}
            for attribut in attributs:
                if attribut in template_info:
                    h[attribut] = template_info[attribut]

            r['services'].append(h)

        # Get services
        all_services = self.con.monitoring.shinkenServices(arg)
        logger.info("[GLPI Arbiter] Get all services: %s" % str(all_services))
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
            logger.info("[GLPI Arbiter] Service info in GLPI: %s" % service_info)
            h = {}
            for attribut in attributs:
                if attribut in service_info:
                    h[attribut] = service_info[attribut]

            r['services'].append(h)

        # Get contacts
        all_contacts = self.con.monitoring.shinkenContacts(arg)
         logger.info("[GLPI Arbiter] Get all contacts: %s" % str(all_contacts))
        for contact_info in all_contacts:
            logger.info("[GLPI Arbiter] Contact info in GLPI:" % contact_info)
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

        logger.debug("[GLPI Arbiter] Returning to Arbiter the data: %s" % str(r))
        return r
