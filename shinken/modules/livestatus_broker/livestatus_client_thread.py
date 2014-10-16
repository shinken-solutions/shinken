# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, absolute_import

import time
import socket
import threading
import errno
import select
import copy
import traceback

from shinken.log import logger
from .livestatus import LiveStatus
from .livestatus_response import LiveStatusListResponse
from .livestatus_broker_common import LiveStatusQueryError
from .livestatus_response import LiveStatusResponse

#############################################################################

RECV_SIZE = 8192

#############################################################################

class LiveStatusClientError(Exception):
    pass

class Error:

    class ClientError(LiveStatusClientError):       pass
    class ClientReadError(LiveStatusClientError):   pass
    class ClientWriteError(LiveStatusClientError):  pass
    class ClientTimeout(LiveStatusClientError):     pass
    class ClientLeft(LiveStatusClientError):
        ''' When we try to read a request from the client but it has closed its connection '''
    class Interrupted(LiveStatusClientError):       pass

    client_error = ClientError('Error on communication channel')
    client_left = ClientLeft('Client closed connection')
    interrupted = Interrupted('interrupted')

#############################################################################

class LiveStatusClientThread(threading.Thread):
    ''' A LiveStatus Client Thread will handle a full LS client connection.
    '''
    def __init__(self, client_sock, client_address, livestatus_broker):
        #from .livestatus_broker import LiveStatus_broker
        #assert isinstance(livestatus_broker, LiveStatus_broker)
        super(LiveStatusClientThread, self).__init__()
        self.client_sock = client_sock
        self.client_address = client_address
        broker = self.livestatus_broker = livestatus_broker
        broker_db = copy.copy(broker.db)
        broker_db.max_logs_age = 0
        self.livestatus = LiveStatus(broker.datamgr, broker.query_cache,
                                     broker_db, broker.pnp_path, broker.from_q,
                                     counters=broker.livestatus.counters)
        self.stop_requested = False
        self.buffer_list = []
        now = time.time()
        self.start_time = now
        self.last_read = self.last_write = now
        self.write_timeout = self.read_timeout = 90  # TODO: use parameters from somewhere..
        self.logger = logger
        self.last_query_time = None

    def _has_query(self):
        ''' Check if we have a valid query inside our buffer. For this we just looks if buffer ends with 2 CR ('\n') or its Windows form ('\r\n').
        :return: True if yes, False otherwise.
        '''
        last_bytes = b''
        idx = len(self.buffer_list) - 1
        while idx >= 0:
            last_bytes = self.buffer_list[idx] + last_bytes
            if len(last_bytes) > 1 and last_bytes[-2:] == b'\n\n':
                return True
            if len(last_bytes) > 3:
                return last_bytes[-4:] == b'\r\n\r\n'
            idx -= 1
        return False

    def _read(self, size=RECV_SIZE):
        '''Read at most `size´ bytes of data.
        :return: the data read.
        '''
        try:
            data = self.client_sock.recv(size)
        except socket.error as err:
            if err.args[0] == errno.EWOULDBLOCK: # but should not happen as we are in non-blocking mode..
                return
            else:
                raise Error.ClientReadError('Could not read from client: %s' % err)
        if not data:
            raise Error.client_left
        self.last_read = time.time()
        return data

    def read_request(self):
        '''
        :return: a full bytes buffer which should contain a valid LiveStatus request
        '''

        fds = [ self.client_sock ]
        timeout_time = time.time() + self.read_timeout

        while not self.stop_requested:
            inputready, _, exceptready = select.select(fds, [], [], 1)
            if exceptready:
                raise Error.client_error
            if inputready:
                data = self._read()
                if data:
                    self.buffer_list.append(data)
                    if self._has_query():
                        self.last_query_time = time.time()
                        full_request = b''.join(self.buffer_list)
                        del self.buffer_list[:]
                        return full_request
                    continue
            if time.time() > timeout_time:
                raise Error.ClientTimeout('Timeout reading full request from client')
            timeout_time += self.read_timeout

        raise Error.Interrupted('We have been interrupted')

    def _send_data(self, data):
        fds = [ self.client_sock ]
        total_sent = 0
        len_data = len(data)
        timeout_time = time.time() + self.write_timeout

        while not self.stop_requested:
            _, outputready, exceptready = select.select([], fds, [], 1)
            if exceptready:
                raise Error.client_error
            if not outputready:
                if time.time() - self.last_write > self.write_timeout:
                    raise Error.ClientTimeout('write timeout')
                continue
            try:
                sent = self.client_sock.send(data[total_sent:])
            except socket.error as err:
                if err.args[0] == errno.EWOULDBLOCK: # but should not happen as we are in non-blocking mode..
                    continue
                else:
                    raise Error.ClientWriteError('Could not send response: %s' % err)
            if sent <= 0:
                raise Error.client_left
            self.last_write = time.time()
            total_sent += sent
            if total_sent >= len_data:
                return
            timeout_time += self.write_timeout

        raise Error.interrupted

    def send_response(self, response):
        if not isinstance(response, LiveStatusListResponse):
            response = [ response ]
        for data in response:
            self._send_data(data)

    def request_stop(self):
        self.stop_requested = True

    def handle_request(self, request_data):
        response, _ = self.livestatus.handle_request(request_data)
        try:
            self.send_response(response)
        except LiveStatusQueryError as err:
            code, detail = err.args
            response = LiveStatusResponse()
            response.set_error(code, detail)
            if 'fixed16' in request_data:
                response.responseheader = 'fixed16'
            output, _ = response.respond()
            self.send_response(output)

    def run(self):
        assert isinstance(self.livestatus, LiveStatus)
        self.livestatus.db.open()
        try:
            while not self.stop_requested: # self.stop_requested is(SHOULD BE) checked in all our inner loops
                request_bytes = self.read_request()
                self.handle_request(request_bytes)
        except Error.Interrupted:
            pass
        except Error.ClientLeft as err:
            if self.buffer_list:
                self.logger.error('Client left while some data remaining in input buffer: %s' % err)
        except LiveStatusClientError as err:
            self.logger.error('LiveStatusClientError: %s' % err)
        except Exception as err:
            self.logger.error('Unexpected error: %s ; traceback: %s' % (err, traceback.format_exc()))
        finally:
            try:
                self.client_sock.shutdown(socket.SHUT_RDWR)
            except Exception as err:
                self.logger.warning('Error on client socket shutdown: %s' % err)
            try:
                self.client_sock.close()
            except Exception as err:
                self.logger.warning('Error on client socket close: %s' % err)
            try:
                self.livestatus.db.close()
            except Exception as err:
                self.logger.warning('Error on close database: %s' % err)
