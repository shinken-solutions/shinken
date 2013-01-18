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

LOGCLASS_INFO = 0          # all messages not in any other class
LOGCLASS_ALERT = 1         # alerts: the change service/host state
LOGCLASS_PROGRAM = 2       # important program events (restart, ...)
LOGCLASS_NOTIFICATION = 3  # host/service notifications
LOGCLASS_PASSIVECHECK = 4  # passive checks
LOGCLASS_COMMAND = 5       # external commands
LOGCLASS_STATE = 6         # initial or current states
LOGCLASS_INVALID = -1      # never stored
LOGCLASS_ALL = 0xffff
LOGOBJECT_INFO = 0
LOGOBJECT_HOST = 1
LOGOBJECT_SERVICE = 2
LOGOBJECT_CONTACT = 3

from shinken.log import logger

class LoglineWrongFormat(Exception):
    pass


class Logline(dict):
    """A class which represents a line from the logfile
    Public functions:
    fill -- Attach host and/or service objects to a Logline object

    """

    id = 0
    columns = ['logobject', 'attempt', 'logclass', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message', 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type']

    def __init__(self, sqlite_cursor=None, sqlite_row=None, line=None, srcdict=None):
        if srcdict != None:
            for col in Logline.columns:
                logger.info("[Livestatus Log Lines] Set %s, %s"% (col, srcdict[col]))
                setattr(self, col, srcdict[col])
        elif sqlite_cursor != None and sqlite_row != None:
            for idx, col in enumerate(sqlite_cursor):
                if col[0] == 'class':
                    setattr(self, 'logclass', sqlite_row[idx])
                else:
                    setattr(self, col[0], sqlite_row[idx])
        elif line != None:
            line = line.encode('UTF-8').rstrip()
            # [1278280765] SERVICE ALERT: test_host_0
            if line[0] != '[' and line[11] != ']':
                logger.warning("[Livestatus Log Lines] Invalid line: %s" % line)
                raise LoglineWrongFormat
            else:
                service_states = {
                    'OK': 0,
                    'WARNING': 1,
                    'CRITICAL': 2,
                    'UNKNOWN': 3,
                    'RECOVERY': 0
                }
                host_states = {
                    'UP': 0,
                    'DOWN': 1,
                    'UNREACHABLE': 2,
                    'UNKNOWN': 3,
                    'RECOVERY': 0
                }

                # type is 0:info, 1:state, 2:program, 3:notification, 4:passive, 5:command
                logobject = LOGOBJECT_INFO
                logclass = LOGCLASS_INVALID
                attempt, state = [0] * 2
                command_name, comment, contact_name, host_name, message, plugin_output, service_description, state_type = [''] * 8
                time = line[1:11]
                first_type_pos = line.find(' ') + 1
                last_type_pos = line.find(':')
                first_detail_pos = last_type_pos + 2
                type = line[first_type_pos:last_type_pos]
                options = line[first_detail_pos:]
                message = line
                if type == 'CURRENT SERVICE STATE':
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_STATE
                    host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
                elif type == 'INITIAL SERVICE STATE':
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_STATE
                    host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
                elif type == 'SERVICE ALERT':
                    # SERVICE ALERT: srv-40;Service-9;CRITICAL;HARD;1;[Errno 2] No such file or directory
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_ALERT
                    host_name, service_description, state, state_type, attempt, plugin_output = options.split(';', 5)
                    state = service_states[state]
                elif type == 'SERVICE DOWNTIME ALERT':
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_ALERT
                    host_name, service_description, state_type, comment = options.split(';', 3)
                elif type == 'SERVICE FLAPPING ALERT':
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_ALERT
                    host_name, service_description, state_type, comment = options.split(';', 3)

                elif type == 'CURRENT HOST STATE':
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_STATE
                    host_name, state, state_type, attempt, plugin_output = options.split(';', 4)
                elif type == 'INITIAL HOST STATE':
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_STATE
                    host_name, state, state_type, attempt, plugin_output = options.split(';', 4)
                elif type == 'HOST ALERT':
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_ALERT
                    host_name, state, state_type, attempt, plugin_output = options.split(';', 4)
                    state = host_states[state]
                elif type == 'HOST DOWNTIME ALERT':
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_ALERT
                    host_name, state_type, comment = options.split(';', 2)
                elif type == 'HOST FLAPPING ALERT':
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_ALERT
                    host_name, state_type, comment = options.split(';', 2)

                elif type == 'SERVICE NOTIFICATION':
                    # tust_cuntuct;test_host_0;test_ok_0;CRITICAL;notify-service;i am CRITICAL  <-- normal
                    # SERVICE NOTIFICATION: test_contact;test_host_0;test_ok_0;DOWNTIMESTART (OK);notify-service;OK
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_NOTIFICATION
                    contact_name, host_name, service_description, state_type, command_name, check_plugin_output = options.split(';', 5)
                    if '(' in state_type:  # downtime/flapping/etc-notifications take the type UNKNOWN
                        state_type = 'UNKNOWN'
                    state = service_states[state_type]
                elif type == 'HOST NOTIFICATION':
                    # tust_cuntuct;test_host_0;DOWN;notify-host;i am DOWN
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_NOTIFICATION
                    contact_name, host_name, state_type, command_name, check_plugin_output = options.split(';', 4)
                    if '(' in state_type:
                        state_type = 'UNKNOWN'
                    state = host_states[state_type]

                elif type == 'PASSIVE SERVICE CHECK':
                    logobject = LOGOBJECT_SERVICE
                    logclass = LOGCLASS_PASSIVECHECK
                    host_name, service_description, state, check_plugin_output = options.split(';', 3)
                elif type == 'PASSIVE HOST CHECK':
                    logobject = LOGOBJECT_HOST
                    logclass = LOGCLASS_PASSIVECHECK
                    host_name, state, check_plugin_output = options.split(';', 2)
                elif type == 'SERVICE EVENT HANDLER':
                    # SERVICE EVENT HANDLER: test_host_0;test_ok_0;CRITICAL;SOFT;1;eventhandler
                    logobject = LOGOBJECT_SERVICE
                    host_name, service_description, state, state_type, attempt, command_name = options.split(';', 5)
                    state = service_states[state]

                elif type == 'HOST EVENT HANDLER':
                    logobject = LOGOBJECT_HOST
                    host_name, state, state_type, attempt, command_name = options.split(';', 4)
                    state = host_states[state]

                elif type == 'EXTERNAL COMMAND':
                    logobject = LOGOBJECT_INFO
                    logclass = LOGCLASS_COMMAND
                elif type.startswith('starting...') or \
                     type.startswith('shutting down...') or \
                     type.startswith('Bailing out') or \
                     type.startswith('active mode...') or \
                     type.startswith('standby mode...') or \
                     type.startswith('Debug') or \
                     type.startswith('Warning') or \
                     type.startswith('Info'):
                    logobject = LOGOBJECT_INFO
                    logclass = LOGCLASS_PROGRAM
                else:
                    logger.debug("[Livestatus Log Lines] Does not match")
                    pass

                Logline.id += 1
                self.lineno = Logline.id
                setattr(self, 'logobject', int(logobject))
                setattr(self, 'attempt', int(attempt))
                setattr(self, 'logclass', int(logclass))
                setattr(self, 'command_name', command_name)
                setattr(self, 'comment', comment)
                setattr(self, 'contact_name', contact_name)
                setattr(self, 'host_name', host_name)
                setattr(self, 'message', message)
                setattr(self, 'options', '') # Fix a mismatch of number of fields with old databases and new ones
                setattr(self, 'plugin_output', plugin_output)
                setattr(self, 'service_description', service_description)
                setattr(self, 'state', state)
                setattr(self, 'state_type', state_type)
                setattr(self, 'time', int(time))
                setattr(self, 'type', type)

    def as_tuple(self):
        return tuple([str(getattr(self, col)) for col in Logline.columns])

    def as_dict(self):
        return dict(zip(Logline.columns, [getattr(self, col) for col in Logline.columns]))

    def __str__(self):
        return "line: %s" % self.message

    def fill(self, datamgr):
        """Attach host and/or service objects to a Logline object

        Lines describing host or service events only contain host_name
        and/or service_description. This method finds the corresponding
        objects and adds them to the line as attributes log_host
        and/or log_service

        """
        if hasattr(self, 'logobject') and self.logobject == LOGOBJECT_HOST:
            try:
                setattr(self, 'log_host', datamgr.get_host(self.host_name))
            except Exception, e:
                logger.error("[Livestatus Log Lines] Error on host: %s" % e)
                pass
        elif hasattr(self, 'logobject') and self.logobject == LOGOBJECT_SERVICE:
            try:
                setattr(self, 'log_host', datamgr.get_host(self.host_name))
                setattr(self, 'log_service', datamgr.get_service(self.host_name, self.service_description))
            except Exception, e:
                logger.error("[Livestatus Log Lines] Error on service: %s" % e)
                pass
        else:
            setattr(self, 'log_host', None)
            setattr(self, 'log_service', None)
        return self
