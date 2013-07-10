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

# This Class is an Arbiter module for having a webservice
# where you can push external commands

"""This is a new version of the ws_arbiter. This ws_arbiter supports
multiple external commands.

It can support the following incoming data:
host1, service1, value1, host2, service2, value2

Here is a short command line example:
2 hosts (host1 and host2), one service each (Service1 and Service2)

curl --data "host_name=host1&service_description=Service1
&return_code=0&output=OK+%7C+Service1%3D53%25&time_stamp=1365446900
&host_name=host2&service_description=Service2
&return_code=0&output=OK+%7C+Service2%3D60%25&time_stamp=1365446900" http://shinken_server:7760/push_check_result

It is now possible to do bulk data on the webservice.
"""

import os
import sys
import select
import time
######################## WIP   don't launch it!

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

from shinken.webui.bottlewebui import Bottle, run, static_file, view, route, request, response, abort, parse_auth

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'ws_arbiter',
    'external': True,
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    instance = Ws_arbiter(plugin)
    return instance

# Main app var. Will be fill with our running module instance
app = None


def get_commands(time_stamps, hosts, services, return_codes, outputs):
    """Composing a command list based on the information received in
    POST request"""

    commands = []

    current_time_stamp = int(time.time())

    def _compose_command(t, h, s, r, o):
        """Simple function to create a command from the inputs"""
        cmd = ""
        if not s or s == "":
            cmd = '[%s] PROCESS_HOST_CHECK_RESULT;%s;%s;%s' % (t if t is not None else current_time_stamp, h, r, o)
        else:
            cmd = '[%s] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s' % (t if t is not None else current_time_stamp, h, s, r, o)
        logger.debug("[Ws_arbiter] CMD: %s" % (cmd))
        commands.append(cmd)

    # Trivial case: empty commmand list
    if (return_codes is None or len(return_codes) == 0):
        return commands

    # Sanity check: if we get N return codes, we must have N hosts.
    # The other values could be None
    if (len(return_codes) != len(hosts)):
        logger.error("[Ws_arbiter] number of return codes (%d) does not match number of hosts (%d)" % (len(return_codes), len(hosts)))
        abort(400, "number of return codes does not match number of hosts")

    map(_compose_command, time_stamps, hosts, services, return_codes, outputs)
    logger.debug("[Ws_arbiter] commands = %s" % (str(commands)))
    return commands


def get_page():
    commands_list = []

    try:
        # Getting lists of informations for the commands
        time_stamp_list = []
        host_name_list = []
        service_description_list = []
        return_code_list = []
        output_list = []
        time_stamp_list = request.forms.getall(key='time_stamp')
        logger.debug("[Ws_arbiter] time_stamp_list: %s" % (time_stamp_list))
        host_name_list = request.forms.getall(key='host_name')
        logger.debug("[Ws_arbiter] host_name_list: %s" % (host_name_list))
        service_description_list = request.forms.getall(key='service_description')
        logger.debug("[Ws_arbiter] service_description_list: %s" % (service_description_list))
        return_code_list = request.forms.getall(key='return_code')
        logger.debug("[Ws_arbiter] return_code_list: %s" % (return_code_list))
        output_list = request.forms.getall(key='output')
        logger.debug("[Ws_arbiter] output_list: %s" % (output_list))
        commands_list = get_commands(time_stamp_list, host_name_list, service_description_list, return_code_list, output_list)
    except Exception, e:
        logger.error("[Ws_arbiter] failed to get the lists: %s" % str(e))
        commands_list = []

    # We check for auth if it's not anonymously allowed
    if app.username != 'anonymous':
        basic = parse_auth(request.environ.get('HTTP_AUTHORIZATION', ''))
        # Maybe the user not even ask for user/pass. If so, bail out
        if not basic:
            abort(401, 'Authentication required')
        # Maybe he do not give the good credential?
        if basic[0] != app.username or basic[1] != app.password:
            abort(403, 'Authentication denied')

    # Adding commands to the main queue()
    logger.debug("[Ws_arbiter] commands =  %s" % str(sorted(commands_list)))
    for c in sorted(commands_list):
        ext = ExternalCommand(c)
        app.from_q.put(ext)

    # OK here it's ok, it will return a 200 code


# This module will open an HTTP service, where a user can send a command, like a check
# return.
class Ws_arbiter(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        try:
            self.username = getattr(modconf, 'username', 'anonymous')
            self.password = getattr(modconf, 'password', '')
            self.port = int(getattr(modconf, 'port', '7760'))
            self.host = getattr(modconf, 'host', '0.0.0.0')
        except AttributeError:
            logger.error("[Ws_arbiter] The module is missing a property, check module declaration in shinken-specific.cfg")
            raise

    # We initialize the HTTP part. It's a simple wsgi backend
    # with a select hack so we can still exit if someone ask it
    def init_http(self):
        logger.info("[Ws_arbiter] Starting WS arbiter http socket")
        self.srv = run(host=self.host, port=self.port, server='wsgirefselect')
        # And we link our page
        route('/push_check_result', callback=get_page, method='POST')

    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        global app

        # Change process name (seen in ps or top)
        self.set_proctitle(self.name)

        # It's an external module, so we need to be sure that we manage
        # the signals
        self.set_exit_handler()

        # Go for Http open :)
        self.init_http()

        # We fill the global variable with our Queue() link
        # with the arbiter, because the page should be a non-class
        # one function
        app = self

        # We will loop forever on the http socket
        input = [self.srv.socket]

        # Main blocking loop
        while not self.interrupted:
            input = [self.srv.socket]
            inputready, _, _ = select.select(input, [], [], 1)
            for s in inputready:
                # If it's a web request, ask the webserver to do it
                if s == self.srv.socket:
                    self.srv.handle_request()
