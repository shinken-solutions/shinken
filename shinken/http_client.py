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

import time
import socket
import cPickle
import zlib
import json

# Pycurl part
import pycurl
pycurl.global_init(pycurl.GLOBAL_ALL)
import urllib
from StringIO import StringIO

from shinken.bin import VERSION
from shinken.log import logger
PYCURL_VERSION = pycurl.version_info()[1]

class HTTPException(Exception):
    pass


HTTPExceptions = (HTTPException,)


class HTTPClient(object):
    def __init__(self, address='', port=0, use_ssl=False, timeout=3, data_timeout=120, uri='', strong_ssl=False):
        self.address = address
        self.port    = port
        self.timeout = timeout
        self.data_timeout = data_timeout
        
        if not uri:
            if use_ssl:
                self.uri = "https://%s:%s/" % (self.address, self.port)
            else:
                self.uri = "http://%s:%s/" % (self.address, self.port)
        else:
            self.uri = uri
        
        self.con     = pycurl.Curl()
        
        # Remove the Expect: 100-Continue default behavior of pycurl, because swsgiref do not
        # manage it
        self.con.setopt(pycurl.HTTPHEADER, ['Expect:', 'Keep-Alive: 300', 'Connection: Keep-Alive'])
        self.con.setopt(pycurl.USERAGENT,  'shinken:%s pycurl:%s' % (VERSION, PYCURL_VERSION) )
        self.con.setopt(pycurl.FOLLOWLOCATION, 1)
        self.con.setopt(pycurl.FAILONERROR, True)
        self.con.setopt(pycurl.CONNECTTIMEOUT, self.timeout)
        self.con.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        

        # Also set the SSL options to do not look at the certificates too much
        # unless the admin asked for it
        if strong_ssl:
            self.con.setopt(pycurl.SSL_VERIFYPEER, 1)
            self.con.setopt(pycurl.SSL_VERIFYHOST, 2)
        else:
            self.con.setopt(pycurl.SSL_VERIFYPEER, 0)
            self.con.setopt(pycurl.SSL_VERIFYHOST, 0)
            

    
    # Try to get an URI path
    def get(self, path, args={}, wait='short'):
        c = self.con
        c.setopt(c.POST, 0)
        c.setopt(pycurl.HTTPGET, 1)


        # For the TIMEOUT, it will depends if we are waiting for a long query or not
        # long:data_timeout, like for huge broks receptions
        # short:timeout, like for just "ok" connection
        if wait == 'short':
            c.setopt(c.TIMEOUT, self.timeout)
        else:
            c.setopt(c.TIMEOUT, self.data_timeout)

        #if proxy:
        #    c.setopt(c.PROXY, proxy)
        #print "GO TO", self.uri+path+'?'+urllib.urlencode(args)
        c.setopt(c.URL, str(self.uri+path+'?'+urllib.urlencode(args)))
        # Ok now manage the response
        response = StringIO()
        c.setopt(pycurl.WRITEFUNCTION, response.write)
        #c.setopt(c.VERBOSE, 1)
        try:
            c.perform()
        except pycurl.error, error:
            errno, errstr = error
            raise HTTPException ('Connexion error to %s : %s' % (self.uri, errstr))
        r = c.getinfo(pycurl.HTTP_CODE)
        # Do NOT close the connexion, we want a keep alive

        if r != 200:
            err = response.getvalue()
            logger.error("There was a critical error : %s" % err)
            raise Exception ('Connexion error to %s : %s' % (self.uri, r))
        else:
            # Manage special return of pycurl
            ret  = json.loads(response.getvalue().replace('\\/', '/'))
            # print "GOT RAW RESULT", ret, type(ret)
            return ret
        

    # Try to get an URI path
    def post(self, path, args, wait='short'):
        # Take args, pickle them and then compress the result
        for (k,v) in args.iteritems():
            args[k] = zlib.compress(cPickle.dumps(v), 2)
        # Ok go for it!
        
        c = self.con
        c.setopt(pycurl.HTTPGET, 0)
        c.setopt(c.POST, 1)

        # For the TIMEOUT, it will depends if we are waiting for a long query or not
        # long:data_timeout, like for huge broks receptions
        # short:timeout, like for just "ok" connection
        if wait == 'short':
            c.setopt(c.TIMEOUT, self.timeout)
        else:
            c.setopt(c.TIMEOUT, self.data_timeout)
        #if proxy:
        #    c.setopt(c.PROXY, proxy)
        # Pycurl want a list of tuple as args
        postargs = [(k,v) for (k,v) in args.iteritems()]
        c.setopt(c.HTTPPOST, postargs)
        c.setopt(c.URL, str(self.uri+path))
        # Ok now manage the response
        response = StringIO()
        c.setopt(pycurl.WRITEFUNCTION, response.write)
        #c.setopt(c.VERBOSE, 1)
        try:
            c.perform()
        except pycurl.error, error:
            errno, errstr = error
            raise HTTPException ('Connexion error to %s : %s' % (self.uri, errstr))

        r = c.getinfo(pycurl.HTTP_CODE)
        # Do NOT close the connexion
        #c.close()
        if r != 200:
            err = response.getvalue()
            logger.error("There was a critical error : %s" % err)
            raise Exception ('Connexion error to %s : %s' % (self.uri, r))
        else:
            # Manage special return of pycurl
            #ret  = json.loads(response.getvalue().replace('\\/', '/'))
            ret = response.getvalue()
            return ret

        
        
        # Should return us pong string
        return ret

    
