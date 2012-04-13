# Copyright (C) 2009-2012 :
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
import cPickle
import os
import re
import time

try:
    from pymongo.connection import Connection
except ImportError:
    Connection = None

from shinken.log import logger
from shinken.objects import *
from shinken.macroresolver import MacroResolver


class DiscoveryManager:
    def __init__(self, path, macros, overwrite, runners, output_dir=None, dbmod='', db_direct_insert=False):
        # i am arbiter-like
        self.log = logger
        self.overwrite = overwrite
        self.runners = runners
        self.output_dir = output_dir
        self.dbmod = dbmod
        self.db_direct_insert = db_direct_insert
        self.log.load_obj(self)
        self.config_files = [path]
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
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.remove_templates()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependencies()
        self.conf.is_correct()

        self.discoveryrules = self.conf.discoveryrules
        self.discoveryruns = self.conf.discoveryruns
        
        m = MacroResolver()
        m.init(self.conf)
        
        # Hash = name, and in it (key, value)
        self.disco_data = {}
        # Hash = name, and in it rules that apply
        self.disco_matches = {}

        self.init_database()


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
                    print "ERROR : cannot use Mongodb database : please install the pymongo librairy"
                    break
                # Now try to connect
                try:
                    uri = mod.uri
                    database = mod.database
                    self.dbconnection = Connection(uri)
                    self.db = getattr(self.dbconnection, database)
                    print "Connection to Mongodb:%s:%s is OK" % (uri, database)
                except Exception, exp:
                    logger.log('Error in database init : %s' % exp)

    # Look if the name is a IPV4 address or not
    def is_ipv4_addr(self, name):
        p = r"^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$"
        return (re.match(p, name) is not None)


    def read_disco_buf(self):
        buf = self.raw_disco_data
        for l in buf.split('\n'):
            #print ""
            # If it's not a disco line, bypass it
            if not re.search('::', l):
                continue
            #print "line", l
            elts = l.split('::')
            if len(elts) <= 1:
                #print "Bad discovery data"
                continue
            name = elts[0].strip()

            # We can choose to keep only the basename
            # of the nameid, so strip the fqdn
            # But not if it's a plain ipv4 addr
            if self.conf.strip_idname_fqdn:
                if not self.is_ipv4_addr(name):
                    name = name.split('.', 1)[0]
            
            data = '::'.join(elts[1:])
            
            # Register the name
            if not name in self.disco_data:
                self.disco_data[name] = {}

            # Now get key,values
            if not '=' in data:
                continue

            elts = data.split('=')
            if len(elts) <= 1:
                continue

            key = elts[0].strip()
            value = elts[1].strip()
            print "-->", name, key, value
            self.disco_data[name][key] = value


    def match_rules(self):
        for name in self.disco_data:
            datas = self.disco_data[name]
            for r in self.discoveryrules:
                if r.is_matching_disco_datas(datas):
                    if name not in self.disco_matches:
                        self.disco_matches[name] = []
                    self.disco_matches[name].append(r)
                    print "Generating", name, r.writing_properties


    def is_allowing_runners(self, name):
        name = name.strip()

        # If we got no value, it's * by default
        if '*' in self.runners:
            return True

        #print self.runners
        #If we match the name, ok
        for r in self.runners:
            r_name = r.strip()
            #            print "Look", r_name, name
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
            print "I'm launching", r.get_name(), "with a %d seconds timeout" % self.conf.runners_timeout
            r.launch(timeout=self.conf.runners_timeout)


    def wait_for_runners_ends(self):
        all_ok = False
        while not all_ok:
            all_ok = True
            for r in self.allowed_runners():
                if not r.is_finished():
                    #print "Check finished of", r.get_name()
                    r.check_finished()
                b = r.is_finished()
                if not b:
                    #print r.get_name(), "is not finished"
                    all_ok = False
            time.sleep(0.1)


    def get_runners_outputs(self):
        for r in self.allowed_runners():
            if r.is_finished():
                print r.discoveryrun_name, r.current_launch
                if r.current_launch.exit_status != 0:
                    print "Error on run"
        self.raw_disco_data = '\n'.join(r.get_output() for r in self.allowed_runners() if r.is_finished())
        if len(self.raw_disco_data) != 0:
            print "Got Raw disco data", self.raw_disco_data
        else:
            print "Got no data!"
            for r in self.allowed_runners():
                print "DBG", r.current_launch


    # Write all configuration we've got
    def write_config(self):
        for name in self.disco_data:
            print "Writing", name, "configuration"
            self.write_host_config(name)
            self.write_service_config(name)


    # We search for all rules of type host, and we merge them
    def write_host_config(self, host):
        host_rules = []
        for (name, rules) in self.disco_matches.items():
            if name != host:
                continue
            rs = [r for r in rules if r.creation_type == 'host']
            host_rules.extend(rs)

        # If no rule, bail out
        if len(host_rules) == 0:
            return
    
        # now merge them
        d = {'host_name' : host}
        for r in host_rules:
            for k,v in r.writing_properties.iteritems():
                # If it's a + (add) property, add with a ,
                if k.startswith('+'):
                    prop = k[1:]
                    # If the d do not already have this prop,
                    # just push it
                    if not prop in d:
                        d[prop] = v
                    # oh, must add with a , so
                    else:
                        d[prop] = d[prop] + ',' + v
                else:
                    d[k] = v
        print "Will generate an host", d
        
        # Maybe we do not got a directory output, but
        # a bdd one.
        if self.output_dir:
            self.write_host_config_to_file(host, d)

        # Maybe we want a database insert
        if self.db:
            self.write_host_config_to_db(host, d)
            
        
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
        cfg_p = os.path.join(p, host+'.cfg')
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
        for (name, rules) in self.disco_matches.items():
            if name != host:
                continue
            rs = [r for r in rules if r.creation_type == 'service']
            print "RS", rs
            for r in rs:
                if 'service_description' in r.writing_properties:
                    desc = r.writing_properties['service_description']
                    if not desc in srv_rules:
                        srv_rules[desc] = []
                    srv_rules[desc].append(r)

        #print "Generate services for", host
        #print srv_rules
        for (desc, rules) in srv_rules.items():
            d = {'service_description' : desc, 'host_name' : host}
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
        cfg_host_p = os.path.join(p, host+'.cfg')
        if not os.path.exists(cfg_host_p):
            print "No host configuration available, I bail out"
            return

        cfg_p = os.path.join(p, desc+'.cfg')
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

        print "Saving in database", d
        d['_id'] = host
        table.save(d)
        print "saved"
        del d['_id']
