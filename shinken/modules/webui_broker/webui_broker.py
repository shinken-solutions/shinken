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


"""
This Class is a plugin for the Shinken Broker. It is in charge
to get brok and recreate real objects, and propose a Web intnerface :)
"""

import traceback
import sys
import os
import time
import traceback
import select
import threading
import base64
import cPickle

from shinken.basemodule import BaseModule
from shinken.message import Message
from shinken.webui.bottle import Bottle, run, static_file, view, route, request, response
from shinken.misc.regenerator import Regenerator
from shinken.log import logger
from shinken.modulesmanager import ModulesManager
from shinken.daemon import Daemon
from shinken.util import safe_print, to_bool

#Local import
from shinken.misc.datamanager import datamgr
from helper import helper

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
class Webui_broker(BaseModule, Daemon):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)

        self.plugins = []

        self.port = int(getattr(modconf, 'port', '7767'))
        self.host = getattr(modconf, 'host', '0.0.0.0')
        self.auth_secret = getattr(modconf, 'auth_secret').encode('utf8', 'replace')
        self.http_backend = getattr(modconf, 'http_backend', 'auto')
        self.login_text = getattr(modconf, 'login_text', None)
        self.allow_html_output = to_bool(getattr(modconf, 'allow_html_output', '0'))
        self.remote_user_enable = getattr(modconf, 'remote_user_enable', '0')
        self.remote_user_variable = getattr(modconf, 'remote_user_variable', 'X_REMOTE_USER')

        # Load the photo dir and make it a absolute path
        self.photo_dir = getattr(modconf, 'photo_dir', 'photos')
        self.photo_dir = os.path.abspath(self.photo_dir)
        print "Webui : using the backend", self.http_backend



        

    # We check if the photo directory exists. If not, try to create it
    def check_photo_dir(self):
        print "Checking photo path", self.photo_dir
        if not os.path.exists(self.photo_dir):
            print "Truing to create photo dir", self.photo_dir
            try:
                os.mkdir(self.photo_dir)
            except Exception, exp:
                print "Photo dir creation failed", exp
                
        

    # Called by Broker so we can do init stuff
    # TODO : add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        print "Init of the Webui '%s'" % self.name





    def main(self):
        self.log = logger
        self.log.load_obj(self)
        
        # Daemon like init
        self.debug_output = []

        self.modules_manager = ModulesManager('webui', self.find_modules_path(), [])
        self.modules_manager.set_modules(self.modules)
        # We can now output some previouly silented debug ouput
        self.do_load_modules()
        for inst in self.modules_manager.instances:
            f = getattr(inst, 'load', None)
            if f and callable(f):
                f(self)
                
        
        for s in self.debug_output:
            print s
        del self.debug_output

        self.check_photo_dir()
        self.rg = Regenerator()
        self.datamgr = datamgr
        datamgr.load(self.rg)
        self.helper = helper

        self.request = request
        self.response = response
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


    # A plugin send us en external command. We just put it
    # in the good queue
    def push_external_command(self, e):
        print "WebUI: got an external command", e.__dict__
        self.from_q.put(e)
        

    # Real main function
    def do_main(self):
        #I register my exit function
        self.set_exit_handler()
        print "Go run"

        # We ill protect the operations on
        # the non read+write with a lock and
        # 2 int
        self.global_lock = threading.RLock()
        self.nb_readers = 0
        self.nb_writers = 0

        
        self.data_thread = None

        # Check if the view dir really exist
        if not os.path.exists(bottle.TEMPLATE_PATH[0]):
            logger.log('ERROR : the view path do not exist at %s' % bottle.TEMPLATE_PATH)
            sys.exit(2)

        self.load_plugins()

        # Declare the whole app static files AFTER the plugin ones
        self.declare_common_static()
        
        
        

        # Launch the data thread"
        self.data_thread = threading.Thread(None, self.manage_brok_thread, 'datathread')
        self.data_thread.start()
        # TODO : look for alive and killing

        # Ok, you want to know why we are using a data thread instead of
        # just call for a select with q._reader, the underliying file 
        # handle of the Queue()? That's just because under Windows, select
        # only manage winsock (so network) file descriptor! What a shame!
        print "Starting WebUI application"
        srv = run(host=self.host, port=self.port, server=self.http_backend)

        # ^ IMPORTANT ^
        # We are not managing the lock at this
        # level because we got 2 types of requests:
        # static images/css/js : no need for lock
        # pages : need it. So it's managed at a
        # function wrapper at loading pass


                    
    # It's the thread function that will get broks
    # and update data. Will lock the whole thing
    # while updating
    def manage_brok_thread(self):
        print "Data thread started"
        while True:
           l = self.to_q.get()
           
           for b in l:
              # For updating, we cannot do it while
              # answer queries, so wait for no readers
              self.wait_for_no_readers()
              try:
               #print "Got data lock, manage brok"
                  self.rg.manage_brok(b)
                  for mod in self.modules_manager.get_internal_instances():
                      try:
                          mod.manage_brok(b)
                      except Exception , exp:
                          print exp.__dict__
                          logger.log("[%s] Warning : The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(),str(exp)))
                          logger.log("[%s] Exception type : %s" % (self.name, type(exp)))
                          logger.log("Back trace of this kill: %s" % (traceback.format_exc()))
                          self.modules_manager.set_to_restart(mod)
              except Exception, exp:            
                  msg = Message(id=0, type='ICrash', data={'name' : self.get_name(), 'exception' : exp, 'trace' : traceback.format_exc()})
                  self.from_q.put(msg)
                  # wait 2 sec so we know that the broker got our message, and die
                  time.sleep(2)
                  # No need to raise here, we are in a thread, exit!
                  os._exit(2)
              finally:
                  # We can remove us as a writer from now. It's NOT an atomic operation
                  # so we REALLY not need a lock here (yes, I try without and I got
                  # a not so accurate value there....)
                  self.global_lock.acquire()
                  self.nb_writers -= 1
                  self.global_lock.release()


    # Here we will load all plugins (pages) under the webui/plugins
    # directory. Each one can have a page, views and htdocs dir that we must
    # route correctly
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
                            method = entry.get('method', 'GET')
                            print "link function", f, "and route", r, "method", method
                            
                            # Ok, we will just use the lock for all
                            # plugin page, but not for static objects
                            # so we set the lock at the function level.
                            lock_version = self.lockable_function(f)
                            f = route(r, callback=lock_version, method=method)
                            
                    # If the plugin declare a static entry, register it
                    # and remeber : really static! because there is no lock
                    # for them!
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
        print "Declaring static route", static_route
        def plugin_static(path):
            print "Ask %s and give %s" % (path, os.path.join(m_dir, 'htdocs'))
            return static_file(path, root=os.path.join(m_dir, 'htdocs'))
        route(static_route, callback=plugin_static)


    # It will say if we can launch a page rendering or not.
    # We can only if there is no writer running from now
    def wait_for_no_writers(self):
        can_run = False
        while True:
            self.global_lock.acquire()
            # We will be able to run
            if self.nb_writers == 0:
                # Ok, we can run, register us as readers
                self.nb_readers += 1
                self.global_lock.release()
                break
            # Oups, a writer is in progress. We must wait a bit
            self.global_lock.release()
            # Before checking again, we should wait a bit
            # like 1ms
            time.sleep(0.001)


    # It will say if we can launch a brok management or not
    # We can only if there is no readers running from now
    def wait_for_no_readers(self):
        start = time.time()
        while True:
            self.global_lock.acquire()
            # We will be able to run
            if self.nb_readers == 0:
                # Ok, we can run, register us as writers
                self.nb_writers += 1
                self.global_lock.release()
                break
            # Ok, we cannot run now, wait a bit
            self.global_lock.release()
            # Before checking again, we should wait a bit
            # like 1ms
            time.sleep(0.001)
            # We should warn if we cannot update broks
            # for more than 30s because it can be not good
            if time.time() - start > 30:
                print "WARNING: we are in lock/read since more than 30s!"
                start = time.time()

        

    # We want a lock manager version of the plugin fucntions
    def lockable_function(self, f):
        print "We create a lock verion of", f
        def lock_version(**args):
            self.wait_for_no_writers()
            t = time.time()
            try:
                return f(**args)
            finally:
                print "rendered in", time.time() - t
                # We can remove us as a reader from now. It's NOT an atomic operation
                # so we REALLY not need a lock here (yes, I try without and I got
                # a not so accurate value there....)
                self.global_lock.acquire()
                self.nb_readers -= 1
                self.global_lock.release()
        print "The lock version is", lock_version
        return lock_version


    def declare_common_static(self):
        @route('/static/photos/:path#.+#')
        def give_photo(path):
            # If the file really exist, give it. If not, give a dummy image.
            if os.path.exists(os.path.join(self.photo_dir, path+'.jpg')):
                return static_file(path+'.jpg', root=self.photo_dir)
            else:
                return static_file('images/user.png', root=os.path.join(bottle_dir, 'htdocs'))

        # Route static files css files
        @route('/static/:path#.+#')
        def server_static(path):
            return static_file(path, root=os.path.join(bottle_dir, 'htdocs'))

        # And add the favicon ico too
        @route('/favicon.ico')
        def give_favicon():
            return static_file('favicon.ico', root=os.path.join(bottle_dir, 'htdocs', 'images'))





    def check_auth(self, user, password):
        print "Checking auth of", user #, password
        c = self.datamgr.get_contact(user)
        print "Got", c
        if not c:
            print "Warning: You need to have a contact having the same name as your user %s" % user
        
        # TODO : do not forgot the False when release!
        is_ok = False#(c is not None)#False
        
        for mod in self.modules_manager.get_internal_instances():
            try:
                f = getattr(mod, 'check_auth', None)
                print "Get check_auth", f, "from", mod.get_name()
                if f and callable(f):
                    r = f(user, password)
                    if r:
                        is_ok = True
                        # No need for other modules
                        break
            except Exception , exp:
                print exp.__dict__
                logger.log("[%s] Warning : The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(),str(exp)))
                logger.log("[%s] Exception type : %s" % (self.name, type(exp)))
                logger.log("Back trace of this kill: %s" % (traceback.format_exc()))
                self.modules_manager.set_to_restart(mod)        

        # Ok if we got a real contact, and if a module auth it
        return (is_ok and c is not None)

        

    def get_user_auth(self):
        # First we look for the user sid
        # so we bail out if it's a false one
        user_name = self.request.get_cookie("user", secret=self.auth_secret)

        # If we cannot check the cookie, bailout
        if not user_name:
            return None

        c = self.datamgr.get_contact(user_name)
        return c



    # Try to got for an element the graphs uris from modules
    def get_graph_uris(self, elt, graphstart, graphend):
        safe_print("Checking graph uris ", elt.get_full_name())

        uris = []
        for mod in self.modules_manager.get_internal_instances():
            try:
                f = getattr(mod, 'get_graph_uris', None)
                safe_print("Get graph uris ", f, "from", mod.get_name())
                if f and callable(f):
                    r = f(elt, graphstart, graphend)
                    uris.extend(r)
            except Exception , exp:
                print exp.__dict__
                logger.log("[%s] Warning : The mod %s raise an exception: %s, I'm tagging it to restart later" % (self.name, mod.get_name(),str(exp)))
                logger.log("[%s] Exception type : %s" % (self.name, type(exp)))
                logger.log("Back trace of this kill: %s" % (traceback.format_exc()))
                self.modules_manager.set_to_restart(mod)        

        safe_print("Will return", uris)
        # Ok if we got a real contact, and if a module auth it
        return uris
