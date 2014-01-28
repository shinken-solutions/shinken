.. _prerequisites_1_2:



==============================
Prerequisites for Shinken 1.2 
==============================


This page lists the prerequisites of shinken. A packager can use these dependencies when creating a package for his distribution and others can use it as a reference when installing on a new OS which is unsupported until now.




Build Dependencies for certain modules 
---------------------------------------

These packages are only needed if one or more of the required modules are not contained in the distros repositories or only in a version that is not sufficiently high enough.

The package names are from Debian/Ubuntu, please adapt as needed
  * build-essential
  * libperl-dev
  * libsqlite3-dev
  * python-dev
  * libmysqlclient-dev
  * libevent-dev
  * python-setuptools



Core, Libs and Modules 
-----------------------


  * Python >= 2.4 for CORE
  * Python >= 2.6 for WebUI and Skonf 
  * Pyro >= 4.0, if possible 4.9 or 4.14
  * pysqlite:sqlite3  >= <version> for livestatus
  * MySQL_python:MySQLdb >= <version> for ndomod
  * pymongo >= 2.1 : for WebUI
  * pycurl for Skonf configuration  pack management

  * paramiko (only if you use installer script)
  * netifaces (only if you use installer script)




Optional Python Modules for Extended Features 
----------------------------------------------


  * kombu : only if you use canopsis module
  * simplejson : only if python 2.5 used
  * python-ldap : active directory authentication (needed by Shinken WebUI ActiveDir_UI module)
  * ujson : `ujson`_ (preferred by Livestatus over simplejson)
  * Python >= 2.7 for running the Shinken Test Suite. **This is mandatory for developers.**


Additional Software 
--------------------

  * sqlite3
  * nmap : for discovery feature
  * unzip
  * nagios-plugins
  * mongodb
.. _ujson: http://pypi.python.org/pypi/ujson/