#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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



import sys
import os
import re
import time
import copy
import random
import string
# Always initialize random...
random.seed(time.time())
try:
    import uuid
except ImportError:
    uuid = None

try:
    from pymongo.connection import Connection
except ImportError:
    Connection = None

from shinken.log import logger
from shinken.objects import *
from shinken.objects.config import Config
from shinken.macroresolver import MacroResolver
from shinken.modulesmanager import ModulesManager



def get_uuid(self):
    if uuid:
        return uuid.uuid1().hex
    # Ok for old python like 2.4, we will lie here :)
    return int(random.random() * sys.maxint)


# Look if the name is a IPV4 address or not
def is_ipv4_addr(name):
    p = r"^([01]?\d\d?|2[0-4]\d|25[0-5])" \
        r"\.([01]?\d\d?|2[0-4]\d|25[0-5])" \
        r"\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$"
    return (re.match(p, name) is not None)



def by_order(r1, r2):
    if r1.discoveryrule_order == r2.discoveryrule_order:
        return 0
    if r1.discoveryrule_order > r2.discoveryrule_order:
        return 1
    if r1.discoveryrule_order < r2.discoveryrule_order:
        return -1

class DiscoveredHost(object):
    my_type = 'host'  # we fake our type for the macro resolving

    macros = {
        'HOSTNAME':          'name',
    }

    def __init__(self, name, rules, runners, merge=False, first_level_only=False):
        self.name = name
        self.data = {}
        self.rules = rules
        self.runners = runners
        self.merge = merge

        self.matched_rules = []
        self.launched_runners = []

        self.in_progress_runners = []
        self.properties = {}
        self.customs = {}
        self.first_level_only = first_level_only

    # In final phase, we keep only _ properties and
    # rule based one
    def update_properties(self, final_phase=False):
        d = {}
        if final_phase:
            for (k, v) in self.data.iteritems():
                if k.startswith('_'):
                    d[k] = v
        else:
            d = copy.copy(self.data)

        d['host_name'] = self.name
        # Set address directive if an ip exists
        if 'ip' in self.data:
            d['address'] = self.data['ip']

        self.matched_rules.sort(by_order)

        for r in self.matched_rules:
            for k, v in r.writing_properties.iteritems():
                # If it's a + (add) property, append
                if k.startswith('+'):
                    kprop = k[1:]
                    # If the d do not already have this prop,
                    # create list
                    if kprop not in d:
                        print 'New prop', kprop
                        d[kprop] = []

                elif not k.startswith('-'):
                    kprop = k
                    if kprop not in d:
                        print 'New prop', kprop
                    else:
                        print 'Prop', kprop, 'reset with new value'
                    d[kprop] = []

                for prop in string.split(v, ','):
                    prop = prop.strip()
                    # checks that prop does not already exist and adds
                    if prop not in d[kprop]:
                        if len(d[kprop]) > 0:
                            print 'Already got', ','.join(d[kprop]), 'add', prop
                        else:
                            print 'Add', prop
                        d[kprop].append(prop)

            # Now look for - (rem) property
            for k, v in r.writing_properties.iteritems():
                if k.startswith('-'):
                    kprop = k[1:]
                    if kprop in d:
                        for prop in string.split(v, ','):
                            prop = prop.strip()
                            if prop in d[kprop]:
                                print 'Already got', ','.join(d[kprop]), 'rem', prop
                                d[kprop].remove(prop)

        # Change join prop list in string with a ',' separator
        for (k, v) in d.iteritems():
            if isinstance(d[k], list):
                d[k] = ','.join(d[k])

        self.properties = d
        print 'Update our properties', self.name, d

        # For macro-resolving, we should have our macros too
        self.customs = {}
        for (k, v) in self.properties.iteritems():
            self.customs['_' + k.upper()] = v


    # Manager ask us our properties for the configuration, so
    # we keep only rules properties and _ ones
    def get_final_properties(self):
        self.update_properties(final_phase=True)
        return self.properties


    def get_to_run(self):
        self.in_progress_runners = []

        if self.first_level_only:
            return

        for r in self.runners:
            # If we already launched it, we don't want it :)
            if r in self.launched_runners:
                print 'Sorry', r.get_name(), 'was already launched'
                continue
            # First level discovery are for large scan, so not for here
            if r.is_first_level():
                print 'Sorry', r.get_name(), 'is first level'
                continue
            # And of course it must match our data
            print 'Is ', r.get_name(), 'matching??', r.is_matching_disco_datas(self.properties)
            if r.is_matching_disco_datas(self.properties):
                self.in_progress_runners.append(r)



    def need_to_run(self):
        return len(self.in_progress_runners) != 0



    # Now we try to match all our hosts with the rules
    def match_rules(self):
        print 'And our data?', self.data
        for r in self.rules:
            # If the rule was already successfully for this host, skip it
            if r in self.matched_rules:
                print 'We already apply the rule', r.get_name(), 'for the host', self.name
                continue
            print 'Looking for match with a new rule', r.get_name(), 'for the host', self.name
            if r.is_matching_disco_datas(self.data):
                self.matched_rules.append(r)
                print "Generating a new rule", self.name, r.writing_properties
        self.update_properties()



    def read_disco_buf(self, buf):
        print 'Read buf in', self.name
        for l in buf.split('\n'):
            # print ""
            # If it's not a disco line, bypass it
            if not re.search('::', l):
                continue
            # print "line", l
            elts = l.split('::', 1)
            if len(elts) <= 1:
                # print "Bad discovery data"
                continue
            name = elts[0].strip()

            # We can choose to keep only the basename
            # of the nameid, so strip the fqdn
            # But not if it's a plain ipv4 addr
            # TODO : gt this! if self.conf.strip_idname_fqdn:
            if not is_ipv4_addr(name):
                name = name.split('.', 1)[0]

            data = '::'.join(elts[1:])

            # Maybe it's not me?
            if name != self.name:
                if not self.merge:
                    print 'Bad data for me? I bail out data!'
                    data = ''
                else:
                    print 'Bad data for me? Let\'s switch !'
                    self.name = name

            # Now get key,values
            if '=' not in data:
                continue

            elts = data.split('=', 1)
            if len(elts) <= 1:
                continue

            key = elts[0].strip()
            value = elts[1].strip()
            print "INNER -->", name, key, value
            self.data[key] = value


    def launch_runners(self):
        for r in self.in_progress_runners:
            print "I", self.name, " is launching", r.get_name(), "with a %d seconds timeout" % 3600
            r.launch(timeout=3600, ctx=[self])
            self.launched_runners.append(r)


    def wait_for_runners_ends(self):
        all_ok = False
        while not all_ok:
            print 'Loop wait runner for', self.name
            all_ok = True
            for r in self.in_progress_runners:
                if not r.is_finished():
                    # print "Check finished of", r.get_name()
                    r.check_finished()
                b = r.is_finished()
                if not b:
                    # print r.get_name(), "is not finished"
                    all_ok = False
            time.sleep(0.1)


    def get_runners_outputs(self):
        for r in self.in_progress_runners:
            if r.is_finished():
                print'Get output', self.name, r.discoveryrun_name, r.current_launch
                if r.current_launch.exit_status != 0:
                    print "Error on run"
        raw_disco_data = '\n'.join(r.get_output() for r in self.in_progress_runners
                                   if r.is_finished())
        if len(raw_disco_data) != 0:
            print "Got Raw disco data", raw_disco_data
        else:
            print "Got no data!"
            for r in self.in_progress_runners:
                print "DBG", r.current_launch
        # Now get the data for me :)
        self.read_disco_buf(raw_disco_data)


class DiscoveryManager:
    def __init__(self, path, macros, overwrite, runners, output_dir=None,
                 dbmod='', db_direct_insert=False, only_new_hosts=False,
                 backend=None, modules_path='', merge=False, conf=None, first_level_only=False):
        # i am arbiter-like
        self.log = logger
        self.overwrite = overwrite
        self.runners = runners
        self.output_dir = output_dir
        self.dbmod = dbmod
        self.db_direct_insert = db_direct_insert
        self.only_new_hosts = only_new_hosts
        self.log.load_obj(self)
        self.merge = merge
        self.config_files = [path]
        # For specific backend, to override the classic file/db behavior
        self.backend = backend
        self.modules_path = modules_path
        self.first_level_only = first_level_only

        if not conf:
            self.conf = Config()


            buf = self.conf.read_config(self.config_files)

            # Add macros on the end of the buf so they will
            # overwrite the resource.cfg ones
            for (m, v) in macros:
                buf += '\n$%s$=%s\n' % (m, v)

            raw_objects = self.conf.read_config_buf(buf)
            self.conf.create_objects_for_type(raw_objects, 'arbiter')
            self.conf.create_objects_for_type(raw_objects, 'module')
            self.conf.early_arbiter_linking()
            self.conf.create_objects(raw_objects)
            self.conf.linkify_templates()
            self.conf.apply_inheritance()
            self.conf.explode()
            self.conf.apply_implicit_inheritance()
            self.conf.fill_default()
            self.conf.remove_templates()
            self.conf.linkify()
            self.conf.apply_dependencies()
            self.conf.is_correct()
        else:
            self.conf = conf

        self.discoveryrules = self.conf.discoveryrules
        self.discoveryruns = self.conf.discoveryruns

        m = MacroResolver()
        m.init(self.conf)

        # Hash = name, and in it (key, value)
        self.disco_data = {}
        # Hash = name, and in it rules that apply
        self.disco_matches = {}

        self.init_database()
        self.init_backend()


    def add(self, obj):
        pass


    # We try to init the database connection
    def init_database(self):
        self.dbconnection = None
        self.db = None

        if self.dbmod == '':
            return

        for mod in self.conf.modules:
            if getattr(mod, 'module_name', '') == self.dbmod:
                if Connection is None:
                    print "ERROR : cannot use Mongodb database : please install the pymongo library"
                    break
                # Now try to connect
                try:
                    uri = mod.uri
                    database = mod.database
                    self.dbconnection = Connection(uri)
                    self.db = getattr(self.dbconnection, database)
                    print "Connection to Mongodb:%s:%s is OK" % (uri, database)
                except Exception, exp:
                    logger.error('Database init : %s', exp)


    # We try to init the backend if we got one
    def init_backend(self):
        if not self.backend or not isinstance(self.backend, basestring):
            return

        print "Doing backend init"
        for mod in self.conf.modules:
            if getattr(mod, 'module_name', '') == self.backend:
                print "We found our backend", mod.get_name()
                self.backend = mod
        if not self.backend:
            print "ERROR : cannot find the module %s" % self.backend
            sys.exit(2)
        self.modules_manager = ModulesManager('discovery', self.modules_path, [])
        self.modules_manager.set_modules([mod])
        self.modules_manager.load_and_init()
        self.backend = self.modules_manager.instances[0]
        print "We got our backend!", self.backend



    def loop_discovery(self):
        still_loop = True
        i = 0
        while still_loop:
            i += 1
            print '\n'
            print 'LOOP' * 10, i
            still_loop = False
            for (name, dh) in self.disco_data.iteritems():
                dh.update_properties()
                to_run = dh.get_to_run()
                print 'Still to run for', name, to_run
                if dh.need_to_run():
                    still_loop = True
                    dh.launch_runners()
                    dh.wait_for_runners_ends()
                    dh.get_runners_outputs()
                    dh.match_rules()



    def read_disco_buf(self):
        buf = self.raw_disco_data
        for l in buf.split('\n'):
            # print ""
            # If it's not a disco line, bypass it
            if not re.search('::', l):
                continue
            # print "line", l
            elts = l.split('::', 1)
            if len(elts) <= 1:
                # print "Bad discovery data"
                continue
            name = elts[0].strip()

            # We can choose to keep only the basename
            # of the nameid, so strip the fqdn
            # But not if it's a plain ipv4 addr
            if self.conf.strip_idname_fqdn:
                if not is_ipv4_addr(name):
                    name = name.split('.', 1)[0]

            data = '::'.join(elts[1:])

            # Register the name
            if name not in self.disco_data:
                self.disco_data[name] = DiscoveredHost(name,
                                                       self.discoveryrules,
                                                       self.discoveryruns,
                                                       merge=self.merge,
                                                       first_level_only=self.first_level_only)

            # Now get key,values
            if '=' not in data:
                continue

            elts = data.split('=', 1)
            if len(elts) <= 1:
                continue

            dh = self.disco_data[name]
            key = elts[0].strip()
            value = elts[1].strip()
            print "-->", name, key, value
            dh.data[key] = value


    # Now we try to match all our hosts with the rules
    def match_rules(self):
        for (name, dh) in self.disco_data.iteritems():
            for r in self.discoveryrules:
                # If the rule was already successfully for this host, skip it
                if r in dh.matched_rules:
                    print 'We already apply the rule', r.get_name(), 'for the host', name
                    continue
                if r.is_matching_disco_datas(dh.data):
                    dh.matched_rules.append(r)
                    if name not in self.disco_matches:
                        self.disco_matches[name] = []
                    self.disco_matches[name].append(r)
                    print "Generating", name, r.writing_properties
            dh.update_properties()


    def is_allowing_runners(self, name):
        name = name.strip()

        # If we got no value, it's * by default
        if '*' in self.runners:
            return True

        # print self.runners
        # If we match the name, ok
        for r in self.runners:
            r_name = r.strip()
            # print "Look", r_name, name
            if r_name == name:
                return True

        # Not good, so not run this!
        return False


    def allowed_runners(self):
        return [r for r in self.discoveryruns if self.is_allowing_runners(r.get_name())]


    def launch_runners(self):
        allowed_runners = self.allowed_runners()

        if len(allowed_runners) == 0:
            print "ERROR : there is no matching runners selected!"
            return

        for r in allowed_runners:
            print "I'm launching %s with a %d seconds timeout" % \
                  (r.get_name(), self.conf.runners_timeout)
            r.launch(timeout=self.conf.runners_timeout)


    def wait_for_runners_ends(self):
        all_ok = False
        while not all_ok:
            '''
            all_ok = True
            for r in self.allowed_runners():
                if not r.is_finished():
                    #print "Check finished of", r.get_name()
                    r.check_finished()
                b = r.is_finished()
                if not b:
                    #print r.get_name(), "is not finished"
                    all_ok = False
            '''
            all_ok = self.is_all_ok()
            time.sleep(0.1)


    def is_all_ok(self):
        all_ok = True
        for r in self.allowed_runners():
            if not r.is_finished():
                # print "Check finished of", r.get_name()
                r.check_finished()
            b = r.is_finished()
            if not b:
                # print r.get_name(), "is not finished"
                all_ok = False
        return all_ok


    def get_runners_outputs(self):
        for r in self.allowed_runners():
            if r.is_finished():
                print r.discoveryrun_name, r.current_launch
                if r.current_launch.exit_status != 0:
                    print "Error on run"
        self.raw_disco_data = '\n'.join(r.get_output() for r in self.allowed_runners()
                                        if r.is_finished())
        if len(self.raw_disco_data) != 0:
            print "Got Raw disco data", self.raw_disco_data
        else:
            print "Got no data!"
            for r in self.allowed_runners():
                print "DBG", r.current_launch


    # Write all configuration we've got
    def write_config(self):
        # Store host to del in a separate array to remove them after look over items
        items_to_del = []
        still_duplicate_items = True
        managed_element = True
        while still_duplicate_items:
            # If we didn't work in the last loop, bail out
            if not managed_element:
                still_duplicate_items = False
            print "LOOP"
            managed_element = False
            for name in self.disco_data:
                if name in items_to_del:
                    continue
                managed_element = True
                print('Search same host to merge.')
                dha = self.disco_data[name]
                # Searching same host and update host macros
                for oname in self.disco_data:
                    dhb = self.disco_data[oname]
                    # When same host but different properties are detected
                    if dha.name == dhb.name and dha.properties != dhb.properties:
                        for (k, v) in dhb.properties.iteritems():
                            # Merge host macros if their properties are different
                            if k.startswith('_') and \
                                    k in dha.properties and dha.properties[k] != dhb.properties[k]:
                                dha.data[k] = dha.properties[k] + ',' + v
                                print('Merged host macro:', k, dha.properties[k])
                                items_to_del.append(oname)

                        print('Merged ' + oname + ' in ' + name)
                        dha.update_properties()
                    else:
                        still_duplicate_items = False

        # Removing merged element
        for item in items_to_del:
            print('Deleting ' + item)
            del self.disco_data[item]

        # New loop to reflect changes in self.disco_data since it isn't possible
        # to modify a dict object when reading it.
        for name in self.disco_data:
            print "Writing", name, "configuration"
            self.write_host_config(name)
            self.write_service_config(name)


    # We search for all rules of type host, and we merge them
    def write_host_config(self, host):
        dh = self.disco_data[host]

        d = dh.get_final_properties()
        final_host = dh.name

        print "Will generate a host", d
        # Maybe we do not got a directory output, but
        # a bdd one.
        if self.output_dir:
            self.write_host_config_to_file(final_host, d)

        # Maybe we want a database insert
        if self.db:
            self.write_host_config_to_db(final_host, d)

        if self.backend:
            self.backend.write_host_config_to_db(final_host, d)

    # Will wrote all properties/values of d for the host
    # in the file
    def write_host_config_to_file(self, host, d):
        p = os.path.join(self.output_dir, host)
        print "Want to create host path", p
        try:
            os.mkdir(p)
        except OSError, exp:
            # If directory already exist, it's not a problem
            if not exp.errno != '17':
                print "Cannot create the directory '%s' : '%s'" % (p, exp)
                return
        cfg_p = os.path.join(p, host + '.cfg')
        if os.path.exists(cfg_p) and not self.overwrite:
            print "The file '%s' already exists" % cfg_p
            return

        buf = self.get_cfg_bufer(d, 'host')

        # Ok, we create it so (or overwrite)
        try:
            fd = open(cfg_p, 'w')
            fd.write(buf)
            fd.close()
        except OSError, exp:
            print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
            return


    # Generate all service for a host
    def write_service_config(self, host):
        srv_rules = {}
        dh = self.disco_data[host]
        for r in dh.matched_rules:
            if r.creation_type == 'service':
                if 'service_description' in r.writing_properties:
                    desc = r.writing_properties['service_description']
                    if desc not in srv_rules:
                        srv_rules[desc] = []
                    srv_rules[desc].append(r)

        # print "Generate services for", host
        # print srv_rules
        for (desc, rules) in srv_rules.items():
            d = {'service_description': desc, 'host_name': host}
            for r in rules:
                d.update(r.writing_properties)
            print "Generating", desc, d

            # Maybe we do not got a directory output, but
            # a bdd one.
            if self.output_dir:
                self.write_service_config_to_file(host, desc, d)


    # Will wrote all properties/values of d for the host
    # in the file
    def write_service_config_to_file(self, host, desc, d):
        p = os.path.join(self.output_dir, host)

        # The host conf should already exist
        cfg_host_p = os.path.join(p, host + '.cfg')
        if not os.path.exists(cfg_host_p):
            print "No host configuration available, I bail out"
            return

        cfg_p = os.path.join(p, desc + '.cfg')
        if os.path.exists(cfg_p) and not self.overwrite:
            print "The file '%s' already exists" % cfg_p
            return

        buf = self.get_cfg_bufer(d, 'service')

        # Ok, we create it so (or overwrite)
        try:
            fd = open(cfg_p, 'w')
            fd.write(buf)
            fd.close()
        except OSError, exp:
            print "Cannot create the file '%s' : '%s'" % (cfg_p, exp)
            return


    # Create a define t { } with data in d
    def get_cfg_bufer(self, d, t):
        tab = ['define %s {' % t]
        for (key, value) in d.items():
            tab.append('  %s   %s' % (key, value))
        tab.append('}\n')
        return '\n'.join(tab)


    # Will wrote all properties/values of d for the host
    # in the database
    def write_host_config_to_db(self, host, d):
        table = None
        # Maybe we directly insert/enable the hosts,
        # or in the SkonfUI we want to go with an intermediate
        # table to select/enable only some
        if self.db_direct_insert:
            table = self.db.hosts
        else:
            table = self.db.discovered_hosts
        cur = table.find({'host_name': host})
        exists = cur.count() > 0
        if exists and not self.overwrite:
            print "The host '%s' already exists in the database table %s" % (host, table)
            return

        # It can be the same check if db_direct_insert but whatever
        if self.only_new_hosts:
            for t in [self.db.hosts, self.db.discovered_hosts]:
                r = table.find({'_id': host})
                if r.count() > 0:
                    print "This is not a new host on", self.db.hosts
                    return

        print "Saving in database", d
        d['_id'] = host
        d['_discovery_state'] = 'discovered'
        table.save(d)
        print "saved"
        del d['_id']
