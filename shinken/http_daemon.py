#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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

import select
import errno
import time
import socket
import copy
import cPickle
import inspect
import json
import zlib
import threading
try:
    import ssl
except ImportError:
    ssl = None
from wsgiref import simple_server

from log import logger

# Let's load bottlecore! :)
from shinken.webui import bottlecore as bottle
bottle.debug(True)



class InvalidWorkDir(Exception):
    pass


class PortNotFree(Exception):
    pass


class WSGIRefServerSelect(bottle.ServerAdapter):
    def run(self, handler):  # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        srv = make_server(self.host, self.port, handler, **self.options)
        return srv



class SecureServer(simple_server.WSGIServer):
    pass


class SecureHandler (simple_server.WSGIRequestHandler):
    def handle (self):
        #for part in self.connection.getpeercert()["subject"]:
        #    print "DBG", part[0][0]
        #    if part[0][0] == "commonName":
        #        print "### client is %s" % part[0][1]
        #        break
        #else:
        #    raise ssl.CertificateError, "no matching user"
        simple_server.WSGIRequestHandler.handle(self)
        
    def get_environ( self):
        env = simple_server.WSGIRequestHandler.get_environ( self)

        if isinstance( self.request, ssl.SSLSocket):
            env['HTTPS'] = 'on'
        return env


class SecureAdapter (bottle.ServerAdapter):
    def run (self, handler):
        srv = simple_server.make_server(self.host, self.port, handler,
                                        server_class=SecureServer,
                                        #handler_class=SecureHandler,
                                        **self.options)
        print "SOCKET?", srv.socket

        print srv.__dict__
        print srv.RequestHandlerClass.__dict__
        print "ENVIRON"
        
        srv.socket = ssl.wrap_socket(srv.socket,
                        keyfile="/tmp/ssl.key", certfile="/tmp/ssl.cert", server_side=True)
        return srv



class HTTPDaemon(object):
        def __init__(self, host, port, use_ssl=False):
            self.port = port
            self.host = host
            # Port = 0 means "I don't want pyro"
            if self.port == 0:
                return

            self.uri = 'http://%s:%s' % (self.host, self.port)
            logger.info("Initializing HTTP connection with host:%s port:%s ssl:%s" % (host, port, str(use_ssl)))


            # Hack the BaseHTTPServer so only IP will be looked by wsgiref, and not names
            __import__('BaseHTTPServer').BaseHTTPRequestHandler.address_string = lambda x:x.client_address[0]
            # And port already use now raise an exception
            try:
                #self.srv = bottle.run(host=self.host, port=self.port, server=WSGIRefServerSelect, quiet=False)
                self.srv = bottle.run(host=self.host, port=self.port, server=SecureAdapter, quiet=False)
            except socket.error, exp:
                msg = "Error: Sorry, the port %d is not free: %s" % (port, str(exp))
                raise PortNotFree(msg)
            except Exception, e:
                # must be a problem with pyro workdir:
                raise InvalidWorkDir(e)

            self.lock = threading.RLock()

            #@bottle.error(code=500)
            #def error500(err):
            #    print err.__dict__
            #    return 'FUCKING ERROR 500', str(err)

            
        
        # Get the server socket but not if disabled or closed
        def get_sockets(self):
            if self.port == 0 or self.srv is None:
                return []
            return [self.srv.socket]



        def register(self, obj):
            methods = inspect.getmembers(obj, predicate=inspect.ismethod)
            for (fname, f) in methods:
                # Slip private functions
                if fname.startswith('_'):
                    continue
                # Get the args of the function to catch them in the queries
                argspec = inspect.getargspec(f)
                args = argspec.args
                varargs = argspec.varargs
                keywords = argspec.keywords
                defaults = argspec.defaults
                # remove useless self in args, because we alredy got a bonded method f
                if 'self' in args:
                    args.remove('self')
                print "Registering", fname, args
                # WARNING : we MUST do a 2 levels function here, or the f_wrapper
                # will be uniq and so will link to the last function again
                # and again
                def register_callback(fname, args, f, obj, lock):
                    def f_wrapper():
                        need_lock = getattr(f, 'need_lock', True)
                        
                        # Warning : put the bottle.response set inside the wrapper
                        # because outside it will break bottle
                        d = {}
                        method = getattr(f, 'method', 'get').lower()
                        for aname in args:
                            v = None
                            if method == 'post':
                                v = bottle.request.forms.get(aname, None)
                                # Post args are zlibed and cPickled
                                if v is not None:
                                    v = zlib.decompress(v)
                                    v = cPickle.loads(v)
                            elif method == 'get':
                                v = bottle.request.GET.get(aname, None)
                            if v is None:
                                raise Exception('Missing argument %s' % aname)
                            d[aname] = v
                        if need_lock:
                            logger.debug("HTTP: calling lock for %s" % fname)
                            lock.acquire()

                        ret = f(**d)

                        # Ok now we can release the lock
                        if need_lock:
                            lock.release()

                        encode = getattr(f, 'encode', 'json').lower()
                        j = json.dumps(ret)
                        return j
                    # Ok now really put the route in place
                    bottle.route('/'+fname, callback=f_wrapper, method=getattr(f, 'method', 'get').upper())
                register_callback(fname, args, f, obj, self.lock)

            # Add a simple / page
            def slash():
                return "OK"
            bottle.route('/', callback=slash)


        def unregister(self, obj):
            return


        def handleRequests(self, s):
            self.srv.handle_request()
            
            
        def create_uri(address, port, obj_name, use_ssl=False):
            return "PYRO:%s@%s:%d" % (obj_name, address, port)


        def set_timeout(con, timeout):
            con._pyroTimeout = timeout


        # Close all sockets and delete the server object to be sure
        # no one is still alive
        def shutdown(con):
            print "STOP HTTP"
            for s in con.get_sockets():
                s.close()
            con.srv = None



        def get_socks_activity(self, timeout):
            try:
                ins, _, _ = select.select(self.get_sockets(), [], [], timeout)
            except select.error, e:
                errnum, _ = e
                if errnum == errno.EINTR:
                    return []
                raise
            return ins


daemon_inst = None
