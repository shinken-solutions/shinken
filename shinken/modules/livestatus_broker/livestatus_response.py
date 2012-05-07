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

class LiveStatusResponse:

    """A class which represents the response to a livestatus request.

    Public functions:
    respond -- Add a header to the response text
    format_live_data -- Take the raw output and format it according to
    the desired output format (csv or json)

    """

    separators = map(lambda x: chr(int(x)), [10, 59, 44, 124])
    
    def __init__(self, responseheader = 'off', outputformat = 'csv', keepalive = 'off', columnheaders = 'off', separators = separators):
        self.responseheader = responseheader
        self.outputformat = outputformat
        self.keepalive = keepalive
        self.columnheaders = columnheaders
        self.separators = separators
        self.statuscode = 200
        self.output = ''
        pass


    def __str__(self):
        output = "LiveStatusResponse:\n"
        for attr in ["responseheader", "outputformat", "keepalive", "columnheaders", "separators"]:
            output += "response %s: %s\n" % (attr, getattr(self, attr))
        return output

    def load(self, query):
        self.query = query

    def respond(self):
        self.output += '\n'
        if self.responseheader == 'fixed16':
            responselength = len(self.output)
            self.output = '%3d %11d\n' % (self.statuscode, responselength) + self.output

        return self.output, self.keepalive

    def format_live_data(self, result, columns, aliases):
        if self.query.stats_query:
            return self.format_live_data_stats(result, columns, aliases)
        lines = []
        showheader = False
        query_with_columns = len(columns) != 0
        if not query_with_columns:
            columns = self.query.table_class_map[self.query.table][1].lsm_columns
            # There is no pre-selected list of columns. In this case
            # we output all columns.
        if self.outputformat == 'csv':
            for item in result:
                # Construct one line of output for each object found
                l = []
                for c in columns:
                    attribute = 'lsm_'+c
                    try:
                        value = getattr(item, attribute)(self.query)
                    except Exception:
                        if hasattr(item, attribute):
                            value = getattr(item.__class__, attribute).im_func.default
                        else:
                            # If nothing else helps, leave the column blank
                            value = ''
                    if isinstance(value, list):
                        l.append(self.separators[2].join(str(x) for x in value))
                    elif isinstance(value, bool):
                        if value == True:
                            l.append('1')
                        else:
                            l.append('0')
                    else:
                        try:
                            l.append(str(value))
                        except UnicodeEncodeError:
                            l.append(value.encode('utf-8', 'replace'))
                        except Exception:
                            l.append('')
                lines.append(self.separators[1].join(l))
            if len(lines) > 0:
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
                if len(aliases) > 0:
                    # This is for statements like "Stats: .... as alias_column
                    lines.insert(0, self.separators[1].join([aliases[col] for col in columns]))
                else:
                    lines.insert(0, self.separators[1].join(columns))
            self.output = self.separators[0].join(lines)

        elif self.outputformat == 'json' or self.outputformat == 'python':
            for item in result:
                rows = []
                for c in columns:
                    attribute = 'lsm_'+c
                    try:
                        value = getattr(item, attribute)(self.query)
                    except Exception, exp:
                        if hasattr(item, attribute):
                            #print "FALLBACK: %s.%s" % (type(item), attribute)
                            value = getattr(item.__class__, attribute).im_func.default
                        else:
                            rows.append(u'')
                            continue
                    if isinstance(value, bool):
                        if value == True:
                            rows.append(1)
                        else:
                            rows.append(0)
                    else:
                        try:
                            rows.append(value)
                        except UnicodeEncodeError:
                            rows.append(value.encode('utf-8', 'replace'))
                        except Exception:
                            rows.append(u'')
                lines.append(rows)
            if self.columnheaders == 'on':
                if len(aliases) > 0:
                    lines.insert(0, [str(aliases[col]) for col in columns])
                else:
                    lines.insert(0, columns)
            if self.outputformat == 'json':
                self.output = dumps(lines)
            else:
                self.output = str(lines)

    def format_live_data_stats(self, result, columns, aliases):
        lines = []
        showheader = False
        if self.outputformat == 'csv':
            # statsified results always have columns (0, 1, 2, ...)
            for item in result:
                # Construct one line of output for each object found
                l = []
                for x in [item[c] for c in columns]:
                    if isinstance(x, list):
                        l.append(self.separators[2].join(str(y) for y in x))
                    elif isinstance(x, bool):
                        if x == True:
                            l.append("1")
                        else:
                            l.append("0")
                    else:
                        try:
                            l.append(str(x))
                        except UnicodeEncodeError:
                            l.append(x.encode("utf-8", "replace"))
                        except Exception:
                            l.append("")
                lines.append(self.separators[1].join(l))
            if len(lines) > 0:
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
                if len(aliases) > 0:
                    # This is for statements like "Stats: .... as alias_column
                    lines.insert(0, self.separators[1].join([aliases[col] for col in columns]))
                else:
                    lines.insert(0, self.separators[1].join(columns))
            self.output = self.separators[0].join(lines)
        elif self.outputformat == 'json' or self.outputformat == 'python':
            for item in result:
                rows = []
                for c in columns:
                    if isinstance(item[c], bool):
                        if object[c] == True:
                            rows.append(1)
                        else:
                            rows.append(0)
                    else:
                        rows.append(item[c])
                lines.append(rows)
            if self.columnheaders == 'on':
                if len(aliases) > 0:
                    lines.insert(0, [str(aliases[col]) for col in columns])
                else:
                    lines.insert(0, columns)
            if self.outputformat == 'json':
                self.output = dumps(lines)
            else:
                self.output = str(lines)
