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
This class is for linking the WebUI with active directory,
like check passwords, or get photos.
"""

import os

try:
    import ldap
except ImportError:
    ldap = None

from shinken.log import logger
from shinken.basemodule import BaseModule

logger.info ("Loading the AD module")

properties = {
    'daemons': ['webui', 'skonf'],
    'type': 'ad_webui'
    }


# called by the plugin manager
def get_instance(plugin):
    logger.debug("Get an Active Directory/OpenLdap UI module for plugin %s" % plugin.get_name())
    if not ldap:
        raise Exception('The module python-ldap is not found. Please install it.')
    instance = AD_Webui(plugin)
    return instance


class AD_Webui(BaseModule):
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
        # Switch between active directory and OpenLdap mode
        self.mode = getattr(modconf, 'mode', 'ad')
        if self.mode not in ['ad', 'openldap']:
            raise Exception('WebUI Auth ldap module error, mode is not in ad or openldap')

        self.retrieveAttributes = {
            'ad' : ["userPrincipalName", "thumbnailPhoto", "samaccountname", "email"],
            'openldap' : ["cn", "jpegphoto", "uid", "mail"]
            }[self.mode]
        self.photo_attr = {
            'ad' : 'thumbnailPhoto',
            'openldap' : 'jpegPhoto'
            }[self.mode]
        self.name_id = {
            'ad' : 'userPrincipalName',
            'openldap' : 'uid'
            }[self.mode]
        self.auth_key = {
            'ad' : 'userPrincipalName',
            'openldap' : 'dn'
            }[self.mode]
        self.search_format = {
            'ad' : "(| (samaccountname=%s)(mail=%s))",
            'openldap' : "(| (uid=%s)(mail=%s))"
            }[self.mode]
        

    # Try to connect if we got true parameter
    def init(self):
        if not self.active:
            return
#        self.connect()

    def connect(self):
        logger.debug("Trying to initalize the AD/Ldap connection")
        self.con = ldap.initialize(self.ldap_uri)
        self.con.set_option(ldap.OPT_REFERRALS, 0)

        print "Trying to connect to AD/Ldap", self.ldap_uri, self.username, self.password, self.basedn
        # Any errors will throw an ldap.LDAPError exception
        # or related exception so you can ignore the result
        self.con.simple_bind_s(self.username, self.password)
        print "AD/Ldap Connection done"


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

        print "AD/LDAP: search for contact", contact.get_name()
        searchScope = ldap.SCOPE_SUBTREE
        ## retrieve all attributes
        #retrieveAttributes = ["userPrincipalName", "thumbnailPhoto", "samaccountname", "email"]

        cname = contact.get_name()
        email = contact.email
        searchFilter = self.search_format % (cname, email)
        print "Filter", searchFilter
        try:
            ldap_result_id = self.con.search(self.basedn, searchScope, searchFilter, self.retrieveAttributes)
            result_set = []
            while 1:
                result_type, result_data = self.con.result(ldap_result_id, 0)
                if (result_data == []):
                    print "No result for", cname
                    return None

                if result_type == ldap.RES_SEARCH_ENTRY:
                    (_, elts) = result_data[0]
                    try:
                        account_name = elts[self.name_id][0]
                    except Exception:
                        account_name = str(result_data[0])
                    # Got a result, try to get photo to write file
                    print "Find account printicpalname", account_name
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
        print "AD/LDAP: manage_initial_broks_done_brok, go for pictures"

        searchScope = ldap.SCOPE_SUBTREE
        ## retrieve all attributes - again adjust to your needs - see documentation for more options
        #retrieveAttributes = ["userPrincipalName", "thumbnailPhoto", "samaccountname", "email"]

        print "Contacts?", len(self.app.datamgr.get_contacts())

        for c in self.app.datamgr.get_contacts():
            print "Doing photo lookup for contact", c.get_name()
            elts = self.find_contact_entry(c)

            if elts is None:
                print "No ldap entry for", c.get_name()
                continue

            # Ok, try to get photo from the entry
            try:
                photo = elts[self.photo_attr][0]
                try:
                    p = os.path.join(self.app.photo_dir, c.get_name()+'.jpg')
                    f = open(p, 'wb')
                    f.write(photo)
                    f.close()
                    print "Phto wrote for", c.get_name()
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
            print "AD/Ldap: invalid user (not founded)", user
            return False

        # first we need to find the principalname of this entry
        # because it can be a user name like j.gabes, but we should auth by ldap
        # with j.gabes@google.com for example
        elts = self.find_contact_entry(c)

        try:
            # On AD take the uid / principalename
            if self.mode == 'ad':
                account_name = elts[self.auth_key][0]
            else: # For openldap, use the full DN
                account_name = elts[self.auth_key]
        except KeyError:
            print "Cannot find the %s entry, so use the user entry" % self.auth_key
            account_name = user

        local_con = ldap.initialize(self.ldap_uri)
        local_con.set_option(ldap.OPT_REFERRALS, 0)

        # Any errors will throw an ldap.LDAPError exception
        # or related exception so you can ignore the result
        try:
            local_con.simple_bind_s(account_name, password)
            print "AD/Ldap Connection done with", user, password
            return True
        except ldap.LDAPError, exp:
            print "Ldap auth error:", exp

        # The local_con will automatically close this connection when
        # the object will be deleted, so no close need

        # No good? so no auth :)
        return False
