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


import os
import csv


from shinken.basemodule import BaseModule
from shinken.log import logger


properties = {
    'daemons': ['arbiter'],
    'type': 'csv_tag',
    }


# called by the plugin manager to get a module
def get_instance(plugin):
    logger.info("[CSV Tag] Get a CSVTag module for plugin %s" % plugin.get_name())

    # Catch errors
    path = plugin.path
    id_field = plugin.id_field
    id_strip_options = getattr(plugin, 'id_strip_options', '')
    use_properties = getattr(plugin, 'use_properties', '')
    macros_properties = getattr(plugin, 'macros_properties', '')
    method = getattr(plugin, 'method', 'replace')
    ignore_hosts = getattr(plugin, 'ignore_hosts', None)

    instance = CSV_Tag_Arbiter(plugin, path, use_properties, macros_properties, method, ignore_hosts, id_field, id_strip_options)
    return instance




# Cleaning functions
def strip_lower(s):
    return s.lower()

def strip_nofqdn(s):
    # No .? not a full fqdn
    if not '.' in s:
        return s
    tmp = s.split('.', 1)
    # Warning: maybe it's an ipv4 (v6 just bail out before, did you at least
    # read the code???), if so don't touch it
    is_ip = False
    try:
        # Very simple, but should be ok I think
        i = int(tmp[0])
        if 0 < i < 255:
            is_ip = True
    except ValueError:
        is_ip = False
    # If it was an ip, return it and pray for the poor admin that will have
    # to manage full ip names....
    if is_ip:
        return s
    return tmp[0]
    

# Just print some stuff
class CSV_Tag_Arbiter(BaseModule):
    def __init__(self, mod_conf, path, use_properties, macros_properties, method, ignore_hosts, id_field, id_strip_options):
        BaseModule.__init__(self, mod_conf)
        self.path = path
        self.csv = None
        
        self.use_properties_names = [t.strip() for t in use_properties.split(',') if t]
        self.use_properties = []
        self.macros_properties_names = [t.strip() for t in macros_properties.split(',') if t]
        self.macros_properties = []
        
        self.method = method
        self.id_strip_options = id_strip_options
        if ignore_hosts:
            self.ignore_hosts = [h.strip() for h in ignore_hosts.split(', ')]
            logger.debug("[CSV Tag] Ignoring hosts : %s" % self.ignore_hosts)
        else:
            self.ignore_hosts = []
        self.id_field = id_field
        if not self.id_field:
            raise Exception("[CSV Tag] missing mandatory option id_field")
        self.id_field_idx = -1
        
        self.cleaning_functions = []
        _d = {'lower': strip_lower, 'nofqdn':strip_nofqdn}
        for e in self.id_strip_options.split('|'):
            e = e.strip()
            if not e:
                continue
            f = _d.get(e, None)
            if not f:
                raise Exception('[CSV Tag] Unknown strip option:%s' % e)
            self.cleaning_functions.append(f)

        self.lines = []
        self.first_line = None
        self.index = {}
        

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[CSV Tag] Initialization of the ip range tagger module")
        with open(self.path, 'rb') as self.csv:
            reader = csv.reader(self.csv)
            for row in reader:
                self.lines.append(row)
        # Take the first line as the Key lines
        if len(self.lines) == 0:
            return
        # We take and remove the first line
        self.first_line = self.lines.pop(0)
        # Search the index of the id_field
        try:
            self.id_field_idx = self.first_line.index(self.id_field)
        except ValueError:
            raise Exception('[CSV Tag] The id_field %s cannot be found on the first line' % self.id_field)
        # Now look at the index of the use_properties entry
        for fname in self.use_properties_names:
            try:
                fidx = self.first_line.index(fname)
                self.use_properties.append(fidx)
            except ValueError:
                raise Exception('[CSV Tag] The use_properties field %s cannot be found on the first line' % fname)
        # Same but for macros_properties_names
        for fname in self.macros_properties_names:
            try:
                fidx = self.first_line.index(fname)
                if not fname.startswith('_'):
                    fname = '_'+fname
                self.macros_properties.append( (fname, fidx) )
            except ValueError:
                raise Exception('[CSV Tag] The macros_properties field %s cannot be found on the first line' % fname)
        
        # Now apply for each the lines the strip operations
        i = 0
        for line in self.lines:
            try:
                v = line[self.id_field_idx]
            except IndexError:
                logger.warning('[CSV Tag] One line of the csv file is missing the id_field index')
            for f in self.cleaning_functions:
                v = f(v)
            line[self.id_field_idx] = v
            self.index[v] = i
            i += 1
        


    def hook_early_configuration(self, arb):
        logger.info("[CSVTag] in hook early config")
        for h in arb.conf.hosts:
            if not hasattr(h, 'host_name'):
                continue

            hname = h.get_name()
            if hname in self.ignore_hosts:
                logger.debug("[CSV Tag] Ignoring host %s" % hname)
                continue

            # Now look at the clean the host entry
            idx = self.index.get(hname, None)
            if not idx: #not found, skip this one
                continue
            
            # Look at the line for this host
            line = self.lines[idx]

            logger.debug("[CSV Tag] host name match %s" % hname)

            csv_use_values = []
            for fidx in self.use_properties:
                try:
                    csv_value = line[fidx].strip()
                    if csv_value:
                        csv_use_values.append(csv_value)
                except IndexError:
                    logger.warning('[CSV Tag] one line is missing a use_properties entry')
            csv_use_value = ','.join(csv_use_values)

            if csv_use_value:
                # 4 cases: append , replace and set
                # append will join with the value if exist (on the END)
                # prepend will join with the value if exist (on the BEGINING)
                # replace will replace it if NOT existing
                # set put the value even if the property exists
                if self.method == 'append':
                    orig_v = getattr(h, 'use', '')
                    new_v = ','.join([orig_v, csv_use_value])
                    setattr(h, 'use', new_v)
                
                # Same but we put before
                if self.method == 'prepend':
                    orig_v = getattr(h, 'use', '')
                    new_v = ','.join([csv_use_value, orig_v])
                    setattr(h, 'use', new_v)

                if self.method == 'replace':
                    if not hasattr(h, 'use'):
                        # Ok, set the value!
                        setattr(h, 'use', csv_use_value)

                if self.method == 'set':
                    setattr(h, 'use', csv_use_value)

            # Now the macros, here we just set them
            for (fname, fidx) in self.macros_properties:
                try:
                    csv_value = line[fidx].strip()
                    if csv_value:
                        setattr(h, fname, csv_value)
                except IndexError:
                    logger.warning('[CSV Tag] one line is missing a macros_properties entry')
                

        # We finish? We can clean now
        self.lines = None
            
            
