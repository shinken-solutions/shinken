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

#print "Loaded AD module"

properties = {
    'daemons' : ['webui'],
    'type' : 'graphite_webui'
    }


#called by the plugin manager
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



    # For a perf_data like /=30MB;4899;4568;1234;0  /var=50MB;4899;4568;1234;0 /toto=
    # return ('/', '30'), ('/var', '50')
    def get_metric_and_value(self, perf_data):
        res = []
        s = perf_data.strip()
        # Get all metrics non void
        elts = s.split(' ')
        metrics = [e for e in elts if e != '']

        for e in metrics:
 #           print "Graphite : groking : ", e
            elts = e.split('=', 1)
            if len(elts) != 2:
                continue
            #name = elts[0]
            name = re.sub("[^a-zA-Z0-9]", "_", elts[0])
            raw = elts[1]
            # get the first value of ;
            if ';' in raw:
                elts = raw.split(';')
                value = elts[0]
            else:
                value = raw
            # bailout if need
            if value == '':
                continue

            # Try to get the int/float in it :)
            m = re.search("(\d*\.*\d*)", value)
            if m:
                value = m.groups(0)[0]
            else:
                continue
#            print "graphite : got in the end :", name, value
            res.append((name, value))
        return res
        


    # Ask for an host or a service the graph UI that the UI should
    # give to get the graph image link and PNP page link too.
    def get_graph_uris(self, elt, graphstart, graphend):
        if not elt:
            return []

        t = elt.__class__.my_type
        r = []

        # Do we have a template ?
        if os.path.isfile(self.templates_path+'/'+elt.check_command.get_name().split('!')[0]):
            template_html = ''
            with open(self.templates_path+'/'+elt.check_command.get_name().split('!')[0],'r') as template_file:
                template_html += template_file.read()
            # Read the template file, as template string python object
            template_file.closed
            html=Template(template_html)
            # Build the dict to instanciate the template string
            values = {}
            values['graphstart'] = graphstart
            values['graphend'] = graphend 
            if t == 'host':
                values['host'] = re.sub("[^a-zA-Z0-9]", "_",elt.host_name)
                values['service'] = '__HOST__'
            if t == 'service':
                values['host'] = re.sub("[^a-zA-Z0-9]", "_",elt.host.host_name)
                values['service'] = re.sub("[^a-zA-Z0-9]", "_",elt.service_description)
            values['uri'] = self.uri
            # Split, we may have several images.
            for img in html.substitute(values).split('\n'):
                if not img == "":
                    v = {}
                    v['link'] = self.uri
                    v['img_src'] = img.replace('"',"'")
                    r.append(v)
            # No need to continue, we have the images already.      					
            return r
             
        # If no template is present, then the usual way

        if t == 'host':
            couples = self.get_metric_and_value(elt.perf_data)

            # If no values, we can exit now
            if len(couples) == 0:
                return []

            base_uri = self.uri + 'render/?width=586&height=308'
            # Send a bulk of all metrics at once
            for (metric, _) in couples:
                uri = base_uri +  "&target=%s.__HOST__.%s" % (re.sub("[^a-zA-Z0-9]", "_",elt.host_name), metric)
                v = {}
                v['link'] = self.uri
                v['img_src'] = uri
                r.append(v)

            return r
        if t == 'service':
            couples = self.get_metric_and_value(elt.perf_data)

            # If no values, we can exit now
            if len(couples) == 0:
                return []

            base_uri = self.uri + 'render/?width=586&height=308'
            
            # Send a bulk of all metrics at once
            for (metric, _) in couples:
                uri = base_uri + "&target=%s.%s.%s" % (re.sub("[^a-zA-Z0-9]", "_",elt.host.host_name), re.sub("[^a-zA-Z0-9]", "_",elt.service_description), metric)
                v = {}
                v['link'] = self.uri
                v['img_src'] = uri
                r.append(v)
				
            return r

        # Oups, bad type?
        return []
