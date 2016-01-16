.. _introduction/about:


==============
About Shinken
==============

Shinken is an open source monitoring framework written in Python under the terms of the `GNU Affero General Public License`_.  It was created in 2009 as a simple proof of concept of a `Nagios`_ patch. The first release of Shinken was the December 1st of 2009 as simple monitoring tool.  Since the 2.0 version (April 2014) Shinken is described as a monitoring framework due to its high number of modules.  For the same reason, modules are now in separated repositories. You can find some in the `shinken-monitoring organization's page`_ on Github.



The Shinken Project
===================

Shinken is now an open source monitoring *framework*, but was first created to be a open source monitoring *solution*.
This difference is important for the team, a framework does not have the same use than an all in one solution.
The main idea when developing Shinken is the flexibility which is our definition of framework.  Nevertheless, Shinken was first made differently and we try to keep all the good things that made it a monitoring solution:
   * Easy to install: install is generally done with pip, but some packages are available (deb / rpm) and we are planning to provide nightly builds.
   * Easy for new users: once installed, Shinken provides a simple command line interface to install new modules and packs.
   * Easy to migrate from Nagios: we want Nagios configuration and plugins to work in Shinken, so that it is a "in place" replacement.
     Plugins provide great flexibility and are a big legacy codebase to use. It would be a shame not to use all this community work.
   * Multi-platform:  Python is available for many Operating Systems.  We try to write generic code to keep this possible.
   * Utf8 compliant:  Python is here to do that.  Shinken is currently compatible with Python 2.6-2.7 version, but Python 3.X is even more character encoding friendly.
   * Independent from other monitoring solutions:  Our goal is to provide a modular *tool* that can integrate with others through standard interfaces). Flexibility first.
   * Flexible:  From an architecture point of view, scalability is our first design principle.  Cloud computing is make architecture moving a lot, we have to fit to it.
   * Fun to code:  Python ensures good code readability.  Adding code should not be a pain when developing.

This is basically what Shinken is made of.  Maybe add the "keep it simple" Linux principle and it is prefect.  There is nothing we don't want, we consider every features / ideas.


Features
=========

Shinken has a lot of featuress, we started to list some of them in the last paragraph. Let us go into detail:

  * Role separated daemons:  we want a daemon to do one thing, and one thing well.  There are 6 of them but one is not compulsory.
  * Great flexibility:  you didn't get that already?  Shinken modules allow it to talk to almost everything you can imagin.

  Those to points involve all the following:

  * Data export to databases:

      * Graphite
      * InfluxDB
      * RRD
      * GLPI
      * CouchDB
      * Livestatus  (MK_Livestatus reimplementation)
      * Socket write for other purpose (Splunk, Logstash, Elastic Search)
      * MySQL (NDO reimplementation)
      * Oracle (NDO reimplementation)

  * Integration with web user interfaces:

      * WebUI (Shinken own User Interface: https://github.com/shinken-monitoring/mod-webui/wiki)
      * Thruk
      * Adagios
      * Multisite
      * Nagvis
      * PNP4Nagios
      * NConf
      * Centreon (With NDO, not fully working, not recommended)


  * Import config from databases:

      * GLPI
      * Amazon EC2
      * MySQL
      * MongoDB
      * Canonical Landscape


  * Shinken provides sets of configurations, named packs, for a huge number of services:

      * Databases (Mysql, Oracle, MSSQL, memcached, mongodb, influxdb etc.)
      * Routers, Switches (Cisco, Nortel, Procurve etc.)
      * OS (Linux, windows, Aix, HP-UX etc.)
      * Hypervisors (VMWare, Vsphere)
      * Protocols (HTTP, SSH, LDAP, DNS, IMAP, FTP, etc.)
      * Application (Weblogic, Exchange, Active Directory, Tomcat, Asterisk, etc.)
      * Storage (IBM-DS, Safekit, Hacmp, etc.)

  * Smart SNMP polling:  The SNMP Booster module is a must have if you have a huge infrastructure of routers and switches.

  * Scalability: no server overloading, you just have to install new daemons on another server and load balancing is done.


  But Shinken is even more:

  * Realm concept: you can monitor independent environments / customers.
  * DMZ monitroing: some daemon have passive facilities, so that firewalls don't block monitoring.
  * Business impacts:  Shinken can differentiate impact of a critical alert on a toaster versus the web store.
  * Efficient correlation between parent-child relationship and business process rules.
  * High availability:  daemons can have spare ones.
  * Business rules:  For a higher level of monitoring, Shinken can notify you only if 3 out 5 of your server are down
  * Very open-minded team:  help and suggestions are always welcome.


Release cycle
==============


The Shinken team is setting up a new release cycle with an objective of 4 release per year.
Each release is divided into three parts:  re-factoring (few weeks), features (one month), freezing (one month).
Roadmap is available in a `specific Github issue`_, feature addition can be discussed there.
The technical point of view about a specific feature is discussed in a separate, individual issue.


Release code names
===================

Jean Gabès keeps the right to name the code-name of each release.  That is the only thing Jean will keeps for himself in this project as its founder. :)


.. _Nagios: http://www.nagios.org
.. _GNU Affero General Public License: http://www.gnu.org/licenses/agpl.txt
.. _shinken-monitoring organization's page: https://github.com/shinken-monitoring
.. _specific Github issue: https://github.com/naparuba/shinken/labels/CURRENT%20ROADMAP
