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

from collections import namedtuple

from shinken.log import logger
from livestatus_broker_common import LiveStatusQueryError

try:
    from ujson import dumps, loads
except ImportError:
    try:
        from simplejson import dumps, loads, JSONEncoder
        # ujson's dumps() cannot handle a separator parameter, which is
        # needed to avoid unnecessary spaces in the json output
        # That's why simplejson and json manipulate the encoder class
        JSONEncoder.item_separator = ','
        JSONEncoder.key_separator = ':'
    except ImportError:
        from json import dumps, loads, JSONEncoder
        JSONEncoder.item_separator = ','
        JSONEncoder.key_separator = ':'


Separators = namedtuple('Separators',
                        ('line', 'field', 'list', 'pipe')) # pipe is used within livestatus_broker.mapping 


class LiveStatusListResponse(list):
    ''' A class to be able to recognize list of data/bytes to be sent vs plain data/bytes. '''

    def __iter__(self):
        '''Iter over the values and eventual sub-values. This so also
recursively iter of the values of eventual sub-LiveStatusListResponse. '''
        for value in super(LiveStatusListResponse, self).__iter__():
            if isinstance(value, LiveStatusListResponse):
                for v2 in value:
                    yield v2
            else:
                yield value

    def total_len(self):
        '''
        :return: The total "len" of what's contained in this LiveStatusListResponse instance.
If this instance contains others LiveStatusListResponse instances then their total_len() will also used.
        '''
        return sum(len(value) for value in self)

    def clean(self):
        idx = len(self) - 1
        while idx >= 0:
            v = self[idx]
            if isinstance(v, LiveStatusListResponse):
                v.clean()
            del self[idx]
            idx -= 1


class LiveStatusResponse:
    """A class which represents the response to a LiveStatusRequest.

    Public functions:
    respond -- Add a header to the response text
    format_live_data -- Take the raw output and format it according to
    the desired output format (csv or json)

    """

    separators = Separators('\n', ';', ',', '|')

    def __init__(self, responseheader='off', outputformat='csv', keepalive='off', columnheaders='off', separators=separators):
        self.responseheader = responseheader
        self.outputformat = outputformat
        self.keepalive = keepalive
        self.columnheaders = columnheaders
        self.separators = separators
        self.statuscode = 200
        self.output = LiveStatusListResponse()

    def __str__(self):
        output = "LiveStatusResponse:\n"
        for attr in ["responseheader", "outputformat", "keepalive", "columnheaders", "separators"]:
            output += "response %s: %s\n" % (attr, getattr(self, attr))
        return output

    def set_error(self, statuscode, data):
        del self.output[:]
        self.output.append( LiveStatusQueryError.messages[statuscode] % data )
        self.statuscode = statuscode

    def load(self, query):
        self.query = query

    def get_response_len(self, rsp=None):
        if rsp is None:
            rsp = self.output
        if isinstance(rsp, LiveStatusListResponse):
            return rsp.total_len()
        else:
            return len(rsp)

    def respond(self):
        if self.responseheader == 'fixed16':
            responselength = 1 + self.get_response_len() # 1 for the final '\n'
            self.output.insert(0, '%3d %11d\n' % (self.statuscode, responselength))
        self.output.append('\n')
        return self.output, self.keepalive

    def _compact(self, lines):
        if len(lines) >= 4 * 4096:
            self.output.append(lines)
            lines = LiveStatusListResponse()
        return lines

    def format_live_data(self, result, columns, aliases):
        '''

        :param result:
        :param columns:
        :param aliases:
        :return:
        '''
        if self.query.stats_query:
            return self.format_live_data_stats(result, columns, aliases)

        showheader = False
        query_with_columns = len(columns) != 0
        if not query_with_columns:
            columns = self.query.table_class_map[self.query.table][1].lsm_columns
            # There is no pre-selected list of columns. In this case
            # we output all columns.

        lines = LiveStatusListResponse()
        if self.outputformat == 'csv':
            for item in result:
                # Construct one line of output for each object found
                l = []
                lines = self._compact(lines)
                for c in columns:
                    attribute = 'lsm_' + c
                    try:
                        value = getattr(item, attribute)(self.query)
                    except Exception:
                        if hasattr(item, attribute):
                            value = getattr(item.__class__, attribute).im_func.default
                        else:
                            # If nothing else helps, leave the column blank
                            value = ''

                    if isinstance(value, list):
                        l.append(self.separators.list.join(str(x) for x in value))
                    elif isinstance(value, bool):
                        l.append('1' if value else '0')
                    else:
                        try:
                            l.append(str(value))
                        except UnicodeEncodeError as err:
                            logger.warning('UnicodeEncodeError on str() of: %r : %s' % (value, err))
                            l.append(value.encode('utf-8', 'replace'))
                        except Exception as err:
                            logger.warning('Unexpected error on str() of: %r : %s' % (value, err))
                            l.append('')

                lines.append(self.separators.field.join(l) + self.separators.line)

            if len(lines) > 0:
                lines[-1] = lines[-1][:-1]  # remove last separator added
                if self.columnheaders != 'off' or not query_with_columns:
                    if len(aliases) > 0:
                        showheader = True
                    else:
                        showheader = True
                        if not query_with_columns:
                            # Show all available columns
                            pass
            elif self.columnheaders == 'on':
                showheader = True

            if showheader:
                lines.insert(0, self.separators.field.join(
                    (aliases[col] for col in columns) if len(aliases)
                    else columns
                ) + self.separators.line)

            self.output.append(lines)

        elif self.outputformat == 'json' or self.outputformat == 'python':
            for item in result:
                #lines = self._compact(lines)
                rows = []
                for c in columns:
                    attribute = 'lsm_' + c
                    try:
                        value = getattr(item, attribute)(self.query)
                    except Exception as exp:
                        if hasattr(item, attribute):
                            #print "FALLBACK: %s.%s" % (type(item), attribute)
                            value = getattr(item.__class__, attribute).im_func.default
                        else:
                            rows.append(u'')
                            continue

                    if isinstance(value, bool):
                        rows.append(1 if value else 0)
                    else:
                        try:
                            rows.append(value)
                        except UnicodeEncodeError as err:
                            logger.warning('UnicodeEncodeError on str() of: %r : %s' % (value, err))
                            rows.append(value.encode('utf-8', 'replace'))
                        except Exception as err:
                            logger.warning('Unexpected error on str() of: %r : %s' % (value, err))
                            rows.append(u'')
                lines.append(rows)

            if self.columnheaders == 'on':
                lines.insert(0, (str(aliases[col]) for col in columns) if len(aliases) else columns)

            self.output.append( (dumps if self.outputformat == 'json' else str)(lines) )

        else:
            # TODO: handle some error..
            raise RuntimeError('Unhandled output format: %r' % self.outputformat)

    def format_live_data_stats(self, result, columns, aliases):
        showheader = False
        lines = LiveStatusListResponse()
        if self.outputformat == 'csv':
            # statsified results always have columns (0, 1, 2, ...)
            for item in result:
                lines = self._compact(lines)
                # Construct one line of output for each object found
                l = []
                for value in [item[c] for c in columns]:
                    if isinstance(value, list):
                        l.append(self.separators.list.join(str(y) for y in value))
                    elif isinstance(value, bool):
                        l.append('1' if value else '0')
                    else:
                        try:
                            l.append(str(value))
                        except UnicodeEncodeError as err:
                            logger.warning('UnicodeEncodeError on str() of: %r : %s' % (value, err))
                            l.append(value.encode("utf-8", "replace"))
                        except Exception as err:
                            logger.warning('Unexpected error on str() of: %r : %s' % (value, err))
                            l.append("")
                lines.append(self.separators.field.join(l) + self.separators.line)
            # end for item in result

            if len(lines) > 0:
                lines[-1] = lines[-1][:-1] # skip last added separator
                if self.columnheaders != 'off' or len(columns) == 0:
                    if len(aliases) > 0:
                        showheader = True
                    else:
                        showheader = True
                        if len(columns) == 0:
                            # Show all available columns
                            #columns = sorted(object.keys())
                            pass
            elif self.columnheaders == 'on':
                showheader = True

            if showheader:
                lines.insert(0, self.separators.field.join(
                    (str(aliases[col]) for col in columns) if len(aliases)
                    else columns))
                lines[0] += self.separators.line

            self.output.append(lines)

        elif self.outputformat == 'json' or self.outputformat == 'python':
            encode = dumps if self.outputformat == 'json' else str
            for item in result:
                #lines = self._compact(lines)
                rows = []
                for c in columns:
                    if isinstance(item[c], bool):
                        rows.append(1 if item[c] else 0)
                    else:
                        rows.append(item[c])
                lines.append(rows)

            if self.columnheaders == 'on':
                lines.insert(0, (str(aliases[col]) for col in columns) if len(aliases) else columns)

            self.output.append(encode(lines))
