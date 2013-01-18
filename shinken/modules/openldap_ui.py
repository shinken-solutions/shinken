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


"""
This class is for linking the WebUI with OpenLDAP directory service,
like check passwords, or get photos.
"""

import ldap
import os

from shinken.log import logger
from shinken.basemodule import BaseModule

properties = {
    'daemons' : ['webui'],
    'type' : 'openldap_webui'
    }

#called by the plugin manager
def get_instance(plugin):
    print "Get an OpenLDAP UI module for plugin %s" % plugin.get_name()
    
    instance = OpenLDAP_Webui(plugin)
    return instance


class OpenLDAP_Webui(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.ldap_uri = getattr(modconf, 'ldap_uri', None)
        self.username = getattr(modconf, 'username', '')
        self.password = getattr(modconf, 'password', '')
        self.basedn = getattr(modconf, 'basedn', '')
        # If we got no uri, we bailout...
        if not self.ldap_uri:
            self.active = False
        else:
            self.active = True
        self.con = None

    # Try to connect if we got true parameter
    def init(self):
        if not self.active:
            return
#        self.connect()


    def connect(self):
        print "Trying to initialize the Ldap connection"
        self.con = ldap.initialize(self.ldap_uri)
        self.con.set_option(ldap.OPT_REFERRALS,0)

        print "Trying to connect to Ldap", self.ldap_uri, self.username, self.password, self.basedn
        # Any errors will throw an ldap.LDAPError exception
        # or related exception so you can ignore the result
        self.con.simple_bind_s(self.username, self.password)
        print "Ldap Connection done"
        

    def disconnect(self):
        self.con = None


    # To load the webui application
    def load(self, app):
        self.app = app


    # Give the entry for a contact
    def find_contact_entry(self, contact):
        if not self.active:
            return None

        if not contact:
            return None

        # First we try to connect, because there is no "KEEP ALIVE" option
        # available, so we will get a drop after one day...
        self.connect()
        
        print "LDAP : search for contact", contact.get_name()
        searchScope = ldap.SCOPE_SUBTREE
        ## retrieve all attributes
        retrieveAttributes = ["cn", "jpegphoto", "uid", "mail"]

        cname = contact.get_name()
        email = contact.email
        searchFilter = "(| (uid=%s)(mail=%s))" % (cname, email)
        print "Filter", searchFilter
        try:
            ldap_result_id = self.con.search(self.basedn, searchScope, searchFilter, retrieveAttributes)
            result_set = []
            while 1:
                result_type, result_data = self.con.result(ldap_result_id, 0)
                if (result_data == []):
                    print "No result for", cname
                    return None

                if result_type == ldap.RES_SEARCH_ENTRY:
                    (_, elts) = result_data[0]
		    #print "Search for user"
		    #elts['dn'] =  str(result_data[0][0])
                    try :
                        account_name = elts['uid'][0]
                    except Exception:
                        account_name = str(result_data[0])
                    # Got a result, try to get photo to write file
                    print "Find account uid", account_name
                    return elts
        except ldap.LDAPError, e:
            print "Ldap error", e, e.__dict__
            return None
        # Always clean on exit
        finally:
            self.disconnect()
    

    # One of our goal is to look for contacts and get all pictures
    def manage_initial_broks_done_brok(self, b):
        if self.con is None:
            return
        print "LDAP : manage_initial_broks_done_brok, go for pictures"

        searchScope = ldap.SCOPE_SUBTREE
        ## retrieve all attributes - again adjust to your needs - see documentation for more options
        retrieveAttributes = ["cn", "jpegphoto", "uid", "mail"]

        print "Contacts?", len(self.app.datamgr.get_contacts())

        for c in self.app.datamgr.get_contacts():
            print "Doing photo lookup for contact", c.get_name()
            elts = self.find_contact_entry(c)

            if elts is None:
                print "No ldap entry for", c.get_name()
                continue

            # Ok, try to get photo from the entry
            try:
                photo = elts['jpegPhoto'][0]
                try:
                    p = os.path.join(self.app.photo_dir, c.get_name()+'.jpg')
                    f = open(p, 'wb')
                    f.write(photo)
                    f.close()
                    print "Photo wrote for", c.get_name()
                except Exception, exp:
                    print "Cannot write", p, ":", exp
            except KeyError:
                print "No photo for", c.get_name()



    # Try to auth a user in the ldap dir
    def check_auth(self, user, password):
        # If we do not have an ldap uri, no auth :)
        if not self.ldap_uri:
            return False
        
        print "Trying to auth by ldap", user, password

        c = self.app.datamgr.get_contact(user)

        if not c:
            print "Ldap : invalid user (not founded)", user
            return False

        # first we need to find the principalname of this entry
        # because it can be a user name like j.gabes, but we should auth by ldap
        # with j.gabes@google.com for example
        elts = self.find_contact_entry(c)
	print elts
        try :
            account_name = elts['dn']
        except KeyError:
            print "Cannot find the uid entry, so use the user entry"
            account_name = user

        local_con = ldap.initialize(self.ldap_uri)
        local_con.set_option(ldap.OPT_REFERRALS,0)
        
        # Any errors will throw an ldap.LDAPError exception
        # or related exception so you can ignore the result
        try:
            local_con.simple_bind_s(account_name, password)
            print "Ldap Connection done with", user, password
            return True
        except ldap.LDAPError, exp:
            print "LMdap auth error:", exp
        
        # The local_con will automatically close this connection when 
        # the object will be deleted, so no close need

        # No good? so no auth :)
        return False
        
