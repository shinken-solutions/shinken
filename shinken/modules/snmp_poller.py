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
    'daemons': ['poller', 'scheduler'],
    'type': 'snmp_poller',
    'external': False,
    'phases': ['running', ],
    # To be a real worker module, you must set this
    'worker_capable': True,
    }


def get_instance(mod_conf):
    """called by the plugin manager to get a poller"""
    print "Get a snmp poller module for plugin %s" % mod_conf.get_name()
    instance = Snmp_poller(mod_conf)
    return instance


class SNMPAsyncClient(object):
    """SNMP asynchron Client.
    Launch async SNMP request
    """
    def __init__(self, host, community, version, datasource,
                 warning, critical, inverse, interval_length,
                 data_type, instance, memcached):

        self.hostname = host
        self.community = community
        self.version = version
        self.data_type = data_type
        self.instance = instance
        self.warning = warning
        self.critical = critical
        self.inverse = inverse
        self.interval_length = interval_length

        self.memcached = memcached
        self.datasource = datasource

        self.check_interval = None
        self.state = 'creation'
        self.start_time = datetime.now()
        self.timeout = 5

        # Check if obj is in memcache
        self.obj_key = str(self.hostname)
        try:
            self.obj = self.memcached.get(self.obj_key)
        except ValueError, e:
            self.set_exit("Memcached error: `%s'"
                          % self.memcached.get(self.obj_key),
                          rc=3)
            return
        if not self.obj:
            self.set_exit("Host not found in memcache: `%s'" % self.hostname,
                          rc=3)
            return

        # check if datatype is in datasource
        if not self.data_type in self.datasource['DATASOURCE']['TYPE']:
            self.set_exit("Type: `%s' not found in datatype" % self.data_type,
                          rc=3)
            return
        # check if at least one oid is define in the datasource
        # for this datatype
        self.oids = self.datasource['DATASOURCE']['TYPE'][data_type]['OIDS']
        if len(self.oids) == 0:
            self.set_exit("No oid(s) define for datatype: `%s'"
                          % self.data_type,
                          rc=3)
            return
        # Find service check_interval
        tmp_oid = self.oids.values()[0] % self.__dict__
        tmp_dict = {'instance': instance}
        for interval, el in self.obj.items():
            if el and 'OIDS' in el and tmp_oid in el['OIDS'].keys():
                self.check_interval = interval
                break

        if self.check_interval is None:
            # Possible ???
            self.set_exit("Interval not found in memcache", rc=3)
            return

        # Check if the check is forced
        if self.obj[self.check_interval]['forced']:
            self.obj[self.check_interval]['forced'] = False
            self.memcached.set(self.obj_key, self.obj)
            # Check forced
            data_validity = False
        # Check datas validity
        elif self.obj[self.check_interval]['check_time'] is None:
            # Datas not valid : no data
            data_validity = False
        else:
            td = timedelta(seconds=(self.check_interval
                                    *
                                    self.interval_length))
            data_valid = self.obj[self.check_interval]['check_time'] + td \
                                                        > self.start_time
            if data_valid:
                # Datas valid
                data_validity = True
                message, rc = self.format_output()
                message = "From cache: " + message
                self.set_exit(message, rc=rc)
                self.is_done()
                return
            else:
                # Datas not valide: datas too old
                data_validity = False

        # Save old datas
        self.obj[self.check_interval]['old_check_time'] = \
                                self.obj[self.check_interval]['check_time']
        self.obj[self.check_interval]['old_OIDS'] = \
                                self.obj[self.check_interval]['OIDS']
        self.memcached.set(self.obj_key, self.obj)

        # Get all oids which have to be checked
        self.oids_to_check = self.obj[self.check_interval]['OIDS'].keys()

        if not False:
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
                for tableRow in varBindTable:
                    for oid, val in tableRow:
                        oid = "." + oid.prettyPrint()
                        oid_list.append(oid)
                        if oid in self.oids_to_check:
                            oid_dict[oid] = str(val)

                if len(self.oids_to_check) > len(oid_dict):
                    self.set_exit("Oids missing in SNMP response: %s" %
                                          str(errorStatus),
                                  rc=3)
                    return wholeMsg

                self.obj[self.check_interval]['check_time'] = self.start_time
                self.obj[self.check_interval]['OIDS'] = oid_dict
                # save data
                self.memcached.set(self.obj_key, self.obj)

                transportDispatcher.jobFinished(1)

                # Generate request for next row
                aBP.setVarBinds(self.reqPDU,
                                [(x, v2c.null) for x, y in varBindTable[-1]])
                aBP.setRequestID(self.reqPDU, v2c.getNextRequestID())
                transportDispatcher.sendMessage(encoder.encode(self.reqMsg),
                                                transportDomain,
                                                transportAddress)

                if time.time() - self.startedAt > self.timeout:
                    self.set_exit("Request timed out", rc=3)

                self.startedAt = time.time()

        # Prepare output
        message, rc = self.format_output()
        self.set_exit(message, rc=rc)
        self.is_done()

        return wholeMsg

    def callback_timer(self, timeNow):
        if timeNow - self.startedAt > self.timeout:
            self.set_exit("Request timed out", rc=3)
            self.is_done()
            return

    def is_done(self):
        return self.state == 'received'

    def set_exit(self, message, rc=3):
        self.rc = rc
        self.execution_time = datetime.now() - self.start_time
        self.execution_time = self.execution_time.seconds
        self.message = message
        self.state = 'received'

    def format_output(self):
        # Get datasource type : DELTA, TEXT or INT
        if 'ds_type' in self.datasource['DATASOURCE']['TYPE'][self.data_type]:
            ds_type = self.datasource['DATASOURCE']['TYPE'][self.data_type]['ds_type']
        elif 'ds_type' in self.datasource['DATASOURCE']:
            ds_type = self.datasource['DATASOURCE']['ds_type']
        else:
            ds_type = 'TEXT'

        message, rc = getattr(self, 'format_' + ds_type.lower() + '_output')()
        return message, rc

    def define_rc(self, value):
        """ Set return code
        """
        # Get operator
        if self.inverse:
            comp = operator.le
        else:
            comp = operator.ge
        # Get return code
        if self.critical and self.warning:
            if comp(value, self.critical):
                rc = 2
            elif comp(value, self.warning):
                rc = 1
            else:
                rc = 0
        else:
            # no warning or critical defined
            rc = 0
        return rc

    def format_text_output(self):
        """ Format output for text type
        """
        message = self.get_name()
        rc = 0
        return u"%s" % message, rc

    def format_delta_output(self):
        """ Format output for delta type
        """
        rc = 3
        name = self.get_name()
        unit = self.get_unit()
        ds_min = self.get_ds_min()
        ds_max = self.get_ds_max()
        calc = self.get_calc()

        # Search out
        if not 'out' in self.datasource['DATASOURCE']['TYPE'][self.data_type]['OIDS']:
            return ("Missing `out' parameter in"
                    "datasource for type `%s'" % self.data_type)
        else:
            out_oid = self.datasource['DATASOURCE']['TYPE'][self.data_type]['OIDS']['out']
            out_oid = out_oid % self.__dict__
            # Get datas in memcached
            if out_oid in self.obj[self.check_interval]['OIDS']:
                out = self.obj[self.check_interval]['OIDS'][out_oid]
            else:
                # Possible ???
                return "Data not find in memcached", rc
            # Get old datas
            if self.obj[self.check_interval]['old_OIDS']:
                if out_oid in self.obj[self.check_interval]['old_OIDS']:
                    old_out = self.obj[self.check_interval]['old_OIDS'][out_oid]
                else:
                    return "Waiting for old data1", rc
            else:
                return "Waiting for old data2", rc
            if old_out is None:
                return "Waiting for old data3", rc
            # Get times
            check_time = self.obj[self.check_interval]['check_time']
            old_check_time = self.obj[self.check_interval]['old_check_time']
            # Calculation
            t_delta = check_time - old_check_time
            d_delta = float(out) - float(old_out)
            value = d_delta / t_delta.seconds
            # Datasource calculation
            if calc != '':
                ns = vars(math).copy()
                ns['__builtins__'] = None
                calc = calc.replace('out', str(value))
                value = eval(calc, ns)
            # Prepare message
            perf = u"%s=%0.2f%s;;;%s;%s" % (name, value, unit, ds_min, ds_max)
            message = u"%s: %0.2f%s" % (name, value, unit)
            # Set return code
            rc = self.define_rc(value)

        return message + " | " + perf, rc

    def format_int_output(self):
        """ for type for int type
        """
        return self.format_float_ouput()

    def format_float_ouput(self):
        """ for type for int/float type
        """
        rc = 3
        name = self.get_name()
        unit = self.get_unit()
        ds_min = self.get_ds_min()
        ds_max = self.get_ds_max()
        calc = self.get_calc()
        # Search out
        if not 'out' in self.datasource['DATASOURCE']['TYPE'][self.data_type]['OIDS']:
            return ("Missing `out' parameter in"
                    "datasource for type `%s'" % self.data_type, rc)
        else:
            out_oid = self.datasource['DATASOURCE']['TYPE'][self.data_type]['OIDS']['out']
            out_oid = out_oid % self.__dict__
            # Get datas in memcached
            if out_oid in self.obj[self.check_interval]['OIDS']:
                value = self.obj[self.check_interval]['OIDS'][out_oid]
            else:
                return "Data not find in memcached", rc
            # Calculation
            if calc != '':
                ns = vars(math).copy()
                ns['__builtins__'] = None
                calc = calc.replace('out', str(value))
                value = eval(calc, ns)

            perf = u"%s=%0.2f%s;;;%s;%s" % (name, value, unit, ds_min, ds_max)
            message = u"%s: %0.2f%s" % (name, value, unit)
            # Set return code
            rc = self.define_rc(value)

        return message + " | " + perf, rc

    def get_name(self):
        """ Get oid value from datasource
        """
        name = 'No name found'
        if 'name' in self.datasource['DATASOURCE']['TYPE'][self.data_type]['OIDS']:
            oid = self.datasource['DATASOURCE']['TYPE'][self.data_type]['OIDS']['name']
            oid = oid % self.__dict__
            if oid in self.obj[self.check_interval]['OIDS']:
                name = self.obj[self.check_interval]['OIDS'][oid]
            else:
                name = oid
        return name

    # unit, ds_max, ds_min, calc could be grouped
    def get_unit(self):
        """ Get unit from datasource
        """
        unit = ''
        # Search unit
        if 'unit' in self.datasource['DATASOURCE']['TYPE'][self.data_type]:
            unit = self.datasource['DATASOURCE']['TYPE'][self.data_type]['unit']
        elif 'unit' in self.datasource['DATASOURCE']:
            unit = self.datasource['DATASOURCE']['unit']
        return unit

    def get_ds_min(self):
        """ Get ds_min from datasource
        """
        ds_min = ''
        # Search ds_min
        if 'ds_min' in self.datasource['DATASOURCE']['TYPE'][self.data_type]:
            ds_min = self.datasource['DATASOURCE']['TYPE'][self.data_type]['ds_min']
        elif 'ds_min' in self.datasource['DATASOURCE']:
            ds_min = self.datasource['DATASOURCE']['ds_min']
        return ds_min

    def get_ds_max(self):
        """ Get ds_max from datasource
        """
        ds_max = ''
        # Search ds_max
        if 'ds_max' in self.datasource['DATASOURCE']['TYPE'][self.data_type]:
            ds_max = self.datasource['DATASOURCE']['TYPE'][self.data_type]['ds_max']
        elif 'ds_max' in self.datasource['DATASOURCE']:
            ds_max = self.datasource['DATASOURCE']['ds_max']
        return ds_max

    def get_calc(self):
        """ Get calc from datasource
        """
        calc = ''
        # Search calc
        if 'calc' in self.datasource['DATASOURCE']['TYPE'][self.data_type]:
            calc = self.datasource['DATASOURCE']['TYPE'][self.data_type]['calc']
        elif 'calc' in self.datasource['DATASOURCE']:
            ds_max = self.datasource['DATASOURCE']['calc']
        return calc


def parse_args(cmd_args):
    #Default params
    host = None
    community = 'public'
    version = '2c'
    datasource = None
    update = 300
    data_type = None
    instance = 0
    critical = None
    warning = None
    inverse = False
    #Manage the options
    try:
        options, args = getopt.getopt(cmd_args,
                        'H:C:V:i:u:w:c:t:I',
                        ['hostname=', 'community=', 'snmp-version=',
                         'type=', 'help', 'version', 'inverse',
                         'instance=', 'warning=', 'critical='])
    except getopt.GetoptError, err:
        # If we got problem, bail out
        return (host, community, version,
                data_type, instance)
    #print  "Opts", opts, "Args", args
    for option_name, value in options:
        if option_name in ("-H", "--hostname"):
            hostname = value
        elif option_name in ("-w", "--warning"):
            warning = float(value)
        elif option_name in ("-c", "--critical"):
            critical = float(value)
        elif option_name in ("-C", "--community"):
            community = value
        elif option_name in ("-I", "--inverse"):
            inverse = True
        elif option_name in ("-t", "--type"):
            data_type = value
        elif option_name in ("-i", "--instance"):
            instance = value
        elif option_name in ("-V", "--snmp-version"):
            version = value

    return (hostname, community, version,
            warning, critical, inverse,
            data_type, instance)


class Snmp_poller(BaseModule):
    """Just print some stuff
    """
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.datasource_file = getattr(mod_conf, 'datasource_file', None)
        self.memcached_host = getattr(mod_conf, 'memcached_host', "127.0.0.1")
        self.memcached_port = getattr(mod_conf, 'memcached_port', 11211)
        self.interval_length = None

        # Kill snmp booster if config_file is not set
    def init(self):
        """Called by poller to say 'let's prepare yourself guy'"""
        print "Initialization of the snmp poller module"
        self.i_am_dying = False

        # Config validation
        if self.datasource_file is None:
            logger.error("Please set config_file parameter")
            self.i_am_dying = True
            return

        # Prepare memcached connection
        memcached_address = "%s:%s" % (self.memcached_host,
                                       self.memcached_port)
        self.memcached = memcache.Client([memcached_address], debug=0)
        # Check if memcached server is available
        if not self.memcached.get_stats():
            logger.error("Memcache server (%s) "
                         "is not reachable" % memcached_address)
            self.i_am_dying = True
            return

        # Read datasource file
        self.datasource = ConfigObj(self.datasource_file,
                                    interpolation='template')
        # Store config in memcache
        self.memcached.set('datasource', self.datasource)
        self.interval_length = self.memcached.get('interval_length')

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
        self.interval_length = self.memcached.get('interval_length')
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
                     warning, critical, inverse,
                     data_type, instance) = args
                    #print args
                else:
                    # Set an error so we will quit tis check
                    command = None

                # If we do not have the good args, we bail out for this check
                if host is None:
                    chk.status = 'done'
                    chk.exit_status = 2
                    chk.get_outputs("Error : `host' parameter is not correct.",
                                    8012)
                    chk.execution_time = 0.0
                    continue

                # Ok we are good, we go on
                n = SNMPAsyncClient(host, community, version, self.datasource,
                                    warning, critical, inverse,
                                    self.interval_length,
                                    data_type, instance, self.memcached)
                chk.con = n

    # Check the status of checks
    # if done, return message finished :)
    # REF: doc/shinken-action-queues.png (5)
    def manage_finished_checks(self):
        to_del = []

        # First look for checks in timeout
#        for c in self.checks:
#            if c.status == 'launched':
                #c.con.look_for_timeout()

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
            #if c.status == 'launched' and c.con.is_done():
            if c.status == 'launched' and c.con.is_done():
                n = c.con
                c.status = 'done'
                c.exit_status = getattr(n, 'rc', 3)
                c.get_outputs(getattr(n,
                                      'message',
                                      'Error in launching command.'),
                              8012)
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

    #id = id of the worker
    #s = Global Queue Master->Slave
    #m = Queue Slave->Master
    #return_queue = queue managed by manager
    #c = Control Queue for the worker
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
        if self.interval_length != sche.conf.interval_length:
            self.memcached.set('interval_length', sche.conf.interval_length)
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
                        critical, warning, inverse,
                              data_type, instance) = args
                        tmp_dict = {'instance': instance}

                        # Get related OIDs for this service
                        oids = self.datasource['DATASOURCE']['TYPE'][data_type]['OIDS']
                        if len(oids) == 0:
                            # No oids define for this data_type in datasource..
                            continue
                        # Get key from memcached
                        obj_key = str(s.host_name)
                        # looking for old datas
                        obj = self.memcached.get(obj_key)

                        # Don't force check on first launch
                        forced = False
                        if s.last_chk != 0:
                            if s.state_type == 'SOFT':
                                # Detect if the checked is forced by an error
                                t = timedelta(seconds=(s.retry_interval *
                                                            s.interval_length))
                                forced = obj[s.check_interval]['check_time'] \
                                                        + td > datetime.now()
                            else:
                                # Detect if the checked is forced by an UI/Com
                                forced = (s.next_chk - s.last_chk) < \
                                         s.check_interval * s.interval_length
                            # TODO: what append if is forced
                            # by an interface en SOFT type ?

                        if obj:
                            # Host found
                            # try to find if this oid is already in memcache
                            tmp_key = oids.keys()[0]
                            tmp_oid = oids[tmp_key] % tmp_dict
                            obj_oids = dict([(oid, i) for i in obj.keys()
                                            for oid in obj[i]['OIDS'].keys()])
                            if not tmp_oid in obj_oids:
                                # No OID for this check_interval
                                if not s.check_interval in obj:
                                    obj[s.check_interval] = {
                                          'check_time': None,
                                          'OIDS': dict([(oid % tmp_dict, None)
                                                    for oid in oids.values()]),
                                          'old_check_time': None,
                                          'old_OIDS': None,
                                          'forced': forced,
                                        }
                                # New OID
                                else:
                                    for oid in oids.values():
                                        if not oid in obj[s.check_interval]['OIDS']:
                                            obj[s.check_interval]['OIDS'][oid % tmp_dict] = None

                                self.memcached.set(obj_key, obj)
                            else:
                                # OID is already in memcache
                                # Check if check_interval didn't change
                                for oid in oids.values():
                                    oid = oid % tmp_dict
                                    if not oid in obj[s.check_interval]:
                                        # oid isNOT in good check_interval dict
                                        # => We need to deplace it
                                        old_interval = obj_oids[oid]
                                        obj[s.check_interval]['OIDS'][oid] = \
                                                obj[old_interval]['OIDS'][oid]
                                    else:
                                        # oid is in good check_interval dict
                                        # => do nothing
                                        pass
                            if forced:
                                # Set forced
                                obj[s.check_interval]['forced'] = forced
                                self.memcached.set(obj_key, obj)
                        else:
                            # No old datas for this host
                            new_obj = {s.check_interval:
                                        {'check_time': None,
                                          'OIDS': dict([(oid % tmp_dict, None)
                                                   for oid in oids.values()]),
                                          'old_check_time': None,
                                          'old_OIDS': None,
                                          'forced': forced,
                                        }
                                      }
                            # Save new host in memcache
                            self.memcached.set(obj_key, new_obj)
