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
import zlib
import base64
import json
import sys
import pickle
import io
if six.PY2:
    from urllib import urlencode
else:
    from urllib.parse import urlencode

# Pycurl part
import pycurl
pycurl.global_init(pycurl.GLOBAL_ALL)
PYCURL_VERSION = pycurl.version_info()[1]

from shinken.bin import VERSION
from shinken.log import logger

class HTTPException(Exception):
    pass


HTTPExceptions = (HTTPException,)

class FileReader(object):
    def __init__(self, fp):
        self.fp = fp
    def read_callback(self, size):
        return self.fp.read(size)


class HTTPClient(object):
    def __init__(self, address='', port=0, use_ssl=False, timeout=3,
                 data_timeout=120, uri='', strong_ssl=False, proxy=''):
        self.address = address
        self.port = port
        self.timeout = timeout
        self.data_timeout = data_timeout

        if not uri:
            if use_ssl:
                self.uri = "https://%s:%s/" % (self.address, self.port)
            else:
                self.uri = "http://%s:%s/" % (self.address, self.port)
        else:
            self.uri = uri

        self.get_con  = self.__create_con(proxy, strong_ssl)
        self.post_con = self.__create_con(proxy, strong_ssl)
        self.put_con  = self.__create_con(proxy, strong_ssl)


    def __create_con(self, proxy, strong_ssl):
        con = pycurl.Curl()
        con.setopt(con.VERBOSE, 0)
        # Remove the Expect: 100-Continue default behavior of pycurl, because swsgiref do not
        # manage it
        con.setopt(pycurl.HTTPHEADER, ['Expect:', 'Keep-Alive: 300', 'Connection: Keep-Alive'])
        con.setopt(pycurl.USERAGENT, 'shinken:%s pycurl:%s' % (VERSION, PYCURL_VERSION))
        con.setopt(pycurl.FOLLOWLOCATION, 1)
        con.setopt(pycurl.FAILONERROR, True)
        con.setopt(pycurl.CONNECTTIMEOUT, self.timeout)
        con.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)

        if proxy:
            con.setopt(pycurl.PROXY, proxy)

        # Also set the SSL options to do not look at the certificates too much
        # unless the admin asked for it
        if strong_ssl:
            con.setopt(pycurl.SSL_VERIFYPEER, 1)
            con.setopt(pycurl.SSL_VERIFYHOST, 2)
        else:
            con.setopt(pycurl.SSL_VERIFYPEER, 0)
            con.setopt(pycurl.SSL_VERIFYHOST, 0)

        return con


    def set_proxy(self, proxy):
        if proxy:
            logger.debug('PROXY SETTING PROXY %s', proxy)
            self.get_con.setopt(pycurl.PROXY, proxy)
            self.post_con.setopt(pycurl.PROXY, proxy)
            self.put_con.setopt(pycurl.PROXY, proxy)


    # Try to get an URI path
    def get(self, path, args={}, wait='short'):
        c = self.get_con
        c.setopt(c.POST, 0)
        c.setopt(pycurl.HTTPGET, 1)

        # For the TIMEOUT, it will depends if we are waiting for a long query or not
        # long:data_timeout, like for huge broks receptions
        # short:timeout, like for just "ok" connection
        if wait == 'short':
            c.setopt(c.TIMEOUT, self.timeout)
        else:
            c.setopt(c.TIMEOUT, self.data_timeout)

        c.setopt(c.URL, self.uri + path + '?' + urlencode(args))
        # Ok now manage the response
        response = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION, response.write)
        c.setopt(c.VERBOSE, 0)
        try:
            c.perform()
        except pycurl.error as error:
            errno, errstr = error.args
            raise HTTPException('Connection error to %s : %s' % (self.uri, errstr))
        r = c.getinfo(pycurl.HTTP_CODE)
        # Do NOT close the connection, we want a keep alive

        if r != 200:
            err = response.getvalue().decode("utf-8")
            logger.error("There was a critical error : %s", err)
            raise HTTPException('Connection error to %s : %s' % (self.uri, r))
        else:
            # Manage special return of pycurl
            ret = json.loads(response.getvalue().decode("utf-8").replace('\\/', '/'))
            # print("GOT RAW RESULT", ret, type(ret))
            return ret


    # Try to get an URI path
    def post(self, path, args, wait='short'):
        size = 0
        # Take args, pickle them and then compress the result
        for (k, v) in args.items():
            args[k] = base64.b64encode(zlib.compress(pickle.dumps(v), 2))
            size += len(args[k])
        # Ok go for it!

        c = self.post_con
        c.setopt(pycurl.HTTPGET, 0)
        c.setopt(c.POST, 1)

        # For the TIMEOUT, it will depends if we are waiting for a long query or not
        # long:data_timeout, like for huge broks receptions
        # short:timeout, like for just "ok" connection
        if wait == 'short':
            c.setopt(c.TIMEOUT, self.timeout)
        else:
            c.setopt(c.TIMEOUT, self.data_timeout)
        # if proxy:
        #    c.setopt(c.PROXY, proxy)
        # Pycurl want a list of tuple as args
        c.setopt(c.HTTPPOST, list(args.items()))
        c.setopt(c.URL, self.uri + path)
        # Ok now manage the response
        response = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION, response.write)
        c.setopt(c.VERBOSE, 0)
        try:
            c.perform()
        except pycurl.error as error:
            errno, errstr = error.args
            raise HTTPException('Connection error to %s : %s' % (self.uri, errstr))

        r = c.getinfo(pycurl.HTTP_CODE)
        # Do NOT close the connection
        # c.close()
        if r != 200:
            err = response.getvalue().decode("utf-8")
            logger.error("There was a critical error : %s", err)
            raise HTTPException('Connection error to %s : %s' % (self.uri, r))
        else:
            # Manage special return of pycurl
            # ret  = json.loads(response.getvalue().replace('\\/', '/'))
            ret = response.getvalue().decode("utf-8")
            return ret

        # Should return us pong string
        return ret


    # Try to get an URI path
    def put(self, path, v, wait='short'):

        c = self.put_con
        filesize = len(v)
        f = io.BytesIO(v)

        c.setopt(pycurl.INFILESIZE, filesize)
        c.setopt(pycurl.PUT, 1)
        c.setopt(pycurl.READFUNCTION, FileReader(f).read_callback)

        # For the TIMEOUT, it will depends if we are waiting for a long query or not
        # long:data_timeout, like for huge broks receptions
        # short:timeout, like for just "ok" connection
        if wait == 'short':
            c.setopt(c.TIMEOUT, self.timeout)
        else:
            c.setopt(c.TIMEOUT, self.data_timeout)
        # if proxy:
        #    c.setopt(c.PROXY, proxy)
        # Pycurl want a list of tuple as args
        c.setopt(c.URL, self.uri + path)
        c.setopt(c.VERBOSE, 0)
        # Ok now manage the response
        response = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION, response.write)
        # c.setopt(c.VERBOSE, 1)
        try:
            c.perform()
        except pycurl.error as error:
            errno, errstr = error
            f.close()
            raise HTTPException('Connection error to %s : %s' % (self.uri, errstr))

        f.close()
        r = c.getinfo(pycurl.HTTP_CODE)
        # Do NOT close the connection
        # c.close()
        if r != 200:
            err = response.getvalue().decode("utf-8")
            logger.error("There was a critical error : %s", err)
            raise HTTPException('Connection error to %s : %s' % (self.uri, r))
        else:
            ret = response.getvalue().decode("utf-8")
            return ret
