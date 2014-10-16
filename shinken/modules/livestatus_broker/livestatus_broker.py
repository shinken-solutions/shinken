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

"""
This Class is a plugin for the Shinken Broker. It is in charge
to get broks, recreate real objects and present them through
a livestatus query interface
"""

import select
import socket
import os
import time
import errno
import re
import traceback
import Queue
import threading
import gc

from shinken.macroresolver import MacroResolver
from shinken.basemodule import BaseModule
from shinken.message import Message
from shinken.log import logger
from shinken.modules.livestatus_broker.livestatus_client_thread import LiveStatusClientThread
from shinken.modulesmanager import ModulesManager
from shinken.objects.module import Module
from shinken.daemon import Daemon
from shinken.misc.datamanager import datamgr

# Local import
from livestatus import LiveStatus
from livestatus_regenerator import LiveStatusRegenerator
from livestatus_query_cache import LiveStatusQueryCache



def full_safe_close(socket):
    try:
        socket.shutdown(2)
    except Exception as err:
        logger.warning('Error on socket shutdown: %s' % err)
    try:
        socket.close()
    except Exception as err:
        logger.warning('Error on socket close: %s' % err)


# Class for the LiveStatus Broker
# Get broks and listen to livestatus query language requests
class LiveStatus_broker(BaseModule, Daemon):

    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        # We can be in a scheduler. If so, we keep a link to it to speed up regenerator phase
        self.scheduler = None
        self.plugins = []
        self.use_threads = (getattr(modconf, 'use_threads', '0') == '1')
        self.host = getattr(modconf, 'host', '127.0.0.1')
        if self.host == '*':
            self.host = '0.0.0.0'
        self.port = getattr(modconf, 'port', None)
        self.socket = getattr(modconf, 'socket', None)
        if self.port == 'none':
            self.port = None
        if self.port:
            self.port = int(self.port)
        if self.socket == 'none':
            self.socket = None
        self.allowed_hosts = getattr(modconf, 'allowed_hosts', '')
        ips = [ip.strip() for ip in self.allowed_hosts.split(',') if ip]
        self.allowed_hosts = [ip for ip in ips if re.match(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip)]
        if len(ips) != len(self.allowed_hosts):
            logger.warning("[Livestatus Broker] Warning: the list of allowed hosts is invalid. %s" % str(ips))
            logger.warning("[Livestatus Broker] Warning: the list of allowed hosts is invalid. %s" % str(self.allowed_hosts))
            raise
        self.pnp_path = getattr(modconf, 'pnp_path', '')
        self.debug = getattr(modconf, 'debug', None)
        self.debug_queries = (getattr(modconf, 'debug_queries', '0') == '1')
        self.debug_queries = True
        self.use_query_cache = (getattr(modconf, 'query_cache', '0') == '1')
        if getattr(modconf, 'service_authorization', 'loose') == 'strict':
            self.service_authorization_strict = True
        else:
            self.service_authorization_strict = False
        if getattr(modconf, 'group_authorization', 'strict') == 'strict':
            self.group_authorization_strict = True
        else:
            self.group_authorization_strict = False

        #  This is an "artificial" module which is used when an old-style
        #  shinken-specific.cfg without a separate logstore-module is found.
        self.compat_sqlite = {
            'module_name': 'LogStore',
            'module_type': 'logstore_sqlite',
            'use_aggressive_sql': "0",
            'database_file': getattr(modconf, 'database_file', None),
            'archive_path': getattr(modconf, 'archive_path', None),
            'max_logs_age': getattr(modconf, 'max_logs_age', None),
        }
        # We need to have our regenerator now because it will need to load
        # data from scheduler before main() if in scheduler of course
        self.rg = LiveStatusRegenerator(self.service_authorization_strict, self.group_authorization_strict)
        self.client_connections = {} # keys will be socket of client, values are LiveStatusClientThread instances
        self.db = None
        self._listening_thread = threading.Thread(target=self._listening_thread_run)

    def add_compatibility_sqlite_module(self):
        if len([m for m in self.modules_manager.instances if m.properties['type'].startswith('logstore_')]) == 0:
            #  this shinken-specific.cfg does not use the new submodules
            for k in self.compat_sqlite.keys():
                if self.compat_sqlite[k] == None:
                    del self.compat_sqlite[k]
            dbmod = Module(self.compat_sqlite)
            self.modules_manager.set_modules([dbmod])
            self.modules_manager.load_and_init()
            self.modules_manager.instances[0].load(self)

    # Called by Broker so we can do init stuff
    # TODO: add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        logger.info("[Livestatus Broker] Init of the Livestatus '%s'" % self.name)
        self.prepare_pnp_path()
        m = MacroResolver() # TODO: don't know/think these 2 lines are necessary..
        m.output_macros = ['HOSTOUTPUT', 'HOSTPERFDATA', 'HOSTACKAUTHOR', 'HOSTACKCOMMENT', 'SERVICEOUTPUT', 'SERVICEPERFDATA', 'SERVICEACKAUTHOR', 'SERVICEACKCOMMENT']
        self.rg.load_external_queue(self.from_q)

    # This is called only when we are in a scheduler
    # and just before we are started. So we can gain time, and
    # just load all scheduler objects without fear :) (we
    # will be in another process, so we will be able to hack objects
    # if need)
    def hook_pre_scheduler_mod_start(self, sched):
        logger.info("[Livestatus Broker] pre_scheduler_mod_start::" % str(sched.__dict__))
        self.rg.load_from_scheduler(sched)

    # In a scheduler we will have a filter of what we really want as a brok
    def want_brok(self, b):
        return self.rg.want_brok(b)

    def prepare_pnp_path(self):
        if not self.pnp_path:
            self.pnp_path = False
        elif not os.access(self.pnp_path, os.R_OK):
            logger.warning("[Livestatus Broker] PNP perfdata path %s is not readable" % self.pnp_path)
        elif not os.access(self.pnp_path, os.F_OK):
            logger.warning("[Livestatus Broker] PNP perfdata path %s does not exist" % self.pnp_path)
        if self.pnp_path and not self.pnp_path.endswith('/'):
            self.pnp_path += '/'

    def set_debug(self):
        fdtemp = os.open(self.debug, os.O_CREAT | os.O_WRONLY | os.O_APPEND)
        ## We close out and err
        os.close(1)
        os.close(2)
        os.dup2(fdtemp, 1)  # standard output (1)
        os.dup2(fdtemp, 2)  # standard error (2)

    def main(self):
        self.set_proctitle(self.name)

        self.log = logger
        self.log.load_obj(self)
        # Daemon like init
        self.debug_output = []

        self.modules_manager = ModulesManager('livestatus', self.find_modules_path(), [])
        self.modules_manager.set_modules(self.modules)
        # We can now output some previously silenced debug output
        self.do_load_modules()
        for inst in self.modules_manager.instances:
            if inst.properties["type"].startswith('logstore'):
                f = getattr(inst, 'load', None)
                if f and callable(f):
                    f(self)
                break
        for s in self.debug_output:
            logger.debug("[Livestatus Broker] %s" % s)
        del self.debug_output
        self.add_compatibility_sqlite_module()
        self.datamgr = datamgr
        datamgr.load(self.rg)
        self.query_cache = LiveStatusQueryCache()
        if not self.use_query_cache:
            self.query_cache.disable()
        self.rg.register_cache(self.query_cache)

        try:
            #import cProfile
            #cProfile.runctx('''self.do_main()''', globals(), locals(),'/tmp/livestatus.profile')
            self.do_main()
        except Exception, exp:
            msg = Message(id=0, type='ICrash', data={
                'name': self.get_name(),
                'exception': exp,
                'trace': traceback.format_exc()
            })
            self.from_q.put(msg)
            # wait 2 sec so we know that the broker got our message, and die
            time.sleep(2)
            raise

    # A plugin send us en external command. We just put it
    # in the good queue
    def push_external_command(self, e):
        logger.info("[Livestatus Broker] Got an external command: %s" % str(e.__dict__))
        self.from_q.put(e)

    # Real main function
    def do_main(self):
        # Maybe we got a debug dump to do
        if self.debug:
            self.set_debug()
        # I register my exit function
        self.set_exit_handler()
        logger.info("[Livestatus Broker] Go run")

        # Open the logging database
        self.db = self.modules_manager.instances[0]
        assert isinstance(self.db, BaseModule)
        self.db.open()
        if hasattr(self.db, 'prepare_log_db_table'):
            self.db.prepare_log_db_table()
            # Immediately archive data. This also splits old-style (storing logs
            # from more than one day) up into many single-day databases
            if self.db.max_logs_age > 0:
                self.db.log_db_do_archive()

        # We ill protect the operations on
        # the non read+write with a lock and
        # 2 int
        self.global_lock = threading.RLock()
        self.nb_readers = 0
        self.nb_writers = 0

        self.data_thread = None

        # Check if some og the required directories exist
        #if not os.path.exists(bottle.TEMPLATE_PATH[0]):
        #    logger.error('The view path do not exist at %s' % bottle.TEMPLATE_PATH)
        #    sys.exit(2)

        self.load_plugins()

        if self.use_threads:
            # Launch the data thread"
            logger.info("[Livestatus Broker] Starting Livestatus application")
            self.data_thread = threading.Thread(None, self.manage_brok_thread, 'datathread')
            self.data_thread.start()
            self.lql_thread = threading.Thread(None, self.manage_lql_thread, 'lqlthread')
            self.lql_thread.start()
            self.data_thread.join()
            self.lql_thread.join()
        else:
            self.manage_lql_thread()


    # It's the thread function that will get broks
    # and update data. Will lock the whole thing
    # while updating
    def manage_brok_thread(self):
        logger.info("[Livestatus Broker] Data thread started")
        while True:
            l = self.to_q.get()
            for b in l:
                # Un-serialize the brok data
                b.prepare()
                # For updating, we cannot do it while
                # answer queries, so wait for no readers
                self.wait_for_no_readers()
                try:
                    logger.debug("[Livestatus Broker] Got data lock, manage brok")
                    self.rg.manage_brok(b)
                    for mod in self.modules_manager.get_internal_instances():
                        try:
                            mod.manage_brok(b)
                        except Exception, exp:
                            logger.debug("[Livestatus Broker] %s" % str(exp.__dict__))
                            logger.warning("[%s] The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(), str(exp)))
                            logger.debug("[%s] Exception type: %s" % (self.name, type(exp)))
                            logger.debug("Back trace of this kill: %s" % (traceback.format_exc()))
                            self.modules_manager.set_to_restart(mod)
                except Exception, exp:
                    msg = Message(id=0, type='ICrash', data={
                        'name': self.get_name(),
                        'exception': exp,
                        'trace': traceback.format_exc()
                    })
                    self.from_q.put(msg)
                    # wait 2 sec so we know that the broker got our message, and die
                    time.sleep(2)
                    # No need to raise here, we are in a thread, exit!
                    os._exit(2)
                #finally:
                    # We can remove us as a writer from now. It's NOT an atomic operation
                    # so we REALLY not need a lock here (yes, I try without and I got
                    # a not so accurate value there....)
                    self.global_lock.acquire()
                    self.nb_writers -= 1
                    self.global_lock.release()

    # Here we will load all plugins (pages) under the webui/plugins
    # directory. Each one can have a page, views and htdocs dir that we must
    # route correctly
    def load_plugins(self):
        pass

    # It will say if we can launch a page rendering or not.
    # We can only if there is no writer running from now
    def wait_for_no_writers(self):
        while True:
            self.global_lock.acquire()
            # We will be able to run
            if self.nb_writers == 0:
                # Ok, we can run, register us as readers
                self.nb_readers += 1
                self.global_lock.release()
                break
            # Oups, a writer is in progress. We must wait a bit
            self.global_lock.release()
            # Before checking again, we should wait a bit
            # like 1ms
            time.sleep(0.001)

    # It will say if we can launch a brok management or not
    # We can only if there is no readers running from now
    def wait_for_no_readers(self):
        start = time.time()
        while True:
            self.global_lock.acquire()
            # We will be able to run
            if self.nb_readers == 0:
                # Ok, we can run, register us as writers
                self.nb_writers += 1
                self.global_lock.release()
                break
            # Ok, we cannot run now, wait a bit
            self.global_lock.release()
            # Before checking again, we should wait a bit
            # like 1ms
            time.sleep(0.001)
            # We should warn if we cannot update broks
            # for more than 30s because it can be not good
            if time.time() - start > 30:
                logger.warning("[Livestatus Broker] WARNING: we are in lock/read since more than 30s!")
                start = time.time()

    def manage_brok(self, brok):
        """We use this method mostly for the unit tests"""
        brok.prepare()
        self.rg.manage_brok(brok)
        for mod in self.modules_manager.get_internal_instances():
            try:
                mod.manage_brok(brok)
            except Exception, exp:
                logger.debug("[Livestatus Broker] %s" % str(exp.__dict__))
                logger.warning("[%s] The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(), str(exp)))
                logger.debug("[%s] Exception type: %s" % (self.name, type(exp)))
                logger.debug("Back trace of this kill: %s" % (traceback.format_exc()))
                self.modules_manager.set_to_restart(mod)

    def do_stop(self):
        logger.info("[Livestatus Broker] So I quit")
        for s in self.input:
            full_safe_close(s)
        # client threads could be stopped and joined by the listening_thread..
        for client in self.client_connections.values():
            assert isinstance(client, LiveStatusClientThread)
            client.request_stop()
        for client in self.client_connections.values():
            assert isinstance(client, LiveStatusClientThread)
            client.join()
        if self._listening_thread:
            self._listening_thread.join()
        try:
            self.db.close()
            pass
        except Exception as err:
            logger.warning('Error on db close: %s' % err)


    def create_listeners(self):
        backlog = 5
        self.listeners = []
        if self.port:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setblocking(0)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(backlog)
            self.listeners.append(server)
            logger.info("[Livestatus Broker] listening on tcp port: %d" % self.port)
        if self.socket:
            if os.path.exists(self.socket):
                os.remove(self.socket)
            # I f the socket dir is not existing, create it
            if not os.path.exists(os.path.dirname(self.socket)):
                os.mkdir(os.path.dirname(self.socket))
            os.umask(0)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.setblocking(0)
            sock.bind(self.socket)
            sock.listen(backlog)
            self.listeners.append(sock)
            logger.info("[Livestatus Broker] listening on unix socket: %s" % str(self.socket))
        self.input = self.listeners[:]


    def _listening_thread_run(self):
        while not self.interrupted:
            # Check for pending livestatus requests
            inputready, _, exceptready = select.select(self.input, [], [], 1)

            if len(exceptready) > 0:
                pass

            if len(inputready) > 0:
                for s in inputready:
                # We will identify sockets by their filehandle number
                # during the rest of this loop
                    #socketid = s.fileno()
                    if s in self.listeners:
                        # handle the server socket
                        sock, address = s.accept()
                        if isinstance(address, tuple):
                            client_ip, _ = address
                            if self.allowed_hosts and client_ip not in self.allowed_hosts:
                                logger.warning("[Livestatus Broker] Connection attempt from illegal ip address %s" % str(client_ip))
                                full_safe_close(sock)
                                continue

                        new_client = self.client_connections[sock] = LiveStatusClientThread(sock, address, self)
                        new_client.start()
                        self.livestatus.count_event('connections')

                # end for s in inputready:

            # At the end of this loop we probably will discard connections
            kick_connections = []
            for sock, client in self.client_connections.items():
                assert isinstance(client, LiveStatusClientThread)
                if client.is_alive():
                    pass
                else:
                    kick_connections.append(sock)

            for sock in kick_connections:
                del self.client_connections[sock]

            # try to force release memory:
            for name in 'query', 'response', 'data':
                try:                exec 'del %s' % name
                except NameError:   pass
            gc.collect()

    # It's the thread function that will get broks
    # and update data. Will lock the whole thing
    # while updating
    def manage_lql_thread(self):
        logger.info("[Livestatus Broker] Livestatus query thread started")
        # This is the main object of this broker where the action takes place
        self.livestatus = LiveStatus(self.datamgr, self.query_cache, self.db, self.pnp_path, self.from_q)
        self.create_listeners()
        self._listening_thread.start()

        while not self.interrupted:
            if self.use_threads:
                self.wait_for_no_writers()
                self.livestatus.counters.calc_rate()
            else:
                try:
                    l = self.to_q.get(True, 1)
                    for b in l:
                        # Un-serialize the brok data
                        b.prepare()
                        self.rg.manage_brok(b)
                        for mod in self.modules_manager.get_internal_instances():
                            try:
                                mod.manage_brok(b)
                            except Exception, exp:
                                logger.debug("[Livestatus Broker] %s" % str(exp.__dict__))
                                logger.warning("[%s] Warning: The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(), str(exp)))
                                logger.debug("[%s] Exception type: %s" % (self.name, type(exp)))
                                logger.debug("Back trace of this kill: %s" % (traceback.format_exc()))
                                self.modules_manager.set_to_restart(mod)
                except Queue.Empty:
                    self.livestatus.counters.calc_rate()
                except IOError, e:
                    if hasattr(os, 'errno') and e.errno != os.errno.EINTR:
                        raise
                except Exception, exp:
                    logger.debug("[Livestatus Broker] %s" % str(exp.__dict__))
                    logger.error("[%s] Warning: The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(), str(exp)))
                    logger.debug("[%s] Exception type: %s" % (self.name, type(exp)))
                    logger.debug("Back trace of this kill: %s" % (traceback.format_exc()))
                    raise

            # Commit log broks to the database
            self.db.commit_and_rotate_log_db()

        # end: while not self.interrupted:

        self.do_stop()

    def write_protocol(self, request, response):
        if self.debug_queries:
            print "REQUEST>>>>>\n" + request + "\n\n"
            #print "RESPONSE<<<<\n" + response + "\n\n"
