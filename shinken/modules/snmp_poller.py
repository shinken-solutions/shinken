#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Thibault Cohen, thibault.cohen@savoirfairelinux.com
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


#This Class is an example of an Scheduler module
#Here for the configuration phase AND running one

import os
import re
import sys
import signal
import time
import socket
import struct
import binascii
import getopt
import shlex
import operator
import math
from datetime import datetime, timedelta
from Queue import Empty

import memcache
from configobj import ConfigObj, Section
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto.api import v2c

from shinken.log import logger
from shinken.basemodule import BaseModule
from shinken.check import Check
from shinken.macroresolver import MacroResolver


properties = {
    'daemons': ['poller', 'scheduler', 'arbiter'],
    'type': 'snmp_poller',
    'external': False,
    'phases': ['running', 'late_configuration'],
    # To be a real worker module, you must set this
    'worker_capable': True,
    }


def get_instance(mod_conf):
    """called by the plugin manager to get a poller"""
    print "Get a snmp poller module for plugin %s" % mod_conf.get_name()
    instance = Snmp_poller(mod_conf)
    return instance

def rpn_calculator(rpn_list):
    try:
        st = []
        for el in rpn_list:
            if el is None:
                continue
            if hasattr(operator, str(el)):
                y, x = st.pop(),st.pop()
                z = getattr(operator, el)(x, y)
            else:
                z = float(el)
            st.append(z)

        assert len(st) <= 1

        if len(st) == 1:
            return(st.pop())

    except Exception, e:
        print('Calc Error: ' + str(e) + str(rpn_list))
        return "Calc error"

class SNMPHost(object):
    def __init__(self, host, community, version):
        self.host = host
        self.community = community
        self.version = version
        self.frequences = {}
        self.instances = {}

    def update_service(self, service):
        if service.check_interval in self.frequences:
            # interval found
            if not service.key in self.frequences[service.check_interval].services:
                # service not found
                self.frequences[service.check_interval].services[service.key] = service
            else:
                # service found dot nothing
                pass
            # TODO search service in other interval !!!
        else:
            # Interval not found
            self.frequences[service.check_interval] = {}
            # Create new freq
            new_freq = SNMPFrequence(service.check_interval)
            new_freq.services[service.key] = service
            self.frequences[service.check_interval] = new_freq

    def find_frenquences(self, service_key):
        tmp = dict([(key, interval) for interval,f in self.frequences.items() for key in f.services.keys()])
        if service_key in tmp:
            return tmp[service_key]
        else:
            # TODO
            # Not found ???
            return None

    def get_oids_by_interval(self, interval):
        return dict([(snmpoid.oid, snmpoid) for s in self.frequences[interval].services.values() for snmpoid in s.oids.values()])

    def get_oids_for_instance_mapping(self, interval, datasource):
        base_oids = {}
        for s in self.frequences[interval].services.values():
            if hasattr(s.instance, 'find') and s.instance.startswith("map("):
                base_oid_name = s.instance[4:-1]
                if base_oid_name in datasource['MAPPING']:
                    oid = datasource['MAPPING'][base_oid_name]['base_oid']
                    base_oids[oid] = s.instance

        return base_oids

    def format_output(self, frequence, key):
        m, r = self.frequences[frequence].format_output(key)
        return m, r

    def map_instances(self, frequence):
        for s in self.frequences[frequence].services.values():
            s.map_instances(self.instances)


class SNMPFrequence(object):
    def __init__(self, frequence):
        self.frequence = frequence
        self.check_time = None
        self.old_check_time = None
        self.services = {}
        self.forced = None

    def format_output(self, key):
        return self.services[key].format_output(self.check_time, self.old_check_time)

class SNMPService(object):
    def __init__(self, service, host, triggergroup, dstemplate, instance, instance_name):
        self.host = host
        self.check_interval = service.check_interval
        self.triggergroup = triggergroup
        self.triggers = {}
        self.dstemplate = dstemplate
        self.instance = instance
        self.instance_name = instance_name
        self.oids = {}
        self.key = (dstemplate, instance, instance_name)

    def map_instances(self, instances):
        if self.instance_name in instances:
            # Set instance
            self.instance = instances[self.instance_name]
            for snmpoid in self.oids.values():
                snmpoid.oid = re.sub("map\(.*\)", self.instance, snmpoid.oid)
            return True
        return False

    def format_output(self, check_time, old_check_time):
        for snmpoid in self.oids.values():
            snmpoid.format_output(check_time, old_check_time)

        # Get return code
        rc = self.get_trigger_result()
        # Get perf
        perf = " ".join([snmpoid.perf for snmpoid in self.oids.values() if snmpoid.perf])
        # Get output
        out = " - ".join([snmpoid.out for snmpoid in self.oids.values() if snmpoid.out])
        # Get name
        if self.instance_name:
            name = self.instance_name
        elif self.instance:
            name = self.instance
        else:
            name = self.dstemplate
        
        if not perf: 
            message = "%s: %s" % (name, out)
        else:
            message = "%s: %s" % (name, out)
            message = "%s | %s" % (message, perf)

        return message, rc

    def get_trigger_result(self):
        errors = {'critical': 2,
                  'warning' : 1,
                  'ok'      : 0}

        try:
            for error_name in ['critical', 'warning']:
                error_code = errors[error_name]
                for trigger_name, trigger in self.triggers.items():
                    rpn_list = []
                    if error_name in trigger: 
                        for el in trigger[error_name]:
                            # function ?
                            tmp = el.split(".")
                            if len(tmp) > 1:
                                # detect oid with function
                                ds, fct = tmp
                                if self.oids[ds].value is None:
                                    return int(trigger['default_status'])
                                fct, args = fct.split("(")
                                if hasattr(self.oids[ds], fct):
                                    if args == ')':
                                        value = getattr(self.oids[ds], fct)()
                                    else:
                                        args = args[:-1]
                                        args = args.split(",")
                                        value = getattr(self.oids[ds], fct)(**args)
                                else:
                                    # TODO
                                    print "NOT FUNCTION FOUND: `%s'" % fct
                            elif el in self.oids:
                                # detect oid
                                value = self.oids[ds].value
                            else:
                                value = el
                            rpn_list.append(value)

                        error = rpn_calculator(rpn_list)
                        if error:
                            return error_code
            return errors['ok']
        except Exception, e:
            # TODO
            print "ERROR", str(e)
            self.out = "Error calculating return code" 
            return int(trigger['default_status'])

    def set_triggers(self, datasource):
        if self.triggergroup in datasource['TRIGGERGROUP']:
            triggers = datasource['TRIGGERGROUP'][self.triggergroup]
            # if triggers is a str
            if isinstance(triggers, str):
                # Transform to list
                triggers = [triggers,]
            for trigger_name in triggers:
                if trigger_name in datasource['TRIGGER']:
                    self.triggers[trigger_name] = {}
                    if 'warning' in datasource['TRIGGER'][trigger_name]:
                        self.triggers[trigger_name]['warning'] = datasource['TRIGGER'][trigger_name]['warning']
                    if 'critical' in datasource['TRIGGER'][trigger_name]:
                        self.triggers[trigger_name]['critical'] = datasource['TRIGGER'][trigger_name]['critical']
                    if 'default_status' in datasource['TRIGGER'][trigger_name]:
                        self.triggers[trigger_name]['default_status'] = datasource['TRIGGER'][trigger_name]['default_status']
                    elif 'default_status' in datasource['TRIGGER']:
                        self.triggers[trigger_name]['default_status'] = datasource['TRIGGER']['default_status']

    def find_oids(self, datasource):
        ds = datasource['DSTEMPLATE'][self.dstemplate]['ds']
        if isinstance(ds, str):
            ds = [ds,]

        for source in ds:
            try:
                oid = datasource['DATASOURCE'][source]['ds_oid']
            except:
                # TODO
                print "ERROR: OID not found"
                pass

            # Determining oid
            oid = oid % self.__dict__
            # Search type
            ds_type = None
            if 'ds_type' in datasource['DATASOURCE'][source]:
                ds_type = datasource['DATASOURCE'][source]['ds_type']
            elif 'ds_type' in datasource['DATASOURCE']:
                ds_type = datasource['DATASOURCE']['ds_type']
            else:
                # TODO
                ds_type = 'TEXT'
                print "ERROR : ds_type not found"
            # Search name
            name = source
            if 'ds_name' in datasource['DATASOURCE'][source]:
                name = datasource['DATASOURCE'][source]['ds_name']
            elif 'ds_name' in datasource['DATASOURCE']:
                name = datasource['DATASOURCE']['ds_name']
            # Search unit
            unit = ''
            if 'ds_unit' in datasource['DATASOURCE'][source]:
                unit = datasource['DATASOURCE'][source]['ds_unit']
            elif 'ds_unit' in datasource['DATASOURCE']:
                unit = datasource['DATASOURCE']['ds_unit']
            # Search ds_min
            ds_min = ''
            if 'ds_min' in datasource['DATASOURCE'][source]:
                ds_min = datasource['DATASOURCE'][source]['ds_min']
            elif 'ds_min' in datasource['DATASOURCE']:
                ds_min = datasource['DATASOURCE']['ds_min']
            # Search ds_max
            ds_max = ''
            if 'ds_max' in datasource['DATASOURCE'][source]:
                ds_max = datasource['DATASOURCE'][source]['ds_max']
            elif 'ds_max' in datasource['DATASOURCE']:
                ds_max = datasource['DATASOURCE']['ds_max']
            # Search calc
            calc = None
            if 'ds_calc' in datasource['DATASOURCE'][source]:
                calc = datasource['DATASOURCE'][source]['ds_calc']
            elif 'ds_calc' in datasource['DATASOURCE']:
                calc = datasource['DATASOURCE']['ds_calc']
            # Search limit
            limit = ''
            if 'ds_limit' in datasource['DATASOURCE'][source]:
                limit = datasource['DATASOURCE'][source]['ds_limit']
            elif 'ds_limit' in datasource['DATASOURCE']:
                limit = datasource['DATASOURCE']['ds_limit']

            snmp_oid = SNMPOid(oid, ds_type, name, ds_max, ds_min, unit, calc, limit)
            self.oids[source] = snmp_oid


class SNMPOid(object):
    def __init__(self, oid, ds_type, name, ds_max='', ds_min='', unit='', calc=None, limit=''):
        self.oid = oid
        self.type_ = ds_type
        self.name = name
        self.max_ = ds_max
        self.min_ = ds_min
        self.unit = unit
        self.calc = calc
        self.limit = limit
        # Message printed
        self.out = None
        # Raw value (before calculation)
        self.raw_value = None
        # Raw old value (before calculation)
        self.raw_old_value = None
        # Value (after calculation)
        self.value = None
        # Old value (after calculation)
        self.old_value = None
        self.perf = ""

    # Zabbix functions
    def prct(self):
        return float(self.value) * 100 / float(self.max_)

    def last(self):
        return self.value
    # End zabbix functions

    def calculation(self, value):
        return rpn_calculator([value,] + self.calc)

    def format_output(self, check_time, old_check_time):
        getattr(self, 'format_' + self.type_.lower() + '_output')(check_time, old_check_time)

    def format_text_output(self, check_time, old_check_time):
        """ Format output for text type
        """
        self.value = "%(raw_value)s" % self.__dict__
        self.out = "%(name)s: %(value)s%(unit)s" % self.__dict__

    def format_derive_output(self, check_time, old_check_time):
        """ Format output for derive type
        """
        if self.raw_old_value == None:
            # Need more data to get derive
            self.out = "Waiting data"
            self.perf = ''
        else:
            raw_value = self.raw_value
            # detect counter reset
            if self.raw_value < self.raw_old_value:
                # Counter reseted
                raw_value = (float(self.limit) - float(self.raw_old_value)) + float(raw_value)
                print "Counter resetedCounter resetedCounter resetedCounter resetedCounter resetedCounter reseted", self.limit, self.raw_old_value, raw_value

            # Get derive
            t_delta = check_time - old_check_time
            if t_delta.seconds == 0:
                print "HOW ??? is it possible ?"
                print "t_deltat_deltat_deltat_deltat_delta == 0:", t_delta
            else:
                d_delta = float(raw_value) - float(self.raw_old_value)
                value = d_delta / t_delta.seconds
                value = "%0.2f" % value
                # Make calculation
                if self.calc:
                    self.value = self.calculation(value)
                else:
                    self.value = value

                self.value = float(self.value)
                self.out = "%(name)s: %(value)0.2f%(unit)s" % self.__dict__
                self.perf = "%(name)s=%(value)0.2f%(unit)s;;%(min_)s;%(max_)s" % self.__dict__

    def format_counter_output(self, check_time, old_check_time):
        """ Format output for counter type
        """
        if self.raw_value == None:
            # No data, is it possible??
            self.out = "No Data found ... maybe we have to wait ..."
            self.perf = ''
        else:
            raw_value = self.raw_value
            # detect counter reset
            if self.raw_value < self.raw_old_value:
                # Counter reseted
                raw_value = (self.limit - self.old_value) + raw_value
            # Make calculation
            if self.calc:
                self.value = self.calculation(raw_value)
            else:
                self.value = raw_value

            self.value = float(self.value)
            self.out = "%(name)s: %(value)0.2f%(unit)s" % self.__dict__
            self.out = self.out % self.__dict__

    def format_gauge_output(self, check_time, old_check_time):
        """ Format output for gauge type
        """
        if self.raw_value == None:
            # No data, is it possible??
            self.out = "No Data found ... maybe we have to wait ..."
            self.perf = ''
        else:
            raw_value = self.raw_value
            # Make calculation
            if self.calc:
                self.value = self.calculation(raw_value)
            else:
                self.value = raw_value

            self.value = float(self.value)
            self.out = "%(name)s: %(value)0.2f%(unit)s" % self.__dict__
            self.perf = "%(name)s=%(out)s%(unit)s;;%(min_)s;%(max_)s" % self.__dict__


class SNMPAsyncClient(object):
    """SNMP asynchron Client.
    Launch async SNMP request
    """
    def __init__(self, host, community, version, datasource,
                 triggergroup, dstemplate, instance, instance_name,
                 memcached_address):

        self.hostname = host
        self.community = community
        self.version = version
        self.dstemplate = dstemplate
        self.instance = instance
        self.triggergroup = triggergroup
        self.serv_key = (dstemplate, instance, instance_name)

        self.interval_length = 60

        self.memcached = memcache.Client([memcached_address], debug=0)
        self.datasource = datasource

        self.check_interval = None
        self.state = 'creation'
        self.start_time = datetime.now()
        self.timeout = 5

        self.obj = None

        # Check if obj is in memcache
        self.obj_key = str(self.hostname)
        try:
            # LOCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
            self.obj = self.memcached.get(self.obj_key)
        except ValueError, e:
            self.set_exit("Memcached error: `%s'"
                          % self.memcached.get(self.obj_key),
                          rc=3)
            return
        if not isinstance(self.obj, SNMPHost):
            print "Host not found in memcache", self.hostname, self.obj
            self.set_exit("Host not found in memcache: `%s'" % self.hostname,
                          rc=3)
            return

        # Find service check_interval
        self.check_interval = self.obj.find_frenquences(self.serv_key)
        if self.check_interval is None:
            # Possible ???
            self.set_exit("Interval not found in memcache", rc=3)
            return

        # Check if map is done
        s = self.obj.frequences[self.check_interval].services[self.serv_key]
        if isinstance(s.instance, str):
            self.mapping_done = not s.instance.startswith("map(")
        else:
            self.mapping_done = True

        # Check if the check is forced
        if self.obj.frequences[self.check_interval].forced:
            # Check forced !!
            self.obj.frequences[self.check_interval].forced = False
            data_validity = False

        elif not self.mapping_done:
            data_validity = False
        # Check datas validity
        elif self.obj.frequences[self.check_interval].check_time is None:
            # Datas not valid : no data
            data_validity = False
        else:
            td = timedelta(seconds=(self.check_interval
                                    *
                                    self.interval_length))
            data_valid = self.obj.frequences[self.check_interval].check_time + td \
                                                        > self.start_time
            if data_valid:
                # Datas valid
                data_validity = True
                message, rc = self.obj.format_output(self.check_interval, self.serv_key)
                message = "From cache: " + message
                self.set_exit(message, rc=rc)
                return
            else:
                # Datas not valide: datas too old
                data_validity = False

        # Save old datas
        self.obj.frequences[self.check_interval].old_check_time = \
                                self.obj.frequences[self.check_interval].check_time
        for oid in self.obj.frequences[self.check_interval].services[self.serv_key].oids.values():
            oid.old_value = oid.value
            oid.raw_old_value = oid.raw_value

        self.memcached.set(self.obj_key, self.obj, time=604800)
        # UNLOCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK

        # Get all oids which have to be checked
        self.oids_to_check = self.obj.get_oids_by_interval(self.check_interval)
        if self.oids_to_check == {}:
            self.set_exit("No OID found" + " - " + self.obj_key + " - "+ str(self.serv_key), rc=3)
            return

        # SNMP table header
        tmp_oids = [oid[1:] for oid in self.oids_to_check]
        self.headVars = []
        for oid in tmp_oids:
            # TODO: FIX IT =>
            # Launch :  snmpbulkget .1.3.6.1.2.1.2.2.1.8
            #     to get.1.3.6.1.2.1.2.2.1.8.2
            # Because : snmpbulkget .1.3.6.1.2.1.2.2.1.8.2
            #     returns value only for .1.3.6.1.2.1.2.2.1.8.3
            oid = oid.rsplit(".", 1)[0]
            try:
                oid = tuple(int(i) for i in oid.split("."))
            except ValueError:
                # TODO
                continue
            self.headVars.append(v2c.ObjectIdentifier(oid))

        # Mapping
        self.mapping_oids = self.obj.get_oids_for_instance_mapping(self.check_interval, self.datasource)
        tmp_oids = [oid[1:] for oid in self.mapping_oids]
        for oid in tmp_oids:
            try:
                oid = tuple(int(i) for i in oid.split("."))
            except ValueError:
                # TODO
                continue
            self.headVars.append(v2c.ObjectIdentifier(oid))

        # Build PDU
        self.reqPDU = v2c.GetBulkRequestPDU()
        v2c.apiBulkPDU.setDefaults(self.reqPDU)
        v2c.apiBulkPDU.setNonRepeaters(self.reqPDU, 0)
        v2c.apiBulkPDU.setMaxRepetitions(self.reqPDU, 25)
        v2c.apiBulkPDU.setVarBinds(self.reqPDU,
                                   [(x, v2c.null) for x in self.headVars])

        # Build message
        self.reqMsg = v2c.Message()
        v2c.apiMessage.setDefaults(self.reqMsg)
        v2c.apiMessage.setCommunity(self.reqMsg, self.community)
        v2c.apiMessage.setPDU(self.reqMsg, self.reqPDU)

        self.startedAt = time.time()

        transportDispatcher = AsynsockDispatcher()
        transportDispatcher.registerTransport(udp.domainName,
                                udp.UdpSocketTransport().openClientMode())

        transportDispatcher.registerRecvCbFun(self.callback)
        transportDispatcher.registerTimerCbFun(self.callback_timer)
        transportDispatcher.sendMessage(encoder.encode(self.reqMsg),
                                        udp.domainName,
                                        (self.hostname, 161))
        transportDispatcher.jobStarted(1)
        try:
            transportDispatcher.runDispatcher()
        except Exception, e:
            self.set_exit("Request error on dispatcher: " + str(e), rc=3)
        transportDispatcher.closeDispatcher()

    def callback(self, transportDispatcher, transportDomain, transportAddress,
                 wholeMsg, reqPDU=None, headVars=None):
        aBP = v2c.apiBulkPDU
        # Get PDU
        if reqPDU:
            self.reqPDU = reqPDU
        if headVars:
            self.headVars = headVars

        while wholeMsg:
            self.rspMsg, wholeMsg = decoder.decode(wholeMsg,
                                                   asn1Spec=v2c.Message())
            self.rspPDU = v2c.apiMessage.getPDU(self.rspMsg)

            if aBP.getRequestID(self.reqPDU) == aBP.getRequestID(self.rspPDU):
                # Check for SNMP errors reported
                errorStatus = aBP.getErrorStatus(self.rspPDU)
                if errorStatus and errorStatus != 2:
                    self.set_exit("REQUEST ERROR: " + str(errorStatus), rc=3)
                    return wholeMsg
                # Format var-binds table
                varBindTable = aBP.getVarBindTable(self.reqPDU, self.rspPDU)
                # Report SNMP table
                oid_dict = {}
                oid_list = []
                mapping_instance = {}
                for tableRow in varBindTable:
                    for oid, val in tableRow:
                        oid = "." + oid.prettyPrint()
                        oid_list.append(oid)
                        if oid in self.oids_to_check:
                            # Get values
                            oid_dict[oid] = str(val)
                        if any([oid.startswith(m_oid + ".") for m_oid in self.mapping_oids]):
                            # Get mapping
                            for m_oid in self.mapping_oids:
                                if oid.startswith(m_oid + "."):
                                    instance = oid.replace(m_oid + ".", "")
                                    mapping_instance[str(val)] = instance

#                if len(self.oids_to_check) > len(oid_dict):
#                    print "self.oids_to_check", self.oids_to_check
#                    print "oid_dict", oid_dict
#                    self.set_exit("Oids missing in SNMP response: %s" %
#                                          str(errorStatus),
#                                  rc=3)
#                    return wholeMsg

                # LOCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
                try:
                    self.obj = self.memcached.get(self.obj_key)
                except ValueError, e:
                    print "Callback Memcached error:, Callback Memcached error: Callback Memcached error:Callback Memcached error:"
                    self.set_exit("Memcached error: `%s'"
                                  % self.memcached.get(self.obj_key),
                                  3, transportDispatcher)
                    return wholeMsg

                # MAPPING
                if not self.mapping_done:
                    self.obj.instances = mapping_instance
                    s = self.obj.frequences[self.check_interval].services[self.serv_key]
                    mapping = self.obj.map_instances(self.check_interval)
                    self.memcached.set(self.obj_key, self.obj, time=604800)
                    self.set_exit("MAPPING waiting next check", 3, transportDispatcher)
                    return

                # Save values
                self.oids_to_check = self.obj.get_oids_by_interval(self.check_interval)
                for oid, value in oid_dict.items():
                    self.oids_to_check[oid].raw_value = str(value)

                self.obj.frequences[self.check_interval].check_time = self.start_time
                
                # save data
                self.memcached.set(self.obj_key, self.obj, time=604800)


                # UNLOCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
#                transportDispatcher.jobFinished(1)

                # Generate request for next row
                aBP.setVarBinds(self.reqPDU,
                                [(x, v2c.null) for x, y in varBindTable[-1]])
                aBP.setRequestID(self.reqPDU, v2c.getNextRequestID())
                transportDispatcher.sendMessage(encoder.encode(self.reqMsg),
                                                transportDomain,
                                                transportAddress)

                if time.time() - self.startedAt > self.timeout:
                    self.set_exit("Request timed out", 3, transportDispatcher)

                self.startedAt = time.time()

        # Prepare output
#        message, rc = self.format_output()
        message, rc = self.obj.format_output(self.check_interval, self.serv_key)
        self.set_exit(message, rc, transportDispatcher)

        return wholeMsg

    def callback_timer(self, timeNow):
        if timeNow - self.startedAt > self.timeout:
            self.set_exit("Request timed out", rc=3)
            return

    def is_done(self):
        return self.state == 'received'

    # Check if we are in timeout. If so, just bailout
    # and set the correct return code from timeout
    # case
    def look_for_timeout(self):
        now = datetime.now()
        t_delta = now - self.start_time
        if t_delta.seconds > self.timeout:
        # TODO add `unknown_on_timeout` option
#            if self.unknown_on_timeout:
#                rc = 3
#            else:
            rc = 3
            message = 'Error : connection timeout after %d seconds' % self.timeout
            self.set_exit(message, rc)

    def set_exit(self, message, rc=3, transportDispatcher=None):
        self.rc = rc
        self.execution_time = datetime.now() - self.start_time
        self.execution_time = self.execution_time.seconds
        self.message = message
        self.state = 'received'
#        print "message", message
        if transportDispatcher:
            transportDispatcher.jobFinished(1)


def parse_args(cmd_args):
    #Default params
    host = None
    community = 'public'
    version = '2c'
    dstemplate = None
    triggergroup = None
    instance = 0
    instance_name = None

    #Manage the options
    try:
        options, args = getopt.getopt(cmd_args,
                        'H:C:V:i:t:T:n:',
                        ['hostname=', 'community=', 'snmp-version=',
                         'dstemplate=', 'help', 'version',
                         'instance=', 'instance-name=' ])
    except getopt.GetoptError, err:
        # If we got problem, bail out
        return (host, community, version,
                triggergroup, dstemplate, instance)
    for option_name, value in options:
        if option_name in ("-H", "--hostname"):
            host = value
        elif option_name in ("-C", "--community"):
            community = value
        elif option_name in ("-t", "--dstemplate"):
            dstemplate = value
        elif option_name in ("-T", "--triggergroup"):
            triggergroup = value
        elif option_name in ("-i", "--instance"):
            instance = value
        elif option_name in ("-V", "--snmp-version"):
            version = value
        elif option_name in ("-n", "--instance-name"):
            instance_name = value

    return (host, community, version,
            triggergroup, dstemplate, instance,
            instance_name)


class Snmp_poller(BaseModule):
    """ SNMP Poller module class
        Improve SNMP checks
    """
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.datasource_file = getattr(mod_conf, 'datasource_file', None)
        self.memcached_host = getattr(mod_conf, 'memcached_host', "127.0.0.1")
        self.memcached_port = getattr(mod_conf, 'memcached_port', 11211)
        self.memcached_address = "%s:%s" % (self.memcached_host,
                                       self.memcached_port)

        # Called by poller to say 'let's prepare yourself guy'
    def init(self):
        """Called by poller to say 'let's prepare yourself guy'"""
        print "Initialization of the snmp poller module"
        self.i_am_dying = False

        if self.datasource_file is None:
            # Kill snmp booster if config_file is not set
            logger.error("Please set config_file parameter")
            self.i_am_dying = True
            return

        # Prepare memcached connection
        self.memcached = memcache.Client([self.memcached_address], debug=0)
        # Check if memcached server is available
        if not self.memcached.get_stats():
            logger.error("Memcache server (%s) "
                         "is not reachable" % self.memcached_address)
            self.i_am_dying = True
            return

        # Read datasource file
        # Config validation
        try:
            self.datasource = ConfigObj(self.datasource_file,
                                        interpolation='template')
        except Exception, e:
            logger.error("Readin datasource file error: `%s'" % str(e))
            self.i_am_dying = True
            return

        # Store config in memcache
        self.memcached.set('datasource', self.datasource, time=604800)

    def get_new_checks(self):
        """ Get new checks if less than nb_checks_max
            If no new checks got and no check in queue,
            sleep for 1 sec
            REF: doc/shinken-action-queues.png (3)
        """
        try:
            while(True):
                #print "I", self.id, "wait for a message"
                try:
                    msg = self.s.get(block=False)
                except IOError, e:
                    # IOError: [Errno 104] Connection reset by peer
                    msg = None
                if msg is not None:
                    self.checks.append(msg.get_data())
                #print "I", self.id, "I've got a message!"
        except Empty, exp:
            if len(self.checks) == 0:
                time.sleep(1)

    def launch_new_checks(self):
        """ Launch checks that are in status
            REF: doc/shinken-action-queues.png (4)
        """
        for chk in self.checks:
            now = time.time()
            if chk.status == 'queue':
                # Ok we launch it
                chk.status = 'launched'
                chk.check_time = now

                # Want the args of the commands so we parse it like a shell
                # shlex want str only
                clean_command = shlex.split(chk.command.encode('utf8',
                                                               'ignore'))
                # If the command seems good
                if len(clean_command) > 1:
                    # we do not want the first member, check_snmp thing
                    args = parse_args(clean_command[1:])
                    (host, community, version,
                     triggergroup, dstemplate, instance, instance_name) = args

                # If we do not have the good args, we bail out for this check
                if host is None:
                    chk.status = 'done'
                    chk.exit_status = 2
                    chk.get_outputs('Error : the parameters host or command are not correct.', 8012)
                    chk.execution_time = 0.0
                    continue

                # Ok we are good, we go on
                n = SNMPAsyncClient(host, community, version, self.datasource,
                                    triggergroup, dstemplate, instance, instance_name,
                                    self.memcached_address)
                chk.con = n

    # Check the status of checks
    # if done, return message finished :)
    # REF: doc/shinken-action-queues.png (5)
    def manage_finished_checks(self):
        to_del = []

        # First look for checks in timeout
        for c in self.checks:
            if c.status == 'launched':
                c.con.look_for_timeout()

        # Now we look for finished checks
        for c in self.checks:
            # First manage check in error, bad formed
            if c.status == 'done':
                to_del.append(c)
                try:
                    self.returns_queue.put(c)
                except IOError, exp:
                    print "[%d]Exiting: %s" % (self.id, exp)
                    sys.exit(2)
                continue
            # Then we check for good checks
            if c.status == 'launched' and c.con.is_done():
                n = c.con
                c.status = 'done'
                c.exit_status = getattr(n, 'rc', 3)
                c.get_outputs(str(getattr(n, 'message', 'Error in launching command.')), 8012)
                c.execution_time = getattr(n, 'execution_time', 0.0)

                # unlink our object from the original check
                if hasattr(c, 'con'):
                    delattr(c, 'con')

                # and set this check for deleting
                # and try to send it
                to_del.append(c)
                try:
                    self.returns_queue.put(c)
                except IOError, exp:
                    print "[%d]Exiting: %s" % (self.id, exp)
                    sys.exit(2)

        # And delete finished checks
        for chk in to_del:
            self.checks.remove(chk)

    # id = id of the worker
    # s = Global Queue Master->Slave
    # m = Queue Slave->Master
    # return_queue = queue managed by manager
    # c = Control Queue for the worker
    def work(self, s, returns_queue, c):
        print "[Snmp] Module SNMP started!"
        ## restore default signal handler for the workers:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        timeout = 1.0
        self.checks = []

        self.returns_queue = returns_queue
        self.s = s
        self.t_each_loop = time.time()
        while True:
            begin = time.time()
            msg = None
            cmsg = None

            # If we are diyin (big problem!) we do not
            # take new jobs, we just finished the current one
            if not self.i_am_dying:
                # REF: doc/shinken-action-queues.png (3)
                self.get_new_checks()
                # REF: doc/shinken-action-queues.png (4)
                self.launch_new_checks()
            # REF: doc/shinken-action-queues.png (5)
            self.manage_finished_checks()

            # Now get order from master
            try:
                cmsg = c.get(block=False)
                if cmsg.get_type() == 'Die':
                    print "[%d]Dad say we are diing..." % self.id
                    break
            except:
                pass

            #TODO : better time management
            time.sleep(.1)

            timeout -= time.time() - begin
            if timeout < 0:
                timeout = 1.0

    def hook_add_actions(self, sche):
        # TODO split and put one part in arbiter... ???
        for s in sche.services:
            for a in s.actions:
                if isinstance(a, Check):
                    if a.module_type == 'snmp_poller':
                        # Clean command
                        clean_command = shlex.split(a.command.encode('utf8',
                                                                    'ignore'))
                        # If the command doesn't seem good
                        if len(clean_command) <= 1:
                            # TODO Bad command ???
                            continue

                        # we do not want the first member, check_snmp thing
                        args = parse_args(clean_command[1:])
                        (host, community, version,
                         triggergroup, dstemplate, instance, instance_name) = args

                        # Get key from memcached
                        obj_key = str(host)
                        # looking for old datas
                        obj = self.memcached.get(obj_key)

                        # Don't force check on first launch
                        forced = False
                        if not obj is None:
                            # Host found
                            # try to find if this oid is already in memcache
                            if not s.check_interval in obj.frequences:
                                print "NOTFOUDNDDD", obj_key, s.service_description
                                # possible ??
                                continue
                            if not obj.frequences[s.check_interval].check_time is None:
                                # Forced or not forced check ??
#                                if s.last_chk != 0: 
                                if True:
                                    if s.state_type == 'SOFT':
                                        forced = True
                                        # Detect if the checked is forced by an error
                                        # needed ???
#                                        t_delta = timedelta(seconds=(s.retry_interval *
#                                                                     s.interval_length))
#                                        t_delta = t_delta + timedelta(5)
#                                        forced = obj.frequences[s.check_interval].check_time \
#                                                                + t_delta > datetime.now()
                                    else:
                                        # Detect if the checked is forced by an UI/Com
                                        # TODO Add/remove 5 seconds
                                        forced = (s.next_chk - s.last_chk) < \
                                                 s.check_interval * s.interval_length
                                    # TODO: what append if is forced
                                    # by an interface en SOFT type ?
                                if forced:
                                    # Set forced
                                    print "FORCED", obj_key, s.service_description
                                    obj.frequences[s.check_interval].forced = forced

                            self.memcached.set(obj_key, obj, time=604800)
                        else:
                            # Host Not found
                            # TODO
                            pass

    def hook_late_configuration(self, arb):
        for s in arb.conf.services:
            if s.check_command.command.module_type == 'snmp_poller':
                c = s.check_command.command
                m = MacroResolver()
                m.init(arb.conf)
                data = s.get_data_for_checks()
                command_line = m.resolve_command(s.check_command, data)

                # Clean command
                clean_command = shlex.split(command_line.encode('utf8',
                                                            'ignore'))
                # If the command doesn't seem good
                if len(clean_command) <= 1:
                    # TODO Bad command ???
                    continue

                # we do not want the first member, check_snmp thing
                args = parse_args(clean_command[1:])
                (host, community, version,
                 triggergroup, dstemplate, instance, instance_name) = args

                # Get key from memcached
                obj_key = str(host)
                # looking for old datas
                obj = self.memcached.get(obj_key)

                # Don't force check on first launch
                # MERGE WITH OLD DATA BEFORE ARBITER RESTART
                if not obj is None:
                    # Host found
                    new_serv = SNMPService(s, obj, triggergroup, dstemplate, instance, instance_name)
                    new_serv.find_oids(self.datasource)
                    new_serv.set_triggers(self.datasource)
                    obj.update_service(new_serv)
                    obj.frequences[s.check_interval].forced = False
                    self.memcached.set(obj_key, obj, time=604800)
                else:
                    # No old datas for this host
                    new_obj = SNMPHost(host, community, version)
                    new_serv = SNMPService(s, new_obj, triggergroup, dstemplate, instance, instance_name)
                    new_serv.find_oids(self.datasource)
                    new_serv.set_triggers(self.datasource)
                    new_obj.update_service(new_serv)
                    # Save new host in memcache
                    self.memcached.set(obj_key, new_obj, time=604800)
