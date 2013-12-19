.. _the_broker_modules:



Broker modules 
===============


The broker module receives messages from the Schedulers related to host, service check results. In addition to that it receives a copy of the compiled configuration at startup. What is special about the broker, is that without modules, the broker does nothing. It makes the configuration and result data available to modules. Modules are the ones in charge of doing something with the data. This could be exporting this "raw" data into flat files, databases or exposing it as an API.

The modules are presented according to their use cases.

  * Core modules
  * Livestatus Module for frontends
  * Exporting data to metric databases
  * SQL based Modules for frontends
  * Exporting data to logging management systems
  * Legacy modules for migration purposes
  * Modules no longer supported



Core modules 
-------------




simple_log: get all logs into one file 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can get a log for all your daemons in a single file. With the exception of Debug level logs which are not sent through the network as a safe guard.
Shinken state messages are ONLY logged at the debug level in the local log files. These are the ALL CAPS states that some 3rd party interfaces use to mine data from the historical logs. Actual state messages are sent as objects between the various daemons.

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: simple_log
    * path: path of the log file

Here is an example:
  
::

  
  define module{
  
::

       module_name      Simple-log
       module_type      simple_log
       path             /usr/local/shinken/var/nagios.log
       archive_path     /usr/local/shinken/var/archives/
  }




Syslog - Send all logs to a local syslog server 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Send all logs to a local syslog server. Support for remote syslog can be implemented
if requested. Just lookup the syslog module, easy to modify. Use for example with Splunk, graylog2, Logstash, Elastic search, Kibana, or other log management and analysis system.
  
::

  
  define module{
  
::

    module_name Syslog
    module_type syslog
  }




Lightweight forwarder to Splunk 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Shinken state data from the local syslog can also be sent to a Splunk server for indexing, reports, SLA and analysis. Via syslog or better yet, the Splunk lightweight forwarder which supports, TCP, buffering and security parameters.



Livestatus API Module - Thruk, Nagvis and Multisite Web frontends 
------------------------------------------------------------------


There are three well known frontends and various small tools that can interface with the Livestatus API. This API is currently the most efficient method
of sharing live data with external interfaces. It provides a rich query language similar to SQL, authentication, command execution, caching,connections persistence, multiple object methods (JSON, Python). All Livestatus data is kept in memory, there is no disk IO involved. It exposes configuration objects, the current state of the hosts and services as well as historical Shinken state log messages.

  * MK Multisite
  * Thruk
  * NagVis

Have you installed the required packages to use the Livestatus module? You can look at the requirement section of the 10 minute installation guide for the requirement lists.



Livestatus Module 
~~~~~~~~~~~~~~~~~~


It takes the following parameters:
    * module_name: name of the module called by the brokers
    * module_type: livestatus
    * host: IP interface to listen to. The default is '127.0.0.1'. '*' means 'listen on all interfaces'.
    * port: TCP port to listen to. 
    * socket: Unix socket to listen to.
    * allowed_hosts: a comma-separated list of IP-addresses which are allowed to contact the TCP port. Please keep in mind that these must be ip-addresses, NOT host names. (DNS lookups for every incoming livestatus request could hang up and therefore block the module)
    * modules: a comma-separated list of modules (see below)
    * pnp_path: relevant if you use the multisite gui. pnp_path points to the perfdata directory where the pnp4nagios data reside (it's the directory which contains a subdirectory for each host). Multisite needs it to display a small perfdata icon if a rrd file exists.
    * To deactivate an input, the port- and socket-attributes can also take the value "none".

The Livestatus module itself can have sub-modules. In fact, it **must** have at least one submodule responsible for storing log events to a database, SQLite or MongoDB. 



Livestatus module - Logstore Sqlite 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Stores log-broks to an sqlite database.

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: logstore_sqlite
    * use_aggressive_sql: Prefer the use of sql queries to pre-filter data prior to python filtering. This is required for very large installations, as the Python  structures are not indexed when filtering. Optional argument set to 0 by default. To enable set the value to 1. Some erroneous output may occur, but informal testing has shown these corner cases do not occur.
    * read_only: don't send any update to the database. Should be used when you run several livestatus modules : 1 instance is R/W, other are read only.
    * database_file: the path to the sqlite database file which is used to store the log broks/messages. The default is 'var/livestatus.db'
    * archive_path: the path to a subdirectory where database file archives will be created. Every day the data from the last day will be moved to an archive datafile. The default is 'var/archives'.
    * max_logs_age: the maximum age of the log messages (before they are deleted from the database). The default is 1 year. The argument to this parameter takes the form <number>[<period of time>], where <period of time> can be d for days, w for weeks, m for months and y for years. This parameter is currently ignored. In future releases it will be used to automatically delete ancient database files.


Here is an example:
  
::

  
  define module{
  
::

       module_name      Livestatus
       module_type      livestatus
       host             *       ; * = listen on all configured ip addresses
       port             50000   ; port to listen
       socket           /usr/local/shinken/var/rw/live
       modules          logsqlite
  }
  define module{
  
::

       module_name      logsqlite
       module_type      logstore_sqlite
       use_aggressive_sql     0 ; optional, by default set to 0. Only for large installations.
       database_file    /usr/local/shinken/var/livelogs.db
       max_logs_age     3m ; three months. Other time intervals are d=days, w=weeks, y=years
  }




Livestatus module - Logstore MongoDB 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Stores historical log broks(inter daemon Shinken messages) to a MongoDB database. MongoDB is a distributed and very performant database that permits resilience and high availability. The current implementation has a few known broken pieces (some search functions are broken) and there are bugs in the implementation, so it is considered experimental until power users and developers have ironed out the bugs. It is the database of the future for Shinken.

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: logstore_mongodb
    * mongodb_uri: The address of the master. (Default: i_cant_write_the_uri_here_it_messes_the_wiki_up) 
    * replica_set: If you are running a MongoDB cluster (called a "replica set" in MongoDB), you need to specify it's name here. With this option set, you can also write the mongodb_uri as a comma-separated list of host:port items. (But one is enough, it will be used as a "seed")
    * database: <undocumented>
    * collection: <undocumented>
    * max_logs_age: <undocumented>

The configuration looks quite similar to the sqlite one. **In a single-node installation and with decent amount of log traffic, the sqlite backend should be considered best practice, as it needs no extra software and is stable and fast (when run in-memory).**



Livestatus module - Logstore Null 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


In case you don't need any logging (for instance, if you dedicate a livestatus module instance to nagvis), you can use this module.

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: logstore_null


.. _the_broker_modules#network_based_modules_-_graphite_graphing:

Network Based Modules - Graphite graphing 
------------------------------------------


Graphite is a graphing and data analysis tool. It is composed of a web frontend (graphite-web), fixed size databases (whisper) and data redistribution/munging daemon. (carbon) The first step is :ref:`having Graphite installed somewhere <use_with_graphite>`, if you do not have Graphite installed, please do this and come back later.

Pre-requisite : Shinken 1.2.2+ is recommended for the best experience with Graphite.



graphite_perfdata: exports check result performance data to Graphite 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Export all performance data included in check results to Whisper databases managed by Graphite. Data is buffered, then exported once every broker time tick. (Once per second). Should a communication loss occur, it will buffer data for 5 minutes before dropping data. The tick_limit max is configurable, the only limitation is the amount of memory the buffered data can eat.

The graphite broker module (v1.2) sends data to graphite in the following format :

   HOSTNAME.SERVICENAME.METRICNAME
  
It can be optionally enhanced to send it the following format :

   _GRAPHITE_PRE.HOSTNAME.SOURCE.SERVICENAME.METRICNAME._GRAPHITE_POST
  
Each of the three variables are optional :

  * The _GRAPHITE_PRE variable can be set per host/service to provide a more flexible naming convention. (ex. Prod.site1.Hostname.servicename)
  * The _GRAPHITE_POST variable can be set per host/service to specify the more information concerning the variable being stored that graphite can use to determine the retention rule to use for the variable.
  * The SOURCE variable can be set in shinken-specific.cfg for the WebUI module and the Graphite broker.

Metric names are converted from Shinken's format to a more restrictive Graphite naming. Unsupported characters are converted to "_" underscore. So do not be surprised to see that some names differ in the WebUI or directly in Graphite. Permitted characters in Graphite are "A-Za-z_.", the hyphen character is permitted from Shinken, though only future versions of Graphite will support it.

Performance data transfer method can be set to pickle, which is a binary format that can send data more efficiently than raw ascii.

It takes the following parameters:
    * module_name:   name of the module called by the brokers
    * module_type:   graphite_perfdata
    * host:          ip address of the graphite server running a carbon instance
    * port:          port where carbon listens for metrics (default: 2003 for raw socket, 2004 for pickle encoded data)
    * use_pickle:    Use a more efficient transport for sending check results to graphite instead of raw data on the socket (v1.2)
    * tick_limit:    Number of ticks to buffer performance data during a communication outage with Graphite. On tick limit exceeded, flush to /dev/null and start buffering again. (v1.2)
    * graphite_data_source:    Set the source name for all data coming from shinken sent to Graphite. This helps diferentiate between data from other sources for the same hostnames. (ex. Diamond, statsd, ganglia, shinken) (v1.2)

Here is an example:
  
::

  
  define module {
  
::

  module_name Graphite-Perfdata
  host xx.xx.xx.xx
  module_type graphite_perfdata
  port 2004 ; default port 2003 for raw data on the socket, 2004 for pickled data
  use_pickle 1 ; default value is 0, 1 for pickled data
  tick_limit 300 ; Default value 300
  graphite_data_source shinken ; default is that the variable is unset
  }




SQL Based Modules - PNP4Nagios Graphing 
----------------------------------------


PNP4Nagios is a graphing tool that has a web interface for RRDTool based databases. Shinken can export performance data to an npcd database which will feed the RRD files (fixed sized round robin databases). You can :ref:`learn how to install PNP4Nagios <use_with_pnp>` if you haven't done it already.



npcdmod: export perfdatas to a PNP interface 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Export all perfdata for PNP.

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: npcdmod
    * path: path to the npcd config file
Here is an example:
  
::

  
  define module{
   module_name  NPCD
   module_type  npcdmod
   config_file  /usr/local/pnp4nagios/etc/npcd.cfg
  }





SQL Based Modules - Frontend Centreon2 
---------------------------------------


Centreon2 use a NDO database, so you will need the ndodb_mysql module for it.



ndodb_mysql: Export to a NDO Mysql database 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Export status into a NDO/Mysql database. It needs the python module MySQLdb (apt-get install python-mysqldb or easy_install MySQL-python).

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: ndodb_mysql
    * database: database name (ex ndo)
    * user: database user 
    * password: database user passworddt
    * host: database host
    * character_set: utf8 is a good one

Here is an example:
  
::

  
  define module{
  
::

       module_name      ToNdodb_Mysql
       module_type      ndodb_mysql
       database         ndo       ; database name
       user             root      ; user of the database
       password         root      ; must be changed
       host             localhost ; host to connect to
       character_set    utf8      ;optionnal, UTF8 is the default
  }









File based Legacy modules - perfdata export 
--------------------------------------------




service_perfdata: export service perfdatas to a flat file 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: service_perfdata
    * path: path to the service perfdata file you want

Here is an example:
  
::

  
  define module{
  
::

       module_name      Service-Perfdata
       module_type      service_perfdata
       path             /usr/local/shinken/src/var/service-perfdata
  }




host_perfdata: export host perfdatas to a flat file 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: host_perfdata
    * path: path to the host perfdata file you want

Here is an example:
  
::

  
  define module{
  
::

       module_name      Host-Perfdata
       module_type      host_perfdata
       path             /usr/local/shinken/src/var/host-perfdata
  }





Legacy File based Modules - Old CGI or VShell 
----------------------------------------------


The Old CGI and VShell use the flat file export. If you can, avoid it! It has awful performance, all modern UIs no longer use this.



status_dat: export status into a flat file 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Export all status into a flat file in the old Nagios format. It's for small/medium environment because it's very slow to parse. It can be used by the Nagios CGI. It also export the objects.cache file for this interface.

It takes the parameters:
    * module_name: name of the module called by the brokers
    * module_type: status_dat
    * status_file: path of the status.dat file            /usr/local/shinken/var/status.dat
    * object_cache_file: path of the objects.cache file
    * status_update_interval: interval in seconds to generate the status.dat file
  
::

       
Here is an example:
  
::

  
  define module{
  
::

       module_name              Status-Dat
       module_type              status_dat
       status_file              /usr/local/shinken/var/status.data
       object_cache_file        /usr/local/shinken/var/objects.cache
       status_update_interval   15 ; update status.dat every 15s
  }








Deprecated or unsupported modules 
----------------------------------




SQL Based MerlinDB 
~~~~~~~~~~~~~~~~~~~


This interface is no longer supported and is going to be completely removed from Shinken.



SQL based ndodb_oracle - Icinga web frontend using NDO Oracle 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


This interface is no longer supported and is going to be completely removed from Shinken.



CouchDB: Export to a Couchdb database 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


This interface is no longer supported and is going to be completely removed from Shinken.
