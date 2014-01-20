.. _shinken_innovative_features:



Shinken notable innovations 
============================



Summary 
--------

  * Shinken is a true distributed applications which splits the different roles into separate daemons
  * Shinken permits the use of modules to extend and enrich the various Shinken daemons
  * Shinken is 100% python, from its API, frontend, back-end, discovery engine and high performance poller modules

  * Scalability
    * Shinken has a powerful scheduler for supervising tens of thousands of devices v1.2
    * Shinken can supervise multiple independent environments/customers
    * Shinken uses MongoDB to provide a distributed and highly scalable back-end for storing historical event data (experimental)

  * Graphical and statistical analysis
    * Shinken provides integration with the modern time series database, Graphite
    * Shinken provides triggers against performance or event data in the core and in external checks (experimental) v1.2

  * Correlation
    * Shinken differentiates the business impact of a critical alert on a toaster versus the web store
    * Shinken supports efficient correlation between parent-child relationship and business process rules



Notable items for DevOps admins 
--------------------------------


  * Use Shinken and Graphite seamlessly in the Shinken WebUI.  v1.2
  * Export data from Shinken to Graphite and manipulate the data point names with PRE, POST, and SOURCE variables
  * Buffered output to Graphite.
  * Multiple Graphite destination servers.
  * Use check_graphite to poll graphite and generate alerts.
  * Use wildcards in checks against Graphite.
  * Auto-detection, logging and semi-automatic registration of new passive checks. Planned for v1.4
  * Mix and match frontends(Multisite, Nagvis), plugins, alerting(Pagerduty), analysis (Splunk, Logstash, Elastic Search, Kibana)



Notable items for Nagios admins 
--------------------------------


  * Modern, Scalable, HA and distributed out of the box.
  * Business rules, business impacts levels integrated in the core.
  * The code is approachable for sys admins to improve and customize the core and manage additions using modules.
  * Supervision packs(templates+commands+etc) and community
  * For a full comparison: `Shinken versus Nagios page`_.
  * Can you say Graphite integration..

Shinken *is* the modern Nagios, re-implemented in Python, end of story.



Notable items for Zabbix admins 
--------------------------------


  * A powerful and efficient dependency model that does event suppression. Not as flexible as the great Zabbix calculated items, but suffers from much less false positives, which is the whole point, especially at 3am.
  * Uses the Graphite time-series database, which is hands-down one of the most modern, easy to use, fast, powerful and flexible time-series databases. None of the slooowness associated with scaling a SQL based storage for time-series.
  * The code is approachable for sys admins to improve and customize the core and using modules.
  * The new SNMP poller is more intelligent and efficient in its collection against remote devices. Zabbix collects each metric as it is scheduled, so IN/OUT stats of the same interface could be collected at two different times, errr, say what!



Notable items for Zenoss admins 
--------------------------------


  * A working dependency model that does good and efficient event suppression and correlation.
  * 100% open-source...
  * Can you say Graphite integration, MongoDB, distributed architecture and seamless HA.

.. _Shinken versus Nagios page: http://www.shinken-monitoring.org/what-is-in-shinken-not-in-nagios-and-vice-versa/