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
from log import logger

from shinken.webui import bottlecore as bottle

bottle.debug(True)

# Try to import Pyro (3 or 4.1) and if not, Pyro4 (4.2 and 4.3)
try:
    import Pyro
    import Pyro.core
except ImportError:  # ok, no Pyro3, maybe 4
    import Pyro4 as Pyro


""" This class is a wrapper for managing Pyro 3 and 4 version """


class InvalidWorkDir(Exception):
    pass


class PortNotFree(Exception):
    pass

PYRO_VERSION = 'UNKNOWN'


# Try to see if we are Python 3 or 4
try:
    Pyro.core.ObjBase
    # Some one already go here, so we are in 4 if None
    if Pyro.core.ObjBase is None:
        raise AttributeError

    PYRO_VERSION = Pyro.constants.VERSION
    Pyro.errors.CommunicationError = Pyro.errors.ProtocolError
    Pyro.errors.TimeoutError = Pyro.errors.ProtocolError


    class Pyro3Daemon(Pyro.core.Daemon):
        pyro_version = 3
        protocol = 'PYROLOC'

        def __init__(self, host, port, use_ssl=False):
            self.port = port
            # Port = 0 means "I don't want pyro"
            if self.port == 0:
                return
            try:
                Pyro.core.initServer()
            except (OSError, IOError), e:  # must be problem with workdir:
                raise InvalidWorkDir(e)
            # Set the protocol as asked (ssl or not)
            if use_ssl:
                prtcol = 'PYROSSL'
            else:
                prtcol = 'PYRO'

            logger.info("Initializing Pyro connection with host:%s port:%s ssl:%s" %
                        (host, port, str(use_ssl)))
            # Now the real start
            try:
                Pyro.core.Daemon.__init__(self, host=host, port=port, prtcol=prtcol, norange=True)
            except OSError, e:
                # must be problem with workdir:
                raise InvalidWorkDir(e)
            except Pyro.errors.DaemonError, e:
                msg = "Error: Sorry, the port %d is not free: %s" % (port, e)
                raise PortNotFree(msg)

        def register(self, obj, name):
            return self.connect(obj, name)

        def unregister(self, obj):
            try:
                self.disconnect(obj)
            except Exception:
                pass

        def get_sockets(self):
            if self.port != 0:
                return self.getServerSockets()
            return []

        def handleRequests(self, s):
            try:
                Pyro.core.Daemon.handleRequests(self)
            # Sometime Pyro send us xml pickling implementation (gnosis) is not available
            # and I don't know why... :(
            except NotImplementedError:
                pass
            # Maybe it's just a protocol error, like someone with a telnet
            # tying to talk with us, bypass this
            except ProtocolError:
                pass
                logger.warning("Someone is talking to me in a strange language!")


    def create_uri(address, port, obj_name, use_ssl):
        if not use_ssl:
            return "PYROLOC://%s:%d/%s" % (address, port, obj_name)
        else:
            return "PYROLOCSSL://%s:%d/%s" % (address, port, obj_name)


    # Timeout way is also changed between 3 and 4
    # it's a method in 3, a property in 4
    def set_timeout(con, timeout):
        con._setTimeout(timeout)


    def getProxy(uri):
        return Pyro.core.getProxyForURI(uri)


    # Shutdown in 3 take True as arg
    def shutdown(con):
        con.shutdown(True)

    PyroClass = Pyro3Daemon


except AttributeError, exp:

    PYRO_VERSION = Pyro.constants.VERSION
    # Ok, in Pyro 4, interface do not need to
    # inherit from ObjBase, just a dummy class is good
    Pyro.core.ObjBase = dict
    Pyro.errors.URIError = Pyro.errors.ProtocolError
    Pyro.core.getProxyForURI = Pyro.core.Proxy
    Pyro.config.HMAC_KEY = "NOTSET"

    old_versions = ["4.1", "4.2", "4.3", "4.4"]

    # Version not supported for now, we have to work on it
    bad_versions = []
    last_known_working_version = "4.14"
    msg_waitall_issue_versions = ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", '4.8',
                                  '4.9', '4.10', '4.11', '4.12', '4.13']

    class Pyro4Daemon(Pyro.core.Daemon):
        pyro_version = 4
        protocol = 'PYRO'

        def __init__(self, host, port, use_ssl=False):
            self.port = port
            self.host = host
            # Port = 0 means "I don't want pyro"
            if self.port == 0:
                return

            self.uri = 'http://%s:%s' % (self.host, self.port)
            logger.info("Initializing HTTP connection with host:%s port:%s ssl:%s" % (host, port, str(use_ssl)))

            # And port already use now raise an exception
            try:
                self.srv = bottle.run(host=self.host, port=self.port, server='wsgirefselect', quiet=False)
            except socket.error, exp:
                msg = "Error: Sorry, the port %d is not free: %s" % (port, str(exp))
                raise PortNotFree(msg)
            except Exception, e:
                # must be a problem with pyro workdir:
                raise InvalidWorkDir(e)

            #@bottle.error(code=500)
            #def error500(err):
            #    print err.__dict__
            #    return 'FUCKING ERROR 500', str(err)


        # Get the server socket but not if disabled
        def get_sockets(self):
            if self.port == 0:
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
                def register_callback(fname, args, f, obj):
                    def f_wrapper():
                        # Warning : put the bottle.response set inside the wrapper
                        # because outside it will break bottle
                        #bottle.response.content_type = 'application/json'
                        #print "Trying to catch the args need by the function", f, fname, args
                        #print 'And the object', obj
                        d = {}
                        method = getattr(f, 'method', 'get').lower()
                        #print "GOT FUNCITON METHOD", method
                        for aname in args:
                            print "LOOKING FOR", aname, "in", fname, method
                            v = None
                            if method == 'post':
                                v = bottle.request.forms.get(aname, None)
                                # Post args are cPickled
                                if v is not None:
                                    v = cPickle.loads(v)
                            elif method == 'get':
                                v = bottle.request.GET.get(aname, None)
                            if v is None:
                                print "FUCK MISSING ARG"*100, aname
                                raise Exception('Missing argument %s' % aname)
                            d[aname] = v
                        ret = f(**d)

                        return json.dumps(ret)
                    # Ok now really put the route in place
                    bottle.route('/'+fname, callback=f_wrapper, method=getattr(f, 'method', 'get').upper())
                register_callback(fname, args, f, obj)
                    
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


    def getProxy(uri):
        return Pyro.core.Proxy(uri)


    # Shutdown in 4 do not take arg
    def shutdown(con):
        con.srv = None

    PyroClass = Pyro4Daemon


class ShinkenPyroDaemon(PyroClass):
    """Class for wrapping select calls for Pyro"""
    locationStr = '__NOTSET__'  # To by pass a bug in Pyro, this should be set in __init__, but
                                # if we try to print an uninitialized object, it's not happy
    objectsById = []            # Same here...

    def get_socks_activity(self, timeout):
        try:
            ins, _, _ = select.select(self.get_sockets(), [], [], timeout)
        except select.error, e:
            errnum, _ = e
            if errnum == errno.EINTR:
                return []
            raise
        return ins

# Common exceptions to be catch
Pyro_exp_pack = (Pyro.errors.ProtocolError, Pyro.errors.URIError,
                 Pyro.errors.CommunicationError,
                 Pyro.errors.DaemonError, Pyro.errors.ConnectionClosedError,
                 Pyro.errors.TimeoutError, Pyro.errors.NamingError)
