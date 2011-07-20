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


#This Class is a plugin for the Shinken Broker. It is in charge
#to brok information of the service perfdata into the file
#var/service-perfdata
#So it just manage the service_check_return
#Maybe one day host data will be usefull too
#It will need just a new file, and a new manager :)

import traceback
import sys
import os
import time
import traceback

from shinken.basemodule import BaseModule
from shinken.webui.bottle import Bottle, run, static_file, view, route

# Debug
import shinken.webui.bottle as bottle
bottle.debug(True)

#Import bottle lib to make bottle happy
bottle_dir = os.path.abspath(os.path.dirname(bottle.__file__))
sys.path.insert(0, bottle_dir)


bottle.TEMPLATE_PATH.append(os.path.join(bottle_dir, 'views'))
bottle.TEMPLATE_PATH.append(bottle_dir)



#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Webui_broker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)

        self.plugins = []

        self.port = 8080
        self.host = '0.0.0.0'



    # Called by Broker so we can do init stuff
    # TODO : add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        print "Init of the Webui '%s'" % self.name



    def main(self):
        try:
            #import cProfile
            #cProfile.runctx('''self.do_main()''', globals(), locals(),'/tmp/livestatus.profile')
            self.do_main()
        except Exception, exp:            
            msg = Message(id=0, type='ICrash', data={'name' : self.get_name(), 'exception' : exp, 'trace' : traceback.format_exc()})
            self.from_q.put(msg)
            # wait 2 sec so we know that the broker got our message, and die
            time.sleep(2)
            raise


    # Real main function
    def do_main(self):
        #I register my exit function
        self.set_exit_handler()
        print "Go run"

        # Check if the view dir really exist
        if not os.path.exists(bottle.TEMPLATE_PATH[0]):
            logger.log('ERROR : the view path do not exist at %s' % bottle.TEMPLATE_PATH)
            sys.exit(2)

        self.load_plugins()

        # Declare the whole app static files AFTER the plugin ones
        self.declare_common_static()
        
        print "Starting WebUI application"
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
                print "Try to laod pages", pages
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
        def plugin_static(path):
            return static_file(path, root=os.path.join(m_dir, 'htdocs'))
        route(static_route, callback=plugin_static)



    def declare_common_static(self):
        # Route static files css files
        @route('/static/:path#.+#')
        def server_static(path):
            return static_file(path, root=os.path.join(bottle_dir, 'htdocs'))

