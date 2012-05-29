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


#This Class is an example of an Scheduler module
#Here for the configuration phase AND running one


import sys
import signal
import time
import socket
import struct
import binascii
import asyncore
import getopt
import shlex

try :
    import OpenSSL
    SSLWantReadError = OpenSSL.SSL.WantReadError
    SSLSysCallError = OpenSSL.SSL.SysCallError
    SSLZeroReturnError = OpenSSL.SSL.ZeroReturnError
    SSLError = OpenSSL.SSL.Error
except ImportError:
    OpenSSL = None
    SSLWantReadError = None
    SSLSysCallError = None
    SSLZeroReturnError = None
    SSLError = None

from Queue import Empty
from shinken.basemodule import BaseModule


properties = {
    'daemons' : ['poller'],
    'type' : 'nrpe_poller',
    'external' : False,
    # To be a real worker module, you must set this
    'worker_capable' : True,
    }


#called by the plugin manager to get a broker
def get_instance(mod_conf):
    print "Get a nrpe poller module for plugin %s" % mod_conf.get_name()
    instance = Nrpe_poller(mod_conf)
    return instance


class NRPE:
    # Really build the buffer query with our command
    def build_query(self, command):
        '''
        Build a query packet
         00-01     : NRPE protocol version
         02-03     : packet type (01 : query, 02 : response)
         04-07     : CRC32
         08-09     : return code of the check if packet type is response
         10-1034   : command (nul terminated)
         1035-1036 : reserved 
        '''
        crc = 0

        if not command:
            self.state = 'received'
            self.rc = 3
            self.message = "Error : no command asked from nrpe query"
            return

        # We pack it, then we compute CRC32 of this first query
        self.query = struct.pack(">2hih1024scc",02,01,crc,0,command,'N','D')
        crc = binascii.crc32(self.query)
        
        # we restart with the crc value this time
        # because python2.4 do not have pack_into.
        self.query = struct.pack(">2hih1024scc",02,01,crc,0,command,'N','D')

    
    def init_query(self,host, port, use_ssl, command):
        self.state = 'creation'
        #print 'build with', command
        self.build_query(command)
        self.host = host
        self.port = port
        

#    def send(self):
#        self.state = 'sent'
#        try:
#            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            self.s.settimeout(9)
#            self.s.connect((self.host, self.port))
#            print "Sending", len(self.query)
#            self.s.send(self.query)
#        except socket.error,exp:
#            self.rc = 2
#            self.message = str(exp)
#            self.state = 'received'
#            return(self.rc, self.message)
        
#    def get(self):
#        # If we already got an error, get out now
#        if self.state == 'received':
#            return (self.rc, self.message)
#        try:
#            data = self.s.recv(1034)
#            self.s.close()
#        except socket.error,exp:
#            self.rc = 2
#            self.message = str(exp)
#            self.state = 'received'
#            return(self.rc, self.message)
#        return data

    # Read a return and extract return code
    # and output
    def read(self, data):
        if self.state == 'received':
            return (self.rc, self.message)

        self.state = 'received'
        # TODO : check crc

        try:
            response = struct.unpack(">2hih1024s", data)
        except: # bad format...
            self.rc = 3
            self.message = "Error : cannot read output from nrpe daemon..."
            return (self.rc, self.message)

        self.rc = response[3]
        # the output is fill with \x00 at the end. We 
        # should clean them
        self.message = response[4].strip('\x00')
        crc_orig = response[2]
        
        return (self.rc, self.message)





class NRPEAsyncClient(asyncore.dispatcher):

    def __init__(self, host, port, use_ssl, timeout, unknown_on_timeout, msg):
        asyncore.dispatcher.__init__(self)

        self.use_ssl = use_ssl
        self.start_time = time.time()
        self.timeout = timeout
        self.unknown_on_timeout = unknown_on_timeout

        # Instanciate our nrpe helper
        self.nrpe = NRPE()
        self.nrpe.init_query(host, 5666, use_ssl, msg)

        # And now we create a socket for our connection
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if use_ssl:
            # The admin want a ssl connection, but there is not openssl
            # lib installed :(
            if OpenSSL is None:
                self.set_exit(2, "Error : the openssl lib for Python is not installed.")
                return
            else:
                # Ok we can wrap the socket
                #print "Wrapping ssl!"
                self.wrap_ssl()

        try:
            #print "Connect to", host, port
            self.connect( (host, port) )
        except socket.error,exp:
            self.set_exit(2, str(exp))
        

    def wrap_ssl(self):
        self.context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
        self.context.set_cipher_list('ADH')
        self.socket = OpenSSL.SSL.Connection(self.context, self.socket)
        self.set_accept_state()


    def handle_connect(self):
        pass


    def handle_close(self):
        self.close()

        
    def set_exit(self, rc, message):
        self.rc = rc
        self.message = message
        self.execution_time = time.time() - self.start_time
        self.nrpe.state = 'received'


    # Check if we are in timeout. If so, just bailout
    # and set the correct return code from timeout
    # case
    def look_for_timeout(self):
        now = time.time()
        if now - self.start_time > self.timeout:
            if self.unknown_on_timeout:
                rc = 3
            else:
                rc = 2
            message = 'Error : connection timeout after %d seconds' % self.timeout
            self.set_exit(rc, message)


    # We got a read for the socket. We do it if we do not already
    # finished. Maybe it's just a SSL handshake continuation, if so
    # we continue it and wait for handshake finish
    def handle_read(self):
        if not self.is_done():
            try:
                buf = self.recv(1034)
            except socket.error, exp:
                print exp
                self.set_exit(2, str(exp))
                return

            # if we are in ssl, there can be a handshake
            # problem : we can't talk until we finished
            # it, sorry
            except SSLWantReadError, exp:
                try: 
                    self.socket.do_handshake()
                except SSLWantReadError, exp:
                    return
                return

            # We can have nothing, it's just that the server
            # do not want to talk to us :(
            except SSLZeroReturnError :
                buf = ''

            except SSLSysCallError:
                buf = ''

            except SSLError:
                bug = ''

            # Maybe we got nothing from the server (it refuse our ip,
            # or refuse arguments...)
            if len(buf) != 0:
                (rc, message) = self.nrpe.read(buf)
                self.set_exit(rc, message)
            else:
                self.set_exit(2, "Error : nothing return from the nrpe server")
            
            # We can close the socket, we are done
            self.close()

    # Did we finished our job?
    def writable(self):
        return not self.is_done() and (len(self.nrpe.query) > 0)

    # We can write to the socket. If we are in the ssl handshake phase
    # we just continue it and return. If we finished it, we can write our
    # query
    def handle_write(self):
        if self.writable():
            try : 
                sent = self.send(self.nrpe.query)
            except socket.error, exp:
                # In case of problem, just bail out
                # as error
                self.set_exit(2, str(exp))
                return

            # if we are in ssl, there can be a handshake
            # problem : we can't talk until we finished
            # it, sorry
            except SSLWantReadError, exp:
                try: 
                    self.socket.do_handshake()
                except SSLWantReadError, exp:
                    # still not finished, we continue
                    return
                return
            # Maybe we did not send all our query
            # so we bufferize it
            self.nrpe.query = self.nrpe.query[sent:]

    
    def is_done(self):
        return self.nrpe.state == 'received'



def parse_args(cmd_args):
    #Default params
    host = None
    command = None
    port = 5666
    unknown_on_timeout = False
    timeout = 10
    use_ssl = True
    add_args = []

    #Manage the options
    try:
        opts, args = getopt.getopt(cmd_args, "H::p::nut::c::a::", [])
    except getopt.GetoptError, err:
        # If we got problem, bail out
        return (host, port, unknown_on_timeout, command, timeout, use_ssl, add_args)
    #print  "Opts", opts, "Args", args
    for o, a in opts:
        if o in ("-H"):
            host = a
        elif o in ("-p"):
            port = int(a)
        elif o in ("-c"):
            command = a
        elif o in ('-t'):
            timeout = int(a)
        elif o in ('-u'):
            unknown_on_timeout = True
        elif o in ('-n'):
            use_ssl = False
        elif o in ('-a'):
            # Here we got a, btu also all 'args'
            add_args.append(a)
            add_args.extend(args)
            
    return (host, port, unknown_on_timeout, command, timeout, use_ssl, add_args)





#Just print some stuff
class Nrpe_poller(BaseModule):
    
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)


    # Called by poller to say 'let's prepare yourself guy'
    def init(self):
        print "Initialization of the nrpe poller module"
        self.i_am_dying = False


    # Get new checks if less than nb_checks_max
    # If no new checks got and no check in queue,
    # sleep for 1 sec
    # REF: doc/shinken-action-queues.png (3)
    def get_new_checks(self):
        try:
            while(True):
                #print "I", self.id, "wait for a message"
                msg = self.s.get(block=False)
                if msg is not None:
                    self.checks.append(msg.get_data())
                #print "I", self.id, "I've got a message!"
        except Empty , exp:
            if len(self.checks) == 0:
                time.sleep(1)



    # Launch checks that are in status
    # REF: doc/shinken-action-queues.png (4)
    def launch_new_checks(self):
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
                    # we do not want the first member, check_nrpe thing
                    args = parse_args(clean_command[1:])
                    (host, port, unknown_on_timeout, command, timeout, use_ssl, add_args) = args
                    #print (host, port, unknown_on_timeout, command, timeout, use_ssl, add_args)
                else:
                    # Set an error so we will quit tis check
                    command = None
                    
                # If we do not have the good args, we bail out for this check
                if command is None or host is None:
                    chk.status = 'done'
                    chk.exit_status = 2
                    chk.get_outputs('Error : the parameters host or command are not correct.', 8012)
                    chk.execution_time = 0.0
                    continue
                
                # Ok we are good, we go on
                total_args = [command]
                total_args.extend(add_args)
                cmd = r'!'.join(total_args)
                n = NRPEAsyncClient(host, port, use_ssl, timeout, unknown_on_timeout, cmd)
                chk.con = n


    # Check the status of checks
    # if done, return message finished :)
    # REF: doc/shinken-action-queues.png (5)
    def manage_finished_checks(self):
        to_del = []
        
        # First look for checks in timeout
        for c in self.checks:
            if c.status == 'launched':
                c.con.look_for_timeout()

        # We check if all new things in connections
        asyncore.poll(timeout=1)
        
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
        print "[Nrpe] Module NRPE started!"
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


