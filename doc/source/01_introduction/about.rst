.. _introduction/about:


==============
About Shinken
==============

Shinken is an open source monitoring framework written in Python under the terms of the `GNU Affero General Public License`_ .
It was created in 2009 as a simple proof of concept of a `Nagios`_ patch. The first release of Shinken was the December 1st of 2009 as simple monitoring tool.
Since the 2.0 version (April 2014) Shinken is described as a monitoring framework due to its high number of modules.
For the same reason, module are now in separated repositories. You can find some in the `shinken-monitoring organization's page`_ on Github



Shinken Project
================

Shinken is now an open source monitoring *framework* but was first created to be a open source monitoring *solution*.
This difference is important for the team, a framework does not have the same use than a all in one solution.
The main idea when developing Shinken is the flexibility which is our definition of framework.
Nevertheless, Shinken was first made differently and we try to keep all the good things that made it a monitoring solution :
   * Easy to install : install is mainly done with pip but some packages are available (deb / rpm) and we are planning to provide nightly build.
   * Easy for new users : once installed, Shinken provide a simple command line interface to install new module and packs.
   * Easy to migrate from Nagios : we want Nagios configuration and plugins to work in Shinken so that it is a "in place" replacement.
     Plugins provide great flexibility and are a big legacy codebase to use. It would be a shame not to use all this community work
   * Multi-platform : python is available in a lot of OS. We try to write generic code to keep this possible.
   * Utf8 compliant : python is here to do that. For now Shinken is compatible with 2.6-2.7 version but python 3.X is even more character encoding friendly.
   * Independent from other monitoring solution : our goal is to provide a modular *tool* that can integrate with others through standard interfaces). Flexibility first.
   * Flexible : in a architecture point view. It is very close to our scalability wish. Cloud computing is make architecture moving a lot, we have to fit to it.
   * Fun to code : python ensure good code readability. Adding code should not be a pain when developing.

This is basically what Shinken is made of. Maybe add the "keep it simple" Linux principle and it's prefect. There is nothing we don't want, we consider every features / ideas.


Features
=========

.. note:: This list should be enhanced to be more readable.


Shinken has a lot of features, we started to list some of them in the last paragraph. Let's go into details :

  * Shinken is a true distributed applications which splits the different roles into separate daemons
  * Shinken permits the use of modules to extend and enrich the various Shinken daemons
  * Shinken is 100% python, from its API, frontend, back-end, discovery engine and high performance poller modules
  * Scalability

    * Shinken has a powerful scheduler for supervising tens of thousands of devices
    * Shinken can supervise multiple independent environments/customers

  * Graphical and statistical analysis :  Shinken provides integration with the modern time series database, Graphite

  * Correlation

    * Shinken differentiates the business impact of a critical alert on a toaster versus the web store
    * Shinken supports efficient correlation between parent-child relationship and business process rules

  * Use Shinken and Graphite seamlessly in the Shinken WebUI.  v1.2
  * Export data from Shinken to Graphite and manipulate the data point names with PRE, POST, and SOURCE variables
  * Buffered output to Graphite.
  * Multiple Graphite destination servers.
  * Use check_graphite to poll graphite and generate alerts.
  * Use wildcards in checks against Graphite.
  * Auto-detection, logging and semi-automatic registration of new passive checks. Planned for v1.4
  * Mix and match frontends(Multisite, Nagvis), plugins, alerting(Pagerduty), analysis (Splunk, Logstash, Elastic Search, Kibana)
  * Modern, Scalable, HA and distributed out of the box.
  * Business rules, business impacts levels integrated in the core.
  * The code is approachable for sys admins to improve and customize the core and manage additions using modules.
  * Supervision packs(templates+commands+etc) and community
  * A powerful and efficient dependency model that does event suppression. Not as flexible as the great Zabbix calculated items, but suffers from much less false positives, which is the whole point, especially at 3am.
  * Uses the Graphite time-series database, which is hands-down one of the most modern, easy to use, fast, powerful  and flexible time-series databases. None of the slooowness associated with scaling a SQL based storage for time-series.
  * The code is approachable for sys admins to improve and customize the core and using modules.
  * The new SNMP poller is more intelligent and efficient in its collection against remote devices. Zabbix collects each metric as it is scheduled, so IN/OUT stats of the same interface could be collected at two different times, errr, say what!
  * A working dependency model that does good and efficient event suppression and correlation.
  * 100% open-source...
  * Can you say Graphite integration, MongoDB, distributed architecture and seamless HA.



.. _Nagios: http://www.nagios.org
.. _GNU Affero General Public License: http://www.gnu.org/licenses/agpl.txt
.. _Shiken-Monitoring' page: https://github.com/shinken-monitoring