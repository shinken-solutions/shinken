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
from log import logger

# Let's load bottlecore! :)
from shinken.webui import bottlecore as bottle
bottle.debug(True)



class InvalidWorkDir(Exception):
    pass


class PortNotFree(Exception):
    pass


class HTTPDaemon(object):
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
                        print "CALLING", fname
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
                                # Post args are zlibed and cPickled
                                if v is not None:
                                    print "GOT V", len(v)
                                    v = zlib.decompress(v)
                                    v = cPickle.loads(v)
                            elif method == 'get':
                                v = bottle.request.GET.get(aname, None)
                            if v is None:
                                print "FUCK MISSING ARG"*100, aname
                                raise Exception('Missing argument %s' % aname)
                            d[aname] = v
                        ret = f(**d)
                        #return json.dumps(ret)
                        encode = getattr(f, 'encode', 'json').lower()
                        return json.dumps(ret)
                        #if encode == 'json':
                        #    return json.dumps(ret)
                        #else:
                        #    print "RETURN RAW RESULT"
                        #    return ret
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


        # Just remove teh server, should do the work
        def shutdown(con):
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
