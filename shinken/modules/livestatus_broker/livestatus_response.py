#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


try:
    import json
except ImportError:
    import simplejson as json

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
        self.output = ''
        pass


    def __str__(self):
        output = "LiveStatusResponse:\n"
        for attr in ["responseheader", "outputformat", "keepalive", "columnheaders", "separators"]:
            output += "response %s: %s\n" % (attr, getattr(self, attr))
        return output


    def respond(self):
        self.output += '\n'
        if self.responseheader == 'fixed16':
            statuscode = 200 
            responselength = len(self.output)
            self.output = '%3d %11d\n' % (statuscode, responselength) + self.output

        return self.output, self.keepalive


    def format_live_data(self, result, columns, aliases):
        lines = []
        header = ''
        showheader = False
        #print "my result is", result
        print "outputformat", self.outputformat
        if self.outputformat == 'csv':
            if len(columns) == 0:
                # There is no pre-selected list of columns. In this case
                # we output all columns.
                for object in result:
                    # Construct one line of output for each object found
                    l = []
                    for x in [object[c] for c in sorted(object.keys())]:
                        if isinstance(x, list):
                            l.append(self.separators[2].join(str(y) for y in x))
                        else:
                            l.append(str(x))
                    lines.append(self.separators[1].join(l))
            else:
                for object in result:
                    # Construct one line of output for each object found
                    l = []
                    for x in [object[c] for c in columns]:
                        if isinstance(x, list):
                            l.append(self.separators[2].join(str(y) for y in x))
                        else:
                            l.append(str(x))
                    lines.append(self.separators[1].join(l))
            if len(lines) > 0:
                if self.columnheaders != 'off' or len(columns) == 0:
                    if len(aliases) > 0:
                        showheader = True
                    else:
                        showheader = True
                        if len(columns) == 0:
                            # Show all available columns
                            columns = sorted(object.keys())
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
            for object in result:
                lines.append([object[c] for c in columns])
            if self.columnheaders == 'on':
                if len(aliases) > 0:
                    lines.insert(0, [str(aliases[col]) for col in columns])
                else:
                    lines.insert(0, columns)
            if self.outputformat == 'json':
                self.output = json.dumps(lines, separators=(',', ':'))
            else:
                print "type is ", type(self)
                self.output = str(json.loads(json.dumps(lines, separators=(',', ':'))))
