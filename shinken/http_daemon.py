#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

from __future__ import absolute_import, division, print_function, unicode_literals

import six
import sys
import errno
import time
import socket
import select
import inspect
import json
import zlib
import base64
import threading
import traceback
import io
from bottle import abort

try:
    import ssl
except ImportError:
    ssl = None
    SSLAdapter = None
try:
    from OpenSSL import SSL
except ImportError:
    SSL = None
    SSLAdapter = None

try:
    from cheroot.wsgi import Server as CherryPyWSGIServer
    if SSL is not None:
        from cheroot.ssl.pyopenssl import pyOpenSSLAdapter as SSLAdapter
except ImportError:
    try:
        from cherrypy.wsgiserver import CherryPyWSGIServer
        if SSL is not None:
            if six.PY2:
                from cherrypy.wsgiserver.ssl_pyopenssl import pyOpenSSLAdapter as SSLAdapter
            else:
                # A bug in CherryPy prevents from using pyOpenSSLAdapter
                # with python3: https://github.com/cherrypy/cherrypy/issues/1399
                # This has been fixed in cherrypy >= 9.0.0
                # If performance is an issue, please consider upgrading cherrypy
                from cherrypy.wsgiserver.ssl_builtin import BuiltinSSLAdapter as SSLAdapter
    except ImportError:
        CherryPyWSGIServer = None

if CherryPyWSGIServer and SSLAdapter:
    # Create 'safe' SSL adapter by disabling SSLv2/SSLv3 connections
    class SafeSSLAdapter(SSLAdapter):
        def get_context(self):
            c = SSLAdapter.get_context(self)
            c.set_options(SSL.OP_NO_SSLv2 |
                          SSL.OP_NO_SSLv3)
            return c
else:
    SafeSSLAdapter = None

from wsgiref import simple_server

# load global helper objects for logs and stats computation
from shinken.log import logger
from shinken.stats import statsmgr
from shinken.serializer import deserialize

# Let's load bottle! :)
import bottle
bottle.debug(True)


class InvalidWorkDir(Exception):
    pass


class PortNotFree(Exception):
    pass


# CherryPy is allowing us to have a HTTP 1.1 server, and so have a KeepAlive
class CherryPyServer(bottle.ServerAdapter):

    run_callback = None

    def run(self, handler):  # pragma: no cover
        daemon_thread_pool_size = self.options['daemon_thread_pool_size']
        server = CherryPyWSGIServer(
            (self.host, self.port),
            handler,
            numthreads=daemon_thread_pool_size,
            shutdown_timeout=1
        )
        logger.info('Initializing a CherryPy backend with %d threads', daemon_thread_pool_size)
        use_ssl = self.options['use_ssl']
        ca_cert = self.options['ca_cert']
        ssl_cert = self.options['ssl_cert']
        ssl_key = self.options['ssl_key']
        if SafeSSLAdapter and use_ssl:
            server.ssl_adapter = SafeSSLAdapter(ssl_cert, ssl_key, ca_cert)
        if use_ssl:
            server.ssl_certificate = ssl_cert
            server.ssl_private_key = ssl_key
        if CherryPyServer.run_callback is not None:
            CherryPyServer.run_callback(server)
        return server


class CherryPyBackend(object):
    def __init__(self, host, port, use_ssl, ca_cert, ssl_key,
                 ssl_cert, hard_ssl_name_check, daemon_thread_pool_size):
        self.port = port
        self.use_ssl = use_ssl
        self.srv = None

        try:
            def register_server(server):
                self.srv = server

            CherryPyServer.run_callback = staticmethod(register_server)

            bottle.run(
                host=host,
                port=port,
                server=CherryPyServer,
                quiet=False,
                use_ssl=use_ssl,
                ca_cert=ca_cert,
                ssl_key=ssl_key,
                ssl_cert=ssl_cert,
                daemon_thread_pool_size=daemon_thread_pool_size
            )
        except socket.error as exp:
            msg = "Error: Sorry, the port %d is not free: %s" % (self.port, exp)
            raise PortNotFree(msg)
        except Exception as e:
            # must be a problem with http workdir:
            raise InvalidWorkDir(e)


    # When call, it do not have a socket
    def get_sockets(self):
        return []


    # We stop our processing, but also try to hard close our socket as cherrypy is not doing it...
    def stop(self):
        # TODO: find why, but in ssl mode the stop() is locking, so bailout before
        if self.use_ssl:
            return
        try:
            self.srv.stop()
        except Exception as exp:
            logger.warning('Cannot stop the CherryPy backend : %s', exp)


    # Will run and LOCK
    def run(self):
        try:
            self.srv.start()
        except socket.error as exp:
            msg = "Error: Sorry, the port %d is not free: %s" % (self.port, exp)
            # from None stops the processing of `exp`: prevents exception in
            # exception error
            # PY23COMPAT: raise from not supported in python2
            #raise PortNotFree(msg) from None
            six.raise_from(exp, None)
        finally:
            try:
                self.srv.stop()
            except Exception:
                pass


# WSGIRef is the default HTTP server, it CAN manage HTTPS, but at a Huge cost for the client,
# because it's only HTTP1.0
# so no Keep-Alive, and in HTTPS it's just a nightmare
class WSGIREFAdapter(bottle.ServerAdapter):

    run_callback = None

    def run(self, handler):
        daemon_thread_pool_size = self.options['daemon_thread_pool_size']
        from wsgiref.simple_server import WSGIRequestHandler
        LoggerHandler = WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw):
                    pass
            LoggerHandler = QuietHandler

        srv = simple_server.make_server(
            self.host,
            self.port,
            handler,
            handler_class=LoggerHandler
        )
        logger.info('Initializing a wsgiref backend with %d threads', daemon_thread_pool_size)
        use_ssl = self.options['use_ssl']
        ca_cert = self.options['ca_cert']
        ssl_cert = self.options['ssl_cert']
        ssl_key = self.options['ssl_key']

        if use_ssl:
            if not ssl:
                logger.error("Missing python-openssl library,"
                             "please install it to open a https backend")
                raise Exception("Missing python-openssl library, "
                                "please install it to open a https backend")
            srv.socket = ssl.wrap_socket(
                srv.socket,
                keyfile=ssl_key,
                certfile=ssl_cert,
                server_side=True
            )
        if WSGIREFAdapter.run_callback is not None:
            WSGIREFAdapter.run_callback(srv)
        return srv


class WSGIREFBackend(object):
    def __init__(self, host, port, use_ssl, ca_cert, ssl_key,
                 ssl_cert, hard_ssl_name_check, daemon_thread_pool_size):
        self.daemon_thread_pool_size = daemon_thread_pool_size
        self.srv = None

        try:
            def register_server(server):
                self.srv = server

            WSGIREFAdapter.run_callback = staticmethod(register_server)

            bottle.run(
                host=host,
                port=port,
                server=WSGIREFAdapter,
                quiet=True,
                use_ssl=use_ssl,
                ca_cert=ca_cert,
                ssl_key=ssl_key, ssl_cert=ssl_cert,
                daemon_thread_pool_size=daemon_thread_pool_size
            )
        except socket.error as exp:
            msg = "Error: Sorry, the port %d is not free: %s" % (port, exp)
            raise PortNotFree(msg)


    def get_sockets(self):
        if self.srv.socket:
            return [self.srv.socket]
        else:
            return []


    def get_socks_activity(self, socks, timeout):
        try:
            ins, _, _ = select.select(socks, [], [], timeout)
        except select.error as e:
            if six.PY2:
                err, _ = e
            else:
                err = e.errno
            if err == errno.EINTR:
                return []
            elif err == errno.EBADF:
                logger.error('Failed to handle request: %s', e)
                return []
            raise
        return ins


    # We are asking us to stop, so we close our sockets
    def stop(self):
        for s in self.get_sockets():
            try:
                s.close()
            except Exception:
                pass
            self.srv.socket = None


    # Manually manage the number of threads
    def run(self):
        # Ok create the thread
        nb_threads = self.daemon_thread_pool_size
        # Keep a list of our running threads
        threads = []
        logger.info('Using a %d http pool size', nb_threads)
        while True:
            # We must not run too much threads, so we will loop until
            # we got at least one free slot available
            free_slots = 0
            while free_slots <= 0:
                to_del = [t for t in threads if not t.is_alive()]
                for t in to_del:
                    t.join()
                    threads.remove(t)
                free_slots = nb_threads - len(threads)
                if free_slots <= 0:
                    time.sleep(0.01)

            socks = self.get_sockets()
            # Blocking for 0.1 s max here
            ins = self.get_socks_activity(socks, 0.1)
            if len(ins) == 0:  # trivial case: no fd activity:
                continue
            # If we got activity, Go for a new thread!
            for sock in socks:
                if sock in ins:
                    # GO!
                    t = threading.Thread(
                        None,
                        target=self.handle_one_request_thread,
                        name='http-request',
                        args=(sock,)
                    )
                    # We don't want to hang the master thread just because this one is still alive
                    t.daemon = True
                    t.start()
                    threads.append(t)


    def handle_one_request_thread(self, sock):
        self.srv.handle_request()



class HTTPDaemon(object):
    def __init__(self, host, port, http_backend, use_ssl, ca_cert,
                 ssl_key, ssl_cert, hard_ssl_name_check,
                 daemon_thread_pool_size):
        self.port = port
        self.host = host
        self.srv = None
        # Port = 0 means "I don't want HTTP server"
        if self.port == 0:
            return

        self.use_ssl = use_ssl

        self.registered_fun = {}
        self.registered_fun_names = []
        self.registered_fun_defaults = {}

        protocol = 'http'
        if use_ssl:
            protocol = 'https'
        self.uri = '%s://%s:%s' % (protocol, self.host, self.port)
        logger.info("Opening HTTP socket at %s", self.uri)

        if http_backend == 'cherrypy' or http_backend == 'auto' and CherryPyWSGIServer:
            self.srv = CherryPyBackend(
                host,
                port,
                use_ssl,
                ca_cert,
                ssl_key,
                ssl_cert,
                hard_ssl_name_check,
                daemon_thread_pool_size
            )
        else:
            logger.warning('Loading the old WSGI Backend. CherryPy >= 3 is recommanded instead')
            self.srv = WSGIREFBackend(
                host,
                port,
                use_ssl,
                ca_cert,
                ssl_key,
                ssl_cert,
                hard_ssl_name_check,
                daemon_thread_pool_size
            )

        self.lock = threading.RLock()


    # Get the server socket but not if disabled or closed
    def get_sockets(self):
        if self.port == 0 or self.srv is None:
            return []
        return self.srv.get_sockets()


    def run(self):
        self.srv.run()


    def _parse_request_params(self, cbname, method, request, args=[]):
        """
        Parses the incoming request, and process the callback parametrs

        :param list args: The callback parameters
        :rtype: mixed
        :return: The callback parameters
        """
        if method in ('get', 'post'):
            parms = {}
            for arg in args:
                val = None
                if method == 'post':
                    val = request.forms.get(arg, None)
                elif method == 'get':
                    val = request.GET.get(arg, None)
                if val:
                    parms[arg] = val
                else:
                    # Checks if the missing arg has a default value
                    default_args = self.registered_fun_defaults.get(cbname, {})
                    if arg not in default_args:
                        abort(400, 'Missing argument %s. request=%s' % arg)
            return parms
        elif method == 'put':
            content = request.body
            return deserialize(content)
        else:
            abort(400, 'Unmanaged HTTP method: %s' % method)


    def register(self, obj):
        methods = inspect.getmembers(obj, predicate=inspect.ismethod)
        merge = [
            cbname for (cbname, callback) in methods
            if cbname in self.registered_fun_names
        ]
        if merge != []:
            methods_in = [
                m.__name__ for m in obj.__class__.__dict__.values()
                if inspect.isfunction(m)
            ]
            methods = [m for m in methods if m[0] in methods_in]
        for (cbname, callback) in methods:
            if cbname.startswith('_'):
                continue
            # Get the args of the function to catch them in the queries
            if six.PY2:
                argspec = inspect.getargspec(callback)
                keywords = argspec.keywords
            else:
                argspec = inspect.getfullargspec(callback)
                keywords = argspec.varkw
            args = argspec.args
            varargs = argspec.varargs
            defaults = argspec.defaults
            # If we got some defauts, save arg=value so we can lookup
            # for them after
            if defaults:
                default_args = zip(
                    argspec.args[-len(argspec.defaults):],
                    argspec.defaults
                )
                _d = {}
                for (argname, defavalue) in default_args:
                    _d[argname] = defavalue
                self.registered_fun_defaults[cbname] = _d
            # remove useless self in args, because we alredy got a bonded method callback
            if 'self' in args:
                args.remove('self')
            #print("Registering", cbname, args, obj)
            self.registered_fun_names.append(cbname)
            self.registered_fun[cbname] = (callback)

            # WARNING : we MUST do a 2 levels function here, or the f_wrapper
            # will be uniq and so will link to the last function again
            # and again
            def register_callback(cbname, args, callback, obj, lock):
                def f_wrapper():
                    try:
                        t0 = time.time()
                        args_time = aqu_lock_time = calling_time = json_time = 0
                        need_lock = getattr(callback, 'need_lock', True)

                        # Warning : put the bottle.response set inside the wrapper
                        # because outside it will break bottle
                        method = getattr(callback, 'method', 'get').lower()
                        params = self._parse_request_params(
                            cbname,
                            method,
                            bottle.request,
                            args
                        )

                        t1 = time.time()
                        args_time = t1 - t0

                        if need_lock:
                            logger.debug("HTTP: calling lock for %s", cbname)
                            lock.acquire()

                        t2 = time.time()
                        aqu_lock_time = t2 - t1

                        try:
                            if method in ('get', 'post'):
                                cbres = callback(**params)
                            else:
                                cbres = callback(params)
                        # Always call the lock release if need
                        finally:
                            # Ok now we can release the lock
                            if need_lock:
                                lock.release()

                        t3 = time.time()
                        calling_time = t3 - t2

                        global_time = t3 - t0
                        logger.debug(
                            "Debug perf: %s [args:%s] [aqu_lock:%s] "
                            "[calling:%s] [global:%s]",
                            cbname,
                            args_time,
                            aqu_lock_time,
                            calling_time,
                            global_time
                        )
                        lst = [
                            ('args', args_time),
                            ('aqulock', aqu_lock_time),
                            ('calling', calling_time),
                            ('global', global_time)
                        ]
                        # increase the stats timers
                        for (k, _t) in lst:
                            statsmgr.timing('http.%s.%s' % (cbname, k), _t, 'perf')

                        return cbres
                    except Exception as e:
                        logger.error("HTTP Request error: %s", e)
                        logger.error("function: %s", cbname)
                        logger.error("object: %s", obj)
                        logger.error(traceback.format_exc())
                        abort(500, "Internal Server Error: %s\n. Please check server logs for more details" % e)

                # Ok now really put the route in place
                bottle.route('/' + cbname, callback=f_wrapper,
                             method=getattr(callback, 'method', 'get').upper())
                # and the name with - instead of _ if need
                cbname_dash = cbname.replace('_', '-')
                if cbname_dash != cbname:
                    bottle.route('/' + cbname_dash, callback=f_wrapper,
                                 method=getattr(callback, 'method', 'get').upper())


            register_callback(cbname, args, callback, obj, self.lock)

        # Add a simple / page
        def slash():
            return "OK"
        bottle.route('/', callback=slash)


    def unregister(self, obj):
        return


    def handleRequests(self, s):
        self.srv.handle_request()


    # Close all sockets and delete the server object to be sure
    # no one is still alive
    def shutdown(self):
        if self.srv is not None:
            self.srv.stop()
            self.srv = None


    def get_socks_activity(self, timeout):
        try:
            ins, _, _ = select.select(self.get_sockets(), [], [], timeout)
        except select.error as e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins


# TODO: clean this hack:
# see usage within basemodule & http_daemon.
daemon_inst = None
