#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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

import time
import socket
import asyncore
from log import logger


class LSSyncConnection:
    def __init__(self, addr='127.0.0.1', port=50000, path=None, timeout=10):
        self.addr = addr
        self.port = port
        self.path = path
        self.timeout = timeout

        # We must know if the socket is alive or not
        self.alive = False

        # Now we can inti the sockets
        if path:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.type = 'unix'
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.type = 'tcp'

        # We can now set the socket timeout
        self.socket.settimeout(timeout)
        self.connect()

    def connect(self):
        if not self.alive:
            if self.type == 'unix':
                target = self.path
            else:
                target = (self.addr, self.port)

            try:
                self.socket.connect(target)
                self.alive = True
            except IOError, exp:
                self.alive = False
                logger.warning("Connection problem: %s", str(exp))

    def read(self, size):
        res = ""
        while size > 0:
            data = self.socket.recv(size)
            l = len(data)

            if l == 0:
                logger.warning("0 size read")
                return res  #: TODO raise an error

            size = size - l
            res = res + data
        return res

    def launch_query(self, query):
        if not self.alive:
            self.connect()
        if not query.endswith("\n"):
            query += "\n"
        query += "OutputFormat: python\nKeepAlive: on\nResponseHeader: fixed16\n\n"

        try:
            self.socket.send(query)
            data = self.read(16)
            code = data[0:3]
            logger.debug("RAW DATA: %s", data)

            length = int(data[4:15])
            logger.debug("Len: %d", length)

            data = self.read(length)
            logger.debug("DATA: %s", data)

            if code == "200":
                try:
                    return eval(data)
                except Exception:
                    logger.warning("BAD VALUE RETURN (data=%s)", data)
                    return None
            else:
                logger.warning("BAD RETURN CODE (code= %s, data=%s", code, data)
                return None
        except IOError, exp:
            self.alive = False
            logger.warning("SOCKET ERROR (%s)", str(exp))
            return None

    def exec_command(self, command):
        if not self.alive:
            self.connect()
        if not command.endswith("\n"):
            command += "\n"

        try:
            self.socket.send("COMMAND " + command + "\n")
        except IOError, exp:
            self.alive = False
            logger.warning("COMMAND EXEC error: %s", str(exp))


# Query class for define a query, and its states
class Query(object):

    id = 0

    def __init__(self, q):
        # The query string
        if not q.endswith("\n"):
            q += "\n"
        q += "OutputFormat: python\nKeepAlive: on\nResponseHeader: fixed16\n\n"

        self.q = q
        self.id = Query.id
        Query.id += 1
        # Got some states PENDING -> PICKUP -> DONE
        self.state = 'PENDING'
        self.result = None
        self.duration = 0
        # By default, an error :)
        self.return_code = '500'

    def get(self):
        # print "Someone ask my query", self.q
        self.state = 'PICKUP'
        self.duration = time.time()
        return self.q

    def put(self, r):
        self.result = r
        self.state = 'DONE'
        self.duration = time.time() - self.duration
        # print "Got a result", r


class LSAsynConnection(asyncore.dispatcher):
    def __init__(self, addr='127.0.0.1', port=50000, path=None, timeout=10):
        asyncore.dispatcher.__init__(self)
        self.addr = addr
        self.port = port
        self.path = path
        self.timeout = timeout

        # We must know if the socket is alive or not
        self.alive = False

        # Now we can inti the sockets
        if path:
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.type = 'unix'
        else:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.type = 'tcp'

        # We can now set the socket timeout
        self.socket.settimeout(timeout)
        self.do_connect()

        # And our queries
        # q = Query('GET hosts\nColumns name\n')
        self.queries = []
        self.results = []

        self.current = None

    def stack_query(self, q):
        self.queries.append(q)

    # Get a query and put it in current
    def get_query(self):
        q = self.queries.pop()
        self.current = q
        return q

    def do_connect(self):
        if not self.alive:
            if self.type == 'unix':
                target = self.path
            else:
                target = (self.addr, self.port)
            try:
                self.connect(target)
                self.alive = True
            except IOError, exp:
                self.alive = False
                logger.warning("Connection problem: %s", str(exp))
                self.handle_close()

    def do_read(self, size):
        res = ""
        while size > 0:
            data = self.socket.recv(size)
            l = len(data)
            if l == 0:
                logger.warning("0 size read")
                return res  #: TODO raise an error

            size = size - l
            res = res + data
        return res

    def exec_command(self, command):
        if not self.alive:
            self.do_connect()
        if not command.endswith("\n"):
            command += "\n"

        try:
            self.socket.send("COMMAND " + command + "\n")
        except IOError, exp:
            self.alive = False
            logger.warning("COMMAND EXEC error: %s", str(exp))

    def handle_connect(self):
        pass
        # print "In handle_connect"

    def handle_close(self):
        logger.debug("Closing connection")
        self.current = None
        self.queries = []
        self.close()

    # Check if we are in timeout. If so, just bailout
    # and set the correct return code from timeout
    # case
    def look_for_timeout(self):
        logger.debug("Look for timeout")
        now = time.time()
        if now - self.start_time > self.timeout:
            if self.unknown_on_timeout:
                rc = 3
            else:
                rc = 2
            message = 'Error: connection timeout after %d seconds' % self.timeout
            self.set_exit(rc, message)

    # We got a read for the socket. We do it if we do not already
    # finished. Maybe it's just a SSL handshake continuation, if so
    # we continue it and wait for handshake finish
    def handle_read(self):
        # print "Handle read"

        q = self.current
        # get a read but no current query? Not normal!

        if not q:
            # print "WARNING: got LS read while no current query in progress. I return"
            return

        try:
            data = self.do_read(16)
            code = data[0:3]
            q.return_code = code

            length = int(data[4:15])
            data = self.do_read(length)

            if code == "200":
                try:
                    d = eval(data)
                    # print d
                    q.put(d)
                except Exception:
                    q.put(None)
            else:
                q.put(None)
                return None
        except IOError, exp:
            self.alive = False
            logger.warning("SOCKET ERROR: %s", str(exp))
            return q.put(None)

        # Now the current is done. We put in in our results queue
        self.results.append(q)
        self.current = None

    # Did we finished our job?
    def writable(self):
        b = (len(self.queries) != 0 and not self.current)
        # print "Is writable?", b
        return b

    def readable(self):
        b = self.current is not None
        # print "Readable", b
        return True

    # We can write to the socket. If we are in the ssl handshake phase
    # we just continue it and return. If we finished it, we can write our
    # query
    def handle_write(self):
        if not self.writable():
            logger.debug("Not writable, I bail out")
            return

        # print "handle write"
        try:
            q = self.get_query()
            sent = self.send(q.get())
        except socket.error, exp:
            logger.debug("Write fail: %s", str(exp))
            return

        # print "Sent", sent, "data"


    # We are finished only if we got no pending queries and
    # no in progress query too
    def is_finished(self):
        # print "State:", self.current, len(self.queries)
        return self.current is None and len(self.queries) == 0

    # Will loop over the time until all returns are back
    def wait_returns(self):
        while self.alive and not self.is_finished():
            asyncore.poll(timeout=0.001)

    def get_returns(self):
        r = self.results
        self.results = self.results[:]
        return r

    def launch_raw_query(self, query):
        if not self.alive:
            logger.debug("Cannot launch query. Connection is closed")
            return None

        if not self.is_finished():
            logger.debug(
                "Try to launch a new query in a normal mode"
                " but the connection already got async queries in progress"
            )
            return None

        q = Query(query)
        self.stack_query(q)
        self.wait_returns()
        q = self.results.pop()
        return q.result


class LSConnectionPool(object):
    def __init__(self, con_addrs):
        self.connections = []
        for s in con_addrs:
            if s.startswith('tcp:'):
                s = s[4:]
                addr = s.split(':')[0]
                port = int(s.split(':')[1])
                con = LSAsynConnection(addr=addr, port=port)
            elif s.startswith('unix:'):
                s = s[5:]
                path = s
                con = LSAsynConnection(path=path)
            else:
                logger.info("Unknown connection type for %s", s)

            self.connections.append(con)

    def launch_raw_query(self, query):
        for c in self.connections:
            q = Query(query)
            c.stack_query(q)
        still_working = [c for c in self.connections if c.alive and not c.is_finished()]
        while len(still_working) > 0:
            asyncore.poll(timeout=0.001)
            still_working = [c for c in self.connections if c.alive and not c.is_finished()]
        # Now get all results
        res = []
        for c in self.connections:
            if len(c.get_returns()) > 0:
                q = c.get_returns().pop()
                r = q.result
                logger.debug(str(r))
                res.extend(r)
            c.handle_close()
        return res


if __name__ == "__main__":
    c = LSAsynConnection()
    t = time.time()

    q = Query('GET hosts\nColumns name\n')
    # c.stack_query(q)
    # q2 = Query('GET hosts\nColumns name\n')
    # c.stack_query(q)

    # print "Start to wait"
    # c.wait_returns()
    # print "End to wait"
    # print "Results", c.get_returns()
    # while time.time() - t < 1:
    #    asyncore.poll()


    # while time.time() - t < 1:
    #    asyncore.poll()
    # print c.launch_query('GET hosts\nColumns name')
    # print c.__dict__

    # print "Launch raw query"
    # r = c.launch_raw_query('GET hosts\nColumns name\n')
    # print "Result", r

    cp = LSConnectionPool(['tcp:localhost:50000', 'tcp:localhost:50000'])
    r = cp.launch_raw_query('GET hosts\nColumns name last_check\n')
    logger.debug("Result= %s", str(r))
    logger.debug(int(time.time()))
