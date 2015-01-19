#!/usr/bin/env python
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
This program get hosts informations from running arbiter daemon and 
get service dependencies definition from config pack flat files then
dump services dependencies according to the config files to a json
that can be loaded in hot_dependencies_arbiter module.

servicedependencies file in pack use template host_name that will be
matched in hosts 'use' directive to apply those servicedependency
definition to hosts.

"""


from shinken.objects.arbiterlink import ArbiterLink
import os, sys, optparse, cPickle, shutil
import shinken.daemons.arbiterdaemon
from shinken.arbiterlink import ArbiterLink
from shinken.http_client import HTTPExceptions 
from shinken.log import logger
from shinken.objects.config import Config

# Try to load json (2.5 and higer) or simplejson if failed (python2.4)
try:
    import json
except ImportError:
    # For old Python version, load simple json
    try:
        import simplejson as json
    except ImportError:
        raise SystemExit("Error: you need the json or simplejson module "
                         "for this script")


sat_types = ['arbiter', 'scheduler', 'poller', 'reactionner',
             'receiver', 'broker']

VERSION = '0.2'

class ShinkenAdmin():

    def __init__(self):
        self.arb = None 
        self.conf = None
        self.addr = 'localhost'
        self.port = '7770'
        self.arb_name = 'arbiter-master'

    def do_connect(self, verbose=False):
        '''
        Connect to an arbiter daemon
        Syntax: connect [host]:[port]
        Ex: for Connecting to server, port 7770
        > connect server:7770
        Ex: connect to localhost, port 7770
        > connect
        '''
    
        if verbose:
            print "Connection to %s:%s" % (self.addr, self.port)
        ArbiterLink.use_ssl = False
        self.arb = ArbiterLink({'arbiter_name': self.arb_name, 'address': self.addr, 'port': self.port})
        self.arb.fill_default()
        self.arb.pythonize()
        self.arb.update_infos()
        if not self.arb.reachable:
            sys.exit("Connection to the arbiter got a problem")
        print "Connection OK"
    
    def getconf(self, config):
        '''
        Get the data in the arbiter for a table and some properties
        like hosts  host_name realm
        '''
        files = [config]
        conf = Config()
        conf.read_config_silent = 1

        # Get hosts objects
        properties = [ 'host_name','use','act_depend_of']
        hosts = self.arb.get_objects_properties('hosts', properties)

        # Get services dependencies
        svcdep_buf = conf.read_config(files)
        svc_dep = conf.read_config_buf(svcdep_buf)['servicedependency']

        return (hosts, svc_dep)

    def load_svc_mapping(self, hosts, svc_dep, verbose=False):
        '''
        Make tuples mapping service dependencies. Return a list of tuples 
        and need hosts and service dependencies parameter.
        '''
        r = []
        # Search for host matching "use" template
        for dep in svc_dep:
            # Get host_name and dependent_host_name field from servicedependency
            # config file in packs. Usually values are host's pack template.
            parent_host_name = self.split_and_merge(dep['host_name'])
            try:
                dependent_host_name = self.split_and_merge(dep['dependent_host_name'])
            except KeyError:
                dependent_host_name = parent_host_name
            if verbose:
                print ""
                print 'Service dependency host_name', parent_host_name
                print 'Service dependency dependent_host_name', dependent_host_name

            # Make list before process them by splitting comma separated values.
            dep['service_description'] = self.split_and_merge(dep['service_description'])
            dep['dependent_service_description'] = self.split_and_merge(dep['dependent_service_description'])
            # Construct dependencies tuples
            # Search in host all hosts that use template host_name
            parent_svc_tuples = []
            dependent_svc_tuples = []
            for parent_svc in dep['service_description']:
                parent_svc_tuples += [[ ('service', host[0] + "," + parent_svc) for host in hosts if host_name in host[1] ] for host_name in parent_host_name ]
            for dependent_svc in dep['dependent_service_description']:
                dependent_svc_tuples += [[ ('service', host[0] + "," + dependent_svc) for host in hosts if host_name in host[1] ] for host_name in dependent_host_name ]

            # No need to separate tuples by services here so we merge them
            dependent_tuples = self.split_and_merge(dependent_svc_tuples, split=False)

            if verbose:
                print 'Parent service dependencies tuples list', parent_svc_tuples
                print 'Dependent service dependencies tuples list', dependent_svc_tuples

            # Process !
            for parent_tuples in parent_svc_tuples:
                r.append(self.make_all_dep_tuples(hosts, parent_tuples, dependent_tuples))

        if verbose:
            print ""
            print "Result:", r
        return r

    def make_all_dep_tuples(self, hosts, parent_tuples=[()], dependent_tuples=[[()]] ):
        '''
        List imbrication : List_by_services : [ List_by_hosts : [ Service_dependency_tuples : ( ) ] ]
        '''
        res = []
        for ptuple in parent_tuples:
            parent = { 'host_name' : self.get_dependency_tuple_host_name(ptuple), 'svc_desc' : self.get_dependency_tuple_service_description(ptuple) }
            # Dive into dependent services
            for dtuple in dependent_tuples:
                dependent = { 'host_name' : self.get_dependency_tuple_host_name(dtuple), 'svc_desc' : self.get_dependency_tuple_service_description(dtuple) }
                dependent['host_object'] = next( host for host in hosts if host[0] == dependent['host_name'] )
                res = self.make_dep_tuple(parent, dependent, ptuple, dtuple, res)

        return res

    def make_dep_tuple(self, parent, dependent, ptuple, dtuple, res):
        '''
        Search host dependency and make tuple according to it.
        '''
        try:
            dependent_host_parent = self.get_host_dependency(dependent['host_object'])
            if parent['host_name'] == dependent_host_parent:
                res = (ptuple, dtuple)
        except IndexError:
            if parent['host_name'] == dependent['host_name']:
                res = (ptuple, dtuple)

        return res

    def get_host_dependency(self, dependent_host):
        '''
        Get parent host_name attribute of host.
        '''
        return dependent_host[2][0][0].host_name

    def get_dependency_tuple_host_name(self, tuple):
        '''
        Just get the host name part of a dependency tuple.
        A dependency tuples is : ( 'service', 'host_name, service_description' )
        '''
        return tuple[1].split(',')[0]

    def get_dependency_tuple_service_description(self, tuple):
        '''
        Just get the service description part of a dependency tuple.
        A dependency tuples is : ( 'service', 'host_name, service_description' )
        '''
        return tuple[1].split(',')[1]


    def split_and_merge(self, list, split=True):
        '''
        Split a list on comma separator and merge resulting lists
        into an uniq list then return it
        '''
        res = []
        for elt in list:
            if split:
                res += elt.split(',')
            else:
                res += elt
        return res

    def clean_empty_value(self, r):
        '''
        Empty value comes from unused config pack and then service dep
        is created but without nothing...
        '''
        r_cleaned = []
        for elt in r:
            if elt != []:
                r_cleaned.append(elt)

        return r_cleaned

    def main(self, output_file, config, verbose):
        self.do_connect(verbose)

        # Get needed conf
        hosts, svc_dep = self.getconf(config)
        if verbose:
            print "Hosts:", hosts
            print "Service Dep:", svc_dep

        # Make the map
        r = self.load_svc_mapping(hosts, svc_dep, verbose)

        # Clean mapping from empty value
        r = self.clean_empty_value(r)

        # Write ouput file
        try:
            f = open(output_file + '.tmp', 'wb')
            buf = json.dumps(r)
            f.write(buf)
            f.close()
            shutil.move(output_file + '.tmp', output_file)
            print "File %s wrote" % output_file
        except IOError, exp:
            sys.exit("Error writing the file %s: %s" % (output_file, exp))
        jsonmappingfile = open(output_file, 'w')
        try:
            json.dump(r, jsonmappingfile)
        finally:
            jsonmappingfile.close()


if __name__ == "__main__":
    parser = optparse.OptionParser(
        version="Shinken service hot dependency according to packs (or custom) definition to json mapping %s" % VERSION)
    parser.add_option("-o", "--output", dest='output_file',
                      default='/tmp/shinken_service_dependency:mapping.json',
                      help="Path of the generated json mapping file.")
    parser.add_option('-c', '--config', dest='config', help='Shinken main config file.')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', help='More verbosity. Used to debug')

    opts, args = parser.parse_args()
    if args:
        parser.error("does not take any positional arguments")

    ShinkenAdmin().main(**vars(opts))
