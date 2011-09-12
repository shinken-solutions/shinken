#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

import sys
import os
import time
import traceback
import copy

from shinken.objects import Config
from shinken.daemon import Daemon
from shinken.log import logger
from shinken.webui.bottle import Bottle, run, static_file, view, route

# Debug
import shinken.webui.bottle as bottle
bottle.debug(True)

#Import bottle lib to make bottle happy
bottle_dir = os.path.abspath(os.path.dirname(bottle.__file__))
sys.path.insert(0, bottle_dir)


bottle.TEMPLATE_PATH.append(os.path.join(bottle_dir, 'views'))
bottle.TEMPLATE_PATH.append(bottle_dir)



# hello/bla will use the hello_template.tpl template
@route('/hello/:name')
@view('hello_template')
def hello(name='World'):
    return dict(name=name)


# Output json
@route('/bla')
def bla():
    return {1:2}



# Main WebUI Class
class Webui(Daemon):

    def __init__(self, config_files, is_daemon, do_replace, debug, debug_file):        
        super(Webui, self).__init__('webui', config_files[0], is_daemon, do_replace, debug, debug_file)
        
        self.config_files = config_files

        # Use to know if we must still be alive or not
        self.must_run = True
        
        self.conf = Config()

        self.plugins = []


    def load_config_file(self):
        print "Loading configuration"
        # REF: doc/shinken-conf-dispatching.png (1)
        buf = self.conf.read_config(self.config_files)
        raw_objects = self.conf.read_config_buf(buf)

        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')
        
        self.conf.early_arbiter_linking()

        ### Resume standard operations ###
        self.conf.create_objects(raw_objects)
        
        # Maybe conf is already invalid
        if not self.conf.conf_is_correct:
            sys.exit("***> One or more problems was encountered while processing the config files...")

        # Change Nagios2 names to Nagios3 ones
        self.conf.old_properties_names_to_new()

        # Create Template links
        self.conf.linkify_templates()

        # All inheritances
        self.conf.apply_inheritance()

        # Explode between types
        self.conf.explode()

        # Create Name reversed list for searching list
        self.conf.create_reversed_list()

        # Cleaning Twins objects
        self.conf.remove_twins()

        # Implicit inheritance for services
        self.conf.apply_implicit_inheritance()

        # Fill default values
        self.conf.fill_default()
        
        # Remove templates from config
        self.conf.remove_templates()
        
        # Pythonize values
        self.conf.pythonize()

        # Linkify objects each others
        self.conf.linkify()

        # applying dependancies
        self.conf.apply_dependancies()

        # Hacking some global parameter inherited from Nagios to create
        # on the fly some Broker modules like for status.dat parameters
        # or nagios.log one if there are no already available
        self.conf.hack_old_nagios_parameters()

        # Exlode global conf parameters into Classes
        self.conf.explode_global_conf()

        # set ourown timezone and propagate it to other satellites
        self.conf.propagate_timezone_option()

        # Look for business rules, and create teh dep trees
        self.conf.create_business_rules()
        # And link them
        self.conf.create_business_rules_dependencies()
        
        # Correct conf?
        self.conf.is_correct()

        # The conf can be incorrect here if the cut into parts see errors like
        # a realm with hosts and not schedulers for it
        if not self.conf.conf_is_correct:
            self.conf.show_errors()
            sys.exit("Configuration is incorrect, sorry, I bail out")

        logger.log('Things look okay - No serious problems were detected during the pre-flight check')

        # Now clean objects of temporary/unecessary attributes for live work:
        self.conf.clean()

        # Ok, here we must check if we go on or not.
        # TODO : check OK or not
        self.pidfile = os.path.abspath(self.conf.webui_lock_file)
        self.idontcareaboutsecurity = self.conf.idontcareaboutsecurity
        self.user = self.conf.shinken_user
        self.group = self.conf.shinken_group
        
        self.workdir = os.path.abspath(os.path.dirname(self.pidfile))

        self.port = int(self.conf.webui_port)
        self.host = self.conf.webui_host
        
        logger.log("Configuration Loaded")
        print ""


    # Main loop function
    def main(self):
        try:
            # Log will be broks
            for line in self.get_header():
                self.log.log(line)

            self.load_config_file()
            self.do_daemon_init_and_start()

            ## And go for the main loop
            self.do_mainloop()
        except SystemExit, exp:
            # With a 2.4 interpreter the sys.exit() in load_config_file
            # ends up here and must be handled.
            sys.exit(exp.code)
        except Exception, exp:
            logger.log("CRITICAL ERROR : I got an non recovarable error. I must exit")
            logger.log("You can log a bug ticket at https://sourceforge.net/apps/trac/shinken/newticket for geting help")
            logger.log("Back trace of it: %s" % (traceback.format_exc()))
            raise


    def setup_new_conf(self):
        """ Setup a new conf received from a Master arbiter. """
        conf = self.new_conf
        self.new_conf = None
        self.cur_conf = conf
        self.conf = conf        
        for arb in self.conf.arbiterlinks:
            if (arb.address, arb.port) == (self.host, self.port):
                self.me = arb
                arb.is_me = lambda: True  # we now definitively know who we are, just keep it.
            else:
                arb.is_me = lambda: False # and we know who we are not, just keep it.


    def do_loop_turn(self):
        if self.must_run:
            # Main loop
            self.run()



    # Main function
    def run(self):
        # Now is fun : get all the fun running :)
        my_dir = os.path.abspath(os.path.dirname(__file__))

        # Got in my own dir, and add my path in sys.path
        os.chdir(bottle_dir)
        #os.chdir(my_dir)
        sys.path.append(my_dir)

        # Check if the view dir really exist
        if not os.path.exists(bottle.TEMPLATE_PATH[0]):
            logger.log('ERROR : the view path do not exist at %s' % bottle.TEMPLATE_PATH)
            sys.exit(2)

        self.load_plugins()

        # Declare the whole app static files AFTER the plugin ones
        self.declare_common_static()

        print "Starting application"
        run(host=self.host, port=self.port)



    def load_plugins(self):
        from shinken.webui import plugins
        plugin_dir = os.path.abspath(os.path.dirname(plugins.__file__))
        print "Loading plugin directory : %s" % plugin_dir
        
        # Load plugin directories
        plugin_dirs = [ fname for fname in os.listdir(plugin_dir)
                        if os.path.isdir(os.path.join(plugin_dir, fname)) ]

        print "Plugin dirs", plugin_dirs
        sys.path.append(plugin_dir)
        # We try to import them, but we keep only the one of
        # our type
        for fdir in plugin_dirs:
            print "Try to load", fdir
            mod_path = 'shinken.webui.plugins.%s.%s' % (fdir, fdir)
            try:
                m = __import__(mod_path, fromlist=[mod_path])
                m_dir = os.path.abspath(os.path.dirname(m.__file__))
                sys.path.append(m_dir)

                print "Loaded module m", m
                print m.__file__
                pages = m.pages
                print "Try to load pages", pages
                for (f, entry) in pages.items():
                    routes = entry.get('routes', None)
                    v = entry.get('view', None)
                    static = entry.get('static', False)

                    # IMPORTANT : apply VIEW BEFORE route!
                    if v:
                        print "Link function", f, "and view", v
                        f = view(v)(f)

                    # Maybe there is no route to link, so pass
                    if routes:
                        for r in routes:
                            print "link function", f, "and route", r
                            f = route(r, callback=f)
                        
                    # Ifthe plugin declare a static entry, register it
                    if static:
                        self.add_static(fdir, m_dir)
                        #static_route = '/static/'+fdir+'/:path#.+#'
                        #print "Declaring static entry", static_route, lamb
                        #f = route(static_route, callback=lamb)
                        #def plugin_static(path):
                        #    print "Addr f", plugin_static, plugin_static.entry
                        #    m_dir = plugin_static.m_dir
                        #    print "Get a plugin static file %s from" % path, os.path.join(m_dir, 'htdocs')
                        #    return static_file(path, root=os.path.join(m_dir, 'htdocs'))
                        #g = copy.deepcopy(plugin_static)
                        #print "Addr plugin_static", plugin_static, g, static_route
                        #g.m_dir = m_dir
                        #g.entry = static_route
                        #route(static_route, callback=g)


                # And we add the views dir of this plugin in our TEMPLATE
                # PATH
                bottle.TEMPLATE_PATH.append(os.path.join(m_dir, 'views'))

                # And finally register me so the pages can get data and other
                # useful stuff
                m.app = self
                        
                        
            except Exception, exp:
                logger.log("Warning in loading plugins : %s" % exp)


    def add_static(self, fdir, m_dir):
        static_route = '/static/'+fdir+'/:path#.+#'
        #print "Declaring static entry", static_route, lamb
        #f = route(static_route, callback=lamb)
        def plugin_static(path):
            #print "Addr f", plugin_static, plugin_static.entry
            return static_file(path, root=os.path.join(m_dir, 'htdocs'))
        route(static_route, callback=plugin_static)




    def declare_common_static(self):
        # Route static files css files
        @route('/static/:path#.+#')
        def server_static(path):
            #print "Getting static files from", os.path.join(my_dir, 'htdocs'), path
            return static_file(path, root=os.path.join(bottle_dir, 'htdocs'))




###Old things that can be used in the future :)

    # Helper functions for retention modules
    # So we give our broks and external commands
    def get_retention_data(self):
        r = {}
        r['broks'] = self.broks
        r['external_commands'] = self.external_commands
        return r

    # Get back our data from a retention module
    def restore_retention_data(self, data):
        broks = data['broks']
        external_commands = data['external_commands']
        self.broks.update(broks)
        self.external_commands.extend(external_commands)

