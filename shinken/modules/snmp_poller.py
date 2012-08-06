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
from datetime import datetime, timedelta


import memcache
from configobj import ConfigObj, Section
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto.api import v2c

from Queue import Empty

from shinken.log import logger
from shinken.basemodule import BaseModule

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3
STATE_DEPENDENT = 4
MSG = ''
PERF_MSG = ''

IF_STATUS = {1: 'UP',
             2: 'DOWN',
             3: 'TESTING',
             4: 'UNKNOWN',
             5: 'DORMANT',
             6: 'NotPresent',
             7: 'lowerLayerDown'}

CACHE_FOLDER = '/tmp/check_snmp'
UPDATE_TIME = 300

DEBUG = False
CONFIG = None
OIDS = []
NB_REQUESTS = 0
RECEIVED_REQUESTS = 0

OIDS = []
CONFIG = None

#MC_SERVER = memcache.Client(['127.0.0.1:11211'], debug=0)

properties = {
    'daemons' : ['poller'],
    'type' : 'snmp_poller',
    'external' : False,
    # To be a real worker module, you must set this
    'worker_capable' : True,
    }


def get_instance(mod_conf):
    """called by the plugin manager to get a poller"""
    print "Get a snmp poller module for plugin %s" % mod_conf.get_name()
    instance = Snmp_poller(mod_conf)
    return instance


class SnmpObject(object):
    """ Snmp Object
    """
    host = None
    snmp_type = None
    instance = None
    datas = {}
    date = None
    # old data
    old_datas = None
    old_date = None

    message = ""
    perf = ""

    def __init__(self, host, snmp_type, instance=0):
        self.instance = instance
        self.snmp_type = snmp_type
        self.datas = {}
        self.host = host
        self.date = datetime.now()

    def append_msg(self, msg):
        """Appent text to output
        """
        if self.message != "":
            self.message = " - ".join((self.message, msg))
        else:
            self.message = msg

    def append_perf(self, msg):
        """Append text to perf data
        """
        if self.perf != "":
            self.perf = "".join((self.perf, msg))
        else:
            self.perf = msg

    def __repr__(self):
        return "<SnmpObject: %s.%s on %s>" % (self.snmp_type, self.instance, self.host)

    def compute_output(self):
        """Prepare output
        """
        global CONFIG
        if 'ds_type' in CONFIG['DATASOURCE']['TYPE'][self.snmp_type]:
            ds_type = CONFIG['DATASOURCE']['TYPE'][self.snmp_type]['ds_type']
        else:
            ds_type = CONFIG['DATASOURCE']['ds_type']

        datas = self.datas.copy()
        datas['ds_min'] = CONFIG['DATASOURCE']['ds_min']

        if ds_type == 'TEXT':
            msg = 'OK: %(name)s' % datas
            self.append_msg(msg)
        elif ds_type == 'DERIVE':
            datas['unit'] = CONFIG['DATASOURCE']['TYPE'][self.snmp_type]['unit']
            datas['status_name'] = IF_STATUS[self.datas['status']]
            datas['ds_max'] = CONFIG['DATASOURCE']['TYPE'][self.snmp_type]['ds_max']

            if not self.old_date:
                msg = 'Waiting data'
                self.append_msg(msg)
            else:
                seconds = int(self.date.strftime("%s")) - int(self.old_date.strftime("%s"))
                if seconds == 0:
                    seconds = 1
                    print "SECONDS ==================== 0"
                try:
                    datas['bandwidth'] = (self.datas['ifInOctets'] - self.old_datas['ifInOctets']) / seconds
                except KeyError,e :
                    msg = 'Waiting data'
                    self.append_msg(msg)
                    return

                msg = '%(name)s (%(status)s)%(status_name)s %(bandwidth)s%(unit)s' % datas
                self.append_msg(msg)

                perf_msg = "if_inoctets=%(bandwidth)s%(unit)s;;;%(ds_min)s;%(ds_max)s" % datas
                self.append_perf(perf_msg)

        elif ds_type == 'INT':
            datas['name'] = self.datas['fileName']
            datas['unit'] = CONFIG['DATASOURCE']['TYPE'][self.snmp_type]['unit']
            datas['out'] = CONFIG['DATASOURCE']['TYPE'][self.snmp_type]['out']

            size = "%0.2f" % self.datas['fileSize']
            datas['size'] = eval(datas['out'].replace("$FileSize", size))

            msg = '%(name)s: %(size)0.2f%(unit)s' % datas
            self.append_msg(msg)

            perf_msg = "%(name)s=%(size)0.2f%(unit)s;;;0;" % datas
            self.append_perf(perf_msg)



class SNMPAsyncClient(object):
    """SNMP asynchron Client.
    Launch async SNMP request
    """
    def __init__(self, host, community, version,
                 data_type, instance, memcached):

        self.hostname = host
        self.community = community
        self.data_type = data_type
        self.version = version
        self.data_type = data_type
        self.instance = instance
        self.state = 'creation'
        self.start_time = time.time()
        self.memcached = memcached

        self.timeout = 30

        # check_data validity
        if not self.find_data():
            objs_key = ",".join((self.hostname, self.data_type))
            objs = self.memcached.get(objs_key)
            if objs:
                # Save old data
                for inst, obj in objs.items():
                    obj.old_date = obj.date
                    obj.date = datetime.now()
                    obj.old_datas = obj.datas.copy()
                    objs[obj.instance] = obj

                self.memcached.set(objs_key, objs)

            # SNMP table header
            self.oids = [oid[1:] for oid in OIDS.values()]
            self.headVars = []
            for oid in self.oids:
                oid = oid % {'instance': '$_inst'}
                try:
                    oid = tuple(int(i) for i in oid.split("."))
                except ValueError:
                    continue
                self.headVars.append(v2c.ObjectIdentifier(oid))

            # Build PDU
            self.reqPDU =  v2c.GetBulkRequestPDU()
            v2c.apiBulkPDU.setDefaults(self.reqPDU)
            v2c.apiBulkPDU.setNonRepeaters(self.reqPDU, 0)
            v2c.apiBulkPDU.setMaxRepetitions(self.reqPDU, 25)
            v2c.apiBulkPDU.setVarBinds(self.reqPDU, [ (x, v2c.null) for x in self.headVars ])

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
                                            (self.address, 161))
            transportDispatcher.jobStarted(1)
#            try:
            transportDispatcher.runDispatcher()
#            except Exception, e:
#                self.set_exit("REQUEST ERROR: " + str(e), rc=3)
            transportDispatcher.closeDispatcher()

    def find_data(self):
        objs_key = ",".join((self.hostname, self.data_type))
        objs = self.memcached.get(objs_key)

        if not(objs and self.instance in objs):
            #print "NOT FOUND : " + self.hostname + "_" + str(self.data_type) + "_" + str(self.update)
            return False
        else:
            now = datetime.now()
            if objs[self.instance].date + timedelta(0, self.update) < now:
                #print "NOT VALID ANYMORE : " + self.hostname + "_" + str(self.data_type) + "_" + str(self.update)
                # data is NOT valid anymore
                return False
            else:
                objs[self.instance].compute_output()
                self.set_exit(objs[self.instance].message, rc=0, perf=objs[self.instance].perf)
                #print "FIND AND VALID : " + self.hostname + "_" + str(self.data_type) + "_" + str(self.update)
                return True

    def set_exit(self, message, rc=3, perf=None):
        self.rc = rc
        self.execution_time = time.time() - self.start_time
        if perf:
            self.message = " | ".join((message, perf))
        else:
            self.message = message
        self.state = 'received'

    def callback(self, transportDispatcher, transportDomain, transportAddress,
                 wholeMsg, reqPDU=None, headVars=None):
        if not reqPDU:
            reqPDU=self.reqPDU
        if not headVars:
            headVars=self.headVars

        snmp_types = [d for d, v in CONFIG['DATASOURCE']['TYPE'].items() if isinstance(v, Section) ]
        # Revers OIDS => name
#        OIDS = dict([(name, tuple(oid.split(".")[1:])) for name, oid in CONFIG['OID'].items()])
        OIDS = dict([(name, oid[1:]) for name, oid in CONFIG['DATASOURCE']['TYPE'].items() if not isinstance(oid, Section)])
        reversed_oids = dict([(v,k) for k,v in OIDS.iteritems()])

        while wholeMsg:
            self.rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=v2c.Message())
            self.rspPDU = v2c.apiMessage.getPDU(self.rspMsg)
            # Match response to request
            if v2c.apiBulkPDU.getRequestID(self.reqPDU)==v2c.apiBulkPDU.getRequestID(self.rspPDU):
                # Check for SNMP errors reported
                errorStatus = v2c.apiBulkPDU.getErrorStatus(self.rspPDU)
                if errorStatus and errorStatus != 2:
                    self.set_exit("REQUEST ERROR: " + str(errorStatus), rc=3)
                    return wholeMsg
                # Format var-binds table
                varBindTable = v2c.apiBulkPDU.getVarBindTable(self.reqPDU, self.rspPDU)
                # Report SNMP table
                for tableRow in varBindTable:
                    for oid, val in tableRow:
                        if oid[:-1].prettyPrint() in reversed_oids:
                            fetched_data = "$" + reversed_oids[oid[:-1].prettyPrint()]
                            for snmp_type in snmp_types:
                                if "".join(CONFIG['DATASOURCE']['TYPE'][snmp_type].values()).find(fetched_data) != -1:
                                    guessed_snmp_type = snmp_type
                                    break;

                            for key, value in CONFIG['DATASOURCE']['TYPE'][snmp_type].items():
                                if value.startswith(fetched_data):
                                    instance = str(oid[-1])
                                    obj_key = ",".join((self.hostname, guessed_snmp_type))
                                    snmp_dict = self.memcached.get(obj_key)

                                    if not snmp_dict:
                                        snmp_dict = {}
                                    if not instance in snmp_dict:
                                        # New object
                                        snmp_object = SnmpObject(self.hostname, guessed_snmp_type, instance)
                                    else:
                                        # Old object
                                        snmp_object = snmp_dict[instance]

                                    try:
                                        snmp_object.datas[key] = int(val.prettyPrint())
                                    except ValueError, e:
                                        snmp_object.datas[key] = val.prettyPrint()
                
                                    snmp_dict[instance] = snmp_object
                                    self.memcached.set(obj_key, snmp_dict)

#                            if ".".join(name.prettyPrint().split(".")[:-1]) in self.oids:
    #                            print('from: %s, %s = %s' % (transportAddress,
    #                                                         name.prettyPrint(),
    #                                                         val.prettyPrint()
    #                                                         )
    #                                  )
 #                               self.message = 'from: %s, %s = %s' % (transportAddress,
 #                                                            name.prettyPrint(),
#                                                             val.prettyPrint()
#                                                             )
                            # SAVE DATA


                  # Stop on EOM
                #for oid, val in varBindTable[-1]:
                #    if not isinstance(val, v2c.Null):
                #        break
                #else:
                transportDispatcher.jobFinished(1)


                self.find_data()


#                self.set_exit(snmp_dict[int(self.instance)])

                # Generate request for next row
                v2c.apiBulkPDU.setVarBinds(self.reqPDU,
                                           [ (x, v2c.null) for x,y in varBindTable[-1] ])
                v2c.apiBulkPDU.setRequestID(self.reqPDU, v2c.getNextRequestID())
                transportDispatcher.sendMessage(encoder.encode(self.reqMsg),
                                                transportDomain,
                                                transportAddress)
                if time.time() - self.start_time> self.timeout:
                    self.set_exit("Request timed out", rc=3)
                    return wholeMsg
                self.start_time = time.time()
        return wholeMsg

    def callback_timer(self, timeNow):
        if timeNow - self.startedAt > self.timeout:
            self.set_exit("Request timed out", rc=3)

    def is_done(self):
        return self.state == 'received'


def parse_args(cmd_args):
    #Default params
    host = None
    community = 'public'
    version = '2c'
    datasource = None
    update = 300
    data_type = None
    instance = 0
    #Manage the options
    try:
        options, args = getopt.getopt(cmd_args,
                        'H:C:V:i:u:w:c:t:',
                        ['hostname=', 'community=', 'snmp-version=',
                         'type=', 'help', 'version',
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
            warning = value
        elif option_name in ("-c", "--critical"):
            critical = value
        elif option_name in ("-C", "--community"):
            community = value
        elif option_name in ("-t", "--type"):
            data_type = value
        elif option_name in ("-i", "--instance"):
            instance = value
        elif option_name in ("-V", "--snmp-version"):
            version = value

    return (hostname, community, version,
            data_type, instance)


class Snmp_poller(BaseModule):
    """Just print some stuff
    """
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.datasource_file = getattr(mod_conf, 'datasource_file', None)
        self.memcached_host = getattr(mod_conf, 'memcached_host', "127.0.0.1")
        self.memcached_port = getattr(mod_conf, 'memcached_port', 11211)

        # Kill snmp booster if config_file is not set
    def init(self):
        """Called by poller to say 'let's prepare yourself guy'"""
        print "Initialization of the snmp poller module"
        self.i_am_dying = False

        # Config validation
        if self.datasource_file == None:
            logger.error("Please set config_file parameter")
            self.i_am_dying = True
            return

        # Prepare memcached connection
        memcached_address = "%s:%s" % (self.memcached_host, self.memcached_port)
        self.memcached = memcache.Client([memcached_address], debug=0)
        # Check if memcached server is available
        if not self.memcached.get_stats():
            logger.error("Memcache server (%s) is not reachable" % memcached_address)
            self.i_am_dying = True
            return
            
        # Read datasource file
        self.datasource = ConfigObj(self.datasource_file,
                                    interpolation='template')
        # Store config in memcache
        self.memcached.set('datasource', self.datasource)

#        OIDS = dict([(name, oid) for name, oid in self.config['DATASOURCE']['TYPE'].items() if not isinstance(oid, Section)])

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
        except Empty , exp:
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
                clean_command = shlex.split(chk.command.encode('utf8', 'ignore'))
                # If the command seems good
                if len(clean_command) > 1:
                    # we do not want the first member, check_snmp thing
                    args = parse_args(clean_command[1:])
                    (host, community, version,
                          data_type, instance) = args
                    #print args
                else:
                    # Set an error so we will quit tis check
                    command = None

                # If we do not have the good args, we bail out for this check
                if host is None:
                    chk.status = 'done'
                    chk.exit_status = 2
                    chk.get_outputs("Error : `host' parameter is not correct.", 8012)
                    chk.execution_time = 0.0
                    continue
                
                # Ok we are good, we go on
                n = SNMPAsyncClient(host, community, version,
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
                except IOError , exp:
                    print "[%d]Exiting: %s" % (self.id, exp)
                    sys.exit(2)
                continue
            # Then we check for good checks
            #if c.status == 'launched' and c.con.is_done():
            if c.status == 'launched' and c.con.is_done():
                n = c.con
                c.status = 'done'
                c.exit_status = getattr(n, 'rc', 3)
                c.get_outputs(getattr(n, 'message', 'Error in launching command.'), 8012)
                c.execution_time  = getattr(n, 'execution_time', 0.0)

                # unlink our object from the original check
                if hasattr(c, 'con'):
                    delattr(c, 'con')

                # and set this check for deleting
                # and try to send it
                to_del.append(c)
                try:
                    self.returns_queue.put(c)
                except IOError , exp:
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
            except :
                pass

            #TODO : better time management
            time.sleep(.1)

            timeout -= time.time() - begin
            if timeout < 0:
                timeout = 1.0


