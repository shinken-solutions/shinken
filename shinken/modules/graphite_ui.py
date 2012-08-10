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

"""
This class is for linking the WebUI with Graphite,
for mainly get graphs and links.
"""

import re
import socket
import os

from string import Template
from shinken.basemodule import BaseModule
from datetime import datetime

# print "Loaded AD module"

properties = {
    'daemons': ['webui'],
    'type': 'graphite_webui'
    }


# called by the plugin manager
def get_instance(plugin):
    print "Get an GRAPITE UI module for plugin %s" % plugin.get_name()

    instance = Graphite_Webui(plugin)
    return instance


class Graphite_Webui(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.uri = getattr(modconf, 'uri', None)
        self.templates_path = getattr(modconf, 'templates_path', '/tmp')

        if not self.uri:
            raise Exception('The WebUI Graphite module is missing uri parameter.')

        self.uri = self.uri.strip()
        if not self.uri.endswith('/'):
            self.uri += '/'

        # Change YOURSERVERNAME by our server name if we got it
        if 'YOURSERVERNAME' in self.uri:
            my_name = socket.gethostname()
            self.uri = self.uri.replace('YOURSERVERNAME', my_name)

    # Try to connect if we got true parameter
    def init(self):
        pass

    # To load the webui application
    def load(self, app):
        self.app = app

    # Give the link for the GRAPHITE UI, with a Name
    def get_external_ui_link(self):
        return {'label': 'Graphite', 'uri': self.uri}

    # For a perf_data like /=30MB;4899;4568;1234;0  /var=50MB;4899;4568;1234;0 /toto=
    # return ('/', '30'), ('/var', '50')
    def get_metric_and_value(self, perf_data):
        res = []
        s = perf_data.strip()
        # Get all metrics non void
        elts = s.split(' ')
        metrics = [e for e in elts if e != '']

        for e in metrics:
            #print "Graphite: groking: ", e
            elts = e.split('=', 1)
            if len(elts) != 2:
                continue
            name = self.illegal_char.sub('_', elts[0])
            raw = elts[1]
            # get the first value of ;
            if ';' in raw:
                elts = raw.split(';')
                name_value = {name: elts[0], name + '_warn': elts[1], name + '_crit': elts[2]}
            else:
                value = raw
                name_value = {name: raw}
            # bailout if need
            if name_value[name] == '':
                continue

            # Try to get the int/float in it :)
            for key, value in name_value.items():
                m = re.search("(\d*\.*\d*)(.*)", value)
                if m:
                    name_value[key] = m.groups(0)
                else:
                    continue
#            print "graphite: got in the end:", name, value
            for key, value in name_value.items():
                res.append((key, value))
        return res

    # Private function to replace the fontsize uri parameter by the correct value
    # or add it if not present.
    def _replaceFontSize ( self, url, newsize ):

    # Do we have fontSize in the url alreadu, or not ?
        if re.search('fontSize=',url) is None:
            url = url + '&fontSize=' + newsize
        else:
            url = re.sub(r'(fontSize=)[^\&]+',r'\g<1>' + newsize , url);
        return url




    # Ask for an host or a service the graph UI that the UI should
    # give to get the graph image link and Graphite page link too.
    def get_graph_uris(self, elt, graphstart, graphend, source = 'detail'):
        # Ugly to hard-code such values. But where else should I put them ?
        fontsize={ 'detail': '8', 'dashboard': '18'}
        if not elt:
            return []

        t = elt.__class__.my_type
        r = []

        # Format the start & end time (and not only the date)
        d = datetime.fromtimestamp(graphstart)
        d = d.strftime('%H:%M_%Y%m%d')
        e = datetime.fromtimestamp(graphend)
        e = e.strftime('%H:%M_%Y%m%d')

        filename = elt.check_command.get_name().split('!')[0] + '.graph'

        # Do we have a template for the given source?
        thefile = os.path.join(self.templates_path, source, filename)

        # If not try to use the one for the parent folder
        if not os.path.isfile(thefile):
            thefile = os.path.join(self.templates_path, filename)

        if os.path.isfile(thefile):
            template_html = ''
            with open(thefile, 'r') as template_file:
                template_html += template_file.read()
            # Read the template file, as template string python object
           
            html = Template(template_html)
            # Build the dict to instanciate the template string
            values = {}
            if t == 'host':
                values['host'] = self.illegal_char.sub("_", elt.host_name)
                values['service'] = '__HOST__'
            if t == 'service':
                values['host'] = self.illegal_char.sub("_", elt.host.host_name)
                values['service'] = self.illegal_char.sub("_", elt.service_description)
            values['uri'] = self.uri
            # Split, we may have several images.
            for img in html.substitute(values).split('\n'):
                if not img == "":
                    v = {}
                    v['link'] = self.uri
                    v['img_src'] = img.replace('"', "'") + "&from=" + d + "&until=" + e
                    v['img_src'] = self._replaceFontSize(v['img_src'], fontsize[source])
                    r.append(v)
            # No need to continue, we have the images already.
            return r

        # If no template is present, then the usual way

        if t == 'host':
            couples = self.get_metric_and_value(elt.perf_data)

            # If no values, we can exit now
            if len(couples) == 0:
                return []

            # Remove all non alpha numeric character
            host_name = self.illegal_char.sub('_', elt.host_name)

            # Send a bulk of all metrics at once
            for (metric, _) in couples:
                uri = self.uri + 'render/?width=586&height=308&lineMode=connected&from=' + d + "&until=" + e
                if re.search(r'_warn|_crit', metric):
                    continue
                uri += "&target=%s.__HOST__.%s" % (host_name, metric)
                v = {}
                v['link'] = self.uri
                v['img_src'] = uri
                v['img_src'] = self._replaceFontSize(v['img_src'], fontsize[source])
                r.append(v)

            return r
        if t == 'service':
            couples = self.get_metric_and_value(elt.perf_data)

            # If no values, we can exit now
            if len(couples) == 0:
                return []

            # Remove all non alpha numeric character
            desc = self.illegal_char.sub('_', elt.service_description)
            host_name = self.illegal_char.sub('_', elt.host.host_name)

            # Send a bulk of all metrics at once
            for (metric, value) in couples:
                uri = self.uri + 'render/?width=586&height=308&lineMode=connected&from=' + d + "&until=" + e
                if re.search(r'_warn|_crit', metric):
                    continue
                elif value[1] == '%':
                    uri += "&yMin=0&yMax=100"
                uri += "&target=%s.%s.%s" % (host_name, desc, metric)
                v = {}
                v['link'] = self.uri
                v['img_src'] = uri
                v['img_src'] = self._replaceFontSize(v['img_src'], fontsize[source])
                r.append(v)
            return r

        # Oups, bad type?
        return []
