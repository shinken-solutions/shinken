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
This class is for linking the WebUI with active directory,
like check passwords, or get photos.
"""

import ldap

from shinken.basemodule import BaseModule

print "Loaded AD module"

properties = {
    'daemons' : ['webui'],
    'type' : 'ad_webui'
    }


#called by the plugin manager
def get_instance(plugin):
    print "Get an Active Directory UI module for plugin %s" % plugin.get_name()
    
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

    # Try to connect if we got true parameter
    def init(self):
        if not self.active:
            return
        print "Trying to initalize the AD/Ldap connection"
        self.con = ldap.initialize(self.ldap_uri)
        self.con.set_option(ldap.OPT_REFERRALS,0)

        print "Trying to connect to AD/Ldap"
        # Any errors will throw an ldap.LDAPError exception
        # or related exception so you can ignore the result
        self.con.simple_bind_s(self.username, self.password)
        print "AD/Ldap Connection done"
        


    
