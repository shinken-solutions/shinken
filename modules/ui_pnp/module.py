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
This class is for linking the WebUI with PNP,
for mainly get graphs and links.
"""

import socket

from shinken.log import logger
from shinken.basemodule import BaseModule

properties = {
    'daemons': ['webui'],
    'type': 'pnp_webui'
    }

# called by the plugin manager
def get_instance(plugin):
    logger.info("Get an PNP UI module for plugin %s" % plugin.get_name())

    instance = PNP_Webui(plugin)
    return instance


class PNP_Webui(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.uri = getattr(modconf, 'uri', None)
        self.username = getattr(modconf, 'username', None)
        self.password = getattr(modconf, 'password', '')

        if not self.uri:
            raise Exception('The WebUI PNP module is missing uri parameter.')

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

    # For an element, give the number of elements in
    # the perf_data
    def get_number_of_metrics(self, elt):
        perf_data = elt.perf_data.strip()
        elts = perf_data.split(' ')
        elts = [e for e in elts if e != '']
        return len(elts)

    # Give the link for the PNP UI, with a Name
    def get_external_ui_link(self):
        return {'label': 'PNP4', 'uri': self.uri}

    # Ask for an host or a service the graph UI that the UI should
    # give to get the graph image link and PNP page link too.
    # for now, the source variable does nothing. Values passed to this variable can be : 
    # 'detail' for the element detail page
    # 'dashboard' for the dashboard widget
    # you can customize the url depending on this value. (or not)
    def get_graph_uris(self, elt, graphstart, graphend, source = 'detail'):
        if not elt:
            return []

        t = elt.__class__.my_type
        r = []

        if t == 'host':
            nb_metrics = self.get_number_of_metrics(elt)
            for i in range(nb_metrics):
                v = {}
                v['link'] = self.uri + 'index.php/graph?host=%s&srv=_HOST_' % elt.get_name()
                v['img_src'] = self.uri + 'index.php/image?host=%s&srv=_HOST_&view=0&source=%d&start=%d&end=%d' % (elt.get_name(), i, graphstart, graphend)
                r.append(v)
            return r
        if t == 'service':
            nb_metrics = self.get_number_of_metrics(elt)
            for i in range(nb_metrics):
                v = {}
                v['link'] = self.uri + 'index.php/graph?host=%s&srv=%s' % (elt.host.host_name, elt.service_description)
                v['img_src'] = self.uri + 'index.php/image?host=%s&srv=%s&view=0&source=%d&start=%d&end=%d' % (elt.host.host_name, elt.service_description, i, graphstart, graphend)
                r.append(v)
            return r

        # Oups, bad type?
        return []
