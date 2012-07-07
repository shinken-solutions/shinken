<?php
##
## Authentication
##

#
# Enable or disable user authentication.
# If disabled, no login is prompted to access the GUI and all features will be available (admin privs).
#
define('AUTH_ENABLED', '0');

#
# How to authenticate, if authentication is enabled.
# possible values: [file|sql|ldap|ad_ldap]
#
define('AUTH_TYPE', "file");

#
# Select the login authentication method
# possible values: [login|basic]
# 'login' = authenticate using the ordinary NConf login form
# 'basic' = authenticate using HTTP Basic Authentication (pop-up window for username/password)
#
define('AUTH_METHOD', 'login');

# The HTTP Basic Auth Realm to display when using auth method "basic"
define('BASICAUTH_REALM',  "NConf Basic Auth");

#
# Defines the user name in the history table and in the welcome message.
#If set to "0", the username will be used. If set to "1", the real name will be fetched, depending on which AUTH_TYPE you selected.
#
define('AUTH_FEEDBACK_AS_WELCOME_NAME', '1');

# Groups
define('GROUP_USER',       "user");
define('GROUP_ADMIN',      "admin");
define('GROUP_NOBODY',     "0");

###
###  Auth by "ldap"
###

### LDAP (the tree design must be pam_ldap and nss_ldap compliant)
define('LDAP_SERVER',      "ldaps://ldaphost.mydomain.com");
# The port to connect to. Not used when using URLs. Defaults to 389. (by PHP)
define('LDAP_PORT',        "389");

define('BASE_DN',          "uid=<username>,ou=People,dc=mydomain,dc=com");
define('USER_REPLACEMENT', "<username>");
define('GROUP_DN',         "ou=Group,dc=mydomain,dc=com");
define('ADMIN_GROUP',      "cn=nagiosadmin");
define('USER_GROUP',       "cn=sysadmin");

###
###  Auth by "ad_ldap"
###

### Active Directory
define('AD_LDAP_SERVER',        "ldap://ad-ldaphost.mydomain.com");
define('AD_LDAP_PORT',          "389");
define('AD_BASE_DN',            "CN=<username>,OU=All,OU=Users,DC=my,DC=domain,DC=com");
define('AD_USER_REPLACEMENT',   "<username>");
define('AD_GROUP_ATTRIBUTE',    "memberof");
define('AD_USERNAME_ATTRIBUTE', "displayname");

# if AD_GROUP_DN ist the same for admin and user group:
define('AD_GROUP_DN',           "OU=Group,DC=my,DC=domain,DC=com");
define('AD_ADMIN_GROUP',        "CN=nagiosadmin");
define('AD_USER_GROUP',         "CN=sysadmin");
# if AD_GROUP_DN differs for admins and users:
# you can define FIX GROUPS: (needs empty GROUP_DN)
//define('AD_GROUP_DN',         "");
//define('AD_ADMIN_GROUP',         "CN=nagiosadmin,OU=Group,DC=my,DC=domain,DC=com");
//define('AD_USER_GROUP',          "CN=sysadmin,OU=Group,DC=my,DC=domain,DC=com");

###
###  Auth by "sql"
###

# Use external database (can be any mysql DB)
# if you want to use the NConf DB, leave it commented
//define('AUTH_DBHOST',       "localhost");
//define('AUTH_DBNAME',       "NConf");
//define('AUTH_DBUSER',       "nconf");
//define('AUTH_DBPASS',       "link2db");

# Custom SQL query to run in the user database.
# The query should return exactly one (1) record if:
# - the username exists
# - the password is correct
# - any additional attrs are set (optional for permission check etc.)

# INFO:
# The following queries are examples. They allow user authentication to be managed
# within the NConf DB itself. To enable this, you must configure additional attributes in
# the "contact" class (refer to the documentation for more details).
# Feel free to define your own queries, if you want to access any other existing user database.

#
# if query matches, user will get limited access, for "normal users"
# !!!USERNAME!!! and !!!PASSWORD!!! will be replaced with the username and password from login page
#
define('AUTH_SQLQUERY_USER',     '
SELECT attr_value AS username, id_item AS user_id
  FROM ConfigAttrs,ConfigValues,ConfigItems
 WHERE id_attr=fk_id_attr
 AND id_item=fk_id_item
 AND attr_name="alias"
  HAVING id_item =(SELECT id_item FROM ConfigAttrs,ConfigValues,ConfigItems
   WHERE id_attr=fk_id_attr
   AND id_item=fk_id_item
   AND id_item=user_id
   AND attr_name="contact_name"
   AND attr_value="!!!USERNAME!!!")
  AND id_item =(SELECT id_item FROM ConfigAttrs,ConfigValues,ConfigItems
   WHERE id_attr=fk_id_attr
   AND id_item=fk_id_item
   AND id_item=user_id
   AND attr_name="user_password"
   AND attr_value="!!!PASSWORD!!!")
  AND id_item =(SELECT id_item FROM ConfigAttrs,ConfigValues,ConfigItems
   WHERE id_attr=fk_id_attr
   AND id_item=fk_id_item
   AND id_item=user_id
   AND attr_name="nc_permission"
   AND attr_value="'.GROUP_USER.'");
');

#
#  ::OPTIONAL:: Define ADMIN access here:
# if query matches, user will get FULL ADMIN access, for Administrators
#
define('AUTH_SQLQUERY_ADMIN',     '
SELECT attr_value AS username, id_item AS user_id
  FROM ConfigAttrs,ConfigValues,ConfigItems
 WHERE id_attr=fk_id_attr
 AND id_item=fk_id_item
 AND attr_name="alias"
  HAVING id_item =(SELECT id_item FROM ConfigAttrs,ConfigValues,ConfigItems
   WHERE id_attr=fk_id_attr
   AND id_item=fk_id_item
   AND id_item=user_id
   AND attr_name="contact_name"
   AND attr_value="!!!USERNAME!!!")
  AND id_item =(SELECT id_item FROM ConfigAttrs,ConfigValues,ConfigItems
   WHERE id_attr=fk_id_attr
   AND id_item=fk_id_item
   AND id_item=user_id
   AND attr_name="user_password"
   AND attr_value="!!!PASSWORD!!!")
  AND id_item =(SELECT id_item FROM ConfigAttrs,ConfigValues,ConfigItems
   WHERE id_attr=fk_id_attr
   AND id_item=fk_id_item
   AND id_item=user_id
   AND attr_name="nc_permission"
   AND attr_value="'.GROUP_ADMIN.'");
');

?>
